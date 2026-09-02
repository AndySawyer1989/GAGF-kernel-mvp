from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_delivery_approval_handoff import (
    GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    CommercialPaidAssessmentDeliveryRecordingError,
    GovernanceCommercialPaidAssessmentDeliveryRecordingService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from tests.test_governance_commercial_paid_assessment_delivery_approval_handoff import (
    HIERARCHY,
    build_completed_assessment,
    valid_approval_payload,
)


def build_approved_assessment(
    tmp_path: Path,
) -> GovernanceCommercialPaidAssessmentExecutionService:
    execution_service = build_completed_assessment(
        tmp_path
    )

    readiness_service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    approval_service = (
        GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService(
            readiness_service=readiness_service
        )
    )

    approval_service.handoff(
        **HIERARCHY,
        approval_payload=valid_approval_payload(
            execution_service
        ),
    )

    return execution_service


def valid_human_confirmation(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> dict:
    readiness = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
        .verify(**HIERARCHY)
    )

    report_id = readiness.readiness.execution_result.report_id

    return {
        "delivery_event_id": "delivery-event-001",
        "tenant_id": HIERARCHY["tenant_id"],
        "client_id": HIERARCHY["client_id"],
        "engagement_id": HIERARCHY["engagement_id"],
        "assessment_id": HIERARCHY["assessment_id"],
        "report_id": report_id,
        "delivered_by": "Authorized Human Deliverer",
        "delivered_at": "2026-09-02T20:00:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "customer-message-001",
        "delivery_completed": True,
    }


def test_explicit_human_confirmation_records_governed_delivery(
    tmp_path: Path,
) -> None:
    execution_service = build_approved_assessment(
        tmp_path
    )

    service = (
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        )
    )

    result = service.record(
        **HIERARCHY,
        human_confirmation_payload=valid_human_confirmation(
            execution_service
        ),
    )

    assert result.recording.delivery_status == "delivered"
    assert result.recording.delivery_event.delivery_status == "delivered"

    safe = result.to_dict()

    assert safe["delivery_recorded"] is True
    assert safe["delivery_status"] == "delivered"
    assert safe["delivery_event_id"] == "delivery-event-001"
    assert safe["delivery_event_hash"]
    assert safe["human_delivery_confirmation_hash"]
    assert safe["approved_delivery_snapshot_hash"]

    assert "approved_delivery_payload" not in safe
    assert "delivery_envelope" not in safe
    assert "persistence_result" not in safe

    assert (
        safe["boundaries"][
            "pa005_remains_delivery_event_authority"
        ]
        is True
    )


def test_delivery_recording_is_restart_safe(
    tmp_path: Path,
) -> None:
    execution_service = build_approved_assessment(
        tmp_path
    )

    confirmation = valid_human_confirmation(
        execution_service
    )

    restarted_execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                execution_service.execution_directory
            )
        )
    )

    result = (
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=restarted_execution_service
        )
        .record(
            **HIERARCHY,
            human_confirmation_payload=confirmation,
        )
    )

    assert result.recording.delivery_status == "delivered"


def test_exact_delivery_retry_is_idempotent(
    tmp_path: Path,
) -> None:
    execution_service = build_approved_assessment(
        tmp_path
    )

    service = (
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        )
    )

    confirmation = valid_human_confirmation(
        execution_service
    )

    first = service.record(
        **HIERARCHY,
        human_confirmation_payload=confirmation,
    )

    second = service.record(
        **HIERARCHY,
        human_confirmation_payload=confirmation,
    )

    assert (
        second.recording.delivery_event.delivery_event_hash
        == first.recording.delivery_event.delivery_event_hash
    )
    assert (
        second.recording.delivery_event.delivery_event_id
        == first.recording.delivery_event.delivery_event_id
    )


def test_delivery_requires_explicit_human_completion(
    tmp_path: Path,
) -> None:
    execution_service = build_approved_assessment(
        tmp_path
    )

    confirmation = valid_human_confirmation(
        execution_service
    )
    confirmation["delivery_completed"] = False

    with pytest.raises(
        CommercialPaidAssessmentDeliveryRecordingError,
        match="delivery_completed must be explicitly true",
    ):
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            human_confirmation_payload=confirmation,
        )


def test_delivery_requires_prior_durable_approval(
    tmp_path: Path,
) -> None:
    execution_service = build_completed_assessment(
        tmp_path
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryRecordingError,
        match="approved-delivery snapshot was not found",
    ):
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            human_confirmation_payload=valid_human_confirmation(
                execution_service
            ),
        )


def test_delivery_identity_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    execution_service = build_approved_assessment(
        tmp_path
    )

    confirmation = valid_human_confirmation(
        execution_service
    )
    confirmation["assessment_id"] = "wrong-assessment"

    with pytest.raises(
        CommercialPaidAssessmentDeliveryRecordingError,
        match="assessment_id does not match approved delivery envelope",
    ):
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            human_confirmation_payload=confirmation,
        )


def test_delivery_recording_does_not_create_client_receipt(
    tmp_path: Path,
) -> None:
    execution_service = build_approved_assessment(
        tmp_path
    )

    result = (
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        )
        .record(
            **HIERARCHY,
            human_confirmation_payload=valid_human_confirmation(
                execution_service
            ),
        )
    )

    safe = result.to_dict()

    assert (
        safe["boundaries"]["delivery_is_not_client_receipt"]
        is True
    )
    assert "client_receipt" not in safe
    assert "client_acknowledgment" not in safe
    assert "client_acceptance" not in safe
