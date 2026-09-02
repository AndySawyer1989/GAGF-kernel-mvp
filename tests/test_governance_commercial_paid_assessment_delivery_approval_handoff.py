from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_delivery_approval_handoff import (
    CommercialPaidAssessmentDeliveryApprovalHandoffError,
    GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from tests.test_governance_commercial_paid_assessment_execution import (
    BINDING_HASH,
    build_execution_input,
)


HIERARCHY = {
    "tenant_id": "tenant-001",
    "client_id": "client-001",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}


def build_completed_assessment(
    tmp_path: Path,
) -> GovernanceCommercialPaidAssessmentExecutionService:
    execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=tmp_path / "paid-assessments"
        )
    )

    database_path = (
        execution_service.database_path_for_hierarchy(
            **HIERARCHY
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    execution_service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    return execution_service


def build_service(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService:
    readiness_service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    return GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService(
        readiness_service=readiness_service
    )


def valid_approval_payload(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> dict:
    readiness = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
        .verify(
            **HIERARCHY
        )
    )

    execution_result = readiness.readiness.execution_result

    return {
        "approval_id": "delivery-approval-001",
        "tenant_id": execution_result.tenant_id,
        "client_id": execution_result.client_id,
        "engagement_id": execution_result.engagement_id,
        "assessment_id": execution_result.assessment_id,
        "report_id": execution_result.report_id,
        "approved_by": "Human Delivery Reviewer",
        "approved_at": "2026-09-02T19:30:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }


def test_explicit_human_approval_builds_existing_pa003_envelope(
    tmp_path: Path,
) -> None:
    execution_service = build_completed_assessment(
        tmp_path
    )

    service = build_service(
        execution_service
    )

    result = service.handoff(
        **HIERARCHY,
        approval_payload=valid_approval_payload(
            execution_service
        ),
    )

    assert (
        result.handoff.handoff_status
        == "approved_for_human_delivery"
    )
    assert (
        result.handoff.delivery_envelope.delivery_status
        == "approved_for_human_delivery"
    )

    safe = result.to_dict()

    assert safe["approved_for_human_delivery"] is True
    assert safe["approval_id"] == "delivery-approval-001"
    assert safe["approval_hash"]
    assert safe["delivery_envelope_hash"]
    assert safe["report_id"]

    assert "report_package" not in safe
    assert "execution_result" not in safe
    assert "readiness" not in safe

    assert (
        safe["boundaries"][
            "existing_real_approval_handoff_is_authoritative"
        ]
        is True
    )
    assert (
        safe["boundaries"][
            "pa003_remains_delivery_envelope_authority"
        ]
        is True
    )


def test_handoff_is_restart_safe(
    tmp_path: Path,
) -> None:
    execution_service = build_completed_assessment(
        tmp_path
    )

    payload = valid_approval_payload(
        execution_service
    )

    restarted_execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                execution_service.execution_directory
            )
        )
    )

    result = build_service(
        restarted_execution_service
    ).handoff(
        **HIERARCHY,
        approval_payload=payload,
    )

    assert (
        result.handoff.hierarchy_key
        == (
            "tenant-001/client-001/"
            "engagement-001/assessment-001"
        )
    )
    assert (
        result.handoff.delivery_envelope.delivery_status
        == "approved_for_human_delivery"
    )


def test_handoff_does_not_infer_missing_human_approval(
    tmp_path: Path,
) -> None:
    execution_service = build_completed_assessment(
        tmp_path
    )

    payload = valid_approval_payload(
        execution_service
    )
    payload["delivery_approved"] = False

    with pytest.raises(
        CommercialPaidAssessmentDeliveryApprovalHandoffError,
        match="delivery_approved must be explicitly true",
    ):
        build_service(
            execution_service
        ).handoff(
            **HIERARCHY,
            approval_payload=payload,
        )


def test_handoff_rejects_wrong_report_identity(
    tmp_path: Path,
) -> None:
    execution_service = build_completed_assessment(
        tmp_path
    )

    payload = valid_approval_payload(
        execution_service
    )
    payload["report_id"] = "wrong-report-id"

    with pytest.raises(
        CommercialPaidAssessmentDeliveryApprovalHandoffError,
        match="report_id does not match verified readiness",
    ):
        build_service(
            execution_service
        ).handoff(
            **HIERARCHY,
            approval_payload=payload,
        )


def test_handoff_does_not_record_delivery(
    tmp_path: Path,
) -> None:
    execution_service = build_completed_assessment(
        tmp_path
    )

    database_path = (
        execution_service.database_path_for_hierarchy(
            **HIERARCHY
        )
    )

    before = database_path.read_bytes()

    result = build_service(
        execution_service
    ).handoff(
        **HIERARCHY,
        approval_payload=valid_approval_payload(
            execution_service
        ),
    )

    after = database_path.read_bytes()

    assert after == before
    assert (
        result.to_dict()["boundaries"][
            "approved_for_human_delivery_is_not_delivery"
        ]
        is True
    )
