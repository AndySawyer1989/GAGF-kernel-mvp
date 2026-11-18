from __future__ import annotations

import json
import sqlite3

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowStore,
)
from backend.app.gagf.governance_agent_work_item_store import (
    AgentWorkItemConflictError,
    AgentWorkItemStore,
)
from backend.app.gagf.governance_agent_worker_registry_contract import (
    AgentWorkerRegistrationIntegrityError,
    AgentWorkerRegistrationNotFoundError,
)
from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)
from backend.app.gagf.governance_agent_worker_matcher import (
    AgentWorkerMatcher,
)


TEST_NOW = datetime(2026, 11, 9, 18, 0, tzinfo=timezone.utc)


def make_stores(tmp_path):
    database_path = tmp_path / "agent_workflows.db"
    workflow_store = AgentWorkflowStore(database_path)
    work_item_store = AgentWorkItemStore(database_path)
    return database_path, workflow_store, work_item_store


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
        payload={"source": "registered-claim-test"},
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
):
    return work_item_store.create_work_item(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        work_item_id=work_item_id,
        task_type="code.review",
        idempotency_key=f"create-{tenant_id}-{work_item_id}",
        input_payload={"repository": "test-repository"},
        max_attempts=3,
        now=TEST_NOW + timedelta(seconds=2),
    )


def register_worker(
    registry_store,
    *,
    tenant_id="tenant-a",
    worker_id="worker-a",
    version="1.0.0",
    task_types=("code.review",),
    capabilities=("runtime.python", "tool.pytest"),
    enabled=True,
    now=TEST_NOW,
):
    return registry_store.register_worker(
        tenant_id=tenant_id,
        worker_id=worker_id,
        worker_type="engineering",
        version=version,
        supported_task_types=task_types,
        capabilities=capabilities,
        enabled=enabled,
        now=now,
    )


def registered_claim(
    work_item_store,
    *,
    worker_id="worker-a",
    registration_revision=1,
    required_capabilities=("runtime.python", "tool.pytest"),
    idempotency_key="registered-claim-001",
    now=TEST_NOW + timedelta(seconds=3),
):
    return work_item_store.claim_registered_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id=worker_id,
        expected_registration_revision=registration_revision,
        required_capabilities=required_capabilities,
        lease_seconds=60,
        idempotency_key=idempotency_key,
        now=now,
    )


def test_registered_claim_uses_matcher_and_persists_registration_evidence(
    tmp_path,
):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    registration = register_worker(registry_store)

    matcher = AgentWorkerMatcher(registry_store)
    match = matcher.match(
        tenant_id="tenant-a",
        task_type="code.review",
        required_capabilities=("runtime.python", "tool.pytest"),
    )

    assert match.selected_worker_id == registration.worker_id
    assert (
        match.selected_registration_revision
        == registration.registration_revision
    )

    claimed = work_item_store.claim_registered_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
        worker_id=match.selected_worker_id,
        expected_registration_revision=(
            match.selected_registration_revision
        ),
        required_capabilities=match.required_capabilities,
        lease_seconds=60,
        idempotency_key="registered-claim-001",
        now=TEST_NOW + timedelta(seconds=3),
    )

    assert claimed.state is WorkItemState.CLAIMED
    assert claimed.assigned_worker_id == registration.worker_id
    assert claimed.attempt_count == 1
    assert claimed.fencing_token == 1
    assert claimed.lease_expires_at == (
        TEST_NOW + timedelta(seconds=63)
    )

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )
    claim_events = [
        event for event in events
        if event.event_type == "work_item.claimed"
    ]

    assert len(claim_events) == 1
    assert claim_events[0].payload["registration_revision"] == 1
    assert claim_events[0].payload["required_capabilities"] == [
        "runtime.python",
        "tool.pytest",
    ]
    assert claim_events[0].verify_integrity()


def test_registered_claim_rejects_missing_registration(tmp_path):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    # Initialize the registry table, but do not register this worker.
    registry_store = AgentWorkerRegistryStore(database_path)

    with pytest.raises(AgentWorkerRegistrationNotFoundError):
        registered_claim(work_item_store)


def test_registered_claim_rejects_disabled_worker(tmp_path):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    registration = register_worker(registry_store, enabled=False)

    with pytest.raises(AgentWorkItemConflictError):
        registered_claim(
            work_item_store,
            registration_revision=registration.registration_revision,
        )


def test_registered_claim_rejects_unsupported_task_type(tmp_path):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    registration = register_worker(
        registry_store,
        task_types=("engineering.implementation",),
    )

    with pytest.raises(AgentWorkItemConflictError):
        registered_claim(
            work_item_store,
            registration_revision=registration.registration_revision,
        )


def test_registered_claim_rejects_missing_required_capability(tmp_path):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    registration = register_worker(
        registry_store,
        capabilities=("runtime.python",),
    )

    with pytest.raises(AgentWorkItemConflictError):
        registered_claim(
            work_item_store,
            registration_revision=registration.registration_revision,
            required_capabilities=("runtime.python", "tool.pytest"),
        )


def test_registered_claim_rejects_stale_registration_revision(tmp_path):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    original = register_worker(registry_store)

    updated = register_worker(
        registry_store,
        version="2.0.0",
        now=TEST_NOW + timedelta(minutes=5),
    )

    assert updated.registration_revision == original.registration_revision + 1

    with pytest.raises(AgentWorkItemConflictError):
        registered_claim(
            work_item_store,
            registration_revision=original.registration_revision,
        )


def test_registered_claim_is_tenant_scoped(tmp_path):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store, tenant_id="tenant-a")
    create_pending_item(work_item_store, tenant_id="tenant-a")

    registry_store = AgentWorkerRegistryStore(database_path)
    register_worker(
        registry_store,
        tenant_id="tenant-b",
        worker_id="worker-a",
    )

    with pytest.raises(AgentWorkerRegistrationNotFoundError):
        registered_claim(work_item_store)


def test_registered_claim_fails_closed_when_registry_table_is_missing(
    tmp_path,
):
    _, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    # Deliberately do not instantiate AgentWorkerRegistryStore.
    # The work-item store must not silently accept an unregistered worker.

    with pytest.raises(AgentWorkerRegistrationIntegrityError):
        registered_claim(work_item_store)


def test_registered_claim_rejects_malformed_persisted_registration(
    tmp_path,
):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    register_worker(registry_store)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE gagf_agent_worker_registry
            SET capabilities_json = ?
            WHERE tenant_id = ? AND worker_id = ?
            """,
            ("{", "tenant-a", "worker-a"),
        )

    with pytest.raises(AgentWorkerRegistrationIntegrityError):
        registered_claim(work_item_store)


def test_registered_claim_exact_replay_does_not_increment_attempt_or_fence(
    tmp_path,
):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    register_worker(registry_store)

    first = registered_claim(work_item_store)
    replay = registered_claim(work_item_store)

    assert replay == first
    assert replay.attempt_count == 1
    assert replay.fencing_token == 1

    events = work_item_store.list_events(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )
    assert [
        event.event_type for event in events
    ].count("work_item.claimed") == 1


def test_registered_claim_revalidates_registration_before_idempotent_replay(
    tmp_path,
):
    database_path, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    create_pending_item(work_item_store)

    registry_store = AgentWorkerRegistryStore(database_path)
    register_worker(registry_store)

    first = registered_claim(work_item_store)
    assert first.fencing_token == 1

    disabled = register_worker(
        registry_store,
        enabled=False,
        now=TEST_NOW + timedelta(minutes=5),
    )
    assert disabled.registration_revision == 2

    # Same idempotency key and same original request. Current registry
    # qualification must be checked before the stored replay is returned.
    with pytest.raises(AgentWorkItemConflictError):
        registered_claim(work_item_store)

    persisted = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )
    assert persisted.fencing_token == 1
    assert persisted.attempt_count == 1

def test_list_ready_work_items_is_tenant_scoped_and_deterministic(tmp_path):
    _, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store, tenant_id="tenant-a")
    create_active_workflow(
        workflow_store,
        tenant_id="tenant-b",
        workflow_id="workflow-b",
    )

    for work_item_id in ("work-item-c", "work-item-a", "work-item-b"):
        work_item_store.create_work_item(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            work_item_id=work_item_id,
            task_type="code.review",
            idempotency_key=f"create-{work_item_id}",
            input_payload={},
            available_at=TEST_NOW,
            now=TEST_NOW,
        )

    work_item_store.create_work_item(
        tenant_id="tenant-b",
        workflow_id="workflow-b",
        work_item_id="tenant-b-item",
        task_type="code.review",
        idempotency_key="create-tenant-b-item",
        input_payload={},
        available_at=TEST_NOW,
        now=TEST_NOW,
    )

    records = work_item_store.list_ready_work_items(
        tenant_id="tenant-a",
        now=TEST_NOW + timedelta(seconds=1),
        limit=2,
    )

    assert [record.work_item_id for record in records] == [
        "work-item-a",
        "work-item-b",
    ]
    assert all(record.tenant_id == "tenant-a" for record in records)
    assert all(record.state is WorkItemState.PENDING for record in records)


def test_list_ready_work_items_excludes_future_items(tmp_path):
    _, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)

    work_item_store.create_work_item(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        work_item_id="ready-item",
        task_type="code.review",
        idempotency_key="create-ready-item",
        input_payload={},
        available_at=TEST_NOW,
        now=TEST_NOW,
    )
    work_item_store.create_work_item(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        work_item_id="future-item",
        task_type="code.review",
        idempotency_key="create-future-item",
        input_payload={},
        available_at=TEST_NOW + timedelta(minutes=5),
        now=TEST_NOW,
    )

    records = work_item_store.list_ready_work_items(
        tenant_id="tenant-a",
        now=TEST_NOW + timedelta(seconds=1),
    )

    assert [record.work_item_id for record in records] == ["ready-item"]


@pytest.mark.parametrize("limit", [True, False, 0, -1, 1.5, "2", 501])
def test_list_ready_work_items_rejects_invalid_limits(tmp_path, limit):
    _, _, work_item_store = make_stores(tmp_path)

    with pytest.raises(Exception) as exc_info:
        work_item_store.list_ready_work_items(
            tenant_id="tenant-a",
            now=TEST_NOW,
            limit=limit,
        )

    assert "limit" in str(exc_info.value)


def test_list_ready_work_items_rejects_naive_timestamp(tmp_path):
    _, _, work_item_store = make_stores(tmp_path)

    with pytest.raises(Exception) as exc_info:
        work_item_store.list_ready_work_items(
            tenant_id="tenant-a",
            now=datetime(2026, 11, 9, 18, 0),
        )

    assert "timezone-aware" in str(exc_info.value)


def test_list_ready_work_items_does_not_mutate_items(tmp_path):
    _, workflow_store, work_item_store = make_stores(tmp_path)
    create_active_workflow(workflow_store)
    original = create_pending_item(work_item_store)

    records = work_item_store.list_ready_work_items(
        tenant_id="tenant-a",
        now=TEST_NOW + timedelta(seconds=3),
    )

    assert len(records) == 1
    assert records[0] == original
    assert records[0].attempt_count == 0
    assert records[0].fencing_token == 0
    assert records[0].assigned_worker_id is None
    assert records[0].lease_expires_at is None