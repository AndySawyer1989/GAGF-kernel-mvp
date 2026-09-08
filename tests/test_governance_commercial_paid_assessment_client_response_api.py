from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    CommercialPaidAssessmentClientResponseError,
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


class FakeClientResponseService:
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
        response_payload: dict[str, Any],
    ) -> Result:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
                "response_payload": dict(response_payload),
            }
        )

        if self.error is not None:
            raise CommercialPaidAssessmentClientResponseError(
                self.error
            )

        if (
            response_payload["findings_disposition"]
            == "invented-status"
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "findings_disposition must be one of: "
                "acknowledged, disputed, under_review"
            )

        return Result(
            {
                "result_type": (
                    "governance-commercial-paid-assessment-"
                    "client-response"
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
                "response_id": response_payload[
                    "response_id"
                ],
                "responded_by": response_payload[
                    "responded_by"
                ],
                "responded_at": response_payload[
                    "responded_at"
                ],
                "response_method": response_payload[
                    "response_method"
                ],
                "response_reference": response_payload[
                    "response_reference"
                ],
                "findings_disposition": response_payload[
                    "findings_disposition"
                ],
                "recommendations_disposition": (
                    response_payload[
                        "recommendations_disposition"
                    ]
                ),
                "response_note": response_payload[
                    "response_note"
                ],
                "response_status": (
                    "client_response_recorded"
                ),
                "client_response_recorded": True,
                "boundaries": {
                    "response_requires_prior_receipt": True,
                    "response_is_not_inferred_from_receipt": True,
                    "findings_acknowledgment_is_not_validation": True,
                    "recommendation_acceptance_is_not_implementation": True,
                    "response_is_not_closeout": True,
                    "response_is_not_intervention_authorization": True,
                    "pa007_remains_client_response_authority": True,
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


class UnusedClientAcknowledgmentService:
    def record(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "client acknowledgment service must not be called"
        )


class UnusedCloseoutStatusService:
    def get_status(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "closeout status service must not be called"
        )


class UnusedAdministrativeCloseoutService:
    def record(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "administrative closeout service must not be called"
        )


def build_client(
    response_service: FakeClientResponseService | None = None,
) -> tuple[
    TestClient,
    FakeClientResponseService,
]:
    response_service = (
        response_service
        or FakeClientResponseService()
    )

    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=UnusedReadinessService(),
            approval_service=UnusedApprovalService(),
            recording_service=UnusedRecordingService(),
            status_service=UnusedDeliveryStatusService(),
            lifecycle_status_service=UnusedLifecycleStatusService(),
            client_acknowledgment_service=(
                UnusedClientAcknowledgmentService()
            ),
            client_response_service=response_service,
            closeout_status_service=UnusedCloseoutStatusService(),
            administrative_closeout_service=(
                UnusedAdministrativeCloseoutService()
            ),
        )
    )

    return TestClient(app), response_service


def response_payload(
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "response_id": "client-response-001",
        "responded_by": "ACME Client Representative",
        "responded_at": "2026-09-07T18:30:00+00:00",
        "response_method": "email_reply",
        "response_reference": "response-mail-001",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
        "response_note": (
            "Client accepts recommendations "
            "for planning review."
        ),
    }

    payload.update(overrides)
    return payload


def test_client_response_delegates_explicit_response() -> None:
    client, response_service = build_client()

    response = client.post(
        BASE + "/client-response",
        json=response_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["response_status"]
        == "client_response_recorded"
    )
    assert payload["client_response_recorded"] is True
    assert payload["report_id"] == "report-001"

    assert len(response_service.calls) == 1

    call = response_service.calls[0]

    assert call["tenant_id"] == "tenant-001"
    assert call["client_id"] == "client-001"
    assert call["engagement_id"] == "engagement-001"
    assert call["assessment_id"] == "assessment-001"

    assert call["response_payload"] == response_payload()


def test_client_response_body_contains_no_lineage_authority() -> None:
    client, response_service = build_client()

    response = client.post(
        BASE + "/client-response",
        json=response_payload(),
    )

    assert response.status_code == 200

    sent_payload = response_service.calls[0][
        "response_payload"
    ]

    assert set(sent_payload) == {
        "response_id",
        "responded_by",
        "responded_at",
        "response_method",
        "response_reference",
        "findings_disposition",
        "recommendations_disposition",
        "response_note",
    }

    forbidden = {
        "tenant_id",
        "client_id",
        "engagement_id",
        "assessment_id",
        "report_id",
        "acknowledgment_id",
        "acknowledgment_hash",
        "database_path",
        "repository_path",
    }

    assert forbidden.isdisjoint(sent_payload)


def test_governed_response_conflict_returns_409() -> None:
    client, response_service = build_client(
        FakeClientResponseService(
            error="client response lifecycle artifact already exists"
        )
    )

    response = client.post(
        BASE + "/client-response",
        json=response_payload(),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "client response lifecycle artifact already exists"
    )

    assert len(response_service.calls) == 1


def test_invalid_findings_disposition_returns_409() -> None:
    client, response_service = build_client()

    response = client.post(
        BASE + "/client-response",
        json=response_payload(
            findings_disposition="invented-status"
        ),
    )

    assert response.status_code == 409
    assert (
        "findings_disposition must be one of"
        in response.json()["detail"]
    )

    assert len(response_service.calls) == 1


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("report_id", "forged-report"),
        ("acknowledgment_id", "forged-ack"),
        ("acknowledgment_hash", "f" * 64),
        ("tenant_id", "forged-tenant"),
        ("client_id", "forged-client"),
        ("assessment_id", "forged-assessment"),
        ("database_path", "C:/forged.sqlite3"),
        ("repository_path", "C:/forged-repository"),
    ),
)
def test_client_response_rejects_authority_fields(
    field_name: str,
    field_value: str,
) -> None:
    client, response_service = build_client()

    payload = response_payload()
    payload[field_name] = field_value

    response = client.post(
        BASE + "/client-response",
        json=payload,
    )

    assert response.status_code == 422
    assert response_service.calls == []


def test_client_response_response_does_not_overclaim() -> None:
    client, _ = build_client()

    response = client.post(
        BASE + "/client-response",
        json=response_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    forbidden = (
        "findings_validated",
        "findings_proven",
        "implementation_authorized",
        "intervention_requested",
        "intervention_authorized",
        "execution_authorized",
        "closeout_completed",
        "roi_verified",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload

    boundaries = payload["boundaries"]

    assert (
        boundaries[
            "findings_acknowledgment_is_not_validation"
        ]
        is True
    )
    assert (
        boundaries[
            "recommendation_acceptance_is_not_implementation"
        ]
        is True
    )
    assert (
        boundaries[
            "response_is_not_intervention_authorization"
        ]
        is True
    )
    assert (
        boundaries["response_is_not_closeout"]
        is True
    )
    assert (
        boundaries[
            "pa007_remains_client_response_authority"
        ]
        is True
    )
