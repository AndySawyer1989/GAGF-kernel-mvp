from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_api import (
    create_governance_commercial_paid_assessment_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_results_read_model import (
    CommercialPaidAssessmentResultsReadModelError,
)


HIERARCHY = (
    "tenant-001/"
    "client-001/"
    "engagement-001/"
    "assessment-001"
)

RESULTS_PATH = (
    "/api/v1/governance-paid-assessments/"
    "tenant-001/"
    "client-001/"
    "engagement-001/"
    "assessment-001/"
    "results"
)


class FakeBindingService:
    pass


@dataclass(frozen=True)
class FakeReadModel:
    payload: dict

    def to_dict(self) -> dict:
        return self.payload


class FakeResultsReadModelService:
    def __init__(
        self,
        *,
        payload: dict | None = None,
        error: str | None = None,
    ) -> None:
        self.payload = payload
        self.error = error
        self.calls: list[dict[str, str]] = []

    def read(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> FakeReadModel:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
            }
        )

        if self.error is not None:
            raise CommercialPaidAssessmentResultsReadModelError(
                self.error
            )

        assert self.payload is not None

        return FakeReadModel(
            payload=self.payload
        )


def safe_payload() -> dict:
    return {
        "read_model_type": (
            "governance-commercial-paid-assessment-results-read-model"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": "tenant-001",
        "client_id": "client-001",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "assessment_name": "Governance Health Assessment",
        "hierarchy_key": HIERARCHY,
        "execution_disposition": "executed",
        "execution_status_hash": "status-hash-001",
        "execution_input_binding_hash": "binding-hash-001",
        "assessment_execution_request_hash": "request-hash-001",
        "artifact_count": 10,
        "repository_chain_valid": True,
        "artifact_inventory": [
            {
                "artifact_id": "artifact-001",
                "artifact_type": "scope-configuration",
                "artifact_hash": "artifact-hash-001",
                "sequence_number": 1,
                "chain_hash": "chain-hash-001",
                "schema_version": "1.0.0",
            }
        ],
        "result_artifacts": [
            {
                "artifact_id": "artifact-003",
                "artifact_type": "evidence-quality",
                "artifact_hash": "artifact-hash-003",
                "payload": {
                    "quality_score": 0.95
                },
                "created_at": "2026-09-02T12:00:00+00:00",
                "sequence_number": 3,
                "previous_artifact_hash": "artifact-hash-002",
                "chain_hash": "chain-hash-003",
                "schema_version": "1.0.0",
            }
        ],
        "boundaries": {
            "read_model_is_read_only": True,
            "read_model_is_not_execution_authority": True,
            "read_model_is_not_recovery_authority": True,
            "read_model_is_not_delivery_approval": True,
            "repository_path_not_exposed": True,
            "raw_evidence_payloads_not_exposed": True,
            "evidence_intake_payload_not_exposed": True,
            "scope_configuration_payload_not_exposed": True,
            "result_payloads_are_canonical_paid_artifacts": True,
        },
    }


def build_client(
    tmp_path: Path,
    *,
    results_service: FakeResultsReadModelService,
) -> TestClient:
    execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                tmp_path
                / "paid-assessments"
            )
        )
    )

    app = FastAPI()

    router = (
        create_governance_commercial_paid_assessment_router(
            service=execution_service,
            execution_input_binding_service=(
                FakeBindingService()  # type: ignore[arg-type]
            ),
            results_read_model_service=(
                results_service  # type: ignore[arg-type]
            ),
        )
    )

    app.include_router(router)

    return TestClient(app)


def test_results_endpoint_returns_safe_read_model(
    tmp_path: Path,
) -> None:
    results_service = FakeResultsReadModelService(
        payload=safe_payload()
    )

    client = build_client(
        tmp_path,
        results_service=results_service,
    )

    response = client.get(
        RESULTS_PATH
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["hierarchy_key"] == HIERARCHY
    assert payload["execution_disposition"] == "executed"
    assert payload["artifact_count"] == 10
    assert payload["repository_chain_valid"] is True

    assert (
        payload["boundaries"][
            "raw_evidence_payloads_not_exposed"
        ]
        is True
    )


def test_results_endpoint_passes_exact_hierarchy(
    tmp_path: Path,
) -> None:
    results_service = FakeResultsReadModelService(
        payload=safe_payload()
    )

    client = build_client(
        tmp_path,
        results_service=results_service,
    )

    response = client.get(
        RESULTS_PATH
    )

    assert response.status_code == 200

    assert results_service.calls == [
        {
            "tenant_id": "tenant-001",
            "client_id": "client-001",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
        }
    ]


def test_results_endpoint_maps_read_model_error_to_409(
    tmp_path: Path,
) -> None:
    results_service = FakeResultsReadModelService(
        error=(
            "canonical paid assessment artifact chain is invalid"
        )
    )

    client = build_client(
        tmp_path,
        results_service=results_service,
    )

    response = client.get(
        RESULTS_PATH
    )

    assert response.status_code == 409

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_"
            "RESULTS_READ_MODEL_ERROR"
        )
    )

    assert (
        "artifact chain"
        in payload["detail"]["message"]
    )


def test_results_endpoint_does_not_accept_repository_path(
    tmp_path: Path,
) -> None:
    results_service = FakeResultsReadModelService(
        payload=safe_payload()
    )

    client = build_client(
        tmp_path,
        results_service=results_service,
    )

    response = client.get(
        RESULTS_PATH,
        params={
            "repository_path": (
                "C:/untrusted/browser-selected.sqlite3"
            )
        },
    )

    assert response.status_code == 200

    assert results_service.calls == [
        {
            "tenant_id": "tenant-001",
            "client_id": "client-001",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
        }
    ]


def test_results_endpoint_returns_projection_unchanged(
    tmp_path: Path,
) -> None:
    expected = safe_payload()

    results_service = FakeResultsReadModelService(
        payload=expected
    )

    client = build_client(
        tmp_path,
        results_service=results_service,
    )

    response = client.get(
        RESULTS_PATH
    )

    assert response.status_code == 200
    assert response.json() == expected
