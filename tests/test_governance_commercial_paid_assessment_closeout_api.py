from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_closeout import (
    CommercialPaidAssessmentCloseoutError,
)
from backend.app.gagf.governance_commercial_paid_assessment_closeout_status import (
    CommercialPaidAssessmentCloseoutStatusError,
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


class FakeCloseoutStatusService:
    def __init__(
        self,
        *,
        error: str | None = None,
    ) -> None:
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
            raise CommercialPaidAssessmentCloseoutStatusError(
                self.error
            )

        return Result(
            {
                "status_type": (
                    "governance-commercial-paid-assessment-"
                    "closeout-status"
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
                "found": True,
                "closeout_recorded": True,
                "closeout_status": "assessment_closed",
                "report_id": "report-001",
                "closed_by": "FIP Operator",
                "closed_at": "2026-09-08T15:00:00+00:00",
                "closeout_reason": (
                    "Administrative processing complete."
                ),
                "repository_chain_valid": True,
                "boundaries": {
                    "closeout_status_is_read_only_projection": True,
                    "client_response_is_not_closeout": True,
                    "closeout_is_not_intervention_authorization": True,
                    "pa010_remains_closeout_authority": True,
                },
            }
        )


class FakeAdministrativeCloseoutService:
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
        closeout_payload: dict[str, Any],
    ) -> Result:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
                "closeout_payload": dict(closeout_payload),
            }
        )

        if self.error is not None:
            raise CommercialPaidAssessmentCloseoutError(
                self.error
            )

        return Result(
            {
                "closeout_type": (
                    "governance-commercial-paid-assessment-closeout"
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
                "closeout_status": "assessment_closed",
                "administrative_closeout_recorded": True,
                "closed_by": closeout_payload["closed_by"],
                "closeout_reason": (
                    closeout_payload["closeout_reason"]
                ),
                "closeout_artifact_id": "closeout-artifact-001",
                "closeout_artifact_hash": "a" * 64,
                "repository_chain_valid": True,
                "boundaries": {
                    "closeout_requires_explicit_human_confirmation": True,
                    "response_is_not_closeout": True,
                    "closeout_is_not_intervention_authorization": True,
                    "pa010_remains_closeout_authority": True,
                    "pa013_remains_operator_coordination_authority": True,
                },
            }
        )


class UnusedReadinessService:
    def verify(self, **kwargs: Any) -> Result:
        raise AssertionError("readiness service must not be called")


class UnusedApprovalService:
    def handoff(self, **kwargs: Any) -> Result:
        raise AssertionError("approval service must not be called")


class UnusedRecordingService:
    def record(self, **kwargs: Any) -> Result:
        raise AssertionError("recording service must not be called")


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


class UnusedClientResponseService:
    def record(self, **kwargs: Any) -> Result:
        raise AssertionError(
            "client response service must not be called"
        )


def build_client(
    *,
    closeout_status_service: FakeCloseoutStatusService | None = None,
    administrative_closeout_service: (
        FakeAdministrativeCloseoutService | None
    ) = None,
) -> tuple[
    TestClient,
    FakeCloseoutStatusService,
    FakeAdministrativeCloseoutService,
]:
    closeout_status_service = (
        closeout_status_service
        or FakeCloseoutStatusService()
    )

    administrative_closeout_service = (
        administrative_closeout_service
        or FakeAdministrativeCloseoutService()
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
            client_response_service=UnusedClientResponseService(),
            closeout_status_service=closeout_status_service,
            administrative_closeout_service=(
                administrative_closeout_service
            ),
        )
    )

    return (
        TestClient(app),
        closeout_status_service,
        administrative_closeout_service,
    )


def closeout_payload(
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "closed_by": "FIP Operator",
        "closeout_reason": (
            "Client response recorded and "
            "administrative processing complete."
        ),
        "administrative_closeout_confirmed": True,
    }

    payload.update(overrides)

    return payload


def test_closeout_status_delegates_restart_safe_read() -> None:
    client, status_service, _ = build_client()

    response = client.get(
        BASE + "/closeout-status"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["closeout_recorded"] is True
    assert payload["closeout_status"] == "assessment_closed"
    assert payload["report_id"] == "report-001"
    assert payload["repository_chain_valid"] is True

    assert status_service.calls == [
        {
            "tenant_id": "tenant-001",
            "client_id": "client-001",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
        }
    ]


def test_closeout_status_conflict_returns_409() -> None:
    client, status_service, _ = build_client(
        closeout_status_service=FakeCloseoutStatusService(
            error="governed assessment repository chain is invalid"
        )
    )

    response = client.get(
        BASE + "/closeout-status"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "governed assessment repository chain is invalid"
    )
    assert len(status_service.calls) == 1


def test_closeout_status_exposes_no_internal_authority() -> None:
    client, _, _ = build_client()

    response = client.get(
        BASE + "/closeout-status"
    )

    assert response.status_code == 200

    payload = response.json()

    forbidden = (
        "database_path",
        "repository_path",
        "response_id",
        "response_hash",
        "client_response_artifact_id",
        "client_response_artifact_hash",
        "operator_result",
        "intervention_requested",
        "intervention_authorized",
        "execution_authorized",
        "roi_verified",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload


def test_administrative_closeout_delegates_explicit_action() -> None:
    client, _, closeout_service = build_client()

    response = client.post(
        BASE + "/administrative-closeout",
        json=closeout_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["closeout_status"]
        == "assessment_closed"
    )
    assert (
        payload["administrative_closeout_recorded"]
        is True
    )
    assert payload["report_id"] == "report-001"

    assert len(closeout_service.calls) == 1

    call = closeout_service.calls[0]

    assert call["tenant_id"] == "tenant-001"
    assert call["client_id"] == "client-001"
    assert call["engagement_id"] == "engagement-001"
    assert call["assessment_id"] == "assessment-001"
    assert (
        call["closeout_payload"]
        == closeout_payload()
    )


def test_administrative_closeout_body_has_no_lineage_authority() -> None:
    client, _, closeout_service = build_client()

    response = client.post(
        BASE + "/administrative-closeout",
        json=closeout_payload(),
    )

    assert response.status_code == 200

    sent_payload = closeout_service.calls[0][
        "closeout_payload"
    ]

    assert set(sent_payload) == {
        "closed_by",
        "closeout_reason",
        "administrative_closeout_confirmed",
    }


def test_administrative_closeout_conflict_returns_409() -> None:
    client, _, closeout_service = build_client(
        administrative_closeout_service=(
            FakeAdministrativeCloseoutService(
                error=(
                    "governed closeout requires exactly one "
                    "persisted client-response artifact"
                )
            )
        )
    )

    response = client.post(
        BASE + "/administrative-closeout",
        json=closeout_payload(),
    )

    assert response.status_code == 409
    assert (
        "persisted client-response artifact"
        in response.json()["detail"]
    )
    assert len(closeout_service.calls) == 1


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("tenant_id", "forged-tenant"),
        ("client_id", "forged-client"),
        ("engagement_id", "forged-engagement"),
        ("assessment_id", "forged-assessment"),
        ("report_id", "forged-report"),
        ("response_id", "forged-response"),
        ("response_hash", "f" * 64),
        (
            "client_response_artifact_id",
            "forged-response-artifact",
        ),
        (
            "client_response_artifact_hash",
            "e" * 64,
        ),
        ("database_path", "C:/forged.sqlite3"),
        (
            "repository_path",
            "C:/forged/repository.sqlite3",
        ),
        ("closeout_status", "forged-status"),
        ("closeout_basis", "forged-basis"),
    ),
)
def test_administrative_closeout_rejects_authority_fields(
    field_name: str,
    field_value: str,
) -> None:
    client, _, closeout_service = build_client()

    payload = closeout_payload()
    payload[field_name] = field_value

    response = client.post(
        BASE + "/administrative-closeout",
        json=payload,
    )

    assert response.status_code == 422
    assert closeout_service.calls == []


def test_administrative_closeout_response_does_not_overclaim() -> None:
    client, _, _ = build_client()

    response = client.post(
        BASE + "/administrative-closeout",
        json=closeout_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    forbidden = (
        "findings_validated",
        "findings_proven",
        "recommendation_implemented",
        "implementation_authorized",
        "intervention_requested",
        "intervention_authorized",
        "intervention_executed",
        "execution_authorized",
        "causal_success",
        "roi_verified",
        "remediation_success",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload

    boundaries = payload["boundaries"]

    assert (
        boundaries[
            "closeout_requires_explicit_human_confirmation"
        ]
        is True
    )
    assert boundaries["response_is_not_closeout"] is True
    assert (
        boundaries[
            "closeout_is_not_intervention_authorization"
        ]
        is True
    )
    assert (
        boundaries["pa010_remains_closeout_authority"]
        is True
    )
    assert (
        boundaries[
            "pa013_remains_operator_coordination_authority"
        ]
        is True
    )
