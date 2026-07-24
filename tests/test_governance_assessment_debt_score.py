from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_debt_score import (
    GovernanceAssessmentDebtScoreService,
    GovernanceDebtBand,
    GovernanceDebtScoreError,
    debt_band,
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
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
    GovernanceAssessmentFrictionAggregationService,
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
FRICTION_SERVICE = GovernanceAssessmentFrictionAggregationService()
DEBT_SERVICE = GovernanceAssessmentDebtScoreService()
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_configuration(context=None):
    context = context or build_context()

    return SCOPE_SERVICE.configure(
        context=context,
        assessment_name="Governance Runway Assessment",
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce governance friction",),
        expected_outcomes=("Faster work completion",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow events",
                required=True,
                minimum_record_count=4,
            ),
        ),
        status=ScopeConfigurationStatus.LOCKED,
    )


def build_csv():
    return (
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


def build_pipeline(context=None):
    context = context or build_context()
    source = EvidenceSourceReference(
        source_id="source-001",
        kind=EvidenceSourceKind.CSV,
        display_name="Workflow Export",
    )
    intake = INTAKE_SERVICE.ingest_csv(
        context=context,
        source=source,
        csv_text=build_csv(),
    )
    quality = QUALITY_SERVICE.summarize(
        configuration=build_configuration(context),
        intake_results=(intake,),
    )
    friction = FRICTION_SERVICE.aggregate(
        quality_summary=quality,
        intake_results=(intake,),
    )

    return intake, quality, friction


def build_score(context=None):
    _, quality, friction = build_pipeline(context)

    return DEBT_SERVICE.score(
        quality_summary=quality,
        friction_summary=friction,
    )


def test_debt_band_thresholds_are_stable():
    assert debt_band(19.9) is GovernanceDebtBand.MINIMAL
    assert debt_band(20.0) is GovernanceDebtBand.LOW
    assert debt_band(40.0) is GovernanceDebtBand.MODERATE
    assert debt_band(60.0) is GovernanceDebtBand.HIGH
    assert debt_band(80.0) is GovernanceDebtBand.CRITICAL


def test_score_is_bound_to_full_hierarchy():
    result = build_score()

    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_score_is_bounded_to_one_hundred():
    result = build_score()

    assert 0.0 <= result.score <= 100.0


def test_score_contains_five_components():
    result = build_score()

    assert len(result.components) == 5
    assert {
        component.component_id
        for component in result.components
    } == {
        "friction-intensity",
        "constraint-concentration",
        "work-reach",
        "unrecognized-penalty",
        "evidence-confidence",
    }


def test_component_weights_sum_to_one():
    result = build_score()

    assert sum(
        component.weight
        for component in result.components
    ) == pytest.approx(1.0)


def test_score_matches_component_points():
    result = build_score()

    expected = round(
        sum(
            component.weighted_points
            for component in result.components
        ),
        4,
    )

    assert result.score == expected


def test_dominant_constraint_is_preserved():
    result = build_score()

    assert result.dominant_constraint is (
        ConstraintCategory.APPROVAL_DELAYED
    )


def test_evidence_quality_is_preserved():
    result = build_score()

    assert result.evidence_quality_score == 1.0


def test_score_findings_are_explainable():
    result = build_score()

    assert any(
        "Governance debt is" in finding
        for finding in result.findings
    )
    assert any(
        "Dominant constraint" in finding
        for finding in result.findings
    )
    assert any(
        "unique work items" in finding
        for finding in result.findings
    )


def test_hierarchy_mismatch_is_rejected():
    _, quality, friction = build_pipeline()

    foreign_friction = replace(
        friction,
        tenant_id="tenant-beta",
    )

    with pytest.raises(
        GovernanceDebtScoreError,
        match="hierarchies do not match",
    ):
        DEBT_SERVICE.score(
            quality_summary=quality,
            friction_summary=foreign_friction,
        )


def test_unready_quality_is_rejected():
    _, quality, friction = build_pipeline()
    unready = replace(
        quality,
        quality_score=0.4,
        required_requirements_met=False,
    )

    with pytest.raises(
        GovernanceDebtScoreError,
        match="not ready for debt scoring",
    ):
        DEBT_SERVICE.score(
            quality_summary=unready,
            friction_summary=friction,
        )


def test_evidence_count_mismatch_is_rejected():
    _, quality, friction = build_pipeline()
    mismatched = replace(
        friction,
        total_evidence_events=3,
    )

    with pytest.raises(
        GovernanceDebtScoreError,
        match="evidence count",
    ):
        DEBT_SERVICE.score(
            quality_summary=quality,
            friction_summary=mismatched,
        )


def test_score_hash_is_deterministic():
    first = build_score()
    second = build_score()

    assert first.score_hash == second.score_hash


def test_score_hash_changes_by_tenant():
    alpha = build_score()
    beta = build_score(
        build_context("tenant-beta")
    )

    assert alpha.score_hash != beta.score_hash


def test_score_serializes_public_contract():
    serialized = build_score().to_dict()

    assert serialized["band"] in {
        "minimal",
        "low",
        "moderate",
        "high",
        "critical",
    }
    assert serialized["score"] >= 0.0
    assert len(serialized["components"]) == 5
    assert serialized["dominant_constraint"] == (
        "APPROVAL_DELAYED"
    )


def test_score_result_is_immutable():
    result = build_score()

    with pytest.raises(FrozenInstanceError):
        result.score = 0.0
