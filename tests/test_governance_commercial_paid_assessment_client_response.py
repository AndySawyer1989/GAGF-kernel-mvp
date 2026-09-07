from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_client_acknowledgment import (
    GovernanceCommercialPaidAssessmentClientAcknowledgmentService,
)
from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    CommercialPaidAssessmentClientResponseError,
    GovernanceCommercialPaidAssessmentClientResponseService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    GovernancePaidAssessmentLifecycleQueryService,
)


HIERARCHY = {
    "tenant_id": "tenant-alpha",
    "client_id": "client-acme",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64


def build_context() -> CommercialHierarchyContext:
    return CommercialHierarchyContext(**HIERARCHY)


def build_execution_service(
    tmp_path: Path,
) -> GovernanceCommercialPaidAssessmentExecutionService:
    return GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=tmp_path / "paid-assessments"
    )


def build_repository(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> GovernanceAssessmentRepository:
    database_path = execution_service.database_path_for_hierarchy(
        **HIERARCHY
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    repository.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="complete",
    )

    return repository


def build_delivery_event() -> GovernedPaidAssessmentDeliveryEvent:
    payload = {
        "event_type": (
            "governance-paid-assessment-delivery-event"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        **HIERARCHY,
        "report_id": "report-001",
        "delivery_envelope_hash": HEX_A,
        "delivery_approval_hash": HEX_B,
        "human_delivery_confirmation_hash": HEX_C,
        "delivery_event_id": "delivery-event-001",
        "delivered_by": "FIP Operator",
        "delivered_at": "2026-09-07T18:00:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "mail-message-001",
        "delivery_status": "delivered",
    }

    return GovernedPaidAssessmentDeliveryEvent(
        **HIERARCHY,
        report_id="report-001",
        delivery_envelope_hash=HEX_A,
        delivery_approval_hash=HEX_B,
        human_delivery_confirmation_hash=HEX_C,
        delivery_event_id="delivery-event-001",
        delivered_by="FIP Operator",
        delivered_at="2026-09-07T18:00:00+00:00",
        delivery_method="email",
        delivery_reference="mail-message-001",
        delivery_status="delivered",
        delivery_event_hash=sha256_text(
            canonical_json(payload)
        ),
    )


def persist_delivery(
    repository: GovernanceAssessmentRepository,
) -> None:
    repository.append_artifact(
        context=build_context(),
        artifact_type=DELIVERY_ARTIFACT_TYPE,
        payload=build_delivery_event().to_dict(),
    )


def record_receipt(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> None:
    GovernanceCommercialPaidAssessmentClientAcknowledgmentService(
        execution_service=execution_service
    ).record(
        **HIERARCHY,
        acknowledgment_payload={
            "acknowledgment_id": "client-ack-001",
            "acknowledged_by": "ACME Client Representative",
            "acknowledged_at": "2026-09-07T18:15:00+00:00",
            "acknowledgment_method": "email_reply",
            "acknowledgment_reference": "mail-reply-001",
            "client_acknowledged_receipt": True,
        },
    )


def build_response_payload(
    **overrides,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "response_id": "client-response-001",
        "responded_by": "ACME Client Representative",
        "responded_at": "2026-09-07T18:30:00+00:00",
        "response_method": "email_reply",
        "response_reference": "response-mail-001",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
        "response_note": (
            "Client accepts recommendations for planning review."
        ),
    }

    payload.update(overrides)
    return payload


def prepare_delivered_and_acknowledged(
    tmp_path: Path,
) -> tuple[
    GovernanceCommercialPaidAssessmentExecutionService,
    GovernanceAssessmentRepository,
]:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    persist_delivery(repository)
    record_receipt(execution_service)

    return execution_service, repository


def test_records_client_response_and_advances_lifecycle(
    tmp_path: Path,
) -> None:
    execution_service, repository = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    result = (
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(),
        )
    )

    assert (
        result.response_status
        == "client_response_recorded"
    )
    assert result.report_id == "report-001"
    assert result.response_id == "client-response-001"
    assert result.findings_disposition == "acknowledged"
    assert (
        result.recommendations_disposition
        == "accepted"
    )

    responses = repository.list_artifacts(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(responses) == 1
    assert repository.verify_chain(
        context=build_context()
    ) is True

    lifecycle = (
        GovernancePaidAssessmentLifecycleQueryService(
            repository=repository
        ).get_state(
            context=build_context()
        )
    )

    assert (
        lifecycle.current_stage
        == "client_response_recorded"
    )
    assert lifecycle.delivery_recorded is True
    assert lifecycle.receipt_acknowledged is True
    assert lifecycle.client_response_recorded is True


def test_rejects_response_before_receipt(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    persist_delivery(repository)

    with pytest.raises(
        CommercialPaidAssessmentClientResponseError,
        match=(
            "exactly one persisted client receipt "
            "acknowledgment is required"
        ),
    ):
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(),
        )


def test_rejects_invalid_findings_disposition(
    tmp_path: Path,
) -> None:
    execution_service, _ = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentClientResponseError,
        match="findings_disposition must be one of",
    ):
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(
                findings_disposition="invented-status"
            ),
        )


def test_rejects_invalid_recommendations_disposition(
    tmp_path: Path,
) -> None:
    execution_service, _ = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentClientResponseError,
        match="recommendations_disposition must be one of",
    ):
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(
                recommendations_disposition="invented-status"
            ),
        )


def test_rejects_invalid_response_timestamp(
    tmp_path: Path,
) -> None:
    execution_service, _ = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentClientResponseError,
        match="responded_at must be ISO-8601",
    ):
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(
                responded_at="not-a-timestamp"
            ),
        )


def test_browser_lineage_fields_are_ignored(
    tmp_path: Path,
) -> None:
    execution_service, repository = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    result = (
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(
                tenant_id="forged-tenant",
                report_id="forged-report",
                acknowledgment_id="forged-ack",
                acknowledgment_hash="f" * 64,
                database_path="C:/forged.sqlite3",
            ),
        )
    )

    assert result.tenant_id == HIERARCHY["tenant_id"]
    assert result.report_id == "report-001"

    lifecycle = (
        GovernancePaidAssessmentLifecycleQueryService(
            repository=repository
        ).get_state(
            context=build_context()
        )
    )

    assert lifecycle.client_response_recorded is True


def test_result_preserves_semantic_boundaries(
    tmp_path: Path,
) -> None:
    execution_service, _ = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    payload = (
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(),
        ).to_dict()
    )

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

    forbidden = (
        "findings_validated",
        "implementation_authorized",
        "intervention_authorized",
        "closeout_completed",
        "roi_verified",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload
