from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_assessment_report_package import (
    GovernanceAssessmentReportPackageService,
)
from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernancePaidAssessmentDeliveryEnvelopeService,
    PaidAssessmentDeliveryApproval,
    PaidAssessmentDeliveryEnvelopeError,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    PaidAssessmentExecutionResult,
)
from tests.test_governance_assessment_report_package import (
    build_projection,
)


SERVICE = GovernancePaidAssessmentDeliveryEnvelopeService()
REPORT_SERVICE = GovernanceAssessmentReportPackageService()


def build_report(
    *,
    tenant_id="tenant-alpha",
    client_display_name="Example Client",
):
    return REPORT_SERVICE.build(
        projection=build_projection(tenant_id),
        client_display_name=client_display_name,
        prepared_by="FIP Operator",
    )


def build_execution_result(
    report=None,
    **overrides,
):
    report = report or build_report()

    values = {
        "tenant_id": report.manifest.tenant_id,
        "client_id": report.manifest.client_id,
        "engagement_id": report.manifest.engagement_id,
        "assessment_id": report.manifest.assessment_id,
        "handoff_hash": "a" * 64,
        "assessment_execution_request_hash": "b" * 64,
        "application_request_hash": "b" * 64,
        "application_hash": "c" * 64,
        "demonstration_hash": "d" * 64,
        "persistence_hash": "e" * 64,
        "report_id": report.report_id,
        "artifact_count": 10,
        "application_completed": True,
        "execution_result_hash": "f" * 64,
    }
    values.update(overrides)

    return PaidAssessmentExecutionResult(**values)


def build_approval(
    report=None,
    **overrides,
):
    report = report or build_report()

    values = {
        "approval_id": "delivery-approval-001",
        "tenant_id": report.manifest.tenant_id,
        "client_id": report.manifest.client_id,
        "engagement_id": report.manifest.engagement_id,
        "assessment_id": report.manifest.assessment_id,
        "report_id": report.report_id,
        "approved_by": "FIP Operator",
        "approved_at": "2026-08-18T16:30:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }
    values.update(overrides)

    return PaidAssessmentDeliveryApproval(**values)


def build_envelope(
    *,
    report=None,
    execution_result=None,
    approval=None,
):
    report = report or build_report()
    execution_result = (
        execution_result
        or build_execution_result(report)
    )
    approval = approval or build_approval(report)

    return SERVICE.build_envelope(
        execution_result=execution_result,
        report_package=report,
        delivery_approval=approval,
    )


def test_builds_approved_delivery_envelope():
    envelope = build_envelope()

    assert envelope.delivery_status == (
        "approved_for_human_delivery"
    )


def test_envelope_preserves_full_hierarchy():
    envelope = build_envelope()

    assert envelope.hierarchy_key == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )


def test_envelope_binds_execution_result():
    report = build_report()
    execution = build_execution_result(report)

    envelope = build_envelope(
        report=report,
        execution_result=execution,
    )

    assert (
        envelope.execution_result_hash
        == execution.execution_result_hash
    )
    assert envelope.application_hash == execution.application_hash


def test_envelope_binds_real_report_package():
    report = build_report()

    envelope = build_envelope(report=report)

    assert envelope.report_id == report.report_id
    assert (
        envelope.report_package_hash
        == report.manifest.package_hash
    )
    assert (
        envelope.report_markdown_hash
        == report.manifest.markdown_hash
    )


def test_envelope_binds_delivery_approval():
    report = build_report()
    approval = build_approval(report)

    envelope = build_envelope(
        report=report,
        approval=approval,
    )

    assert (
        envelope.delivery_approval_id
        == approval.approval_id
    )
    assert (
        envelope.delivery_approval_hash
        == approval.approval_hash
    )


def test_rejects_incomplete_application():
    report = build_report()

    execution = build_execution_result(
        report,
        application_completed=False,
    )

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="must be completed",
    ):
        build_envelope(
            report=report,
            execution_result=execution,
        )


def test_rejects_cross_tenant_report():
    authorized_report = build_report(
        tenant_id="tenant-alpha"
    )
    foreign_report = build_report(
        tenant_id="tenant-beta"
    )

    execution = build_execution_result(
        authorized_report
    )
    approval = build_approval(
        foreign_report
    )

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="hierarchy does not match",
    ):
        build_envelope(
            report=foreign_report,
            execution_result=execution,
            approval=approval,
        )


def test_rejects_report_id_mismatch():
    report = build_report()

    execution = build_execution_result(
        report,
        report_id="different-report-id",
    )

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="report_id does not match",
    ):
        build_envelope(
            report=report,
            execution_result=execution,
        )


def test_rejects_delivery_approval_for_other_report():
    report = build_report()

    approval = build_approval(
        report,
        report_id="other-report",
    )

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="approval identity does not match",
    ):
        build_envelope(
            report=report,
            approval=approval,
        )


def test_delivery_requires_scope_approval():
    report = build_report()

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="scope_approved",
    ):
        build_approval(
            report,
            scope_approved=False,
        )


def test_delivery_requires_evidence_boundary_approval():
    report = build_report()

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="evidence_boundary_approved",
    ):
        build_approval(
            report,
            evidence_boundary_approved=False,
        )


def test_delivery_requires_buyer_language_approval():
    report = build_report()

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="buyer_language_approved",
    ):
        build_approval(
            report,
            buyer_language_approved=False,
        )


def test_delivery_requires_explicit_delivery_approval():
    report = build_report()

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="delivery_approved",
    ):
        build_approval(
            report,
            delivery_approved=False,
        )


def test_delivery_approval_hash_is_deterministic():
    report = build_report()

    first = build_approval(report)
    second = build_approval(report)

    assert first.approval_hash == second.approval_hash


def test_envelope_hash_is_deterministic():
    report = build_report()

    first = build_envelope(report=report)
    second = build_envelope(report=report)

    assert first.envelope_hash == second.envelope_hash


def test_different_report_changes_envelope_hash():
    first_report = build_report(
        client_display_name="Example Client"
    )
    second_report = build_report(
        client_display_name="Different Client"
    )

    first = build_envelope(
        report=first_report
    )
    second = build_envelope(
        report=second_report
    )

    assert first.report_id != second.report_id
    assert first.envelope_hash != second.envelope_hash


def test_delivery_approval_is_immutable():
    approval = build_approval()

    with pytest.raises(FrozenInstanceError):
        approval.approved_by = "Other Operator"


def test_envelope_is_immutable():
    envelope = build_envelope()

    with pytest.raises(FrozenInstanceError):
        envelope.delivery_status = "sent"


def test_serialized_envelope_does_not_claim_delivery():
    payload = build_envelope().to_dict()

    assert payload["delivery_status"] == (
        "approved_for_human_delivery"
    )

    forbidden_keys = {
        "delivered",
        "delivery_completed",
        "client_received",
        "client_acknowledged",
        "recommendations_accepted",
        "intervention_authorized",
        "customer_outcome_verified",
        "causation_established",
        "roi_verified",
    }

    assert forbidden_keys.isdisjoint(payload)
