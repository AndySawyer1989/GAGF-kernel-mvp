from __future__ import annotations

from dataclasses import replace

from backend.app.gagf.governance_assessment_primary_diagnosis_evidence import (
    PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY,
    GovernanceAssessmentPrimaryDiagnosisEvidenceService,
)
from backend.app.gagf.governance_assessment_structural_importance_classification import (
    AssessmentStructuralImportanceClassificationSummary,
    StructuralEvidenceSufficiency,
    StructuralImportanceAxes,
    StructuralImportanceClassification,
    StructuralImportanceLevel,
)


def build_condition(
    *,
    category: str,
    level: StructuralImportanceLevel,
    event_count: int = 10,
    event_share: float = 0.1,
    friction_score: float = 20.0,
    work_items: int = 5,
    teams: int = 2,
    lifecycles: int = 5,
    active_days: int = 5,
    precedence_rate: float = 0.5,
    downstream_events: int = 5,
    downstream_constraints: int = 2,
    evidence_quality: float = 0.9,
) -> StructuralImportanceClassification:
    sufficiency = (
        StructuralEvidenceSufficiency(
            event_support=True,
            process_support=True,
            temporal_support=True,
            quality_observed=True,
        )
    )

    axes = (
        StructuralImportanceAxes(
            burden=True,
            process_penetration=True,
            temporal_precedence=(
                precedence_rate > 0
            ),
            downstream_association=(
                downstream_events > 0
            ),
            recurrence=True,
            context_propagation=True,
            evidence_quality=True,
        )
    )

    return (
        StructuralImportanceClassification(
            category=category,
            level=level,
            sufficiency=sufficiency,
            axes=axes,
            event_count=event_count,
            event_share=event_share,
            friction_score=friction_score,
            unique_work_item_count=work_items,
            unique_team_count=teams,
            unique_lifecycle_count=lifecycles,
            active_day_count=active_days,
            precedence_rate=precedence_rate,
            downstream_event_count=(
                downstream_events
            ),
            downstream_constraint_count=(
                downstream_constraints
            ),
            mean_evidence_quality=(
                evidence_quality
            ),
            evidence_hash=(
                f"{category}-evidence"
            ),
            classification_hash=(
                f"{category}-classification"
            ),
        )
    )


def build_summary(
    *conditions: StructuralImportanceClassification,
) -> AssessmentStructuralImportanceClassificationSummary:
    ordered_conditions = tuple(
        conditions
    )

    high = tuple(
        sorted(
            condition.category
            for condition
            in ordered_conditions
            if (
                condition.level
                == StructuralImportanceLevel.HIGH
            )
        )
    )

    moderate = tuple(
        sorted(
            condition.category
            for condition
            in ordered_conditions
            if (
                condition.level
                == StructuralImportanceLevel.MODERATE
            )
        )
    )

    low = tuple(
        sorted(
            condition.category
            for condition
            in ordered_conditions
            if (
                condition.level
                == StructuralImportanceLevel.LOW
            )
        )
    )

    limited = tuple(
        sorted(
            condition.category
            for condition
            in ordered_conditions
            if (
                condition.level
                == StructuralImportanceLevel.LIMITED
            )
        )
    )

    return (
        AssessmentStructuralImportanceClassificationSummary(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
            conditions=ordered_conditions,
            high_importance_conditions=high,
            moderate_importance_conditions=moderate,
            low_importance_conditions=low,
            limited_evidence_conditions=limited,
            summary_hash=(
                "structural-classification-summary"
            ),
        )
    )


def test_analyze_preserves_hierarchy():
    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    build_condition(
                        category="A",
                        level=(
                            StructuralImportanceLevel.HIGH
                        ),
                    )
                )
            )
        )
    )

    assert (
        result.hierarchy_key
        == (
            "tenant-a/client-a/"
            "engagement-a/assessment-a"
        )
    )


def test_analyze_ranks_stronger_condition_first():
    stronger = build_condition(
        category="STRONGER",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        event_share=0.6,
        friction_score=100.0,
        work_items=20,
        teams=5,
        lifecycles=20,
        active_days=20,
        precedence_rate=0.9,
        downstream_events=30,
        downstream_constraints=8,
    )

    weaker = build_condition(
        category="WEAKER",
        level=(
            StructuralImportanceLevel.MODERATE
        ),
        event_share=0.1,
        friction_score=10.0,
        work_items=2,
        teams=1,
        lifecycles=2,
        active_days=2,
        precedence_rate=0.1,
        downstream_events=1,
        downstream_constraints=1,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    weaker,
                    stronger,
                )
            )
        )
    )

    assert (
        result.ranked_conditions
        == (
            "STRONGER",
            "WEAKER",
        )
    )

    assert (
        result.conditions[0].rank
        == 1
    )

    assert (
        result.conditions[1].rank
        == 2
    )


def test_highest_condition_has_relative_score_one():
    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    build_condition(
                        category="A",
                        level=(
                            StructuralImportanceLevel.HIGH
                        ),
                    ),
                    build_condition(
                        category="B",
                        level=(
                            StructuralImportanceLevel.MODERATE
                        ),
                        friction_score=5.0,
                    ),
                )
            )
        )
    )

    assert (
        result.conditions[0]
        .relative_to_highest
        == 1.0
    )


def test_structural_high_receives_more_weight_than_moderate():
    service = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
    )

    assert (
        service._structural_level_weight(
            StructuralImportanceLevel.HIGH
        )
        >
        service._structural_level_weight(
            StructuralImportanceLevel.MODERATE
        )
    )


def test_moderate_is_not_excluded_from_ranking():
    condition = build_condition(
        category="WORK_BLOCKED",
        level=(
            StructuralImportanceLevel.MODERATE
        ),
        event_share=0.5,
        friction_score=80.0,
        work_items=20,
        teams=4,
        lifecycles=20,
        active_days=20,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    condition
                )
            )
        )
    )

    assert (
        result.highest_ranked_condition
        == "WORK_BLOCKED"
    )


def test_limited_is_preserved_but_not_structurally_promoted():
    condition = build_condition(
        category="OVERRIDE",
        level=(
            StructuralImportanceLevel.LIMITED
        ),
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    condition
                )
            )
        )
    )

    assert (
        result.condition_count
        == 1
    )

    assert (
        result.conditions[0]
        .structural_level
        == StructuralImportanceLevel.LIMITED
    )

    assert (
        result.conditions[0]
        .axes
        .structural_importance
        == 0.0
    )


def test_evidence_quality_is_preserved():
    condition = build_condition(
        category="A",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        evidence_quality=0.73,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    condition
                )
            )
        )
    )

    assert (
        result.conditions[0]
        .evidence_quality
        == 0.73
    )


def test_evidence_quality_does_not_directly_change_score():
    first = build_condition(
        category="A",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        evidence_quality=0.99,
    )

    second = build_condition(
        category="B",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        evidence_quality=0.51,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    first,
                    second,
                )
            )
        )
    )

    by_category = {
        condition.category:
            condition
        for condition
        in result.conditions
    }

    assert (
        by_category[
            "A"
        ].explanatory_score
        ==
        by_category[
            "B"
        ].explanatory_score
    )


def test_temporal_position_uses_precedence_and_downstream():
    temporal = build_condition(
        category="TEMPORAL",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        precedence_rate=1.0,
        downstream_events=20,
        downstream_constraints=10,
    )

    non_temporal = build_condition(
        category="NON_TEMPORAL",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        precedence_rate=0.0,
        downstream_events=0,
        downstream_constraints=0,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    temporal,
                    non_temporal,
                )
            )
        )
    )

    by_category = {
        condition.category:
            condition
        for condition
        in result.conditions
    }

    assert (
        by_category[
            "TEMPORAL"
        ].axes.temporal_position
        >
        by_category[
            "NON_TEMPORAL"
        ].axes.temporal_position
    )


def test_burden_is_relative_to_assessment():
    high_burden = build_condition(
        category="HIGH_BURDEN",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        event_share=0.6,
        friction_score=100.0,
    )

    low_burden = build_condition(
        category="LOW_BURDEN",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        event_share=0.1,
        friction_score=10.0,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    high_burden,
                    low_burden,
                )
            )
        )
    )

    by_category = {
        condition.category:
            condition
        for condition
        in result.conditions
    }

    assert (
        by_category[
            "HIGH_BURDEN"
        ].axes.burden
        >
        by_category[
            "LOW_BURDEN"
        ].axes.burden
    )


def test_process_penetration_is_relative():
    broad = build_condition(
        category="BROAD",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        work_items=20,
        teams=6,
        lifecycles=20,
        active_days=20,
    )

    narrow = build_condition(
        category="NARROW",
        level=(
            StructuralImportanceLevel.HIGH
        ),
        work_items=2,
        teams=1,
        lifecycles=2,
        active_days=2,
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    broad,
                    narrow,
                )
            )
        )
    )

    by_category = {
        condition.category:
            condition
        for condition
        in result.conditions
    }

    assert (
        by_category[
            "BROAD"
        ].axes.process_penetration
        >
        by_category[
            "NARROW"
        ].axes.process_penetration
    )


def test_ties_are_broken_by_category():
    a = build_condition(
        category="A",
        level=(
            StructuralImportanceLevel.HIGH
        ),
    )

    b = replace(
        a,
        category="B",
        evidence_hash="B-evidence",
        classification_hash="B-classification",
    )

    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    b,
                    a,
                )
            )
        )
    )

    assert (
        result.ranked_conditions
        == (
            "A",
            "B",
        )
    )


def test_summary_hash_is_deterministic_across_input_order():
    a = build_condition(
        category="A",
        level=(
            StructuralImportanceLevel.HIGH
        ),
    )

    b = build_condition(
        category="B",
        level=(
            StructuralImportanceLevel.MODERATE
        ),
        friction_score=10.0,
    )

    service = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
    )

    first = service.analyze(
        structural_classification_summary=(
            build_summary(
                a,
                b,
            )
        )
    )

    second = service.analyze(
        structural_classification_summary=(
            build_summary(
                b,
                a,
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


def test_condition_hash_is_deterministic():
    condition = build_condition(
        category="A",
        level=(
            StructuralImportanceLevel.HIGH
        ),
    )

    service = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
    )

    first = service.analyze(
        structural_classification_summary=(
            build_summary(
                condition
            )
        )
    )

    second = service.analyze(
        structural_classification_summary=(
            build_summary(
                condition
            )
        )
    )

    assert (
        first.conditions[0]
        .evidence_hash
        ==
        second.conditions[0]
        .evidence_hash
    )


def test_empty_summary_is_supported():
    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary()
            )
        )
    )

    assert (
        result.conditions
        == ()
    )

    assert (
        result.highest_ranked_condition
        is None
    )


def test_output_does_not_claim_root_cause():
    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    build_condition(
                        category="A",
                        level=(
                            StructuralImportanceLevel.HIGH
                        ),
                    )
                )
            )
        )
    )

    payload = (
        result.to_dict()
    )

    assert (
        payload[
            "authority"
        ]
        == PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY
    )

    assert "root_cause" not in payload
    assert "causal" not in payload
    assert "intervention" not in payload
    assert "authorized_action" not in payload


def test_highest_ranked_condition_is_not_named_primary():
    result = (
        GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        .analyze(
            structural_classification_summary=(
                build_summary(
                    build_condition(
                        category="A",
                        level=(
                            StructuralImportanceLevel.HIGH
                        ),
                    )
                )
            )
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "highest_ranked_condition"
        ]
        == "A"
    )

    assert (
        "primary_condition"
        not in payload
    )

    assert (
        "primary_diagnosis"
        not in payload
    )