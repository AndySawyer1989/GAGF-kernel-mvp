from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_agent_workflow_contract import (
    AgentWorkflowContractError,
    AgentWorkflowEvent,
    WorkItemState,
    WorkflowState,
    validate_work_item_transition,
    validate_workflow_transition,
)


def make_event(**overrides):
    values = {
        "event_id": "event-001",
        "event_type": "workflow.created",
        "tenant_id": "tenant-alpha",
        "workflow_id": "workflow-001",
        "correlation_id": "correlation-001",
        "causation_id": None,
        "idempotency_key": "workflow-001-created",
        "occurred_at": datetime(
            2026, 11, 7, 12, 0, tzinfo=timezone.utc
        ),
        "payload": {"workflow_type": "engineering"},
    }
    values.update(overrides)
    return AgentWorkflowEvent.create(**values)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (WorkflowState.CREATED, WorkflowState.ACTIVE),
        (WorkflowState.CREATED, WorkflowState.CANCELLED),
        (WorkflowState.ACTIVE, WorkflowState.AWAITING_APPROVAL),
        (WorkflowState.ACTIVE, WorkflowState.COMPLETED),
        (WorkflowState.AWAITING_APPROVAL, WorkflowState.ACTIVE),
        (WorkflowState.AWAITING_APPROVAL, WorkflowState.COMPLETED),
    ],
)
def test_accepts_legal_workflow_transitions(current, target):
    validate_workflow_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (WorkflowState.CREATED, WorkflowState.COMPLETED),
        (WorkflowState.COMPLETED, WorkflowState.ACTIVE),
        (WorkflowState.FAILED, WorkflowState.ACTIVE),
        (WorkflowState.CANCELLED, WorkflowState.ACTIVE),
        (WorkflowState.ACTIVE, WorkflowState.CREATED),
    ],
)
def test_rejects_illegal_workflow_transitions(current, target):
    with pytest.raises(AgentWorkflowContractError):
        validate_workflow_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (WorkItemState.PENDING, WorkItemState.CLAIMED),
        (WorkItemState.CLAIMED, WorkItemState.RUNNING),
        (WorkItemState.CLAIMED, WorkItemState.PENDING),
        (WorkItemState.RUNNING, WorkItemState.SUCCEEDED),
        (WorkItemState.RUNNING, WorkItemState.RETRY_WAIT),
        (WorkItemState.RETRY_WAIT, WorkItemState.PENDING),
        (WorkItemState.FAILED, WorkItemState.DEAD_LETTER),
    ],
)
def test_accepts_legal_work_item_transitions(current, target):
    validate_work_item_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (WorkItemState.SUCCEEDED, WorkItemState.RUNNING),
        (WorkItemState.DEAD_LETTER, WorkItemState.PENDING),
        (WorkItemState.CANCELLED, WorkItemState.RUNNING),
        (WorkItemState.PENDING, WorkItemState.SUCCEEDED),
        (WorkItemState.RUNNING, WorkItemState.PENDING),
    ],
)
def test_rejects_illegal_work_item_transitions(current, target):
    with pytest.raises(AgentWorkflowContractError):
        validate_work_item_transition(current, target)


def test_event_hash_is_deterministic():
    first = make_event()
    second = make_event()

    assert first.event_hash == second.event_hash
    assert first.verify_integrity()


def test_event_supports_optional_work_item_lineage():
    event = make_event(work_item_id="work-item-001")

    assert event.workflow_id == "workflow-001"
    assert event.work_item_id == "work-item-001"
    assert event.verify_integrity()


def test_event_without_work_item_lineage_is_valid():
    event = make_event()

    assert event.work_item_id is None
    assert event.verify_integrity()


def test_event_hash_changes_when_work_item_changes():
    first = make_event(work_item_id="work-item-001")
    second = make_event(work_item_id="work-item-002")

    assert first.event_hash != second.event_hash


def test_integrity_verification_rejects_modified_event():
    from dataclasses import replace

    event = make_event()
    modified = replace(event, tenant_id="tenant-other")

    assert event.verify_integrity()
    assert not modified.verify_integrity()

def test_event_hash_changes_when_payload_changes():
    first = make_event(payload={"workflow_type": "engineering"})
    second = make_event(payload={"workflow_type": "lead_generation"})

    assert first.event_hash != second.event_hash


def test_event_preserves_tenant_and_correlation_lineage():
    event = make_event(causation_id="event-parent-001")

    assert event.tenant_id == "tenant-alpha"
    assert event.correlation_id == "correlation-001"
    assert event.causation_id == "event-parent-001"


def test_event_normalizes_timestamp_to_utc():
    event = make_event()

    assert event.occurred_at.tzinfo == timezone.utc


def test_event_rejects_naive_timestamp():
    with pytest.raises(AgentWorkflowContractError):
        make_event(occurred_at=datetime(2026, 11, 7, 12, 0))


def test_event_rejects_empty_tenant():
    with pytest.raises(AgentWorkflowContractError):
        make_event(tenant_id="  ")


def test_event_rejects_non_json_payload():
    with pytest.raises(AgentWorkflowContractError):
        make_event(payload={"invalid": object()})


def test_event_rejects_non_finite_json_number():
    with pytest.raises(AgentWorkflowContractError):
        make_event(payload={"invalid": float("nan")})


def test_event_is_immutable():
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.tenant_id = "tenant-other"


def test_event_payload_is_returned_as_independent_data():
    event = make_event()
    payload = event.payload
    payload["workflow_type"] = "changed"

    assert event.payload["workflow_type"] == "engineering"


def test_event_serialization_preserves_integrity():
    event = make_event()
    serialized = event.to_dict()

    assert serialized["tenant_id"] == "tenant-alpha"
    assert serialized["payload"]["workflow_type"] == "engineering"
    assert serialized["event_hash"] == event.event_hash
    assert event.verify_integrity()


def test_contract_rejects_same_state_transition():
    with pytest.raises(AgentWorkflowContractError):
        validate_workflow_transition(
            WorkflowState.ACTIVE,
            WorkflowState.ACTIVE,
        )

    with pytest.raises(AgentWorkflowContractError):
        validate_work_item_transition(
            WorkItemState.RUNNING,
            WorkItemState.RUNNING,
        )
