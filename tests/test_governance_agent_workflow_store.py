import sqlite3

import pytest

from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowConflictError,
    AgentWorkflowIntegrityError,
    AgentWorkflowNotFoundError,
    AgentWorkflowStore,
    AgentWorkflowStoreError,
)


def make_store(tmp_path, *, timeout_seconds=10.0):
    return AgentWorkflowStore(
        tmp_path / "agent_workflows.db",
        timeout_seconds=timeout_seconds,
    )


def create_workflow(
    store,
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-001",
    idempotency_key="create-001",
    payload=None,
):
    return store.create_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        workflow_type="engineering",
        idempotency_key=idempotency_key,
        payload={"source": "test"} if payload is None else payload,
    )


def activate_workflow(
    store,
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-001",
    idempotency_key="transition-001",
):
    return store.transition_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        target_state=WorkflowState.ACTIVE,
        idempotency_key=idempotency_key,
        event_type="workflow.active",
    )


def test_create_workflow_starts_in_created_state(tmp_path):
    store = make_store(tmp_path)

    record = create_workflow(store)

    assert record.workflow_id == "workflow-001"
    assert record.tenant_id == "tenant-a"
    assert record.workflow_type == "engineering"
    assert record.state is WorkflowState.CREATED


def test_creation_appends_integrity_valid_event(tmp_path):
    store = make_store(tmp_path)

    create_workflow(store)

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert len(events) == 1
    assert events[0].event_type == "workflow.created"
    assert events[0].tenant_id == "tenant-a"
    assert events[0].workflow_id == "workflow-001"
    assert events[0].verify_integrity()


def test_creation_is_idempotent_for_same_request(tmp_path):
    store = make_store(tmp_path)

    first = create_workflow(store)
    second = create_workflow(store)

    assert first == second
    assert len(
        store.list_events(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )
    ) == 1


def test_creation_rejects_reused_key_with_different_request(tmp_path):
    store = make_store(tmp_path)

    create_workflow(store)

    with pytest.raises(AgentWorkflowConflictError):
        store.create_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-002",
            workflow_type="engineering",
            idempotency_key="create-001",
            payload={"source": "different"},
        )


def test_creation_rejects_duplicate_workflow_id(tmp_path):
    store = make_store(tmp_path)

    create_workflow(store)

    with pytest.raises(AgentWorkflowConflictError):
        create_workflow(
            store,
            idempotency_key="create-002",
        )


def test_same_workflow_id_is_isolated_between_tenants(tmp_path):
    store = make_store(tmp_path)

    create_workflow(store, tenant_id="tenant-a")
    create_workflow(
        store,
        tenant_id="tenant-b",
        idempotency_key="create-tenant-b",
    )

    tenant_a = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    tenant_b = store.get_workflow(
        tenant_id="tenant-b",
        workflow_id="workflow-001",
    )

    assert tenant_a.tenant_id == "tenant-a"
    assert tenant_b.tenant_id == "tenant-b"


def test_get_workflow_is_tenant_scoped(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    with pytest.raises(AgentWorkflowNotFoundError):
        store.get_workflow(
            tenant_id="tenant-b",
            workflow_id="workflow-001",
        )


def test_get_workflow_rejects_missing_workflow(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(AgentWorkflowNotFoundError):
        store.get_workflow(
            tenant_id="tenant-a",
            workflow_id="missing",
        )


def test_transition_updates_state_and_appends_event(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    record = activate_workflow(store)

    assert record.state is WorkflowState.ACTIVE

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert len(events) == 2
    assert events[1].event_type == "workflow.active"
    assert events[1].verify_integrity()


def test_transition_is_idempotent_for_same_request(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    first = activate_workflow(store)
    second = activate_workflow(store)

    assert first == second

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert len(events) == 2


def test_transition_rejects_reused_key_with_different_request(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    activate_workflow(store)

    with pytest.raises(AgentWorkflowConflictError):
        store.transition_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            target_state=WorkflowState.FAILED,
            idempotency_key="transition-001",
            event_type="workflow.failed",
        )


def test_illegal_transition_does_not_change_state_or_events(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    with pytest.raises(AgentWorkflowStoreError):
        store.transition_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            target_state=WorkflowState.COMPLETED,
            idempotency_key="illegal-transition",
            event_type="workflow.completed",
        )

    record = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert record.state is WorkflowState.CREATED
    assert len(events) == 1


def test_transition_does_not_cross_tenant_boundary(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    with pytest.raises(AgentWorkflowNotFoundError):
        store.transition_workflow(
            tenant_id="tenant-b",
            workflow_id="workflow-001",
            target_state=WorkflowState.ACTIVE,
            idempotency_key="cross-tenant-transition",
            event_type="workflow.active",
        )

    record = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert record.state is WorkflowState.CREATED


def test_completed_workflow_is_terminal(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)
    activate_workflow(store)

    store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.COMPLETED,
        idempotency_key="complete-001",
        event_type="workflow.completed",
    )

    with pytest.raises(AgentWorkflowStoreError):
        store.transition_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            target_state=WorkflowState.ACTIVE,
            idempotency_key="reopen-001",
            event_type="workflow.active",
        )

    record = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert record.state is WorkflowState.COMPLETED


def test_failed_event_insert_rolls_back_state_transition(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    connection = sqlite3.connect(store.database_path)
    try:
        connection.execute(
            """
            CREATE TRIGGER reject_workflow_event
            BEFORE INSERT ON gagf_agent_workflow_events
            WHEN NEW.event_type = 'workflow.active'
            BEGIN
                SELECT RAISE(ABORT, 'forced event insert failure');
            END
            """
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(sqlite3.IntegrityError):
        activate_workflow(store)

    record = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert record.state is WorkflowState.CREATED
    assert len(events) == 1


def test_event_read_detects_tampering(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    connection = sqlite3.connect(store.database_path)
    try:
        connection.execute(
            """
            DROP TRIGGER IF EXISTS
            trg_gagf_agent_workflow_events_no_update
            """
        )
        connection.execute(
            """
            UPDATE gagf_agent_workflow_events
            SET payload_json = ?
            WHERE tenant_id = ?
              AND idempotency_key = ?
            """,
            (
                '{"workflow_type":"tampered"}',
                "tenant-a",
                "create-001",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(AgentWorkflowIntegrityError):
        store.list_events(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )


def test_idempotent_replay_detects_event_tampering(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    connection = sqlite3.connect(store.database_path)
    try:
        connection.execute(
            """
            DROP TRIGGER IF EXISTS
            trg_gagf_agent_workflow_events_no_update
            """
        )
        connection.execute(
            """
            UPDATE gagf_agent_workflow_events
            SET payload_json = ?
            WHERE tenant_id = ?
              AND idempotency_key = ?
            """,
            (
                '{"workflow_type":"tampered"}',
                "tenant-a",
                "create-001",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(AgentWorkflowIntegrityError):
        create_workflow(store)


def test_invalid_payload_value_is_rejected(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(AgentWorkflowStoreError):
        create_workflow(
            store,
            payload={"invalid": object()},
        )


def test_non_mapping_payload_is_rejected(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(AgentWorkflowStoreError):
        create_workflow(store, payload=["not", "a", "mapping"])


def test_non_string_payload_keys_are_rejected(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(AgentWorkflowStoreError):
        create_workflow(store, payload={1: "invalid-key"})


def test_invalid_target_state_type_is_rejected(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    with pytest.raises(AgentWorkflowStoreError):
        store.transition_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            target_state="active",
            idempotency_key="invalid-state",
            event_type="workflow.active",
        )


def test_creation_metadata_cannot_be_overwritten_by_payload(tmp_path):
    store = make_store(tmp_path)

    create_workflow(
        store,
        payload={"workflow_type": "spoofed"},
    )

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    payload = events[0].payload

    assert payload["workflow_type"] == "engineering"
    assert payload["data"]["workflow_type"] == "spoofed"


def test_transition_metadata_cannot_be_overwritten_by_payload(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.ACTIVE,
        idempotency_key="transition-metadata",
        event_type="workflow.active",
        payload={
            "previous_state": "spoofed",
            "target_state": "spoofed",
        },
    )

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    payload = events[-1].payload

    assert payload["previous_state"] == "created"
    assert payload["target_state"] == "active"
    assert payload["data"]["previous_state"] == "spoofed"
    assert payload["data"]["target_state"] == "spoofed"


@pytest.mark.parametrize(
    "operation",
    ["UPDATE", "DELETE"],
)
def test_event_records_are_append_only(tmp_path, operation):
    store = make_store(tmp_path)
    create_workflow(store)

    connection = sqlite3.connect(store.database_path)
    try:
        if operation == "UPDATE":
            statement = """
                UPDATE gagf_agent_workflow_events
                SET event_type = 'tampered'
                WHERE tenant_id = 'tenant-a'
                  AND idempotency_key = 'create-001'
            """
        else:
            statement = """
                DELETE FROM gagf_agent_workflow_events
                WHERE tenant_id = 'tenant-a'
                  AND idempotency_key = 'create-001'
            """

        with pytest.raises(
            sqlite3.IntegrityError,
            match="append-only",
        ):
            connection.execute(statement)

        connection.rollback()
    finally:
        connection.close()

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert len(events) == 1


@pytest.mark.parametrize(
    "timeout_seconds",
    [
        0,
        -1,
        True,
        float("nan"),
        float("inf"),
        "10",
        10 ** 400,
    ],
)
def test_invalid_timeout_is_rejected(tmp_path, timeout_seconds):
    with pytest.raises(AgentWorkflowStoreError):
        make_store(
            tmp_path,
            timeout_seconds=timeout_seconds,
        )

def test_append_workflow_event_persists_without_changing_workflow_state(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)
    activate_workflow(store)

    awaiting = store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.AWAITING_APPROVAL,
        idempotency_key="awaiting-approval-001",
        event_type="approval.requested",
    )

    event = store.append_workflow_event(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        idempotency_key="approval-decision-event-001",
        event_type="approval.approved",
        expected_state=WorkflowState.AWAITING_APPROVAL,
        causation_id="decision-001",
        work_item_id="work-item-001",
        payload={"decision_id": "decision-001"},
    )

    current = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert current == awaiting
    assert current.state is WorkflowState.AWAITING_APPROVAL
    assert event.event_type == "approval.approved"
    assert event.causation_id == "decision-001"
    assert event.work_item_id == "work-item-001"
    assert event.verify_integrity() is True
    assert event.payload["previous_state"] == (
        WorkflowState.AWAITING_APPROVAL.value
    )
    assert event.payload["target_state"] == (
        WorkflowState.AWAITING_APPROVAL.value
    )
    assert event.payload["data"] == {"decision_id": "decision-001"}


def test_append_workflow_event_replay_returns_original_event(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)
    activate_workflow(store)

    store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.AWAITING_APPROVAL,
        idempotency_key="awaiting-approval-001",
        event_type="approval.requested",
    )

    arguments = {
        "tenant_id": "tenant-a",
        "workflow_id": "workflow-001",
        "idempotency_key": "approval-decision-event-001",
        "event_type": "approval.approved",
        "expected_state": WorkflowState.AWAITING_APPROVAL,
        "causation_id": "decision-001",
        "work_item_id": "work-item-001",
        "payload": {"decision_id": "decision-001"},
    }

    first = store.append_workflow_event(**arguments)

    store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.ACTIVE,
        idempotency_key="resume-after-test",
        event_type="workflow.resumed",
    )

    replay = store.append_workflow_event(**arguments)

    assert replay == first

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert sum(
        event.idempotency_key == "approval-decision-event-001"
        for event in events
    ) == 1


def test_append_workflow_event_rejects_reused_key_with_different_content(
    tmp_path,
):
    store = make_store(tmp_path)
    create_workflow(store)
    activate_workflow(store)

    store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.AWAITING_APPROVAL,
        idempotency_key="awaiting-approval-001",
        event_type="approval.requested",
    )

    store.append_workflow_event(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        idempotency_key="decision-event-key",
        event_type="approval.approved",
        expected_state=WorkflowState.AWAITING_APPROVAL,
        payload={"decision_id": "decision-001"},
    )

    with pytest.raises(AgentWorkflowConflictError):
        store.append_workflow_event(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            idempotency_key="decision-event-key",
            event_type="approval.rejected",
            expected_state=WorkflowState.AWAITING_APPROVAL,
            payload={"decision_id": "decision-001"},
        )


def test_append_workflow_event_rejects_unexpected_workflow_state(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    with pytest.raises(AgentWorkflowConflictError):
        store.append_workflow_event(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            idempotency_key="decision-event-key",
            event_type="approval.approved",
            expected_state=WorkflowState.AWAITING_APPROVAL,
            payload={"decision_id": "decision-001"},
        )

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert len(events) == 1


def test_append_workflow_event_is_tenant_scoped(tmp_path):
    store = make_store(tmp_path)
    create_workflow(store)

    with pytest.raises(AgentWorkflowNotFoundError):
        store.append_workflow_event(
            tenant_id="tenant-b",
            workflow_id="workflow-001",
            idempotency_key="decision-event-key",
            event_type="approval.approved",
            expected_state=WorkflowState.CREATED,
            payload={"decision_id": "decision-001"},
        )

    events = store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert len(events) == 1