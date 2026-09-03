from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.gagf.governance_assessment_api_registration import (
    ASSESSMENT_API_REGISTERED_STATE_KEY,
    AssessmentApiRegistrationError,
    register_governance_assessment_api,
)
from backend.app.gagf.governance_assessment_application import (
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)


def route_paths(app: FastAPI) -> tuple[str, ...]:
    return tuple(
        path
        for route in app.routes
        if (path := getattr(route, "path", None)) is not None
    )


def build_execute_payload() -> dict[str, Any]:
    return {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "assessment_name": "Governance Runway Assessment",
        "workflow_names": [
            "Incident Management",
        ],
        "organizational_units": [
            "IT Operations",
        ],
        "period_start": "2026-01-01",
        "period_end": "2026-06-30",
        "objectives": [
            "Reduce governance friction",
        ],
        "expected_outcomes": [
            "Faster completion",
        ],
        "evidence_requirements": [
            {
                "requirement_id": "required-csv",
                "source_kind": "csv",
                "description": "Workflow evidence",
                "required": True,
                "minimum_record_count": 4,
            }
        ],
        "evidence_inputs": [
            {
                "source": {
                    "source_id": "source-001",
                    "kind": "csv",
                    "display_name": "Workflow Export",
                },
                "csv_text": (
                    "event_id,event_type,occurred_at,"
                    "work_item_id\n"
                    "event-001,APPROVAL_DELAYED,"
                    "2026-01-01T12:00:00Z,TICKET-1\n"
                    "event-002,APPROVAL_DELAYED,"
                    "2026-01-01T13:00:00Z,TICKET-2\n"
                    "event-003,WORK_BLOCKED,"
                    "2026-01-02T12:00:00Z,TICKET-3\n"
                    "event-004,ESCALATION,"
                    "2026-01-03T12:00:00Z,TICKET-4\n"
                ),
            }
        ],
        "client_display_name": "ACME Corporation",
        "prepared_by": "FIP Governance Services",
        "maximum_priorities": 3,
    }


def execute_headers() -> dict[str, str]:
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-001",
        "X-Actor-Roles": "assessment:execute",
    }


def test_registration_adds_assessment_routes(
    tmp_path,
):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    assert (
        "/api/v1/governance-assessments/execute"
        in route_paths(app)
    )


def test_registration_returns_application_service(
    tmp_path,
):
    app = FastAPI()

    service = register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    assert isinstance(
        service,
        GovernanceAssessmentApplicationService,
    )


def test_registration_stores_service_on_app_state(
    tmp_path,
):
    app = FastAPI()

    service = register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    assert (
        app.state.governance_assessment_service
        is service
    )


def test_registration_stores_repository_on_app_state(
    tmp_path,
):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    assert isinstance(
        app.state.governance_assessment_repository,
        GovernanceAssessmentRepository,
    )


def test_registration_sets_state_flag(
    tmp_path,
):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    assert getattr(
        app.state,
        ASSESSMENT_API_REGISTERED_STATE_KEY,
    ) is True


def test_registration_is_idempotent(
    tmp_path,
):
    app = FastAPI()

    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    first_service = (
        register_governance_assessment_api(
            app=app,
            database_path=database_path,
        )
    )

    first_route_paths = route_paths(
        app
    )

    second_service = (
        register_governance_assessment_api(
            app=app,
            database_path=database_path,
        )
    )

    assert (
        first_service
        is second_service
    )

    assert (
        route_paths(app)
        == first_route_paths
    )


def test_registration_accepts_existing_repository(
    tmp_path,
):
    app = FastAPI()

    repository = GovernanceAssessmentRepository(
        tmp_path
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        repository=repository,
    )

    assert (
        app.state.governance_assessment_repository
        is repository
    )


def test_registration_creates_parent_directory(
    tmp_path,
):
    app = FastAPI()

    database_path = (
        tmp_path
        / "nested"
        / "data"
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    assert (
        database_path.parent.exists()
    )

    assert (
        database_path.exists()
    )


def test_registration_rejects_repository_and_path(
    tmp_path,
):
    app = FastAPI()

    repository = GovernanceAssessmentRepository(
        tmp_path
        / "first.sqlite3"
    )

    with pytest.raises(
        AssessmentApiRegistrationError,
        match="not both",
    ):
        register_governance_assessment_api(
            app=app,
            repository=repository,
            database_path=(
                tmp_path
                / "second.sqlite3"
            ),
        )


def test_registration_requires_storage_configuration():
    app = FastAPI()

    with pytest.raises(
        AssessmentApiRegistrationError,
        match="required",
    ):
        register_governance_assessment_api(
            app=app
        )


def test_registered_list_endpoint_is_reachable(
    tmp_path,
):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    client = TestClient(
        app
    )

    response = client.get(
        "/api/v1/governance-assessments",
        params={
            "tenant_id": "tenant-alpha",
        },
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "actor-001",
            "X-Actor-Roles": "assessment:read",
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "items": [],
        "count": 0,
    }


def test_registered_unknown_assessment_returns_404(
    tmp_path,
):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    client = TestClient(
        app
    )

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/missing",
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "actor-001",
            "X-Actor-Roles": "assessment:read",
        },
    )

    assert (
        response.status_code
        == 404
    )


def test_database_path_can_be_a_string(
    tmp_path,
):
    app = FastAPI()

    database_path = str(
        tmp_path
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    assert (
        Path(
            database_path
        ).exists()
    )


def test_registration_stores_execution_input_binding_service(
    tmp_path,
):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    assert isinstance(
        app.state.governance_commercial_paid_assessment_execution_input_binding_service,
        GovernanceCommercialPaidAssessmentExecutionInputBindingService,
    )


def test_registration_sets_execution_input_binding_directory(
    tmp_path,
):
    app = FastAPI()

    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    expected_directory = (
        database_path.parent
        / "governance_paid_assessment_execution_inputs"
    )

    assert (
        app.state.governance_paid_assessment_execution_input_directory
        == expected_directory
    )

    binding_service = (
        app.state
        .governance_commercial_paid_assessment_execution_input_binding_service
    )

    assert (
        binding_service.binding_directory
        == expected_directory
    )


def test_registered_execute_creates_execution_input_binding(
    tmp_path,
):
    app = FastAPI()

    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    client = TestClient(
        app
    )

    response = client.post(
        "/api/v1/governance-assessments/execute",
        json=build_execute_payload(),
        headers=execute_headers(),
    )

    assert (
        response.status_code
        == 201
    )

    binding_service = (
        app.state
        .governance_commercial_paid_assessment_execution_input_binding_service
    )

    binding = binding_service.get(
        hierarchy_key=(
            "tenant-alpha/client-acme/"
            "engagement-001/assessment-001"
        )
    )

    assert (
        binding.reused_existing
        is True
    )

    assert (
        binding.execution_input_hash
    )

    assert (
        binding.binding_hash
    )

    assert (
        len(
            binding.evidence_inputs
        )
        == 1
    )

    assert (
        binding.evidence_inputs[0]
        .source_id
        == "source-001"
    )

    assert (
        binding.evidence_inputs[0]
        .source_kind
        == "csv"
    )

    assert (
        "event-001,APPROVAL_DELAYED"
        in binding.evidence_inputs[0]
        .csv_text
    )


def test_registered_execute_reuses_identical_binding(
    tmp_path,
):
    app = FastAPI()

    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    client = TestClient(
        app
    )

    first = client.post(
        "/api/v1/governance-assessments/execute",
        json=build_execute_payload(),
        headers=execute_headers(),
    )

    second = client.post(
        "/api/v1/governance-assessments/execute",
        json=build_execute_payload(),
        headers=execute_headers(),
    )

    assert (
        first.status_code
        == 201
    )

    assert (
        second.status_code
        == 201
    )

    assert (
        first.json()[
            "application_hash"
        ]
        == second.json()[
            "application_hash"
        ]
    )

    binding_service = (
        app.state
        .governance_commercial_paid_assessment_execution_input_binding_service
    )

    binding = binding_service.get(
        hierarchy_key=(
            "tenant-alpha/client-acme/"
            "engagement-001/assessment-001"
        )
    )

    assert (
        binding.reused_existing
        is True
    )


def test_registered_execute_rejects_changed_bound_evidence(
    tmp_path,
):
    app = FastAPI()

    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    client = TestClient(
        app
    )

    first_payload = (
        build_execute_payload()
    )

    first = client.post(
        "/api/v1/governance-assessments/execute",
        json=first_payload,
        headers=execute_headers(),
    )

    assert (
        first.status_code
        == 201
    )

    changed_payload = (
        build_execute_payload()
    )

    changed_payload[
        "evidence_inputs"
    ][0]["csv_text"] = (
        "event_id,event_type,occurred_at,"
        "work_item_id\n"
        "event-999,WORK_BLOCKED,"
        "2026-01-05T12:00:00Z,TICKET-999\n"
    )

    changed = client.post(
        "/api/v1/governance-assessments/execute",
        json=changed_payload,
        headers=execute_headers(),
    )

    assert (
        changed.status_code
        == 409
    )

    assert (
        changed.json()[
            "detail"
        ]["code"]
        == "ASSESSMENT_EXECUTION_INPUT_BINDING_ERROR"
    )

    assert (
        "different execution input hash"
        in changed.json()[
            "detail"
        ]["message"]
    )