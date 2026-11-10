from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_work_item_contract import (
    AgentWorkItemContractError,
    AgentWorkItemRecord,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
)


NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def make_record(**overrides):
    values = {
        "work_item_id": "work-001",
        "tenant_id": "tenant-001",
        "workflow_id": "workflow-001",
        "task_type": "engineering.review",
        "state": WorkItemState.PENDING,
        "correlation_id": "correlation-001",
        "idempotency_key": "work-item-create-001",
        "input_json": '{"z": 2, "a": 1}',
        "created_at": NOW,
        "updated_at": NOW,
        "available_at": NOW,
        "attempt_count": 0,
        "max_attempts": 3,
        "assigned_worker_id": None,
        "lease_expires_at": None,
        "fencing_token": 0,
        "last_error_code": None,
        "last_error_message": None,
    }
    values.update(overrides)
    return AgentWorkItemRecord(**values)


def test_pending_record_is_valid_and_normalizes_json():
    record = make_record()

    assert record.state is WorkItemState.PENDING
    assert record.input_json == '{"a":1,"z":2}'
    assert record.input_payload == {"a": 1, "z": 2}


def test_record_is_immutable():
    record = make_record()

    with pytest.raises(FrozenInstanceError):
        record.state = WorkItemState.CANCELLED


def test_to_dict_returns_serializable_contract_representation():
    record = make_record()

    result = record.to_dict()

    assert result["state"] == "pending"
    assert result["input_payload"] == {"a": 1, "z": 2}
    assert result["created_at"] == NOW.isoformat()
    assert result["fencing_token"] == 0


def test_timezone_aware_timestamps_are_normalized_to_utc():
    eastern_offset = timezone(timedelta(hours=-5))
    local_time = datetime(2026, 11, 9, 7, 0, tzinfo=eastern_offset)

    record = make_record(created_at=local_time)

    assert record.created_at == NOW
    assert record.created_at.utcoffset() == timedelta(0)


def test_naive_timestamp_is_rejected():
    with pytest.raises(AgentWorkItemContractError):
        make_record(created_at=datetime(2026, 11, 9, 12, 0))


@pytest.mark.parametrize(
    "field_name",
    [
        "work_item_id",
        "tenant_id",
        "workflow_id",
        "task_type",
        "correlation_id",
        "idempotency_key",
    ],
)
def test_required_identity_fields_reject_blank_values(field_name):
    with pytest.raises(AgentWorkItemContractError):
        make_record(**{field_name: "   "})


def test_non_enum_state_is_rejected():
    with pytest.raises(AgentWorkItemContractError):
        make_record(state="pending")


def test_claimed_record_requires_worker_lease_and_fencing_token():
    with pytest.raises(AgentWorkItemContractError):
        make_record(state=WorkItemState.CLAIMED)


def test_claimed_record_with_complete_lease_is_valid():
    record = make_record(
        state=WorkItemState.CLAIMED,
        assigned_worker_id="worker-001",
        lease_expires_at=NOW + timedelta(minutes=5),
        fencing_token=1,
        attempt_count=1,
    )

    assert record.assigned_worker_id == "worker-001"
    assert record.fencing_token == 1


def test_running_record_requires_positive_fencing_token():
    with pytest.raises(AgentWorkItemContractError):
        make_record(
            state=WorkItemState.RUNNING,
            assigned_worker_id="worker-001",
            lease_expires_at=NOW + timedelta(minutes=5),
            fencing_token=0,
            attempt_count=1,
        )


def test_non_active_record_cannot_retain_worker_lease():
    with pytest.raises(AgentWorkItemContractError):
        make_record(
            state=WorkItemState.PENDING,
            assigned_worker_id="worker-001",
            lease_expires_at=NOW + timedelta(minutes=5),
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"attempt_count": -1},
        {"attempt_count": 4, "max_attempts": 3},
        {"max_attempts": 0},
        {"fencing_token": -1},
        {"attempt_count": True},
        {"max_attempts": True},
        {"fencing_token": True},
    ],
)
def test_invalid_attempt_and_fencing_values_are_rejected(overrides):
    with pytest.raises(AgentWorkItemContractError):
        make_record(**overrides)


@pytest.mark.parametrize(
    "input_json",
    [
        "not-json",
        "[]",
        '"string"',
        "null",
        "NaN",
    ],
)
def test_invalid_or_non_object_input_json_is_rejected(input_json):
    with pytest.raises(AgentWorkItemContractError):
        make_record(input_json=input_json)


def test_oversized_input_payload_is_rejected():
    import json

    oversized = json.dumps({"value": "x" * 262145})

    with pytest.raises(AgentWorkItemContractError):
        make_record(input_json=oversized)


def test_error_code_and_message_must_be_provided_together():
    with pytest.raises(AgentWorkItemContractError):
        make_record(last_error_code="worker.failed")

    with pytest.raises(AgentWorkItemContractError):
        make_record(last_error_message="Worker failed")


def test_complete_error_metadata_is_valid():
    record = make_record(
        state=WorkItemState.FAILED,
        last_error_code="worker.failed",
        last_error_message="Independent verification failed",
    )

    assert record.last_error_code == "worker.failed"


def test_claimed_record_can_be_reconstructed_without_mutating_original():
    original = make_record()

    claimed = replace(
        original,
        state=WorkItemState.CLAIMED,
        assigned_worker_id="worker-001",
        lease_expires_at=NOW + timedelta(minutes=5),
        fencing_token=1,
        attempt_count=1,
    )

    assert original.state is WorkItemState.PENDING
    assert claimed.state is WorkItemState.CLAIMED
    assert original.fencing_token == 0
    assert claimed.fencing_token == 1