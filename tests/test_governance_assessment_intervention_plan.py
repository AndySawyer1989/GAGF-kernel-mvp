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
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
    GovernanceAssessmentFrictionAggregationService,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    GovernanceAssessmentInterventionPlanService,
    InterventionPlanError,
    InterventionPriority,
    InterventionType,
    priority_for_score,
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
PLAN_SERVICE = GovernanceAssessmentInterventionPlanService()
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_pipeline(context=None):
    context = context or build_context()

    configuration = SCOPE_SERVICE.configure(
        context=context,
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

    return debt, friction


def build_plan(context=None, **kwargs):
    debt, friction = build_pipeline(context)

    return PLAN_SERVICE.rank(
        debt_score=debt,
        friction_summary=friction,
        **kwargs,
    )


def test_priority_thresholds_are_stable():
    assert priority_for_score(29.9) is InterventionPriority.LOW
    assert priority_for_score(30.0) is InterventionPriority.MEDIUM
    assert priority_for_score(55.0) is InterventionPriority.HIGH
    assert priority_for_score(75.0) is InterventionPriority.URGENT


def test_plan_is_bound_to_full_hierarchy():
    plan = build_plan()

    assert plan.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_plan_contains_one_intervention_per_constraint():
    plan = build_plan()

    assert len(plan.interventions) == 3
    assert {
        item.constraint_category
        for item in plan.interventions
    } == {
        ConstraintCategory.APPROVAL_DELAYED,
        ConstraintCategory.WORK_BLOCKED,
        ConstraintCategory.ESCALATION,
    }


def test_approval_constraint_maps_to_streamline_intervention():
    plan = build_plan()
    approval = next(
        item
        for item in plan.interventions
        if item.constraint_category is (
            ConstraintCategory.APPROVAL_DELAYED
        )
    )

    assert approval.intervention_type is (
        InterventionType.STREAMLINE_APPROVAL
    )


def test_interventions_are_ranked_by_value():
    plan = build_plan()

    assert [item.rank for item in plan.interventions] == [
        1,
        2,
        3,
    ]
    assert [
        item.value_score
        for item in plan.interventions
    ] == sorted(
        (item.value_score for item in plan.interventions),
        reverse=True,
    )


def test_top_intervention_matches_first_rank():
    plan = build_plan()

    assert plan.top_intervention is plan.interventions[0]
    assert plan.top_intervention.rank == 1


def test_lower_burden_increases_intervention_value():
    default_plan = build_plan()
    lower_burden_plan = build_plan(
        implementation_burdens={
            ConstraintCategory.APPROVAL_DELAYED: 0.0,
        }
    )

    default = next(
        item
        for item in default_plan.interventions
        if item.constraint_category is (
            ConstraintCategory.APPROVAL_DELAYED
        )
    )
    improved = next(
        item
        for item in lower_burden_plan.interventions
        if item.constraint_category is (
            ConstraintCategory.APPROVAL_DELAYED
        )
    )

    assert improved.value_score > default.value_score


def test_higher_reversibility_increases_value():
    default_plan = build_plan()
    reversible_plan = build_plan(
        reversibility_scores={
            ConstraintCategory.WORK_BLOCKED: 1.0,
        }
    )

    default = next(
        item
        for item in default_plan.interventions
        if item.constraint_category is (
            ConstraintCategory.WORK_BLOCKED
        )
    )
    improved = next(
        item
        for item in reversible_plan.interventions
        if item.constraint_category is (
            ConstraintCategory.WORK_BLOCKED
        )
    )

    assert improved.value_score > default.value_score


def test_intervention_values_are_bounded():
    plan = build_plan(
        implementation_burdens={
            ConstraintCategory.APPROVAL_DELAYED: -10.0,
        },
        reversibility_scores={
            ConstraintCategory.APPROVAL_DELAYED: 10.0,
        },
    )

    for item in plan.interventions:
        assert 0.0 <= item.value_score <= 100.0
        assert 0.0 <= item.implementation_burden <= 1.0
        assert 0.0 <= item.reversibility <= 1.0


def test_intervention_ids_are_deterministic():
    first = build_plan()
    second = build_plan()

    assert [
        item.intervention_id
        for item in first.interventions
    ] == [
        item.intervention_id
        for item in second.interventions
    ]


def test_intervention_ids_change_by_tenant():
    alpha = build_plan()
    beta = build_plan(build_context("tenant-beta"))

    assert {
        item.intervention_id
        for item in alpha.interventions
    }.isdisjoint({
        item.intervention_id
        for item in beta.interventions
    })


def test_plan_hash_is_deterministic():
    assert build_plan().plan_hash == build_plan().plan_hash


def test_plan_hash_changes_when_burden_changes():
    default = build_plan()
    changed = build_plan(
        implementation_burdens={
            ConstraintCategory.APPROVAL_DELAYED: 0.1,
        }
    )

    assert default.plan_hash != changed.plan_hash


def test_hierarchy_mismatch_is_rejected():
    alpha_debt, _ = build_pipeline()
    _, beta_friction = build_pipeline(
        build_context("tenant-beta")
    )

    with pytest.raises(
        InterventionPlanError,
        match="hierarchies do not match",
    ):
        PLAN_SERVICE.rank(
            debt_score=alpha_debt,
            friction_summary=beta_friction,
        )


def test_rationale_is_explainable():
    plan = build_plan()

    for item in plan.interventions:
        assert len(item.rationale) == 4
        assert any(
            "governed events" in reason
            for reason in item.rationale
        )
        assert any(
            "implementation burden" in reason
            for reason in item.rationale
        )


def test_plan_serializes_public_contract():
    serialized = build_plan().to_dict()

    assert serialized["governance_debt_score"] >= 0.0
    assert len(serialized["interventions"]) == 3
    assert serialized["interventions"][0]["rank"] == 1
    assert serialized["top_intervention_id"] == (
        serialized["interventions"][0]["intervention_id"]
    )


def test_plan_is_immutable():
    plan = build_plan()

    with pytest.raises(FrozenInstanceError):
        plan.governance_debt_score = 0.0
