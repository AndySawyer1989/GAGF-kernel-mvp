from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_lifecycle_status import (
    CommercialPaidAssessmentLifecycleStatusError,
)


BASE = (
    "/api/v1/governance-paid-assessments/"
    "tenant-001/client-001/engagement-001/assessment-001"
)


@dataclass
class Result:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class FakeLifecycleStatusService:
    def __init__(
        self,
        *,
        stage: str = "client_receipt_acknowledged",
        error: str | None = None,
    ) -> None:
        self.stage = stage
        self.error = error
        self.calls: list[dict[str, str]] = []

    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> Result:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
            }
        )

        if self.error is not None:
            raise CommercialPaidAssessmentLifecycleStatusError(
                self.error
            )

        if self.stage == "client_response_recorded":
            return Result(
                {
                    "current_stage": "client_response_recorded",
                    "pending_next_step": "none",
                    "delivery_recorded": True,
                    "receipt_acknowledged": True,
                    "client_response_recorded": True,
                    "report_id": "report-001",
                    "findings_disposition": "acknowledged",
                    "recommendations_disposition": "accepted",
                    "lifecycle_artifact_count": 3,
                    "repository_chain_valid": True,
                    "boundaries": {
                        "lifecycle_status_is_read_only_projection": True,
                        "delivery_is_not_receipt": True,
                        "receipt_is_not_response": True,
                        "response_is_not_closeout": True,
                        "response_is_not_intervention_authority": True,
                    },
                }
            )

        return Result(
            {
                "current_stage": "client_receipt_acknowledged",
                "pending_next_step": "record_client_response",
                "delivery_recorded": True,
                "receipt_acknowledged": True,
                "client_response_recorded": False,
                "report_id": "report-001",
                "findings_disposition": None,
                "recommendations_disposition": None,
                "lifecycle_artifact_count": 2,
                "repository_chain_valid": True,
                "boundaries": {
                    "lifecycle_status_is_read_only_projection": True,
                    "delivery_is_not_receipt": True,
                    "receipt_is_not_response": True,
                    "response_is_not_closeout": True,
                    "response_is_not_intervention_authority": True,
                },
            }
        )


class UnusedReadinessService:
    def verify(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "readiness service must not be called"
        )


class UnusedApprovalService:
    def handoff(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "approval service must not be called"
        )


class UnusedRecordingService:
    def record(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "recording service must not be called"
        )


class UnusedDeliveryStatusService:
    def get_status(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "delivery status service must not be called"
        )



class UnusedClientAcknowledgmentService:
    def record(self, **kwargs: Any):
        raise AssertionError(
            "client acknowledgment service must not be called"
        )



class UnusedClientResponseService:
    def record(self, **kwargs: Any):
        raise AssertionError(
            "client response service must not be called"
        )


class UnusedCloseoutStatusService:
    def get_status(self, **kwargs: Any):
        raise AssertionError(
            "closeout status service must not be called"
        )


class UnusedAdministrativeCloseoutService:
    def record(self, **kwargs: Any):
        raise AssertionError(
            "administrative closeout service must not be called"
        )


def build_client(
    lifecycle_status: FakeLifecycleStatusService,
) -> TestClient:
    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=UnusedReadinessService(),
            approval_service=UnusedApprovalService(),
            recording_service=UnusedRecordingService(),
            status_service=UnusedDeliveryStatusService(),
            lifecycle_status_service=lifecycle_status,
            client_acknowledgment_service=UnusedClientAcknowledgmentService(),
            client_response_service=UnusedClientResponseService(),
            closeout_status_service=UnusedCloseoutStatusService(),
            administrative_closeout_service=(
                UnusedAdministrativeCloseoutService()
            ),
        )
    )

    return TestClient(app)


def test_lifecycle_status_projects_receipt_state() -> None:
    lifecycle = FakeLifecycleStatusService()
    client = build_client(lifecycle)

    response = client.get(
        BASE + "/lifecycle-status"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["current_stage"]
        == "client_receipt_acknowledged"
    )
    assert (
        payload["pending_next_step"]
        == "record_client_response"
    )
    assert payload["delivery_recorded"] is True
    assert payload["receipt_acknowledged"] is True
    assert payload["client_response_recorded"] is False
    assert payload["report_id"] == "report-001"
    assert payload["lifecycle_artifact_count"] == 2
    assert payload["repository_chain_valid"] is True

    assert lifecycle.calls == [
        {
            "tenant_id": "tenant-001",
            "client_id": "client-001",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
        }
    ]


def test_lifecycle_status_projects_response_state() -> None:
    lifecycle = FakeLifecycleStatusService(
        stage="client_response_recorded"
    )
    client = build_client(lifecycle)

    response = client.get(
        BASE + "/lifecycle-status"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["current_stage"]
        == "client_response_recorded"
    )
    assert payload["pending_next_step"] == "none"
    assert payload["client_response_recorded"] is True
    assert (
        payload["findings_disposition"]
        == "acknowledged"
    )
    assert (
        payload["recommendations_disposition"]
        == "accepted"
    )


def test_lifecycle_status_conflict_returns_409() -> None:
    lifecycle = FakeLifecycleStatusService(
        error="client response exists without receipt acknowledgment"
    )
    client = build_client(lifecycle)

    response = client.get(
        BASE + "/lifecycle-status"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "client response exists without receipt acknowledgment"
    )


def test_lifecycle_status_response_exposes_no_internal_authority() -> None:
    lifecycle = FakeLifecycleStatusService()
    client = build_client(lifecycle)

    response = client.get(
        BASE + "/lifecycle-status"
    )

    assert response.status_code == 200

    payload = response.json()

    forbidden = (
        "database_path",
        "repository_path",
        "artifact_payload",
        "delivery_event_hash",
        "acknowledgment_hash",
        "response_evidence_hash",
        "intervention_requested",
        "intervention_authorized",
        "execution_authorized",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload

    assert (
        payload["boundaries"][
            "lifecycle_status_is_read_only_projection"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "delivery_is_not_receipt"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "receipt_is_not_response"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "response_is_not_intervention_authority"
        ]
        is True
    )
