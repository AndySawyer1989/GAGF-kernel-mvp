from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_agent_worker_contract import (
    MAX_WORKER_PAYLOAD_BYTES,
    AgentWorkerContractError,
    AgentWorkerOutcome,
    AgentWorkerRequest,
    AgentWorkerResult,
)


def make_request(**overrides):
    values = {
        "request_id": "request-001",
        "tenant_id": "tenant-a",
        "workflow_id": "workflow-001",
        "work_item_id": "work-item-001",
        "worker_id": "engineering-worker",
        "task_type": "code_review",
        "instruction": "Review the proposed implementation.",
        "correlation_id": "correlation-001",
        "idempotency_key": "request-idempotency-001",
        "issued_at": datetime.now(timezone.utc),
        "input_payload": {"change_id": "change-001"},
    }
    values.update(overrides)
    return AgentWorkerRequest.create(**values)


def make_result(request, **overrides):
    values = {
        "request": request,
        "outcome": AgentWorkerOutcome.SUCCESS,
        "executed_at": datetime.now(timezone.utc),
        "output": {"review_status": "completed"},
    }
    values.update(overrides)
    return AgentWorkerResult.create(**values)


def test_request_preserves_execution_context():
    request = make_request()

    assert request.tenant_id == "tenant-a"
    assert request.workflow_id == "workflow-001"
    assert request.work_item_id == "work-item-001"
    assert request.worker_id == "engineering-worker"
    assert request.correlation_id == "correlation-001"
    assert request.idempotency_key == "request-idempotency-001"
    assert request.input_payload == {"change_id": "change-001"}


def test_request_payload_is_canonical():
    first = make_request(
        input_payload={"b": 2, "a": 1}
    )
    second = make_request(
        input_payload={"a": 1, "b": 2}
    )

    assert first.input_json == second.input_json


def test_request_rejects_missing_required_text():
    with pytest.raises(AgentWorkerContractError):
        make_request(tenant_id="   ")


def test_request_rejects_naive_datetime():
    with pytest.raises(AgentWorkerContractError):
        make_request(issued_at=datetime.now())


def test_request_rejects_non_json_payload():
    with pytest.raises(AgentWorkerContractError):
        make_request(input_payload={"invalid": object()})


def test_request_rejects_oversized_payload():
    oversized = {
        "content": "x" * MAX_WORKER_PAYLOAD_BYTES
    }

    with pytest.raises(AgentWorkerContractError):
        make_request(input_payload=oversized)


def test_request_is_immutable():
    request = make_request()

    with pytest.raises(FrozenInstanceError):
        request.tenant_id = "tenant-b"


def test_success_result_preserves_request_context():
    request = make_request()
    result = make_result(request)

    result.validate_against(request)

    assert result.request_id == request.request_id
    assert result.tenant_id == request.tenant_id
    assert result.workflow_id == request.workflow_id
    assert result.work_item_id == request.work_item_id
    assert result.worker_id == request.worker_id
    assert result.correlation_id == request.correlation_id
    assert result.idempotency_key == request.idempotency_key
    assert result.output == {"review_status": "completed"}


@pytest.mark.parametrize(
    "outcome",
    [
        AgentWorkerOutcome.FAILURE,
        AgentWorkerOutcome.RETRYABLE_FAILURE,
        AgentWorkerOutcome.REJECTED,
    ],
)
def test_non_success_results_require_error_details(outcome):
    request = make_request()

    with pytest.raises(AgentWorkerContractError):
        make_result(
            request,
            outcome=outcome,
        )


def test_non_success_result_accepts_structured_error():
    request = make_request()

    result = make_result(
        request,
        outcome=AgentWorkerOutcome.RETRYABLE_FAILURE,
        error_code="TEMPORARY_PROVIDER_FAILURE",
        error_message="The provider is temporarily unavailable.",
    )

    assert result.outcome == AgentWorkerOutcome.RETRYABLE_FAILURE
    assert result.error_code == "TEMPORARY_PROVIDER_FAILURE"


def test_success_result_rejects_error_details():
    request = make_request()

    with pytest.raises(AgentWorkerContractError):
        make_result(
            request,
            error_code="UNEXPECTED_ERROR",
            error_message="Unexpected error.",
        )


def test_result_rejects_naive_execution_datetime():
    request = make_request()

    with pytest.raises(AgentWorkerContractError):
        make_result(
            request,
            executed_at=datetime.now(),
        )


def test_result_rejects_non_json_output():
    request = make_request()

    with pytest.raises(AgentWorkerContractError):
        make_result(
            request,
            output={"invalid": object()},
        )


def test_result_rejects_oversized_output():
    request = make_request()
    oversized = {
        "content": "x" * MAX_WORKER_PAYLOAD_BYTES
    }

    with pytest.raises(AgentWorkerContractError):
        make_result(request, output=oversized)


def test_result_rejects_mismatched_tenant_context():
    request = make_request()
    result = make_result(request)
    different_request = replace(request, tenant_id="tenant-b")

    with pytest.raises(AgentWorkerContractError):
        result.validate_against(different_request)


def test_result_rejects_mismatched_work_item_context():
    request = make_request()
    result = make_result(request)
    different_request = replace(
        request,
        work_item_id="work-item-002",
    )

    with pytest.raises(AgentWorkerContractError):
        result.validate_against(different_request)


def test_result_rejects_mismatched_idempotency_context():
    request = make_request()
    result = make_result(request)
    different_request = replace(
        request,
        idempotency_key="different-key",
    )

    with pytest.raises(AgentWorkerContractError):
        result.validate_against(different_request)


def test_result_is_immutable():
    request = make_request()
    result = make_result(request)

    with pytest.raises(FrozenInstanceError):
        result.tenant_id = "tenant-b"


def test_output_property_returns_independent_dictionary():
    request = make_request()
    result = make_result(request)

    output = result.output
    output["review_status"] = "tampered"

    assert result.output == {"review_status": "completed"}
# Direct-construction validation tests. These bypass the factory methods.

def test_direct_request_rejects_blank_tenant_id():
    request = make_request()
    values = {
        field: getattr(request, field)
        for field in request.__dataclass_fields__
    }
    values["tenant_id"] = "   "

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerRequest(**values)


def test_direct_request_rejects_malformed_json():
    request = make_request()
    values = {
        field: getattr(request, field)
        for field in request.__dataclass_fields__
    }
    values["input_json"] = "{invalid-json"

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerRequest(**values)


def test_direct_request_rejects_unsupported_schema():
    request = make_request()
    values = {
        field: getattr(request, field)
        for field in request.__dataclass_fields__
    }
    values["schema_version"] = 2

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerRequest(**values)


def test_direct_result_rejects_string_outcome():
    request = make_request()
    result = make_result(request)
    values = {
        field: getattr(result, field)
        for field in result.__dataclass_fields__
    }
    values["outcome"] = "success"

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerResult(**values)


def test_direct_result_rejects_success_error_details():
    request = make_request()
    result = make_result(request)
    values = {
        field: getattr(result, field)
        for field in result.__dataclass_fields__
    }
    values["error_code"] = "UNEXPECTED_ERROR"

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerResult(**values)


def test_direct_result_rejects_malformed_json():
    request = make_request()
    result = make_result(request)
    values = {
        field: getattr(result, field)
        for field in result.__dataclass_fields__
    }
    values["output_json"] = "{invalid-json"

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerResult(**values)


def test_direct_result_rejects_unsupported_schema():
    request = make_request()
    result = make_result(request)
    values = {
        field: getattr(result, field)
        for field in result.__dataclass_fields__
    }
    values["schema_version"] = 2

    with pytest.raises(AgentWorkerContractError):
        AgentWorkerResult(**values)
