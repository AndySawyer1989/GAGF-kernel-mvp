import json
import logging
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.app.engineering_agent.config import (
    EngineeringAgentSettings,
)
from backend.app.engineering_agent.contracts.v1 import (
    ApplicationStatusResponse,
    ErrorResponse,
    HealthResponse,
)
from backend.app.engineering_agent.logging import (
    configure_logging,
    get_request_id,
    reset_request_id,
    set_request_id,
)
from backend.app.gagf.governance_agent_bounded_dispatcher import (
    AgentWorkItemDispatchOutcome,
    BoundedDispatchResult,
)
from backend.app.gagf.governance_agent_work_item_contract import (
    AgentWorkItemRecord,
)
from backend.app.gagf.governance_agent_runtime_coordinator import (
    GovernanceAgentRuntimeCoordinationResult,
)
from backend.app.gagf.governance_agent_state_router import (
    AgentWorkflowRoutingDecision,
    WorkflowRoutingAction,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
    WorkItemState,
)
from backend.app.engineering_agent.runtime_identity import (
    AuthenticatedRuntimePrincipal,
    RuntimeAuthenticationError,
    RuntimeIdentityProviderError,
)
from backend.app.engineering_agent.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> EngineeringAgentSettings:
    repository = tmp_path / "repository"
    repository.mkdir()

    return EngineeringAgentSettings(
        repository_path=repository,
        workspace_root=tmp_path / "workspaces",
        data_root=tmp_path / "data",
    )


def test_health_contract() -> None:
    response = HealthResponse(
        status="healthy",
        application="engineering-agent",
        version="0.1.0",
    )

    assert response.status == "healthy"
    assert response.application == "engineering-agent"


def test_status_contract() -> None:
    response = ApplicationStatusResponse(
        application="engineering-agent",
        version="0.1.0",
        api_version="v1",
        initialized=True,
        execution_enabled=False,
        workspace_manager_initialized=False,
        approval_service_initialized=False,
    )

    assert response.api_version == "v1"
    assert response.initialized is True
    assert response.execution_enabled is False


def test_contract_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        HealthResponse(
            status="healthy",
            application="engineering-agent",
            version="0.1.0",
            unexpected_field=True,
        )


def test_error_contract() -> None:
    response = ErrorResponse(
        error={
            "code": "CONFIGURATION_ERROR",
            "message": "Invalid application configuration",
        },
        request_id="test-request-001",
    )

    assert response.error.code == "CONFIGURATION_ERROR"
    assert response.request_id == "test-request-001"


def test_health_endpoint_uses_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    validated = HealthResponse.model_validate(response.json())
    assert validated.application == "engineering-agent"


def test_status_endpoint_uses_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/v1/status")

    assert response.status_code == 200
    validated = ApplicationStatusResponse.model_validate(
        response.json()
    )
    assert validated.initialized is True
    assert validated.execution_enabled is False


def test_openapi_exposes_versioned_contracts(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    assert "HealthResponse" in schemas
    assert "ApplicationStatusResponse" in schemas


def test_http_error_uses_standard_error_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    payload = ErrorResponse.model_validate(response.json())
    assert payload.error.code == "NOT_FOUND"
    assert payload.error.message
    assert payload.request_id == response.headers["X-Request-ID"]


def test_request_validation_error_uses_standard_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    @application.get("/test/validation")
    async def validation_endpoint(quantity: int):
        return {"quantity": quantity}

    with TestClient(application) as client:
        response = client.get(
            "/test/validation",
            params={"quantity": "not-an-integer"},
        )

    assert response.status_code == 422
    payload = ErrorResponse.model_validate(response.json())
    assert payload.error.code == "REQUEST_VALIDATION_ERROR"
    assert payload.request_id == response.headers["X-Request-ID"]


def test_unexpected_exception_uses_standard_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    @application.get("/test/failure")
    async def failure_endpoint():
        raise RuntimeError("internal diagnostic detail")

    with TestClient(
        application,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/test/failure")

    assert response.status_code == 500
    payload = ErrorResponse.model_validate(response.json())
    assert payload.error.code == "INTERNAL_SERVER_ERROR"
    assert payload.error.message == "An unexpected error occurred."
    assert "internal diagnostic detail" not in response.text
    assert payload.request_id == response.headers["X-Request-ID"]


def test_successful_response_includes_request_id(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "healthy"


def test_json_formatter_emits_structured_context() -> None:
    stream = StringIO()
    logger = configure_logging(
        application="engineering-agent-test",
        environment="test",
        stream=stream,
    )
    token = set_request_id("request-structured-001")

    try:
        logger.info(
            "structured test event",
            extra={"event": "test_event"},
        )
    finally:
        reset_request_id(token)

    payload = json.loads(stream.getvalue().strip())

    assert payload["application"] == "engineering-agent-test"
    assert payload["environment"] == "test"
    assert payload["request_id"] == "request-structured-001"
    assert payload["level"] == "INFO"
    assert payload["event"] == "test_event"
    assert payload["message"] == "structured test event"
    assert payload["timestamp"].endswith("+00:00")


def test_request_context_is_reset_after_request(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert get_request_id() == "-"


def test_request_ids_differ_between_requests(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        first = client.get("/health")
        second = client.get("/health")

    first_id = first.headers["X-Request-ID"]
    second_id = second.headers["X-Request-ID"]

    assert first_id != second_id


def test_logging_configuration_does_not_change_root_logger() -> None:
    root = logging.getLogger()
    original_level = root.level
    original_handlers = list(root.handlers)

    configure_logging(
        application="engineering-agent-test",
        environment="test",
        stream=StringIO(),
    )

    assert root.level == original_level
    assert root.handlers == original_handlers

def test_http_completion_log_contains_correlated_request_metadata(
    settings,
    monkeypatch,
):
    stream = StringIO()
    monkeypatch.setenv("ENGINEERING_AGENT_ENVIRONMENT", "test")

    configure_logging(
        application="engineering-agent",
        environment="test",
        stream=stream,
    )

    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200

    records = [
        json.loads(line)
        for line in stream.getvalue().splitlines()
        if line.strip()
    ]

    completion_records = [
        record
        for record in records
        if record.get("event") == "http_request_completed"
    ]

    assert completion_records

    record = completion_records[-1]

    assert record["service"] == "engineering-agent-api"
    assert record["application"] == "engineering-agent"
    assert record["environment"] == "test"
    assert record["request_id"] == response.headers["X-Request-ID"]
    assert record["http_method"] == "GET"
    assert record["http_path"] == "/health"
    assert record["http_status"] == 200
    assert isinstance(record["duration_ms"], (int, float))
    assert record["duration_ms"] >= 0


def test_unexpected_exception_retains_traceback_in_internal_logs(
    settings,
    monkeypatch,
):
    stream = StringIO()
    monkeypatch.setenv("ENGINEERING_AGENT_ENVIRONMENT", "test")

    configure_logging(
        application="engineering-agent",
        environment="test",
        stream=stream,
    )

    application = create_app(settings)

    def raise_test_exception():
        raise RuntimeError("private diagnostic detail")

    application.add_api_route(
        "/_test/raise",
        raise_test_exception,
        methods=["GET"],
    )

    with TestClient(
        application,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/_test/raise")

    assert response.status_code == 500
    assert "private diagnostic detail" not in response.text

    records = [
        json.loads(line)
        for line in stream.getvalue().splitlines()
        if line.strip()
    ]

    exception_records = [
        record
        for record in records
        if record.get("event") == "unhandled_exception"
    ]

    assert exception_records

    record = exception_records[-1]

    assert record["level"] == "ERROR"
    assert record["request_id"] == response.headers["X-Request-ID"]
    assert "RuntimeError" in record["exception"]
    assert "private diagnostic detail" in record["exception"]

def test_valid_traceparent_is_continued_with_new_server_span(
    settings,
    monkeypatch,
):
    stream = StringIO()
    monkeypatch.setenv("ENGINEERING_AGENT_ENVIRONMENT", "test")

    configure_logging(
        application="engineering-agent",
        environment="test",
        stream=stream,
    )

    application = create_app(settings)

    incoming_trace_id = "1234567890abcdef1234567890abcdef"
    incoming_parent_id = "1234567890abcdef"
    incoming_traceparent = (
        f"00-{incoming_trace_id}-{incoming_parent_id}-01"
    )

    with TestClient(application) as client:
        response = client.get(
            "/health",
            headers={"traceparent": incoming_traceparent},
        )

    assert response.status_code == 200

    returned_traceparent = response.headers["traceparent"]
    version, trace_id, server_span_id, flags = (
        returned_traceparent.split("-")
    )

    assert version == "00"
    assert trace_id == incoming_trace_id
    assert server_span_id != incoming_parent_id
    assert len(server_span_id) == 16
    assert flags == "01"

    records = [
        json.loads(line)
        for line in stream.getvalue().splitlines()
        if line.strip()
    ]

    completion = [
        record
        for record in records
        if record.get("event") == "http_request_completed"
    ][-1]

    assert completion["trace_id"] == incoming_trace_id
    assert completion["span_id"] == server_span_id
    assert completion["parent_span_id"] == incoming_parent_id
    assert completion["trace_flags"] == "01"


def test_invalid_traceparent_creates_new_trace(
    settings,
):
    application = create_app(settings)

    invalid_traceparent = (
        "00-00000000000000000000000000000000-"
        "1234567890abcdef-01"
    )

    with TestClient(application) as client:
        response = client.get(
            "/health",
            headers={"traceparent": invalid_traceparent},
        )

    assert response.status_code == 200

    returned = response.headers["traceparent"]
    version, trace_id, span_id, flags = returned.split("-")

    assert version == "00"
    assert trace_id != "0" * 32
    assert span_id != "0" * 16
    assert flags == "00"


def test_missing_traceparent_creates_new_trace(
    settings,
):
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200

    returned = response.headers["traceparent"]
    version, trace_id, span_id, flags = returned.split("-")

    assert version == "00"
    assert len(trace_id) == 32
    assert len(span_id) == 16
    assert flags == "00"


def test_trace_context_is_reset_after_request(
    settings,
):
    from backend.app.engineering_agent.tracing import (
        get_trace_context,
    )

    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert get_trace_context() is None

class _TestRuntimeIdentityProvider:
    def __init__(self, principal=None, error=None):
        self.principal = principal
        self.error = error
        self.calls = 0

    async def authenticate(self, *, authentication_context):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.principal


def _test_runtime_principal(
    permissions=frozenset({"runtime:dispatch"}),
):
    return AuthenticatedRuntimePrincipal(
        tenant_id="trusted-test-tenant",
        actor_id="authenticated-test-actor",
        permissions=permissions,
    )


def test_runtime_dispatch_fails_closed_without_identity_provider(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.post(
            "/v1/workflows/workflow-test-001/dispatch",
            json={"dispatch_cycle_id": "cycle-test-001"},
        )

    assert response.status_code == 503


def test_runtime_dispatch_rejects_invalid_credentials(
    settings: EngineeringAgentSettings,
) -> None:
    provider = _TestRuntimeIdentityProvider(
        error=RuntimeAuthenticationError("invalid credentials")
    )
    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/workflows/workflow-test-001/dispatch",
            json={"dispatch_cycle_id": "cycle-test-001"},
        )

    assert response.status_code == 401
    assert provider.calls == 1


def test_runtime_dispatch_fails_closed_on_identity_provider_error(
    settings: EngineeringAgentSettings,
) -> None:
    provider = _TestRuntimeIdentityProvider(
        error=RuntimeIdentityProviderError("identity service unavailable")
    )
    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/workflows/workflow-test-001/dispatch",
            json={"dispatch_cycle_id": "cycle-test-001"},
        )

    assert response.status_code == 503
    assert provider.calls == 1


def test_runtime_dispatch_rejects_missing_dispatch_permission(
    settings: EngineeringAgentSettings,
) -> None:
    provider = _TestRuntimeIdentityProvider(
        principal=_test_runtime_principal(permissions=frozenset())
    )
    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/workflows/workflow-test-001/dispatch",
            json={"dispatch_cycle_id": "cycle-test-001"},
        )

    assert response.status_code == 403
    assert provider.calls == 1


def test_runtime_dispatch_rejects_caller_supplied_tenant_id(
    settings: EngineeringAgentSettings,
) -> None:
    provider = _TestRuntimeIdentityProvider(
        principal=_test_runtime_principal()
    )
    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/workflows/workflow-test-001/dispatch",
            json={
                "dispatch_cycle_id": "cycle-test-001",
                "tenant_id": "caller-selected-tenant",
            },
        )

    assert response.status_code == 422
    assert provider.calls == 0


def test_runtime_dispatch_uses_authenticated_tenant_and_redacts_routing_only_result(
    settings,
    monkeypatch,
):
    provider = _TestRuntimeIdentityProvider(
        principal=AuthenticatedRuntimePrincipal(
            tenant_id="trusted-tenant-42",
            actor_id="authenticated-actor-42",
            permissions=frozenset({"runtime:dispatch"}),
        )
    )

    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    captured = {}

    routing_decision = AgentWorkflowRoutingDecision(
        tenant_id="trusted-tenant-42",
        workflow_id="workflow-test-001",
        workflow_type="engineering",
        current_state=WorkflowState.CREATED,
        action=WorkflowRoutingAction.PREPARE_ACTIVATION,
        allowed_transitions=(
            WorkflowState.ACTIVE,
            WorkflowState.CANCELLED,
        ),
        requires_human_approval=False,
        terminal=False,
        reason="Workflow is created and may be prepared for activation.",
    )

    coordination_result = GovernanceAgentRuntimeCoordinationResult(
        routing_decision=routing_decision,
        dispatch_result=None,
    )

    def fake_dispatch_workflow(**kwargs):
        captured.update(kwargs)
        return coordination_result

    with TestClient(application) as client:
        container = application.state.container

        monkeypatch.setattr(
            container.runtime_operations,
            "dispatch_workflow",
            fake_dispatch_workflow,
        )

        response = client.post(
            "/v1/workflows/workflow-test-001/dispatch",
            headers={
                "X-Tenant-ID": "attacker-selected-tenant",
            },
            json={
                "dispatch_cycle_id": "dispatch-cycle-test-001",
            },
        )

    assert response.status_code == 200
    assert provider.calls == 1

    assert captured["tenant_id"] == "trusted-tenant-42"
    assert captured["tenant_id"] != "attacker-selected-tenant"
    assert captured["workflow_id"] == "workflow-test-001"

    body = response.json()

    assert body["dispatch_performed"] is False
    assert body["dispatch_result"] is None
    assert body["routing_decision"]["current_state"] == "created"
    assert body["routing_decision"]["action"] == "prepare_activation"

    assert "tenant_id" not in body
    assert "trusted-tenant-42" not in response.text
    assert "attacker-selected-tenant" not in response.text


def test_runtime_dispatch_sanitizes_bounded_dispatch_outcomes(
    settings,
    monkeypatch,
):
    provider = _TestRuntimeIdentityProvider(
        principal=AuthenticatedRuntimePrincipal(
            tenant_id="trusted-tenant-dispatch",
            actor_id="authenticated-dispatch-actor",
            permissions=frozenset({"runtime:dispatch"}),
        )
    )

    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

    claimed_record = AgentWorkItemRecord(
        work_item_id="work-item-claimed",
        tenant_id="trusted-tenant-dispatch",
        workflow_id="workflow-test-002",
        task_type="code.review",
        state=WorkItemState.CLAIMED,
        correlation_id="correlation-claimed",
        idempotency_key="idempotency-claimed",
        input_json='{"secret_payload":"DO_NOT_EXPOSE_RECORD_PAYLOAD"}',
        created_at=now,
        updated_at=now,
        available_at=now,
        attempt_count=1,
        max_attempts=3,
        assigned_worker_id="secret-worker-id",
        lease_expires_at=now.replace(minute=5),
        fencing_token=1,
        last_error_code=None,
        last_error_message=None,
    )

    dispatch_result = BoundedDispatchResult(
        tenant_id="trusted-tenant-dispatch",
        workflow_id="workflow-test-002",
        dispatch_cycle_id="dispatch-cycle-test-002",
        dispatched_at=now,
        candidate_limit=10,
        claim_limit=3,
        candidate_count=3,
        scanned_count=3,
        claimed_count=1,
        outcomes=(
            AgentWorkItemDispatchOutcome(
                work_item_id="work-item-claimed",
                status="claimed",
                reason_codes=(),
                worker_id="secret-worker-id",
                registration_revision=17,
                record=claimed_record,
            ),
            AgentWorkItemDispatchOutcome(
                work_item_id="work-item-unmatched",
                status="unmatched",
                reason_codes=("worker-specific-secret-reason",),
            ),
            AgentWorkItemDispatchOutcome(
                work_item_id="work-item-rejected",
                status="rejected",
                reason_codes=(
                    "claim_conflict:DO_NOT_EXPOSE_RAW_REJECTION",
                ),
            ),
        ),
    )

    routing_decision = AgentWorkflowRoutingDecision(
        tenant_id="trusted-tenant-dispatch",
        workflow_id="workflow-test-002",
        workflow_type="engineering",
        current_state=WorkflowState.ACTIVE,
        action=WorkflowRoutingAction.COORDINATE_WORK,
        allowed_transitions=(
            WorkflowState.AWAITING_APPROVAL,
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        ),
        requires_human_approval=False,
        terminal=False,
        reason="Workflow is active and may coordinate bounded work.",
    )

    coordination_result = GovernanceAgentRuntimeCoordinationResult(
        routing_decision=routing_decision,
        dispatch_result=dispatch_result,
    )

    captured = {}

    def fake_dispatch_workflow(**kwargs):
        captured.update(kwargs)
        return coordination_result

    with TestClient(application) as client:
        container = application.state.container

        monkeypatch.setattr(
            container.runtime_operations,
            "dispatch_workflow",
            fake_dispatch_workflow,
        )

        response = client.post(
            "/v1/workflows/workflow-test-002/dispatch",
            headers={
                "X-Tenant-ID": "attacker-selected-tenant",
            },
            json={
                "dispatch_cycle_id": "dispatch-cycle-test-002",
            },
        )

    assert response.status_code == 200
    assert provider.calls == 1
    assert captured["tenant_id"] == "trusted-tenant-dispatch"
    assert captured["workflow_id"] == "workflow-test-002"

    body = response.json()

    assert body["dispatch_performed"] is True
    assert set(body) == {
        "routing_decision",
        "dispatch_performed",
        "dispatch_result",
    }

    public_dispatch = body["dispatch_result"]

    assert set(public_dispatch) == {
        "dispatch_cycle_id",
        "dispatched_at",
        "candidate_limit",
        "claim_limit",
        "candidate_count",
        "scanned_count",
        "claimed_count",
        "outcomes",
    }

    assert public_dispatch["dispatch_cycle_id"] == "dispatch-cycle-test-002"
    assert public_dispatch["candidate_limit"] == 10
    assert public_dispatch["claim_limit"] == 3
    assert public_dispatch["candidate_count"] == 3
    assert public_dispatch["scanned_count"] == 3
    assert public_dispatch["claimed_count"] == 1

    assert public_dispatch["outcomes"] == [
        {
            "work_item_id": "work-item-claimed",
            "status": "claimed",
            "reason_codes": [],
        },
        {
            "work_item_id": "work-item-unmatched",
            "status": "unmatched",
            "reason_codes": ["no_eligible_worker"],
        },
        {
            "work_item_id": "work-item-rejected",
            "status": "rejected",
            "reason_codes": ["claim_conflict"],
        },
    ]

    for outcome in public_dispatch["outcomes"]:
        assert set(outcome) == {
            "work_item_id",
            "status",
            "reason_codes",
        }

    for secret in (
        "trusted-tenant-dispatch",
        "attacker-selected-tenant",
        "secret-worker-id",
        "worker-specific-secret-reason",
        "DO_NOT_EXPOSE_RECORD_PAYLOAD",
        "DO_NOT_EXPOSE_RAW_REJECTION",
        "registration_revision",
        "assigned_worker_id",
    ):
        assert secret not in response.text


def test_runtime_dispatch_http_uses_real_coordinator_and_dispatcher(
    settings,
):
    tenant_id = "trusted-http-tenant-a"
    other_tenant_id = "isolated-http-tenant-b"
    workflow_id = "workflow-http-integration-001"

    provider = _TestRuntimeIdentityProvider(
        principal=AuthenticatedRuntimePrincipal(
            tenant_id=tenant_id,
            actor_id="authenticated-http-actor",
            permissions=frozenset({"runtime:dispatch"}),
        )
    )

    application = create_app(
        settings,
        runtime_identity_provider=provider,
    )

    with TestClient(application) as client:
        container = application.state.container

        # Create the same workflow identifier under two tenants.
        for current_tenant in (tenant_id, other_tenant_id):
            container.workflow_store.create_workflow(
                tenant_id=current_tenant,
                workflow_id=workflow_id,
                workflow_type="engineering",
                idempotency_key=f"create-{current_tenant}",
                payload={"source": "http-runtime-integration-test"},
            )

            container.workflow_store.transition_workflow(
                tenant_id=current_tenant,
                workflow_id=workflow_id,
                target_state=WorkflowState.ACTIVE,
                idempotency_key=f"activate-{current_tenant}",
                event_type="workflow.activated",
            )

            container.work_item_store.create_work_item(
                tenant_id=current_tenant,
                workflow_id=workflow_id,
                work_item_id=("work-item-http-a" if current_tenant == tenant_id else "work-item-http-b"),
                task_type="code.review",
                idempotency_key=f"create-work-{current_tenant}",
                input_payload={"task": "review"},
            )

            container.worker_registry_store.register_worker(
                tenant_id=current_tenant,
                worker_id=f"worker-{current_tenant}",
                worker_type="engineering",
                version="1.0.0",
                supported_task_types=("code.review",),
                capabilities=("runtime.python", "tool.pytest"),
                enabled=True,
            )

        response = client.post(
            f"/v1/workflows/{workflow_id}/dispatch",
            headers={
                "X-Tenant-ID": other_tenant_id,
            },
            json={
                "dispatch_cycle_id": "http-integration-cycle-001",
                "max_candidates": 10,
                "max_claims": 3,
            },
        )

        # Inspect both tenants' persisted work-item states.
        tenant_a_item = container.work_item_store.get_work_item(
            tenant_id=tenant_id,
            work_item_id="work-item-http-a",
        )

        tenant_b_item = container.work_item_store.get_work_item(
            tenant_id=other_tenant_id,
            work_item_id="work-item-http-b",
        )

    assert response.status_code == 200
    assert provider.calls == 1

    body = response.json()

    assert body["dispatch_performed"] is True
    assert body["routing_decision"]["current_state"] == "active"
    assert body["routing_decision"]["action"] == "coordinate_work"

    dispatch = body["dispatch_result"]

    assert dispatch["candidate_limit"] == 10
    assert dispatch["claim_limit"] == 3
    assert dispatch["candidate_count"] == 1
    assert dispatch["scanned_count"] == 1
    assert dispatch["claimed_count"] == 1

    assert dispatch["outcomes"] == [
        {
            "work_item_id": "work-item-http-a",
            "status": "claimed",
            "reason_codes": [],
        }
    ]

    # The authenticated tenant's item was claimed.
    assert tenant_a_item.state is WorkItemState.CLAIMED
    assert tenant_a_item.assigned_worker_id == f"worker-{tenant_id}"

    # The caller-selected tenant's item was not touched.
    assert tenant_b_item.state is WorkItemState.PENDING
    assert tenant_b_item.assigned_worker_id is None

    # Dispatch claims work; it does not execute the worker.
    assert tenant_a_item.state is not WorkItemState.RUNNING
    assert tenant_a_item.state is not WorkItemState.SUCCEEDED

    # Internal tenant and worker identifiers are not exposed.
    assert tenant_id not in response.text
    assert other_tenant_id not in response.text
    assert f"worker-{tenant_id}" not in response.text
    assert f"worker-{other_tenant_id}" not in response.text