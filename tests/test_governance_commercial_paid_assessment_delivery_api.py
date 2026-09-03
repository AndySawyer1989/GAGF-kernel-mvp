from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_approval_handoff import (
    CommercialPaidAssessmentDeliveryApprovalHandoffError,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadinessError,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    CommercialPaidAssessmentDeliveryRecordingError,
)


BASE = (
    "/api/v1/governance-paid-assessments/"
    "tenant-001/client-001/engagement-001/assessment-001"
)


@dataclass(frozen=True)
class FakeResult:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return self.payload


class FakeReadinessService:
    def __init__(
        self,
        *,
        error: str | None = None,
    ) -> None:
        self.error = error
        self.calls: list[dict[str, str]] = []

    def verify(self, **kwargs: str) -> FakeResult:
        self.calls.append(dict(kwargs))
        if self.error is not None:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                self.error
            )
        return FakeResult(
            {
                "delivery_readiness_status": (
                    "ready_for_delivery_approval_review"
                ),
                "boundaries": {
                    "readiness_is_not_delivery_approval": True,
                },
            }
        )


class FakeApprovalService:
    def __init__(
        self,
        *,
        error: str | None = None,
    ) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def handoff(self, **kwargs: Any) -> FakeResult:
        self.calls.append(dict(kwargs))
        if self.error is not None:
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                self.error
            )
        return FakeResult(
            {
                "handoff_status": "approved_for_human_delivery",
                "approved_for_human_delivery": True,
                "boundaries": {
                    "approved_for_human_delivery_is_not_delivery": True,
                },
            }
        )


class FakeRecordingService:
    def __init__(
        self,
        *,
        error: str | None = None,
    ) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def record(self, **kwargs: Any) -> FakeResult:
        self.calls.append(dict(kwargs))
        if self.error is not None:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                self.error
            )
        return FakeResult(
            {
                "delivery_status": "delivered",
                "delivery_recorded": True,
                "boundaries": {
                    "delivery_is_not_client_receipt": True,
                },
            }
        )


def build_client(
    *,
    readiness: FakeReadinessService | None = None,
    approval: FakeApprovalService | None = None,
    recording: FakeRecordingService | None = None,
) -> tuple[
    TestClient,
    FakeReadinessService,
    FakeApprovalService,
    FakeRecordingService,
]:
    readiness = readiness or FakeReadinessService()
    approval = approval or FakeApprovalService()
    recording = recording or FakeRecordingService()

    app = FastAPI()
    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=readiness,
            approval_service=approval,
            recording_service=recording,
        )
    )

    return (
        TestClient(app),
        readiness,
        approval,
        recording,
    )


def approval_payload() -> dict[str, Any]:
    return {
        "approval_id": "delivery-approval-001",
        "tenant_id": "tenant-001",
        "client_id": "client-001",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "approved_by": "Human Reviewer",
        "approved_at": "2026-09-02T20:00:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }


def confirmation_payload() -> dict[str, Any]:
    return {
        "delivery_event_id": "delivery-event-001",
        "tenant_id": "tenant-001",
        "client_id": "client-001",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivered_by": "Authorized Human Deliverer",
        "delivered_at": "2026-09-02T20:15:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "customer-message-001",
        "delivery_completed": True,
    }


def test_delivery_readiness_endpoint_is_safe_adapter() -> None:
    client, readiness, _, _ = build_client()

    response = client.get(
        BASE + "/delivery-readiness"
    )

    assert response.status_code == 200
    assert (
        response.json()["delivery_readiness_status"]
        == "ready_for_delivery_approval_review"
    )
    assert len(readiness.calls) == 1


def test_missing_readiness_snapshot_returns_404() -> None:
    client, _, _, _ = build_client(
        readiness=FakeReadinessService(
            error="durable PA015 operator-result snapshot was not found"
        )
    )

    response = client.get(
        BASE + "/delivery-readiness"
    )

    assert response.status_code == 404


def test_readiness_conflict_returns_409() -> None:
    client, _, _, _ = build_client(
        readiness=FakeReadinessService(
            error="operator-result snapshot is not bound to current status"
        )
    )

    response = client.get(
        BASE + "/delivery-readiness"
    )

    assert response.status_code == 409


def test_delivery_approval_delegates_explicit_human_payload() -> None:
    client, _, approval, _ = build_client()

    response = client.post(
        BASE + "/delivery-approval",
        json=approval_payload(),
    )

    assert response.status_code == 200
    assert response.json()["approved_for_human_delivery"] is True
    assert len(approval.calls) == 1
    assert (
        approval.calls[0]["approval_payload"]["delivery_approved"]
        is True
    )


def test_delivery_approval_rejects_path_identity_mismatch() -> None:
    client, _, approval, _ = build_client()

    payload = approval_payload()
    payload["assessment_id"] = "wrong-assessment"

    response = client.post(
        BASE + "/delivery-approval",
        json=payload,
    )

    assert response.status_code == 409
    assert approval.calls == []


def test_delivery_approval_rejects_extra_fields() -> None:
    client, _, approval, _ = build_client()

    payload = approval_payload()
    payload["auto_approve"] = True

    response = client.post(
        BASE + "/delivery-approval",
        json=payload,
    )

    assert response.status_code == 422
    assert approval.calls == []


def test_delivery_approval_service_conflict_returns_409() -> None:
    client, _, _, _ = build_client(
        approval=FakeApprovalService(
            error="delivery_approved must be explicitly true"
        )
    )

    response = client.post(
        BASE + "/delivery-approval",
        json=approval_payload(),
    )

    assert response.status_code == 409


def test_delivery_recording_delegates_human_confirmation() -> None:
    client, _, _, recording = build_client()

    response = client.post(
        BASE + "/delivery-recording",
        json=confirmation_payload(),
    )

    assert response.status_code == 200
    assert response.json()["delivery_recorded"] is True
    assert len(recording.calls) == 1
    assert (
        recording.calls[0]["human_confirmation_payload"][
            "delivery_completed"
        ]
        is True
    )


def test_delivery_recording_requires_matching_path_identity() -> None:
    client, _, _, recording = build_client()

    payload = confirmation_payload()
    payload["client_id"] = "wrong-client"

    response = client.post(
        BASE + "/delivery-recording",
        json=payload,
    )

    assert response.status_code == 409
    assert recording.calls == []


def test_delivery_recording_rejects_extra_fields() -> None:
    client, _, _, recording = build_client()

    payload = confirmation_payload()
    payload["client_received"] = True

    response = client.post(
        BASE + "/delivery-recording",
        json=payload,
    )

    assert response.status_code == 422
    assert recording.calls == []


def test_missing_approved_delivery_snapshot_returns_404() -> None:
    client, _, _, _ = build_client(
        recording=FakeRecordingService(
            error="durable approved-delivery snapshot was not found"
        )
    )

    response = client.post(
        BASE + "/delivery-recording",
        json=confirmation_payload(),
    )

    assert response.status_code == 404


def test_delivery_recording_conflict_returns_409() -> None:
    client, _, _, _ = build_client(
        recording=FakeRecordingService(
            error="delivery_completed must be explicitly true"
        )
    )

    response = client.post(
        BASE + "/delivery-recording",
        json=confirmation_payload(),
    )

    assert response.status_code == 409
