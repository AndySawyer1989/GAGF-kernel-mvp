from dataclasses import FrozenInstanceError, replace
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
    ExecutiveAssessmentProjectionError,
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
PROJECTION_SERVICE = (
    GovernanceAssessmentExecutiveProjectionService()
)
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_pipeline(tenant_id="tenant-alpha"):
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

    return configuration, quality, friction, debt, plan, roadmap


def build_projection(tenant_id="tenant-alpha", **kwargs):
    components = build_pipeline(tenant_id)

    return PROJECTION_SERVICE.project(
        configuration=components[0],
        quality_summary=components[1],
        friction_summary=components[2],
        debt_score=components[3],
        intervention_plan=components[4],
        roadmap=components[5],
        **kwargs,
    )


def test_projection_is_bound_to_full_hierarchy():
    projection = build_projection()

    assert projection.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_projection_preserves_assessment_scope():
    projection = build_projection()

    assert projection.assessment_name == (
        "Governance Runway Assessment"
    )
    assert projection.assessment_period == (
        "2026-01-01 to 2026-06-30"
    )
    assert projection.workflow_count == 1
    assert projection.organizational_unit_count == 1


def test_projection_preserves_quality_and_debt():
    projection = build_projection()

    assert projection.evidence_quality_score == 1.0
    assert projection.evidence_quality_grade == "strong"
    assert projection.evidence_ready_for_analysis is True
    assert projection.governance_debt_score >= 0.0


def test_projection_preserves_friction_summary():
    projection = build_projection()

    assert projection.total_friction_score == 9.0
    assert projection.affected_work_item_count == 4
    assert projection.dominant_constraint == (
        "APPROVAL_DELAYED"
    )


def test_projection_limits_executive_priorities():
    projection = build_projection(maximum_priorities=2)

    assert len(projection.priorities) == 2
    assert [priority.rank for priority in projection.priorities] == [
        1,
        2,
    ]


def test_priority_includes_owner_and_horizon():
    projection = build_projection()

    for priority in projection.priorities:
        assert priority.owner_role is not None
        assert priority.target_horizon in {
            "30-day",
            "60-day",
            "90-day",
        }


def test_projection_contains_phase_counts():
    projection = build_projection()

    assert set(projection.roadmap_phase_counts) == {
        "30-day",
        "60-day",
        "90-day",
    }
    assert sum(projection.roadmap_phase_counts.values()) == 3


def test_projection_contains_source_commitments():
    projection = build_projection()

    assert set(projection.source_commitments) == {
        "scope_configuration_hash",
        "evidence_quality_hash",
        "friction_summary_hash",
        "governance_debt_score_hash",
        "intervention_plan_hash",
        "roadmap_hash",
    }


def test_executive_summary_is_explainable():
    projection = build_projection()

    assert "Governance debt is" in projection.executive_summary
    assert "dominant constraint" in projection.executive_summary
    assert "priority interventions" in projection.executive_summary


def test_projection_has_key_findings():
    projection = build_projection()

    assert len(projection.key_findings) >= 4
    assert any(
        "Evidence quality" in finding
        for finding in projection.key_findings
    )
    assert any(
        "Total weighted friction" in finding
        for finding in projection.key_findings
    )


def test_zero_priority_limit_is_rejected():
    with pytest.raises(
        ExecutiveAssessmentProjectionError,
        match="maximum_priorities",
    ):
        build_projection(maximum_priorities=0)


def test_hierarchy_mismatch_is_rejected():
    components = build_pipeline()
    foreign_roadmap = replace(
        components[5],
        tenant_id="tenant-beta",
    )

    with pytest.raises(
        ExecutiveAssessmentProjectionError,
        match="hierarchies do not match",
    ):
        PROJECTION_SERVICE.project(
            configuration=components[0],
            quality_summary=components[1],
            friction_summary=components[2],
            debt_score=components[3],
            intervention_plan=components[4],
            roadmap=foreign_roadmap,
        )


def test_unready_quality_is_rejected():
    components = build_pipeline()
    unready = replace(
        components[1],
        required_requirements_met=False,
    )

    with pytest.raises(
        ExecutiveAssessmentProjectionError,
        match="not ready",
    ):
        PROJECTION_SERVICE.project(
            configuration=components[0],
            quality_summary=unready,
            friction_summary=components[2],
            debt_score=components[3],
            intervention_plan=components[4],
            roadmap=components[5],
        )


def test_wrong_plan_reference_is_rejected():
    components = build_pipeline()
    invalid_roadmap = replace(
        components[5],
        intervention_plan_hash="wrong-plan-hash",
    )

    with pytest.raises(
        ExecutiveAssessmentProjectionError,
        match="does not reference",
    ):
        PROJECTION_SERVICE.project(
            configuration=components[0],
            quality_summary=components[1],
            friction_summary=components[2],
            debt_score=components[3],
            intervention_plan=components[4],
            roadmap=invalid_roadmap,
        )


def test_projection_hash_is_deterministic():
    assert build_projection().projection_hash == (
        build_projection().projection_hash
    )


def test_projection_hash_changes_by_tenant():
    alpha = build_projection()
    beta = build_projection("tenant-beta")

    assert alpha.projection_hash != beta.projection_hash


def test_projection_serializes_public_contract():
    serialized = build_projection().to_dict()

    assert serialized["assessment_name"] == (
        "Governance Runway Assessment"
    )
    assert serialized["evidence_quality_grade"] == "strong"
    assert len(serialized["priorities"]) == 3
    assert serialized["projection_hash"]


def test_projection_is_immutable():
    projection = build_projection()

    with pytest.raises(FrozenInstanceError):
        projection.governance_debt_score = 0.0
