from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.gagf.governance_assessment_api import (
    create_governance_assessment_router,
)
from backend.app.gagf.governance_assessment_application import (
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    CommercialPaidAssessmentExecutionInputBindingError,
)


def build_payload(tenant_id="tenant-alpha"):
    return {
        "tenant_id": tenant_id,
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "assessment_name": "Governance Runway Assessment",
        "workflow_names": ["Incident Management"],
        "organizational_units": ["IT Operations"],
        "period_start": "2026-01-01",
        "period_end": "2026-06-30",
        "objectives": ["Reduce governance friction"],
        "expected_outcomes": ["Faster completion"],
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


@pytest.fixture
def repository(tmp_path):
    return GovernanceAssessmentRepository(
        tmp_path / "api.sqlite3"
    )


@pytest.fixture
def client(repository):
    service = GovernanceAssessmentApplicationService(
        repository=repository
    )
    app = FastAPI()
    app.include_router(
        create_governance_assessment_router(
            service=service
        )
    )
    return TestClient(app)


def execute(client, tenant_id="tenant-alpha"):
    return client.post(
        "/api/v1/governance-assessments/execute",
        json=build_payload(tenant_id),
    )


def test_execute_returns_created(client):
    response = execute(client)

    assert response.status_code == 201
    assert response.json()["completed"] is True


def test_execute_returns_artifact_count(client):
    body = execute(client).json()

    assert body["artifact_count"] == 10
    assert body["application_hash"]


def test_execute_preserves_hierarchy(client):
    body = execute(client).json()

    assert body["hierarchy_key"] == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_execute_is_idempotent(client):
    first = execute(client)
    second = execute(client)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["application_hash"] == (
        second.json()["application_hash"]
    )


def test_execute_rejects_missing_workflows(client):
    payload = build_payload()
    payload["workflow_names"] = []

    response = client.post(
        "/api/v1/governance-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422


def test_execute_rejects_invalid_date(client):
    payload = build_payload()
    payload["period_start"] = "not-a-date"

    response = client.post(
        "/api/v1/governance-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422


def test_get_assessment_returns_record(client):
    execute(client)

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "complete"


def test_get_assessment_is_tenant_scoped(client):
    execute(client)

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-beta/client-acme/"
        "engagement-001/assessment-001"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_NOT_FOUND"
    )


def test_list_assessments_is_tenant_scoped(client):
    execute(client)

    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_list_assessments_rejects_orphan_engagement(client):
    response = client.get(
        "/api/v1/governance-assessments",
        params={
            "tenant_id": "tenant-alpha",
            "engagement_id": "engagement-001",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_QUERY_ERROR"
    )


def test_list_artifacts_returns_ordered_set(client):
    execute(client)

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001/artifacts"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 10
    assert [
        item["sequence_number"]
        for item in response.json()["items"]
    ] == list(range(1, 11))


def test_list_artifacts_filters_by_type(client):
    execute(client)

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001/artifacts",
        params={"artifact_type": "client-report-package"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_summary_returns_verified_chain(client):
    execute(client)

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001/summary"
    )

    assert response.status_code == 200
    assert response.json()["repository_chain_valid"] is True
    assert response.json()["artifact_count"] == 10


def test_summary_missing_assessment_returns_404(client):
    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/missing/summary"
    )

    assert response.status_code == 404


def test_two_tenants_remain_isolated(client):
    alpha = execute(client, "tenant-alpha")
    beta = execute(client, "tenant-beta")

    assert alpha.status_code == 201
    assert beta.status_code == 201
    assert alpha.json()["application_hash"] != (
        beta.json()["application_hash"]
    )
def test_execute_binds_execution_input_before_application(
    repository,
):
    class RecordingBindingService:
        def __init__(self):
            self.requests = []

        def bind(self, *, request):
            self.requests.append(request)

    binding_service = RecordingBindingService()

    service = GovernanceAssessmentApplicationService(
        repository=repository
    )

    app = FastAPI()
    app.include_router(
        create_governance_assessment_router(
            service=service,
            execution_input_binding_service=(
                binding_service
            ),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/governance-assessments/execute",
        json=build_payload(),
    )

    assert response.status_code == 201

    assert len(
        binding_service.requests
    ) == 1

    bound_request = (
        binding_service.requests[0]
    )

    assert bound_request.context.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )

    assert len(
        bound_request.evidence_inputs
    ) == 1

    assert (
        bound_request.evidence_inputs[0].csv_text
        == build_payload()[
            "evidence_inputs"
        ][0]["csv_text"]
    )


def test_execute_returns_binding_conflict(
    repository,
):
    class RejectingBindingService:
        def bind(self, *, request):
            raise (
                CommercialPaidAssessmentExecutionInputBindingError(
                    "immutable execution-input binding already "
                    "exists with a different execution input hash"
                )
            )

    service = GovernanceAssessmentApplicationService(
        repository=repository
    )

    app = FastAPI()
    app.include_router(
        create_governance_assessment_router(
            service=service,
            execution_input_binding_service=(
                RejectingBindingService()
            ),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/governance-assessments/execute",
        json=build_payload(),
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]["code"]
        == "ASSESSMENT_EXECUTION_INPUT_BINDING_ERROR"
    )

    assert (
        "different execution input hash"
        in response.json()["detail"]["message"]
    )


def test_binding_conflict_prevents_application_execution(
    repository,
):
    class RejectingBindingService:
        def bind(self, *, request):
            raise (
                CommercialPaidAssessmentExecutionInputBindingError(
                    "binding conflict"
                )
            )

    class RecordingApplicationService(
        GovernanceAssessmentApplicationService
    ):
        def __init__(self, *, repository):
            super().__init__(
                repository=repository
            )
            self.execute_called = False

        def execute(self, *, request):
            self.execute_called = True
            return super().execute(
                request=request
            )

    service = RecordingApplicationService(
        repository=repository
    )

    app = FastAPI()
    app.include_router(
        create_governance_assessment_router(
            service=service,
            execution_input_binding_service=(
                RejectingBindingService()
            ),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/governance-assessments/execute",
        json=build_payload(),
    )

    assert response.status_code == 409
    assert service.execute_called is False
