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
from backend.app.gagf.governance_assessment_friction_aggregation import (
    GovernanceAssessmentFrictionAggregationService,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    GovernanceAssessmentInterventionPlanService,
    InterventionPriority,
    InterventionType,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_roadmap import (
    AssessmentRoadmapError,
    GovernanceAssessmentRoadmapService,
    RoadmapHorizon,
    RoadmapItemStatus,
    horizon_for_candidate,
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
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_plan(tenant_id="tenant-alpha"):
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

    return PLAN_SERVICE.rank(
        debt_score=debt,
        friction_summary=friction,
    )


def build_roadmap(tenant_id="tenant-alpha", **kwargs):
    return ROADMAP_SERVICE.generate(
        plan=build_plan(tenant_id),
        **kwargs,
    )


def test_horizon_assignment_rules_are_stable():
    plan = build_plan()
    candidate = plan.interventions[0]

    urgent = replace(
        candidate,
        priority=InterventionPriority.URGENT,
    )
    high_low_burden = replace(
        candidate,
        priority=InterventionPriority.HIGH,
        implementation_burden=0.4,
    )
    high_high_burden = replace(
        candidate,
        priority=InterventionPriority.HIGH,
        implementation_burden=0.8,
    )
    medium = replace(
        candidate,
        priority=InterventionPriority.MEDIUM,
    )
    low = replace(
        candidate,
        priority=InterventionPriority.LOW,
    )

    assert horizon_for_candidate(urgent) is RoadmapHorizon.DAY_30
    assert horizon_for_candidate(high_low_burden) is (
        RoadmapHorizon.DAY_30
    )
    assert horizon_for_candidate(high_high_burden) is (
        RoadmapHorizon.DAY_60
    )
    assert horizon_for_candidate(medium) is RoadmapHorizon.DAY_60
    assert horizon_for_candidate(low) is RoadmapHorizon.DAY_90


def test_roadmap_is_bound_to_full_hierarchy():
    roadmap = build_roadmap()

    assert roadmap.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_roadmap_contains_all_three_phases():
    roadmap = build_roadmap()

    assert tuple(
        phase.horizon
        for phase in roadmap.phases
    ) == (
        RoadmapHorizon.DAY_30,
        RoadmapHorizon.DAY_60,
        RoadmapHorizon.DAY_90,
    )


def test_total_items_match_intervention_plan():
    plan = build_plan()
    roadmap = ROADMAP_SERVICE.generate(plan=plan)

    assert roadmap.total_items == len(plan.interventions)


def test_items_preserve_intervention_sequence():
    roadmap = build_roadmap()
    items = tuple(
        item
        for phase in roadmap.phases
        for item in phase.items
    )

    assert sorted(item.sequence for item in items) == [1, 2, 3]


def test_items_receive_default_owner_roles():
    roadmap = build_roadmap()

    for phase in roadmap.phases:
        for item in phase.items:
            assert item.owner_role
            assert item.owner_role.strip() == item.owner_role


def test_owner_role_can_be_overridden():
    roadmap = build_roadmap(
        owner_roles={
            InterventionType.STREAMLINE_APPROVAL: (
                "Chief Operating Officer"
            ),
        }
    )

    item = next(
        item
        for phase in roadmap.phases
        for item in phase.items
        if item.intervention_type is (
            InterventionType.STREAMLINE_APPROVAL
        )
    )

    assert item.owner_role == "Chief Operating Officer"


def test_empty_owner_role_is_rejected():
    with pytest.raises(
        AssessmentRoadmapError,
        match="owner role",
    ):
        build_roadmap(
            owner_roles={
                InterventionType.STREAMLINE_APPROVAL: " ",
            }
        )


def test_each_item_has_measurable_outcome():
    roadmap = build_roadmap()

    for phase in roadmap.phases:
        for item in phase.items:
            assert item.measurable_outcome.endswith(".")


def test_later_phase_items_receive_dependency():
    roadmap = build_roadmap()
    later_items = tuple(
        item
        for phase in roadmap.phases
        if phase.horizon is not RoadmapHorizon.DAY_30
        for item in phase.items
    )

    for item in later_items:
        if item.sequence > 1:
            assert len(item.dependency_ids) == 1


def test_roadmap_items_start_planned():
    roadmap = build_roadmap()

    assert all(
        item.status is RoadmapItemStatus.PLANNED
        for phase in roadmap.phases
        for item in phase.items
    )


def test_item_identifiers_are_deterministic():
    first = build_roadmap()
    second = build_roadmap()

    first_ids = {
        item.roadmap_item_id
        for phase in first.phases
        for item in phase.items
    }
    second_ids = {
        item.roadmap_item_id
        for phase in second.phases
        for item in phase.items
    }

    assert first_ids == second_ids


def test_item_identifiers_change_by_tenant():
    alpha = build_roadmap()
    beta = build_roadmap("tenant-beta")

    alpha_ids = {
        item.roadmap_item_id
        for phase in alpha.phases
        for item in phase.items
    }
    beta_ids = {
        item.roadmap_item_id
        for phase in beta.phases
        for item in phase.items
    }

    assert alpha_ids.isdisjoint(beta_ids)


def test_roadmap_hash_is_deterministic():
    assert build_roadmap().roadmap_hash == (
        build_roadmap().roadmap_hash
    )


def test_roadmap_hash_changes_with_owner_assignment():
    default = build_roadmap()
    changed = build_roadmap(
        owner_roles={
            InterventionType.STREAMLINE_APPROVAL: (
                "Executive Sponsor"
            ),
        }
    )

    assert default.roadmap_hash != changed.roadmap_hash


def test_duplicate_interventions_are_rejected():
    plan = build_plan()
    duplicated = replace(
        plan,
        interventions=(
            plan.interventions[0],
            plan.interventions[0],
        ),
    )

    with pytest.raises(
        AssessmentRoadmapError,
        match="duplicate identifiers",
    ):
        ROADMAP_SERVICE.generate(plan=duplicated)


def test_items_can_be_retrieved_by_horizon():
    roadmap = build_roadmap()

    assert roadmap.items_for_horizon(
        RoadmapHorizon.DAY_30
    ) == roadmap.phases[0].items


def test_roadmap_serializes_public_contract():
    serialized = build_roadmap().to_dict()

    assert serialized["total_items"] == 3
    assert len(serialized["phases"]) == 3
    assert serialized["phases"][0]["horizon"] == "30-day"
    assert serialized["intervention_plan_hash"]


def test_roadmap_is_immutable():
    roadmap = build_roadmap()

    with pytest.raises(FrozenInstanceError):
        roadmap.total_items = 0
