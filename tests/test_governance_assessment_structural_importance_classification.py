from __future__ import annotations

from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
    FrictionBand,
)
from backend.app.gagf.governance_assessment_structural_importance import (
    AssessmentStructuralImportanceEvidenceSummary,
    StructuralBurdenEvidence,
    StructuralConditionEvidence,
    StructuralEvidenceSupport,
    StructuralPenetrationEvidence,
    StructuralTemporalEvidence,
)
from backend.app.gagf.governance_assessment_structural_importance_classification import (
    STRUCTURAL_IMPORTANCE_CLASSIFICATION_AUTHORITY,
    GovernanceAssessmentStructuralImportanceClassificationService,
    StructuralImportanceLevel,
)


def build_condition(
    *,
    category=ConstraintCategory.APPROVAL_DELAYED,
    event_count=5,
    event_share=0.25,
    friction_score=10.0,
    work_items=4,
    teams=3,
    lifecycles=4,
    active_days=3,
    precedence_opportunities=4,
    precedence_count=3,
    precedence_rate=0.75,
    downstream_events=5,
    downstream_constraints=2,
    evidence_quality=0.95,
    scope_breadth=3,
):
    return StructuralConditionEvidence(
        category=category,
        burden=StructuralBurdenEvidence(
            event_count=event_count,
            event_share=event_share,
            friction_score=friction_score,
            friction_band=FrictionBand.HIGH,
            total_duration_minutes=120.0,
        ),
        penetration=StructuralPenetrationEvidence(
            unique_work_item_count=work_items,
            unique_actor_count=4,
            unique_team_count=teams,
            unique_lifecycle_count=lifecycles,
            active_day_count=active_days,
        ),
        temporal=StructuralTemporalEvidence(
            precedence_opportunity_count=(
                precedence_opportunities
            ),
            precedence_count=(
                precedence_count
            ),
            precedence_rate=(
                precedence_rate
            ),
            downstream_event_count=(
                downstream_events
            ),
            downstream_constraint_count=(
                downstream_constraints
            ),
            downstream_lifecycle_count=3,
            downstream_duration_minutes=90.0,
        ),
        support=StructuralEvidenceSupport(
            significance_level="DOMINANT",
            scope_level="SYSTEMIC",
            mean_evidence_quality=(
                evidence_quality
            ),
            diagnostic_support_count=5,
            scope_breadth_count=(
                scope_breadth
            ),
            is_diagnosed_condition=True,
            is_systemic_condition=True,
        ),
        evidence_hash="a" * 64,
    )


def build_summary(
    *conditions,
):
    return (
        AssessmentStructuralImportanceEvidenceSummary(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
            conditions=tuple(
                conditions
            ),
            summary_hash="b" * 64,
        )
    )


def classify(
    condition,
):
    return (
        GovernanceAssessmentStructuralImportanceClassificationService()
        .classify(
            structural_summary=(
                build_summary(
                    condition
                )
            )
        )
    )


def test_high_with_strong_convergent_evidence():
    result = classify(
        build_condition()
    )

    classified = result.conditions[0]

    assert (
        classified.level
        == StructuralImportanceLevel.HIGH
    )

    assert (
        classified.sufficiency.sufficient
        is True
    )

    assert (
        classified.axes.active_count
        == 7
    )


def test_limited_when_event_support_is_insufficient():
    result = classify(
        build_condition(
            event_count=2,
        )
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.LIMITED
    )


def test_limited_when_process_support_is_insufficient():
    result = classify(
        build_condition(
            work_items=1,
        )
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.LIMITED
    )


def test_limited_when_temporal_support_is_insufficient():
    result = classify(
        build_condition(
            active_days=1,
        )
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.LIMITED
    )


def test_limited_when_quality_is_unobserved():
    result = classify(
        build_condition(
            evidence_quality=None,
        )
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.LIMITED
    )


def test_low_requires_sufficient_evidence():
    condition = build_condition(
        event_count=3,
        event_share=0.05,
        work_items=2,
        teams=1,
        lifecycles=1,
        active_days=2,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=0.70,
        scope_breadth=1,
    )

    result = classify(
        condition
    )

    classified = result.conditions[0]

    assert (
        classified.sufficiency.sufficient
        is True
    )

    assert (
        classified.level
        == StructuralImportanceLevel.LOW
    )


def test_low_is_not_used_when_evidence_is_insufficient():
    condition = build_condition(
        event_count=1,
        event_share=0.01,
        work_items=1,
        teams=1,
        lifecycles=1,
        active_days=1,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=None,
        scope_breadth=1,
    )

    result = classify(
        condition
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.LIMITED
    )


def test_moderate_with_three_supported_axes():
    condition = build_condition(
        event_count=4,
        event_share=0.20,
        work_items=3,
        teams=1,
        lifecycles=3,
        active_days=3,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=0.60,
        scope_breadth=1,
    )

    result = classify(
        condition
    )

    classified = result.conditions[0]

    assert (
        classified.axes.burden
        is True
    )

    assert (
        classified.axes.process_penetration
        is True
    )

    assert (
        classified.axes.recurrence
        is True
    )

    assert (
        classified.level
        == StructuralImportanceLevel.MODERATE
    )


def test_high_requires_quality_support():
    result = classify(
        build_condition(
            evidence_quality=0.79,
        )
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.MODERATE
    )


def test_high_requires_structural_path_support():
    result = classify(
        build_condition(
            precedence_opportunities=0,
            precedence_count=0,
            precedence_rate=0.0,
            downstream_events=0,
            downstream_constraints=0,
        )
    )

    assert (
        result.conditions[0].level
        == StructuralImportanceLevel.MODERATE
    )


def test_temporal_precedence_requires_multiple_opportunities():
    result = classify(
        build_condition(
            precedence_opportunities=1,
            precedence_count=1,
            precedence_rate=1.0,
        )
    )

    assert (
        result.conditions[
            0
        ].axes.temporal_precedence
        is False
    )


def test_downstream_association_is_independent():
    result = classify(
        build_condition(
            precedence_opportunities=0,
            precedence_count=0,
            precedence_rate=0.0,
            downstream_events=4,
            downstream_constraints=2,
        )
    )

    assert (
        result.conditions[
            0
        ].axes.downstream_association
        is True
    )


def test_context_propagation_can_come_from_team_breadth():
    result = classify(
        build_condition(
            teams=2,
            scope_breadth=1,
        )
    )

    assert (
        result.conditions[
            0
        ].axes.context_propagation
        is True
    )


def test_context_propagation_can_come_from_scope_breadth():
    result = classify(
        build_condition(
            teams=1,
            scope_breadth=2,
        )
    )

    assert (
        result.conditions[
            0
        ].axes.context_propagation
        is True
    )


def test_classification_is_deterministic():
    condition = build_condition()

    service = (
        GovernanceAssessmentStructuralImportanceClassificationService()
    )

    first = service.classify(
        structural_summary=(
            build_summary(
                condition
            )
        )
    )

    second = service.classify(
        structural_summary=(
            build_summary(
                condition
            )
        )
    )

    assert (
        first.summary_hash
        == second.summary_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )


def test_condition_order_is_canonical():
    first_condition = build_condition(
        category=(
            ConstraintCategory.APPROVAL_DELAYED
        )
    )

    second_condition = build_condition(
        category=(
            ConstraintCategory.SECURITY_REVIEW
        )
    )

    service = (
        GovernanceAssessmentStructuralImportanceClassificationService()
    )

    first = service.classify(
        structural_summary=(
            build_summary(
                first_condition,
                second_condition,
            )
        )
    )

    second = service.classify(
        structural_summary=(
            build_summary(
                second_condition,
                first_condition,
            )
        )
    )

    assert (
        first.summary_hash
        == second.summary_hash
    )


def test_high_condition_is_listed():
    condition = build_condition()

    result = classify(
        condition
    )

    assert (
        result.high_importance_conditions
        == (
            condition.category.value,
        )
    )


def test_moderate_condition_is_listed():
    condition = build_condition(
        event_count=4,
        event_share=0.20,
        work_items=3,
        teams=1,
        lifecycles=3,
        active_days=3,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=0.60,
        scope_breadth=1,
    )

    result = classify(
        condition
    )

    assert (
        result.moderate_importance_conditions
        == (
            condition.category.value,
        )
    )


def test_low_condition_is_listed():
    condition = build_condition(
        event_count=3,
        event_share=0.05,
        work_items=2,
        teams=1,
        lifecycles=1,
        active_days=2,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=0.70,
        scope_breadth=1,
    )

    result = classify(
        condition
    )

    assert (
        result.low_importance_conditions
        == (
            condition.category.value,
        )
    )


def test_limited_condition_is_listed_separately_from_low():
    condition = build_condition(
        event_count=1,
        event_share=0.01,
        work_items=1,
        teams=1,
        lifecycles=1,
        active_days=1,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=None,
        scope_breadth=1,
    )

    result = classify(
        condition
    )

    assert (
        result.limited_evidence_conditions
        == (
            condition.category.value,
        )
    )

    assert (
        result.low_importance_conditions
        == ()
    )


def test_low_does_not_mean_root_cause_absence():
    condition = build_condition(
        event_count=3,
        event_share=0.05,
        work_items=2,
        teams=1,
        lifecycles=1,
        active_days=2,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=0.70,
        scope_breadth=1,
    )

    payload = (
        classify(
            condition
        )
        .conditions[
            0
        ]
        .to_dict()
    )

    assert (
        payload[
            "level"
        ]
        == "LOW"
    )

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "primary_condition"
        not in payload
    )


def test_limited_does_not_mean_low():
    condition = build_condition(
        event_count=1,
        event_share=0.01,
        work_items=1,
        teams=1,
        lifecycles=1,
        active_days=1,
        precedence_opportunities=0,
        precedence_count=0,
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
        evidence_quality=None,
        scope_breadth=1,
    )

    classified = (
        classify(
            condition
        )
        .conditions[
            0
        ]
    )

    assert (
        classified.level
        == StructuralImportanceLevel.LIMITED
    )

    assert (
        classified.sufficiency.sufficient
        is False
    )


def test_summary_contains_no_primary_or_root_cause_claim():
    result = classify(
        build_condition()
    )

    payload = result.to_dict()

    assert (
        "primary_condition"
        not in payload
    )

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "intervention"
        not in payload
    )


def test_authority_is_gagf_fip_only():
    result = classify(
        build_condition()
    )

    assert (
        result.authority
        == STRUCTURAL_IMPORTANCE_CLASSIFICATION_AUTHORITY
    )