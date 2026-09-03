from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_status import (
    CommercialPaidAssessmentDeliveryStatusError,
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


class FakeStatusService:
    def __init__(
        self,
        *,
        found: bool = True,
        error: str | None = None,
    ) -> None:
        self.found = found
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
            raise CommercialPaidAssessmentDeliveryStatusError(
                self.error
            )

        if not self.found:
            return Result(
                {
                    "found": False,
                    "delivery_recorded": False,
                    "delivery_status": None,
                    "report_id": None,
                    "delivered_by": None,
                    "delivered_at": None,
                    "delivery_method": None,
                    "delivery_reference": None,
                    "repository_chain_valid": True,
                    "boundaries": {
                        "delivery_status_is_read_only_projection": True,
                        "delivery_is_not_client_receipt": True,
                    },
                }
            )

        return Result(
            {
                "found": True,
                "delivery_recorded": True,
                "delivery_status": "delivered",
                "report_id": "report-001",
                "delivered_by": "operator-001",
                "delivered_at": "2026-09-03T12:00:00Z",
                "delivery_method": "email",
                "delivery_reference": "message-001",
                "repository_chain_valid": True,
                "boundaries": {
                    "delivery_status_is_read_only_projection": True,
                    "delivery_is_not_client_receipt": True,
                    "delivery_is_not_client_acknowledgment": True,
                    "delivery_is_not_client_response": True,
                    "delivery_is_not_closeout": True,
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


def build_client(
    status: FakeStatusService,
) -> TestClient:
    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=UnusedReadinessService(),
            approval_service=UnusedApprovalService(),
            recording_service=UnusedRecordingService(),
            status_service=status,
        )
    )

    return TestClient(app)


def test_delivery_status_projects_recorded_delivery() -> None:
    status = FakeStatusService()
    client = build_client(status)

    response = client.get(
        BASE + "/delivery-status"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["found"] is True
    assert payload["delivery_recorded"] is True
    assert payload["delivery_status"] == "delivered"
    assert payload["report_id"] == "report-001"
    assert payload["delivered_by"] == "operator-001"
    assert (
        payload["delivered_at"]
        == "2026-09-03T12:00:00Z"
    )
    assert payload["delivery_method"] == "email"
    assert (
        payload["delivery_reference"]
        == "message-001"
    )
    assert payload["repository_chain_valid"] is True

    assert len(status.calls) == 1


def test_delivery_status_not_found_is_200() -> None:
    status = FakeStatusService(
        found=False
    )
    client = build_client(status)

    response = client.get(
        BASE + "/delivery-status"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["found"] is False
    assert payload["delivery_recorded"] is False
    assert payload["delivery_status"] is None


def test_delivery_status_conflict_returns_409() -> None:
    status = FakeStatusService(
        error="governed assessment repository chain is invalid"
    )
    client = build_client(status)

    response = client.get(
        BASE + "/delivery-status"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "governed assessment repository chain is invalid"
    )


def test_delivery_status_response_exposes_no_internal_paths() -> None:
    status = FakeStatusService()
    client = build_client(status)

    response = client.get(
        BASE + "/delivery-status"
    )

    assert response.status_code == 200

    payload = response.json()

    forbidden = (
        "database_path",
        "repository_path",
        "operator_result",
        "approved_delivery_payload",
        "delivery_envelope",
        "artifact_payload",
    )

    for field_name in forbidden:
        assert field_name not in payload

    assert (
        payload["boundaries"][
            "delivery_is_not_client_receipt"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "delivery_is_not_client_acknowledgment"
        ]
        is True
    )