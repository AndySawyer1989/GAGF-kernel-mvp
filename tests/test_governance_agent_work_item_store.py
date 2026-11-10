from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
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


TEST_NOW = datetime(2026, 11, 9, 18, 0, tzinfo=timezone.utc)


def make_stores(tmp_path):
    database_path = tmp_path / "agent_workflows.db"

    workflow_store = AgentWorkflowStore(database_path)
    work_item_store = AgentWorkItemStore(database_path)

    return workflow_store, work_item_store


def create_active_workflow(
    workflow_store,
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-001",
):
    workflow_store.create_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        workflow_type="engineering",
        idempotency_key=f"create-{tenant_id}-{workflow_id}",
        payload={"source": "work-item-test"},
    )

    return workflow_store.transition_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        target_state=WorkflowState.ACTIVE,
        idempotency_key=f"activate-{tenant_id}-{workflow_id}",
        event_type="workflow.activated",
    )


def create_pending_item(
    work_item_store,
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-001",
    work_item_id="work-item-001",
    idempotency_key="create-work-item-001",
    max_attempts=3,
    available_at=None,
    now=None,
):
    effective_now = TEST_NOW if now is None else now

    return work_item_store.create_work_item(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        work_item_id=work_item_id,
        task_type="engineering.review",
        idempotency_key=idempotency_key,
        input_payload={"repository": "test-repository"},
        max_attempts=max_attempts,
        available_at=available_at,
        now=effective_now,
    )


def claim_item(
    work_item_store,
    *,
    worker_id="worker-001",
    idempotency_key="claim-001",
    now=None,
):
    return work_item_store.claim_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id=worker_id,
        lease_seconds=60,
        idempotency_key=idempotency_key,
        now=now,
    )


def test_create_and_retrieve_work_item(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)

    record = create_pending_item(work_item_store)

    assert record.state is WorkItemState.PENDING
    assert record.attempt_count == 0
    assert record.fencing_token == 0
    assert record.assigned_worker_id is None
    assert record.lease_expires_at is None
    assert record.input_payload == {
        "repository": "test-repository"
    }

    retrieved = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert retrieved == record

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert len(events) == 1
    assert events[0].event_type == "work_item.created"
    assert events[0].verify_integrity()


def test_work_item_creation_requires_existing_tenant_workflow(
    tmp_path,
):
    _, work_item_store = make_stores(tmp_path)

    with pytest.raises(AgentWorkItemConflictError):
        create_pending_item(work_item_store)


def test_tenant_cannot_read_another_tenants_work_item(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)

    create_active_workflow(
        workflow_store,
        tenant_id="tenant-a",
        workflow_id="workflow-a",
    )

    create_pending_item(
        work_item_store,
        tenant_id="tenant-a",
        workflow_id="workflow-a",
    )

    with pytest.raises(AgentWorkItemNotFoundError):
        work_item_store.get_work_item(
            tenant_id="tenant-b",
            work_item_id="work-item-001",
        )

    with pytest.raises(AgentWorkItemNotFoundError):
        work_item_store.list_events(
            tenant_id="tenant-b",
            work_item_id="work-item-001",
        )


def test_creation_is_idempotent_for_exact_replay(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)

    first = create_pending_item(
        work_item_store,
        now=TEST_NOW,
    )

    replay = create_pending_item(
        work_item_store,
        now=TEST_NOW + timedelta(seconds=5),
    )

    assert replay == first

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert len(events) == 1


def test_creation_rejects_idempotency_key_reuse_with_different_request(
    tmp_path,
):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)

    create_pending_item(work_item_store)

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.create_work_item(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            work_item_id="work-item-002",
            task_type="engineering.review",
            idempotency_key="create-work-item-001",
            input_payload={"repository": "different-repository"},
        )


def test_claim_requires_active_parent_workflow(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)

    workflow_store.create_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        workflow_type="engineering",
        idempotency_key="workflow-create",
    )

    create_pending_item(work_item_store)

    with pytest.raises(AgentWorkItemConflictError):
        claim_item(work_item_store, now=TEST_NOW)

    record = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert record.state is WorkItemState.PENDING
    assert record.attempt_count == 0


def test_claim_assigns_worker_lease_and_fencing_token(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    claimed = claim_item(
        work_item_store,
        now=now,
    )

    assert claimed.state is WorkItemState.CLAIMED
    assert claimed.assigned_worker_id == "worker-001"
    assert claimed.attempt_count == 1
    assert claimed.fencing_token == 1
    assert claimed.lease_expires_at == now + timedelta(seconds=60)

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert [event.event_type for event in events] == [
        "work_item.created",
        "work_item.claimed",
    ]


def test_claim_exact_replay_does_not_increment_fencing_token(
    tmp_path,
):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    first = claim_item(
        work_item_store,
        now=now,
    )

    replay = claim_item(
        work_item_store,
        now=now + timedelta(seconds=5),
    )

    assert first.fencing_token == 1
    assert replay.fencing_token == 1
    assert replay.attempt_count == 1

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert len(events) == 2


def test_only_one_concurrent_worker_can_claim_item(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    def attempt_claim(worker_number):
        try:
            return work_item_store.claim_work_item(
                tenant_id="tenant-a",
                work_item_id="work-item-001",
                worker_id=f"worker-{worker_number}",
                lease_seconds=60,
                idempotency_key=f"concurrent-claim-{worker_number}",
            )
        except AgentWorkItemConflictError:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(attempt_claim, range(8)))

    successful_claims = [
        result for result in results if result is not None
    ]

    assert len(successful_claims) == 1

    persisted = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert persisted.state is WorkItemState.CLAIMED
    assert persisted.attempt_count == 1
    assert persisted.fencing_token == 1


def test_start_rejects_wrong_worker_and_stale_fencing_token(
    tmp_path,
):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    claimed = claim_item(
        work_item_store,
        now=now,
    )

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.start_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            worker_id="worker-incorrect",
            fencing_token=claimed.fencing_token,
            idempotency_key="start-wrong-worker",
            now=now + timedelta(seconds=1),
        )

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.start_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            worker_id="worker-001",
            fencing_token=claimed.fencing_token + 1,
            idempotency_key="start-stale-token",
            now=now + timedelta(seconds=1),
        )

    started = work_item_store.start_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=claimed.fencing_token,
        idempotency_key="start-valid",
        now=now + timedelta(seconds=1),
    )

    assert started.state is WorkItemState.RUNNING
    assert started.fencing_token == 1
    assert started.assigned_worker_id == "worker-001"


def test_start_rejects_expired_lease(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    claimed = claim_item(
        work_item_store,
        now=now,
    )

    with pytest.raises(AgentWorkItemConflictError):
        work_item_store.start_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            worker_id="worker-001",
            fencing_token=claimed.fencing_token,
            idempotency_key="start-after-expiry",
            now=now + timedelta(seconds=61),
        )


def test_successful_completion_clears_active_lease(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    claimed = claim_item(
        work_item_store,
        now=now,
    )

    started = work_item_store.start_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=claimed.fencing_token,
        idempotency_key="start-valid",
        now=now + timedelta(seconds=1),
    )

    completed = work_item_store.complete_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=started.fencing_token,
        idempotency_key="complete-valid",
        success=True,
        now=now + timedelta(seconds=2),
    )

    assert completed.state is WorkItemState.SUCCEEDED
    assert completed.assigned_worker_id is None
    assert completed.lease_expires_at is None
    assert completed.fencing_token == 1

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert [event.event_type for event in events] == [
        "work_item.created",
        "work_item.claimed",
        "work_item.started",
        "work_item.succeeded",
    ]


def test_failed_completion_requires_error_details(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    claimed = claim_item(
        work_item_store,
        now=now,
    )

    started = work_item_store.start_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=claimed.fencing_token,
        idempotency_key="start-valid",
        now=now + timedelta(seconds=1),
    )

    with pytest.raises(Exception):
        work_item_store.complete_work_item(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
            worker_id="worker-001",
            fencing_token=started.fencing_token,
            idempotency_key="complete-missing-error",
            success=False,
            now=now + timedelta(seconds=2),
        )


def test_failed_completion_records_error_and_clears_lease(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    now = TEST_NOW

    claimed = claim_item(
        work_item_store,
        now=now,
    )

    started = work_item_store.start_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=claimed.fencing_token,
        idempotency_key="start-valid",
        now=now + timedelta(seconds=1),
    )

    failed = work_item_store.complete_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id="worker-001",
        fencing_token=started.fencing_token,
        idempotency_key="complete-failed",
        success=False,
        error_code="WORKER_EXECUTION_FAILED",
        error_message="The worker reported a bounded execution failure.",
        now=now + timedelta(seconds=2),
    )

    assert failed.state is WorkItemState.FAILED
    assert failed.last_error_code == "WORKER_EXECUTION_FAILED"
    assert failed.last_error_message
    assert failed.assigned_worker_id is None
    assert failed.lease_expires_at is None


def test_work_item_events_are_append_only(tmp_path):
    workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    connection = work_item_store._connect()

    try:
        with pytest.raises(Exception):
            connection.execute(
                """
                UPDATE gagf_agent_work_item_events
                SET event_type = 'tampered'
                WHERE tenant_id = ?
                """,
                ("tenant-a",),
            )

        with pytest.raises(Exception):
            connection.execute(
                """
                DELETE FROM gagf_agent_work_item_events
                WHERE tenant_id = ?
                """,
                ("tenant-a",),
            )
    finally:
        connection.close()