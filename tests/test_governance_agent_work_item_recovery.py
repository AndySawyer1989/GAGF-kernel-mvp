from datetime import timedelta

import pytest

from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowStore,
)
from backend.app.gagf.governance_agent_work_item_store import (
    AgentWorkItemConflictError,
    AgentWorkItemNotFoundError,
    AgentWorkItemStore,
)

from test_governance_agent_work_item_store import (
    TEST_NOW,
    claim_item,
    create_active_workflow,
    create_pending_item,
    make_stores,
)


def claim_and_start(work_item_store, *, now=TEST_NOW):
    claimed = claim_item(
        work_item_store,
        now=now,
    )

    started = work_item_store.start_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=claimed.fencing_token,
        idempotency_key="start-recovery-test",
        now=now + timedelta(seconds=1),
    )

    return claimed, started


def test_list_expired_work_items_is_tenant_scoped(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    claim_item(work_item_store, now=TEST_NOW)

    expired = work_item_store.list_expired_work_items(
        tenant_id="tenant-a",
        now=TEST_NOW + timedelta(seconds=61),
    )

    assert len(expired) == 1
    assert expired[0].work_item_id == "work-item-001"
    assert expired[0].state is WorkItemState.CLAIMED

    assert work_item_store.list_expired_work_items(
        tenant_id="tenant-b",
        now=TEST_NOW + timedelta(seconds=61),
    ) == []


def test_expired_claim_returns_to_pending_without_resetting_fence(
    tmp_path,
):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    first_claim = claim_item(work_item_store, now=TEST_NOW)

    recovered = work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-expired-claim",
        now=TEST_NOW + timedelta(seconds=61),
    )

    assert recovered.state is WorkItemState.PENDING
    assert recovered.attempt_count == 1
    assert recovered.fencing_token == first_claim.fencing_token
    assert recovered.assigned_worker_id is None
    assert recovered.lease_expires_at is None

    second_claim = work_item_store.claim_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-002",
        lease_seconds=60,
        idempotency_key="second-claim",
        now=TEST_NOW + timedelta(seconds=62),
    )

    assert second_claim.fencing_token == first_claim.fencing_token + 1
    assert second_claim.attempt_count == 2


def test_expired_running_item_enters_retry_wait(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    _, started = claim_and_start(work_item_store)

    recovery_time = TEST_NOW + timedelta(seconds=62)

    recovered = work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-expired-running",
        now=recovery_time,
    )

    assert recovered.state is WorkItemState.RETRY_WAIT
    assert recovered.available_at == recovery_time
    assert recovered.attempt_count == 1
    assert recovered.fencing_token == started.fencing_token
    assert recovered.assigned_worker_id is None
    assert recovered.lease_expires_at is None
    assert recovered.last_error_code == "LEASE_EXPIRED"


def test_retry_promotion_requires_due_time_and_is_idempotent(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    claim_and_start(work_item_store)

    recovery_time = TEST_NOW + timedelta(seconds=62)

    work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-before-promotion",
        now=recovery_time,
    )

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.promote_due_retry_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            idempotency_key="promote-too-early",
            now=recovery_time - timedelta(seconds=1),
        )

    promoted = work_item_store.promote_due_retry_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="promote-due-retry",
        now=recovery_time,
    )

    replay = work_item_store.promote_due_retry_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="promote-due-retry",
        now=recovery_time + timedelta(seconds=5),
    )

    assert promoted.state is WorkItemState.PENDING
    assert replay == promoted

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert [event.event_type for event in events] == [
        "work_item.created",
        "work_item.claimed",
        "work_item.started",
        "work_item.lease_recovered",
        "work_item.retry_promoted",
    ]


def test_expired_lease_at_attempt_limit_becomes_failed(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(
        work_item_store,
        max_attempts=1,
    )

    claim_item(work_item_store, now=TEST_NOW)

    failed = work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-exhausted",
        now=TEST_NOW + timedelta(seconds=61),
    )

    assert failed.state is WorkItemState.FAILED
    assert failed.attempt_count == 1
    assert failed.max_attempts == 1
    assert failed.last_error_code == "LEASE_EXPIRED_MAX_ATTEMPTS"
    assert failed.last_error_message
    assert failed.assigned_worker_id is None
    assert failed.lease_expires_at is None

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.claim_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            worker_id="worker-002",
            lease_seconds=60,
            idempotency_key="claim-after-exhaustion",
            now=TEST_NOW + timedelta(seconds=62),
        )


def test_recovery_replay_does_not_append_duplicate_event(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    claim_item(work_item_store, now=TEST_NOW)

    first = work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-exact-replay",
        now=TEST_NOW + timedelta(seconds=61),
    )

    replay = work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-exact-replay",
        now=TEST_NOW + timedelta(seconds=120),
    )

    assert replay == first

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert len(events) == 3
    assert events[-1].event_type == "work_item.lease_recovered"


def test_recovery_rejects_wrong_tenant_and_unexpired_lease(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    claim_item(work_item_store, now=TEST_NOW)

    with pytest.raises(AgentWorkItemNotFoundError):
        work_item_store.recover_expired_work_item(
            tenant_id="tenant-b",
            work_item_id="work-item-001",
            idempotency_key="wrong-tenant-recovery",
            now=TEST_NOW + timedelta(seconds=61),
        )

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.recover_expired_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            idempotency_key="premature-recovery",
            now=TEST_NOW + timedelta(seconds=30),
        )


def test_stale_worker_cannot_start_after_recovery_and_reclaim(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    old_claim = claim_item(work_item_store, now=TEST_NOW)

    work_item_store.recover_expired_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        idempotency_key="recover-before-stale-worker",
        now=TEST_NOW + timedelta(seconds=61),
    )

    new_claim = work_item_store.claim_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-002",
        lease_seconds=60,
        idempotency_key="claim-after-recovery",
        now=TEST_NOW + timedelta(seconds=62),
    )

    assert new_claim.fencing_token == old_claim.fencing_token + 1

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.start_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            worker_id="worker-001",
            fencing_token=old_claim.fencing_token,
            idempotency_key="stale-worker-start",
            now=TEST_NOW + timedelta(seconds=63),
        )

    persisted = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert persisted.state is WorkItemState.CLAIMED
    assert persisted.assigned_worker_id == "worker-002"
    assert persisted.fencing_token == new_claim.fencing_token