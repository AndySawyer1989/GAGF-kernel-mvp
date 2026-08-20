import hashlib
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    EXECUTION_EVIDENCE_STATUS_APPROVED,
    GovernanceRealPaidAssessmentExecutionEvidenceService,
    RealAssessmentExecutionEvidenceApproval,
    RealPaidAssessmentExecutionEvidenceError,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    EvidenceDataClassification,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
)


CSV_TEXT = (
    "event_id,event_type,occurred_at,work_item_id\n"
    "event-001,APPROVAL_DELAYED,"
    "2026-01-01T12:00:00Z,TICKET-1\n"
    "event-002,APPROVAL_DELAYED,"
    "2026-01-01T13:00:00Z,TICKET-2\n"
    "event-003,WORK_BLOCKED,"
    "2026-01-02T12:00:00Z,TICKET-3\n"
    "event-004,ESCALATION,"
    "2026-01-03T12:00:00Z,TICKET-4\n"
)


def sha256_text(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def build_intake():
    return RealPaidAssessmentIntake(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        client_display_name="ACME Corporation",
        assessment_name="Governance Runway Assessment",
        operator_name="FIP Operator",
        client_contact_name="Client Representative",
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            RealAssessmentEvidenceDeclaration(
                evidence_id="source-001",
                source_kind="csv",
                description="Redacted workflow export",
                classification=(
                    EvidenceDataClassification.REDACTED
                ),
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=RealAssessmentStorageDeclaration(
            repository_path=(
                r"C:\FIP\pilot-data\client-acme\assessment-001.sqlite3"
            ),
            operator_controlled_location=True,
            access_restricted=True,
            storage_protection_confirmed=True,
            backup_plan_recorded=True,
            retention_period_recorded=True,
            deletion_plan_recorded=True,
        ),
    )


def build_request(csv_text=CSV_TEXT):
    return AssessmentExecutionRequest(
        context=CommercialHierarchyContext(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        ),
        assessment_name="Governance Runway Assessment",
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce governance friction",),
        expected_outcomes=("Faster completion",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        evidence_inputs=(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="source-001",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Workflow Export",
                ),
                csv_text=csv_text,
            ),
        ),
        client_display_name="ACME Corporation",
        prepared_by="FIP Operator",
    )


def build_approval(
    *,
    digest=None,
):
    return RealAssessmentExecutionEvidenceApproval(
        evidence_id="source-001",
        approved_content_sha256=(
            digest or sha256_text(CSV_TEXT)
        ),
        approved_by="FIP Operator",
        approved_at="2026-08-20T18:20:00+00:00",
        execution_evidence_approved=True,
    )


def test_exact_approved_bytes_bind_for_execution():
    result = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=build_intake(),
            request=build_request(),
            approvals=(build_approval(),),
        )
    )

    assert (
        result.binding_status
        == EXECUTION_EVIDENCE_STATUS_APPROVED
    )
    assert result.approved_evidence_ids == ("source-001",)
    assert result.evidence_content_hashes == (
        sha256_text(CSV_TEXT),
    )
    assert (
        result.hierarchy_key
        == "tenant-alpha/client-acme/engagement-001/assessment-001"
    )


def test_modified_bytes_fail_closed():
    modified = CSV_TEXT.replace(
        "WORK_BLOCKED",
        "APPROVAL_REJECTED",
    )

    with pytest.raises(
        RealPaidAssessmentExecutionEvidenceError,
        match="content hash does not match",
    ):
        (
            GovernanceRealPaidAssessmentExecutionEvidenceService()
            .bind(
                intake=build_intake(),
                request=build_request(
                    csv_text=modified
                ),
                approvals=(build_approval(),),
            )
        )


def test_undeclared_execution_source_fails_closed():
    request = build_request()

    changed_request = AssessmentExecutionRequest(
        context=request.context,
        assessment_name=request.assessment_name,
        workflow_names=request.workflow_names,
        organizational_units=request.organizational_units,
        period_start=request.period_start,
        period_end=request.period_end,
        objectives=request.objectives,
        expected_outcomes=request.expected_outcomes,
        evidence_requirements=request.evidence_requirements,
        evidence_inputs=(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="source-999",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Unexpected Export",
                ),
                csv_text=CSV_TEXT,
            ),
        ),
        client_display_name=request.client_display_name,
        prepared_by=request.prepared_by,
    )

    with pytest.raises(
        RealPaidAssessmentExecutionEvidenceError,
        match="do not exactly match intake declarations",
    ):
        (
            GovernanceRealPaidAssessmentExecutionEvidenceService()
            .bind(
                intake=build_intake(),
                request=changed_request,
                approvals=(build_approval(),),
            )
        )


def test_unapproved_sensitive_classification_fails_closed():
    base = build_intake()

    intake = RealPaidAssessmentIntake(
        tenant_id=base.tenant_id,
        client_id=base.client_id,
        engagement_id=base.engagement_id,
        assessment_id=base.assessment_id,
        client_display_name=base.client_display_name,
        assessment_name=base.assessment_name,
        operator_name=base.operator_name,
        client_contact_name=base.client_contact_name,
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            RealAssessmentEvidenceDeclaration(
                evidence_id="source-001",
                source_kind="csv",
                description="Sensitive workflow export",
                classification=(
                    EvidenceDataClassification.REGULATED
                ),
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=base.storage,
    )

    with pytest.raises(
        RealPaidAssessmentExecutionEvidenceError,
        match="classification is not permitted",
    ):
        (
            GovernanceRealPaidAssessmentExecutionEvidenceService()
            .bind(
                intake=intake,
                request=build_request(),
                approvals=(build_approval(),),
            )
        )


def test_binding_does_not_manufacture_execution_authority():
    result = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=build_intake(),
            request=build_request(),
            approvals=(build_approval(),),
        )
    )

    payload = result.to_dict()

    assert payload["boundaries"][
        "evidence_hash_approval_is_not_paid_work_authorization"
    ] is True
    assert payload["boundaries"][
        "evidence_hash_approval_is_not_execution"
    ] is True
    assert payload["boundaries"][
        "content_hash_match_is_not_evidence_truth"
    ] is True
    assert payload["boundaries"][
        "execution_evidence_approval_is_not_production_onboarding"
    ] is True

    assert "assessment_executed" not in payload
    assert "paid_assessment_authorized" not in payload
    assert "customer_outcome_verified" not in payload