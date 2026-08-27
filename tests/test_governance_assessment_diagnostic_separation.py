from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_assessment_diagnostic_separation import (
    DIAGNOSTIC_SEPARATION_AUTHORITY,
    GovernanceAssessmentDiagnosticSeparationService,
    DiagnosticSeparationEvidenceError,
)
from backend.app.gagf.governance_assessment_primary_diagnosis_evidence import (
    AssessmentPrimaryDiagnosisEvidenceSummary,
    PrimaryDiagnosisConditionEvidence,
    PrimaryDiagnosisRelativeAxes,
)
from backend.app.gagf.governance_assessment_structural_importance_classification import (
    StructuralImportanceLevel,
)


def build_condition(
    *,
    category,
    rank,
    score,
    relative_to_highest,
    structural_level=(
        StructuralImportanceLevel.HIGH
    ),
    evidence_quality=0.9,
    event_count=10,
    unique_work_item_count=5,
    active_day_count=4,
):
    axes = (
        PrimaryDiagnosisRelativeAxes(
            burden=score,
            process_penetration=score,
            temporal_position=score,
            structural_importance=score,
        )
    )

    return (
        PrimaryDiagnosisConditionEvidence(
            category=category,

            structural_level=(
                structural_level
            ),

            rank=rank,

            axes=axes,

            relative_to_highest=(
                relative_to_highest
            ),

            evidence_quality=(
                evidence_quality
            ),

            event_count=(
                event_count
            ),

            event_share=(
                score
            ),

            friction_score=(
                score
            ),

            unique_work_item_count=(
                unique_work_item_count
            ),

            unique_team_count=3,

            unique_lifecycle_count=4,

            active_day_count=(
                active_day_count
            ),

            precedence_rate=(
                score
            ),

            downstream_event_count=6,

            downstream_constraint_count=3,

            structural_evidence_hash=(
                f"{category}-structural-evidence"
            ),

            structural_classification_hash=(
                f"{category}-classification"
            ),

            evidence_hash=(
                f"{category}-primary-evidence"
            ),
        )
    )


def build_summary(
    *,
    conditions=None,
):
    if conditions is None:
        conditions = (
            build_condition(
                category="APPROVAL_DELAYED",
                rank=1,
                score=0.80,
                relative_to_highest=1.0,
                evidence_quality=0.95,
                event_count=12,
                unique_work_item_count=7,
                active_day_count=6,
            ),
            build_condition(
                category="SECURITY_REVIEW",
                rank=2,
                score=0.60,
                relative_to_highest=0.75,
                structural_level=(
                    StructuralImportanceLevel.MODERATE
                ),
                evidence_quality=0.85,
                event_count=9,
                unique_work_item_count=5,
                active_day_count=4,
            ),
            build_condition(
                category="WORK_BLOCKED",
                rank=3,
                score=0.40,
                relative_to_highest=0.50,
                structural_level=(
                    StructuralImportanceLevel.MODERATE
                ),
                evidence_quality=0.80,
            ),
        )

    return (
        AssessmentPrimaryDiagnosisEvidenceSummary(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
            conditions=tuple(
                conditions
            ),
            summary_hash=(
                "primary-summary-hash"
            ),
        )
    )


def analyze(
    summary=None,
):
    return (
        GovernanceAssessmentDiagnosticSeparationService()
        .analyze(
            primary_diagnosis_summary=(
                summary
                or
                build_summary()
            )
        )
    )


def test_preserves_hierarchy():
    result = analyze()

    assert (
        result.hierarchy_key
        ==
        "tenant-a/client-a/"
        "engagement-a/assessment-a"
    )


def test_binds_primary_diagnosis_summary_hash():
    result = analyze()

    assert (
        result.primary_diagnosis_summary_hash
        == "primary-summary-hash"
    )


def test_identifies_leading_candidate():
    result = analyze()

    assert (
        result.leading_candidate_category
        == "APPROVAL_DELAYED"
    )

    assert (
        result.leading_candidate.rank
        == 1
    )


def test_identifies_runner_up():
    result = analyze()

    assert (
        result.runner_up_candidate.category
        == "SECURITY_REVIEW"
    )

    assert (
        result.runner_up_candidate.rank
        == 2
    )


def test_identifies_third_ranked_candidate():
    result = analyze()

    assert (
        result.third_ranked_candidate.category
        == "WORK_BLOCKED"
    )

    assert (
        result.third_ranked_candidate.rank
        == 3
    )


def test_absolute_rank_1_to_rank_2_separation():
    result = analyze()

    assert (
        result.metrics
        .rank_1_to_rank_2_absolute
        == 0.2
    )


def test_relative_rank_1_to_rank_2_separation():
    result = analyze()

    assert (
        result.metrics
        .rank_1_to_rank_2_relative
        == 0.25
    )


def test_absolute_rank_1_to_rank_3_separation():
    result = analyze()

    assert (
        result.metrics
        .rank_1_to_rank_3_absolute
        == 0.4
    )


def test_relative_rank_1_to_rank_3_separation():
    result = analyze()

    assert (
        result.metrics
        .rank_1_to_rank_3_relative
        == 0.5
    )


def test_top_3_score_spread():
    result = analyze()

    assert (
        result.metrics
        .top_3_score_spread
        == 0.4
    )


def test_preserves_relative_to_highest():
    result = analyze()

    assert (
        result.metrics
        .leading_relative_to_highest
        == 1.0
    )

    assert (
        result.metrics
        .runner_up_relative_to_highest
        == 0.75
    )


def test_preserves_evidence_quality_without_classifying_confidence():
    result = analyze()

    assert (
        result.support
        .leading_evidence_quality
        == 0.95
    )

    assert (
        result.support
        .runner_up_evidence_quality
        == 0.85
    )

    payload = result.to_dict()

    assert "confidence" not in payload
    assert "confidence_level" not in payload


def test_preserves_structural_levels():
    result = analyze()

    assert (
        result.support
        .leading_structural_level
        == "HIGH"
    )

    assert (
        result.support
        .runner_up_structural_level
        == "MODERATE"
    )


def test_preserves_support_counts():
    result = analyze()

    assert (
        result.support
        .candidate_count
        == 3
    )

    assert (
        result.support
        .ranked_candidate_count
        == 3
    )

    assert (
        result.support
        .evidence_quality_observed_count
        == 3
    )


def test_preserves_leading_and_runner_up_observational_support():
    result = analyze()

    assert (
        result.support
        .leading_event_count
        == 12
    )

    assert (
        result.support
        .runner_up_event_count
        == 9
    )

    assert (
        result.support
        .leading_unique_work_item_count
        == 7
    )

    assert (
        result.support
        .runner_up_unique_work_item_count
        == 5
    )

    assert (
        result.support
        .leading_active_day_count
        == 6
    )

    assert (
        result.support
        .runner_up_active_day_count
        == 4
    )


def test_one_candidate_has_no_pairwise_separation():
    summary = build_summary(
        conditions=(
            build_condition(
                category="APPROVAL_DELAYED",
                rank=1,
                score=0.80,
                relative_to_highest=1.0,
            ),
        )
    )

    result = analyze(
        summary
    )

    assert (
        result.metrics
        .rank_1_score
        == 0.8
    )

    assert (
        result.metrics
        .rank_2_score
        is None
    )

    assert (
        result.metrics
        .rank_1_to_rank_2_absolute
        is None
    )

    assert (
        result.metrics
        .rank_1_to_rank_2_relative
        is None
    )

    assert (
        result.metrics
        .top_3_score_spread
        is None
    )


def test_two_candidates_have_pairwise_but_no_rank_3_metrics():
    summary = build_summary(
        conditions=(
            build_condition(
                category="A",
                rank=1,
                score=0.75,
                relative_to_highest=1.0,
            ),
            build_condition(
                category="B",
                rank=2,
                score=0.50,
                relative_to_highest=0.6667,
            ),
        )
    )

    result = analyze(
        summary
    )

    assert (
        result.metrics
        .rank_1_to_rank_2_absolute
        == 0.25
    )

    assert (
        result.metrics
        .rank_3_score
        is None
    )

    assert (
        result.metrics
        .rank_1_to_rank_3_absolute
        is None
    )

    assert (
        result.metrics
        .top_3_score_spread
        == 0.25
    )


def test_empty_summary_supported():
    result = analyze(
        build_summary(
            conditions=()
        )
    )

    assert (
        result.leading_candidate
        is None
    )

    assert (
        result.runner_up_candidate
        is None
    )

    assert (
        result.third_ranked_candidate
        is None
    )

    assert (
        result.metrics.rank_1_score
        is None
    )

    assert (
        result.support.candidate_count
        == 0
    )


def test_equal_scores_have_zero_separation():
    summary = build_summary(
        conditions=(
            build_condition(
                category="A",
                rank=1,
                score=0.60,
                relative_to_highest=1.0,
            ),
            build_condition(
                category="B",
                rank=2,
                score=0.60,
                relative_to_highest=1.0,
            ),
        )
    )

    result = analyze(
        summary
    )

    assert (
        result.metrics
        .rank_1_to_rank_2_absolute
        == 0.0
    )

    assert (
        result.metrics
        .rank_1_to_rank_2_relative
        == 0.0
    )


def test_zero_highest_score_relative_separation_is_zero():
    summary = build_summary(
        conditions=(
            build_condition(
                category="A",
                rank=1,
                score=0.0,
                relative_to_highest=0.0,
            ),
            build_condition(
                category="B",
                rank=2,
                score=0.0,
                relative_to_highest=0.0,
            ),
        )
    )

    result = analyze(
        summary
    )

    assert (
        result.metrics
        .rank_1_to_rank_2_relative
        == 0.0
    )


def test_rejects_non_contiguous_ranking():
    conditions = list(
        build_summary()
        .conditions
    )

    conditions[1] = replace(
        conditions[1],
        rank=3,
    )

    with pytest.raises(
        DiagnosticSeparationEvidenceError,
        match="contiguous and ordered",
    ):
        analyze(
            build_summary(
                conditions=conditions
            )
        )


def test_rejects_duplicate_categories():
    conditions = (
        build_condition(
            category="A",
            rank=1,
            score=0.8,
            relative_to_highest=1.0,
        ),
        build_condition(
            category="A",
            rank=2,
            score=0.6,
            relative_to_highest=0.75,
        ),
    )

    with pytest.raises(
        DiagnosticSeparationEvidenceError,
        match="duplicate category",
    ):
        analyze(
            build_summary(
                conditions=conditions
            )
        )


def test_rejects_increasing_scores():
    conditions = (
        build_condition(
            category="A",
            rank=1,
            score=0.4,
            relative_to_highest=1.0,
        ),
        build_condition(
            category="B",
            rank=2,
            score=0.8,
            relative_to_highest=1.0,
        ),
    )

    with pytest.raises(
        DiagnosticSeparationEvidenceError,
        match="non-increasing",
    ):
        analyze(
            build_summary(
                conditions=conditions
            )
        )


def test_summary_hash_is_deterministic():
    first = analyze()
    second = analyze()

    assert (
        first.summary_hash
        == second.summary_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )


def test_authority_is_gagf_fip_only():
    result = analyze()

    assert (
        result.authority
        == DIAGNOSTIC_SEPARATION_AUTHORITY
    )

    assert (
        result.authority
        == "GAGF_FIP_ONLY"
    )


def test_output_does_not_claim_confidence_or_causation():
    result = analyze()

    payload = result.to_dict()

    forbidden = (
        "confidence",
        "confidence_level",
        "correctness",
        "root_cause",
        "causal_condition",
        "primary_diagnosis",
        "authorized_action",
        "intervention",
    )

    for field in forbidden:
        assert field not in payload