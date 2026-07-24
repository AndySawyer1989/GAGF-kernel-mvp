from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_debt_score import (
    GovernanceAssessmentDebtScoreService,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    GovernanceAssessmentEvidenceIntakeService,
)
from backend.app.gagf.governance_assessment_evidence_quality import (
    GovernanceAssessmentEvidenceQualityService,
)
from backend.app.gagf.governance_assessment_executive_projection import (
    GovernanceAssessmentExecutiveProjectionService,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    GovernanceAssessmentFrictionAggregationService,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    GovernanceAssessmentInterventionPlanService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_report_package import (
    AssessmentReportPackageError,
    GovernanceAssessmentReportPackageService,
    ReportSectionKind,
)
from backend.app.gagf.governance_assessment_roadmap import (
    GovernanceAssessmentRoadmapService,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
    GovernanceAssessmentScopeConfigurationService,
    ScopeConfigurationStatus,
)


INTAKE_SERVICE = GovernanceAssessmentEvidenceIntakeService()
QUALITY_SERVICE = GovernanceAssessmentEvidenceQualityService()
FRICTION_SERVICE = GovernanceAssessmentFrictionAggregationService()
DEBT_SERVICE = GovernanceAssessmentDebtScoreService()
PLAN_SERVICE = GovernanceAssessmentInterventionPlanService()
ROADMAP_SERVICE = GovernanceAssessmentRoadmapService()
PROJECTION_SERVICE = GovernanceAssessmentExecutiveProjectionService()
REPORT_SERVICE = GovernanceAssessmentReportPackageService()
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_projection(tenant_id="tenant-alpha"):
    context = CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )
    configuration = SCOPE_SERVICE.configure(
        context=context,
        assessment_name="Governance Runway Assessment",
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce friction",),
        expected_outcomes=("Faster delivery",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        status=ScopeConfigurationStatus.LOCKED,
    )
    csv_text = (
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
    intake = INTAKE_SERVICE.ingest_csv(
        context=context,
        source=EvidenceSourceReference(
            source_id="source-001",
            kind=EvidenceSourceKind.CSV,
            display_name="Workflow Export",
        ),
        csv_text=csv_text,
    )
    quality = QUALITY_SERVICE.summarize(
        configuration=configuration,
        intake_results=(intake,),
    )
    friction = FRICTION_SERVICE.aggregate(
        quality_summary=quality,
        intake_results=(intake,),
    )
    debt = DEBT_SERVICE.score(
        quality_summary=quality,
        friction_summary=friction,
    )
    plan = PLAN_SERVICE.rank(
        debt_score=debt,
        friction_summary=friction,
    )
    roadmap = ROADMAP_SERVICE.generate(plan=plan)

    return PROJECTION_SERVICE.project(
        configuration=configuration,
        quality_summary=quality,
        friction_summary=friction,
        debt_score=debt,
        intervention_plan=plan,
        roadmap=roadmap,
    )


def build_package(tenant_id="tenant-alpha", **kwargs):
    values = {
        "projection": build_projection(tenant_id),
        "client_display_name": "ACME Corporation",
        "prepared_by": "FIP Governance Services",
    }
    values.update(kwargs)
    return REPORT_SERVICE.build(**values)


def test_report_is_bound_to_assessment_hierarchy():
    package = build_package()

    assert package.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_report_contains_eight_sections():
    package = build_package()

    assert len(package.sections) == 8
    assert package.manifest.section_count == 8


def test_section_kinds_are_complete():
    package = build_package()

    assert {section.kind for section in package.sections} == {
        ReportSectionKind.EXECUTIVE_SUMMARY,
        ReportSectionKind.ASSESSMENT_SCOPE,
        ReportSectionKind.EVIDENCE_QUALITY,
        ReportSectionKind.GOVERNANCE_DEBT,
        ReportSectionKind.KEY_FINDINGS,
        ReportSectionKind.PRIORITIES,
        ReportSectionKind.ROADMAP,
        ReportSectionKind.EVIDENCE_APPENDIX,
    }


def test_sections_are_sequentially_ordered():
    package = build_package()

    assert [section.order for section in package.sections] == (
        list(range(1, 9))
    )


def test_report_title_contains_client_name():
    package = build_package()

    assert package.title == (
        "Governance Runway Assessment — ACME Corporation"
    )


def test_markdown_contains_required_headings():
    markdown = build_package().markdown

    for heading in (
        "# Governance Runway Assessment — ACME Corporation",
        "## Executive Summary",
        "## Assessment Scope",
        "## Evidence Quality",
        "## Governance Debt",
        "## Priority Interventions",
        "## 30/60/90-Day Roadmap",
        "## Evidence Commitments",
    ):
        assert heading in markdown


def test_markdown_contains_preparer():
    markdown = build_package().markdown

    assert "Prepared by: FIP Governance Services" in markdown


def test_report_contains_governance_debt_score():
    package = build_package()
    projection = build_projection()

    assert (
        f"{projection.governance_debt_score:.2f}"
        in package.markdown
    )


def test_report_contains_ranked_priorities():
    package = build_package()

    assert "1. **" in package.markdown
    assert "Owner:" in package.markdown
    assert "Target:" in package.markdown


def test_report_contains_roadmap_phase_counts():
    package = build_package()

    assert "- 30-day:" in package.markdown
    assert "- 60-day:" in package.markdown
    assert "- 90-day:" in package.markdown


def test_manifest_contains_all_commitments():
    package = build_package()

    assert "scope_configuration_hash" in (
        package.manifest.source_commitments
    )
    assert "executive_projection_hash" in (
        package.manifest.source_commitments
    )


def test_report_id_is_deterministic():
    assert build_package().report_id == build_package().report_id


def test_report_id_changes_by_tenant():
    alpha = build_package()
    beta = build_package("tenant-beta")

    assert alpha.report_id != beta.report_id


def test_package_hash_is_deterministic():
    first = build_package()
    second = build_package()

    assert first.manifest.package_hash == (
        second.manifest.package_hash
    )


def test_package_hash_changes_with_client_name():
    default = build_package()
    changed = build_package(
        client_display_name="Different Client"
    )

    assert default.manifest.package_hash != (
        changed.manifest.package_hash
    )


def test_empty_client_name_is_rejected():
    with pytest.raises(
        AssessmentReportPackageError,
        match="client_display_name",
    ):
        build_package(client_display_name=" ")


def test_empty_preparer_is_rejected():
    with pytest.raises(
        AssessmentReportPackageError,
        match="prepared_by",
    ):
        build_package(prepared_by=" ")


def test_report_serializes_public_contract():
    serialized = build_package().to_dict()

    assert serialized["title"] == (
        "Governance Runway Assessment — ACME Corporation"
    )
    assert len(serialized["sections"]) == 8
    assert serialized["manifest"]["section_count"] == 8
    assert serialized["manifest"]["package_hash"]


def test_report_package_is_immutable():
    package = build_package()

    with pytest.raises(FrozenInstanceError):
        package.title = "Changed"
