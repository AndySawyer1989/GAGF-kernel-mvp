from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_client_acknowledgment import (
    CommercialPaidAssessmentClientAcknowledgmentError,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
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


class FakeClientAcknowledgmentService:
    def __init__(
        self,
        *,
        error: str | None = None,
    ) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        acknowledgment_payload: dict[str, Any],
    ) -> Result:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
                "acknowledgment_payload": dict(
                    acknowledgment_payload
                ),
            }
        )

        if self.error is not None:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                self.error
            )

        if (
            acknowledgment_payload[
                "client_acknowledged_receipt"
            ]
            is not True
        ):
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "client_acknowledged_receipt must be true before "
                "client receipt acknowledgment can be recorded"
            )

        return Result(
            {
                "result_type": (
                    "governance-commercial-paid-assessment-"
                    "client-acknowledgment"
                ),
                "version": "0.1.0",
                "schema_version": "1.0.0",
                "tenant_id": tenant_id,
                "client_id": client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
                "hierarchy_key": "/".join(
                    (
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id,
                    )
                ),
                "report_id": "report-001",
                "acknowledgment_id": (
                    acknowledgment_payload[
                        "acknowledgment_id"
                    ]
                ),
                "acknowledged_by": (
                    acknowledgment_payload[
                        "acknowledged_by"
                    ]
                ),
                "acknowledged_at": (
                    acknowledgment_payload[
                        "acknowledged_at"
                    ]
                ),
                "acknowledgment_method": (
                    acknowledgment_payload[
                        "acknowledgment_method"
                    ]
                ),
                "acknowledgment_reference": (
                    acknowledgment_payload[
                        "acknowledgment_reference"
                    ]
                ),
                "acknowledgment_status": (
                    "client_receipt_acknowledged"
                ),
                "client_receipt_acknowledged": True,
                "boundaries": {
                    "receipt_is_not_findings_acceptance": True,
                    "receipt_is_not_recommendation_acceptance": True,
                    "receipt_is_not_client_response": True,
                    "receipt_is_not_closeout": True,
                    "receipt_is_not_intervention_authority": True,
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


class UnusedLifecycleStatusService:
    def get_status(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "lifecycle status service must not be called"
        )



class UnusedClientResponseService:
    def record(self, **kwargs: Any):
        raise AssertionError(
            "client response service must not be called"
        )


def build_client(
    acknowledgment_service: FakeClientAcknowledgmentService
    | None = None,
) -> tuple[
    TestClient,
    FakeClientAcknowledgmentService,
]:
    acknowledgment_service = (
        acknowledgment_service
        or FakeClientAcknowledgmentService()
    )

    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=UnusedReadinessService(),
            approval_service=UnusedApprovalService(),
            recording_service=UnusedRecordingService(),
            status_service=UnusedDeliveryStatusService(),
            lifecycle_status_service=(
                UnusedLifecycleStatusService()
            ),
            client_acknowledgment_service=(
                acknowledgment_service
            ),
            client_response_service=UnusedClientResponseService(),
        )
    )

    return (
        TestClient(app),
        acknowledgment_service,
    )


def acknowledgment_payload(
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "acknowledgment_id": "client-ack-001",
        "acknowledged_by": "ACME Client Representative",
        "acknowledged_at": "2026-09-06T18:30:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "mail-reply-001",
        "client_acknowledged_receipt": True,
    }

    payload.update(overrides)
    return payload


def test_client_acknowledgment_delegates_explicit_receipt() -> None:
    client, acknowledgment_service = build_client()

    response = client.post(
        BASE + "/client-acknowledgment",
        json=acknowledgment_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["acknowledgment_status"]
        == "client_receipt_acknowledged"
    )
    assert payload["client_receipt_acknowledged"] is True
    assert payload["report_id"] == "report-001"

    assert len(acknowledgment_service.calls) == 1

    call = acknowledgment_service.calls[0]

    assert call["tenant_id"] == "tenant-001"
    assert call["client_id"] == "client-001"
    assert call["engagement_id"] == "engagement-001"
    assert call["assessment_id"] == "assessment-001"

    assert call["acknowledgment_payload"] == (
        acknowledgment_payload()
    )


def test_client_acknowledgment_body_contains_no_lineage_authority() -> None:
    client, acknowledgment_service = build_client()

    response = client.post(
        BASE + "/client-acknowledgment",
        json=acknowledgment_payload(),
    )

    assert response.status_code == 200

    sent_payload = (
        acknowledgment_service.calls[0][
            "acknowledgment_payload"
        ]
    )

    assert set(sent_payload) == {
        "acknowledgment_id",
        "acknowledged_by",
        "acknowledged_at",
        "acknowledgment_method",
        "acknowledgment_reference",
        "client_acknowledged_receipt",
    }

    forbidden = {
        "tenant_id",
        "client_id",
        "engagement_id",
        "assessment_id",
        "report_id",
        "delivery_event_id",
        "delivery_event_hash",
        "acknowledgment_hash",
        "database_path",
        "repository_path",
    }

    assert forbidden.isdisjoint(sent_payload)


def test_nonaffirmative_receipt_returns_409() -> None:
    client, acknowledgment_service = build_client()

    response = client.post(
        BASE + "/client-acknowledgment",
        json=acknowledgment_payload(
            client_acknowledged_receipt=False
        ),
    )

    assert response.status_code == 409
    assert (
        "client_acknowledged_receipt must be true"
        in response.json()["detail"]
    )

    assert len(acknowledgment_service.calls) == 1


def test_governed_acknowledgment_conflict_returns_409() -> None:
    client, acknowledgment_service = build_client(
        FakeClientAcknowledgmentService(
            error="client receipt acknowledgment already exists"
        )
    )

    response = client.post(
        BASE + "/client-acknowledgment",
        json=acknowledgment_payload(),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "client receipt acknowledgment already exists"
    )

    assert len(acknowledgment_service.calls) == 1


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("report_id", "browser-report"),
        ("delivery_event_id", "browser-delivery"),
        ("delivery_event_hash", "f" * 64),
        ("tenant_id", "browser-tenant"),
        ("database_path", "C:/forged.sqlite3"),
        ("repository_path", "C:/forged-repository"),
    ),
)
def test_client_acknowledgment_rejects_authority_fields(
    field_name: str,
    field_value: str,
) -> None:
    client, acknowledgment_service = build_client()

    request_payload = acknowledgment_payload()
    request_payload[field_name] = field_value

    response = client.post(
        BASE + "/client-acknowledgment",
        json=request_payload,
    )

    assert response.status_code == 422
    assert acknowledgment_service.calls == []


def test_client_acknowledgment_response_does_not_overclaim() -> None:
    client, _ = build_client()

    response = client.post(
        BASE + "/client-acknowledgment",
        json=acknowledgment_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    forbidden = (
        "findings_accepted",
        "recommendations_accepted",
        "client_response_recorded",
        "closeout_completed",
        "intervention_requested",
        "intervention_authorized",
        "execution_authorized",
        "roi_verified",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload

    boundaries = payload["boundaries"]

    assert (
        boundaries[
            "receipt_is_not_findings_acceptance"
        ]
        is True
    )
    assert (
        boundaries[
            "receipt_is_not_recommendation_acceptance"
        ]
        is True
    )
    assert (
        boundaries[
            "receipt_is_not_client_response"
        ]
        is True
    )
    assert (
        boundaries[
            "receipt_is_not_closeout"
        ]
        is True
    )
    assert (
        boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )
