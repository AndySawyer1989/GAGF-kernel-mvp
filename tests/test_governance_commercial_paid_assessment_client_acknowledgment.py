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
    CommercialPaidAssessmentClientAcknowledgmentError,
    GovernanceCommercialPaidAssessmentClientAcknowledgmentService,
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
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    GovernancePaidAssessmentLifecycleQueryService,
    LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED,
    NEXT_STEP_RECORD_RESPONSE,
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


def build_delivery_event(
    **overrides,
) -> GovernedPaidAssessmentDeliveryEvent:
    values = {
        **HIERARCHY,
        "report_id": "report-001",
        "delivery_envelope_hash": HEX_A,
        "delivery_approval_hash": HEX_B,
        "human_delivery_confirmation_hash": HEX_C,
        "delivery_event_id": "delivery-event-001",
        "delivered_by": "FIP Operator",
        "delivered_at": "2026-09-03T20:00:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "mail-message-001",
        "delivery_completed": True,
        "delivery_status": "delivered",
    }

    values.update(overrides)

    payload = {
        "event_type": (
            "governance-paid-assessment-delivery-event"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": values["tenant_id"],
        "client_id": values["client_id"],
        "engagement_id": values["engagement_id"],
        "assessment_id": values["assessment_id"],
        "report_id": values["report_id"],
        "delivery_envelope_hash": (
            values["delivery_envelope_hash"]
        ),
        "delivery_approval_hash": (
            values["delivery_approval_hash"]
        ),
        "human_delivery_confirmation_hash": (
            values["human_delivery_confirmation_hash"]
        ),
        "delivery_event_id": (
            values["delivery_event_id"]
        ),
        "delivered_by": values["delivered_by"],
        "delivered_at": values["delivered_at"],
        "delivery_method": values["delivery_method"],
        "delivery_reference": (
            values["delivery_reference"]
        ),
        "delivery_completed": (
            values["delivery_completed"]
        ),
        "delivery_status": values["delivery_status"],
    }

    return GovernedPaidAssessmentDeliveryEvent(
        **values,
        delivery_event_hash=sha256_text(
            canonical_json(payload)
        ),
    )


def persist_delivery(
    repository: GovernanceAssessmentRepository,
    delivery_event: GovernedPaidAssessmentDeliveryEvent,
):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=DELIVERY_ARTIFACT_TYPE,
        payload=delivery_event.to_dict(),
    )


def build_acknowledgment_payload(
    **overrides,
) -> dict[str, object]:
    values: dict[str, object] = {
        "acknowledgment_id": "client-ack-001",
        "acknowledged_by": "ACME Client Representative",
        "acknowledged_at": "2026-09-03T20:15:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "mail-reply-001",
        "client_acknowledged_receipt": True,
    }

    values.update(overrides)
    return values


def build_service(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> GovernanceCommercialPaidAssessmentClientAcknowledgmentService:
    return GovernanceCommercialPaidAssessmentClientAcknowledgmentService(
        execution_service=execution_service
    )


def test_records_explicit_client_receipt_and_persists_lifecycle(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    delivery_event = build_delivery_event()
    persist_delivery(
        repository,
        delivery_event,
    )

    result = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        acknowledgment_payload=build_acknowledgment_payload(),
    )

    assert (
        result.acknowledgment_status
        == "client_receipt_acknowledged"
    )
    assert result.report_id == "report-001"
    assert (
        result.acknowledgment_id
        == "client-ack-001"
    )
    assert (
        result.acknowledged_by
        == "ACME Client Representative"
    )
    assert (
        result.acknowledgment_method
        == "email_reply"
    )
    assert (
        result.acknowledgment_reference
        == "mail-reply-001"
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    acknowledgment_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.artifact_type
        == ACKNOWLEDGMENT_ARTIFACT_TYPE
    ]

    assert len(acknowledgment_artifacts) == 1
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
        == LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED
    )
    assert (
        lifecycle.pending_next_step
        == NEXT_STEP_RECORD_RESPONSE
    )
    assert lifecycle.delivery_recorded is True
    assert lifecycle.receipt_acknowledged is True
    assert lifecycle.client_response_recorded is False
    assert lifecycle.lifecycle_artifact_count == 2


def test_result_does_not_overclaim_client_authority(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    persist_delivery(
        repository,
        build_delivery_event(),
    )

    payload = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        acknowledgment_payload=build_acknowledgment_payload(),
    ).to_dict()

    assert payload["client_receipt_acknowledged"] is True

    forbidden = (
        "findings_accepted",
        "recommendations_accepted",
        "client_response_recorded",
        "client_satisfied",
        "closeout_completed",
        "intervention_requested",
        "intervention_authorized",
        "execution_authorized",
        "roi_verified",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload

    assert (
        payload["boundaries"][
            "receipt_is_not_findings_acceptance"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "receipt_is_not_recommendation_acceptance"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "receipt_is_not_client_response"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "receipt_is_not_intervention_authority"
        ]
        is True
    )


def test_rejects_receipt_when_delivery_does_not_exist(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    build_repository(
        execution_service
    )

    with pytest.raises(
        CommercialPaidAssessmentClientAcknowledgmentError,
        match="exactly one paid assessment delivery event is required",
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            acknowledgment_payload=build_acknowledgment_payload(),
        )


def test_rejects_duplicate_client_receipt(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    persist_delivery(
        repository,
        build_delivery_event(),
    )

    service = build_service(
        execution_service
    )

    service.record(
        **HIERARCHY,
        acknowledgment_payload=build_acknowledgment_payload(),
    )

    with pytest.raises(
        CommercialPaidAssessmentClientAcknowledgmentError,
        match="client receipt acknowledgment already exists",
    ):
        service.record(
            **HIERARCHY,
            acknowledgment_payload=build_acknowledgment_payload(
                acknowledgment_id="client-ack-002",
                acknowledgment_reference="mail-reply-002",
            ),
        )


def test_rejects_nonaffirmative_receipt(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    persist_delivery(
        repository,
        build_delivery_event(),
    )

    with pytest.raises(
        CommercialPaidAssessmentClientAcknowledgmentError,
        match="client_acknowledged_receipt must be true",
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            acknowledgment_payload=build_acknowledgment_payload(
                client_acknowledged_receipt=False
            ),
        )


def test_rejects_acknowledgment_before_delivery(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    persist_delivery(
        repository,
        build_delivery_event(),
    )

    with pytest.raises(
        CommercialPaidAssessmentClientAcknowledgmentError,
        match="acknowledged_at must not occur before delivered_at",
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            acknowledgment_payload=build_acknowledgment_payload(
                acknowledged_at=(
                    "2026-09-03T19:59:00+00:00"
                )
            ),
        )


def test_rejects_tampered_persisted_delivery_event(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    delivery = persist_delivery(
        repository,
        build_delivery_event(),
    )

    with repository._connect() as connection:
        connection.execute(
            "UPDATE governance_assessment_artifacts "
            "SET chain_hash = ? WHERE artifact_id = ?",
            (
                "f" * 64,
                delivery.artifact_id,
            ),
        )

    with pytest.raises(
        Exception,
        match="chain verification failed",
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            acknowledgment_payload=build_acknowledgment_payload(),
        )


def test_browser_payload_cannot_override_delivery_lineage(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    delivery_event = build_delivery_event()
    persist_delivery(
        repository,
        delivery_event,
    )

    payload = build_acknowledgment_payload(
        delivery_event_id="browser-forged-delivery",
        delivery_event_hash="f" * 64,
        report_id="browser-forged-report",
    )

    result = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        acknowledgment_payload=payload,
    )

    assert result.report_id == delivery_event.report_id

    lifecycle = (
        GovernancePaidAssessmentLifecycleQueryService(
            repository=repository
        ).get_state(
            context=build_context()
        )
    )

    assert lifecycle.report_id == delivery_event.report_id
    assert lifecycle.receipt_acknowledged is True
