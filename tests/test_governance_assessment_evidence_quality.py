from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    GovernanceAssessmentEvidenceIntakeService,
)
from backend.app.gagf.governance_assessment_evidence_quality import (
    EvidenceQualityError,
    EvidenceQualityGrade,
    GovernanceAssessmentEvidenceQualityService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
    GovernanceAssessmentScopeConfigurationService,
    ScopeConfigurationStatus,
)


INTAKE_SERVICE = GovernanceAssessmentEvidenceIntakeService()
QUALITY_SERVICE = GovernanceAssessmentEvidenceQualityService()
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_source(
    source_id="source-001",
    kind=EvidenceSourceKind.CSV,
):
    return EvidenceSourceReference(
        source_id=source_id,
        kind=kind,
        display_name=source_id,
    )


def build_configuration(
    *,
    context=None,
    requirements=None,
):
    if context is None:
        context = build_context()

    if requirements is None:
        requirements = (
            EvidenceRequirement(
                requirement_id="requirement-001",
                source_kind=EvidenceSourceKind.CSV,
                description="Ticket export",
                required=True,
                minimum_record_count=2,
            ),
        )

    return SCOPE_SERVICE.configure(
        context=context,
        assessment_name="Governance Runway Assessment",
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce approval delay",),
        expected_outcomes=("Faster resolution",),
        evidence_requirements=requirements,
        status=ScopeConfigurationStatus.LOCKED,
    )


def valid_csv():
    return (
        "event_id,event_type,occurred_at\n"
        "event-001,APPROVAL_DELAYED,2026-01-10T12:00:00Z\n"
        "event-002,WORK_BLOCKED,2026-01-10T13:00:00Z\n"
    )


def build_intake(
    *,
    context=None,
    source=None,
    csv_text=None,
):
    return INTAKE_SERVICE.ingest_csv(
        context=context or build_context(),
        source=source or build_source(),
        csv_text=csv_text or valid_csv(),
    )


def test_quality_grade_values_are_stable():
    assert EvidenceQualityGrade.INSUFFICIENT.value == (
        "insufficient"
    )
    assert EvidenceQualityGrade.STRONG.value == "strong"


def test_summary_is_bound_to_assessment_hierarchy():
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    assert summary.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_complete_valid_evidence_receives_strong_grade():
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    assert summary.total_rows == 2
    assert summary.accepted_rows == 2
    assert summary.rejected_rows == 0
    assert summary.acceptance_rate == 1.0
    assert summary.requirement_coverage_rate == 1.0
    assert summary.quality_score == 1.0
    assert summary.quality_grade is EvidenceQualityGrade.STRONG
    assert summary.ready_for_analysis is True


def test_source_summary_preserves_intake_identity():
    intake = build_intake()
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(intake,),
    )

    source = summary.source_summaries[0]

    assert source.source_id == "source-001"
    assert source.intake_hash == intake.intake_hash
    assert source.acceptance_rate == 1.0


def test_requirement_evaluation_counts_accepted_rows():
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    evaluation = summary.requirement_evaluations[0]

    assert evaluation.minimum_record_count == 2
    assert evaluation.observed_record_count == 2
    assert evaluation.satisfied is True


def test_missing_required_evidence_is_insufficient():
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(),
    )

    assert summary.accepted_rows == 0
    assert summary.required_requirements_met is False
    assert summary.quality_grade is (
        EvidenceQualityGrade.INSUFFICIENT
    )
    assert summary.ready_for_analysis is False
    assert "No evidence sources were submitted." in (
        summary.findings
    )


def test_partial_requirement_is_reported():
    csv_text = (
        "event_id,event_type,occurred_at\n"
        "event-001,WORK_BLOCKED,2026-01-10T12:00:00Z\n"
    )

    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(
            build_intake(csv_text=csv_text),
        ),
    )

    assert summary.required_requirements_met is False
    assert summary.quality_grade is (
        EvidenceQualityGrade.INSUFFICIENT
    )
    assert any(
        "requirement-001 is unmet" in finding
        for finding in summary.findings
    )


def test_rejected_rows_reduce_acceptance_rate():
    csv_text = (
        "event_id,event_type,occurred_at\n"
        "event-001,WORK_BLOCKED,2026-01-10T12:00:00Z\n"
        "event-002,WORK_BLOCKED,not-a-date\n"
    )

    requirements = (
        EvidenceRequirement(
            requirement_id="requirement-001",
            source_kind=EvidenceSourceKind.CSV,
            description="Ticket export",
            required=True,
            minimum_record_count=1,
        ),
    )

    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(
            requirements=requirements
        ),
        intake_results=(
            build_intake(csv_text=csv_text),
        ),
    )

    assert summary.acceptance_rate == 0.5
    assert summary.requirement_coverage_rate == 1.0
    assert summary.quality_score == 0.7
    assert summary.quality_grade is EvidenceQualityGrade.GOOD
    assert summary.ready_for_analysis is True
    assert "1 evidence rows were rejected." in summary.findings


def test_optional_unmet_requirement_does_not_block_required_gate():
    requirements = (
        EvidenceRequirement(
            requirement_id="required-csv",
            source_kind=EvidenceSourceKind.CSV,
            description="Ticket export",
            required=True,
            minimum_record_count=2,
        ),
        EvidenceRequirement(
            requirement_id="optional-interview",
            source_kind=EvidenceSourceKind.INTERVIEW,
            description="Stakeholder interview",
            required=False,
            minimum_record_count=1,
        ),
    )

    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(
            requirements=requirements
        ),
        intake_results=(build_intake(),),
    )

    assert summary.required_requirements_met is True
    assert summary.requirement_coverage_rate == 0.5
    assert summary.quality_score == 0.8
    assert summary.quality_grade is EvidenceQualityGrade.GOOD


def test_duplicate_source_identifiers_are_rejected():
    intake = build_intake()

    with pytest.raises(
        EvidenceQualityError,
        match="duplicate source identifiers",
    ):
        QUALITY_SERVICE.summarize(
            configuration=build_configuration(),
            intake_results=(intake, intake),
        )


def test_foreign_hierarchy_evidence_is_rejected():
    foreign = build_intake(
        context=build_context(tenant_id="tenant-beta")
    )

    with pytest.raises(
        EvidenceQualityError,
        match="hierarchy",
    ):
        QUALITY_SERVICE.summarize(
            configuration=build_configuration(),
            intake_results=(foreign,),
        )


def test_summary_hash_is_deterministic():
    first = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )
    second = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    assert first.summary_hash == second.summary_hash


def test_summary_hash_changes_by_tenant():
    alpha = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    beta_context = build_context(tenant_id="tenant-beta")
    beta = QUALITY_SERVICE.summarize(
        configuration=build_configuration(
            context=beta_context
        ),
        intake_results=(
            build_intake(context=beta_context),
        ),
    )

    assert alpha.summary_hash != beta.summary_hash


def test_summary_serializes_public_contract():
    serialized = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    ).to_dict()

    assert serialized["quality_grade"] == "strong"
    assert serialized["ready_for_analysis"] is True
    assert serialized["source_summaries"][0][
        "accepted_rows"
    ] == 2
    assert serialized["requirement_evaluations"][0][
        "satisfied"
    ] is True


def test_clean_summary_reports_all_requirements_met():
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    assert summary.findings == (
        "All configured evidence requirements were met.",
    )


def test_summary_is_immutable():
    summary = QUALITY_SERVICE.summarize(
        configuration=build_configuration(),
        intake_results=(build_intake(),),
    )

    with pytest.raises(FrozenInstanceError):
        summary.quality_score = 0.0
