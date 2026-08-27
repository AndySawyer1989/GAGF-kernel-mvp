from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.diagnostic_calibration_corpus_analysis import (
    CALIBRATION_CORPUS_ANALYSIS_AUTHORITY,
    CalibrationAnalysisObservation,
    CalibrationCorpusAnalysisError,
    DiagnosticCalibrationCorpusAnalysisService,
)
from backend.app.gagf.diagnostic_calibration_oracle_evaluation import (
    CALIBRATION_ORACLE_EVALUATION_AUTHORITY,
    CalibrationOracleEvaluationResult,
)


SERVICE = (
    DiagnosticCalibrationCorpusAnalysisService()
)


def build_evaluation(
    *,
    scenario_id: str,
    rank_1_hit: bool,
    top_2_hit: bool = True,
    top_3_hit: bool = True,
    reciprocal_rank: float = 1.0,
    candidate_count: int = 3,
    structural_level: str = "HIGH",
    evidence_quality: float = 0.90,
    absolute_separation: float = 0.20,
    relative_separation: float = 0.25,
) -> CalibrationOracleEvaluationResult:
    public_hash = (
        scenario_id
        .encode(
            "utf-8"
        )
        .hex()
        .ljust(
            64,
            "0",
        )[
            :64
        ]
    )

    oracle_hash = (
        (
            scenario_id
            + "-oracle"
        )
        .encode(
            "utf-8"
        )
        .hex()
        .ljust(
            64,
            "1",
        )[
            :64
        ]
    )

    evaluation_hash = (
        (
            scenario_id
            + "-evaluation"
        )
        .encode(
            "utf-8"
        )
        .hex()
        .ljust(
            64,
            "2",
        )[
            :64
        ]
    )

    ranked = (
        "APPROVAL_DELAYED",
        "DEPENDENCY_WAIT",
        "WORK_BLOCKED",
    )

    first_primary_rank = (
        1
        if rank_1_hit
        else (
            2
            if reciprocal_rank == 0.5
            else (
                3
                if reciprocal_rank
                == round(
                    1 / 3,
                    6,
                )
                else None
            )
        )
    )

    return (
        CalibrationOracleEvaluationResult(
            scenario_id=(
                scenario_id
            ),

            public_hash=(
                public_hash
            ),

            oracle_hash=(
                oracle_hash
            ),

            hierarchy_key=(
                "tenant/client/"
                "engagement/"
                f"{scenario_id}"
            ),

            ranked_conditions=(
                ranked
            ),

            planted_primary_conditions=(
                "APPROVAL_DELAYED",
            ),

            planted_secondary_conditions=(
                "DEPENDENCY_WAIT",
            ),

            first_primary_rank=(
                first_primary_rank
            ),

            reciprocal_rank=(
                reciprocal_rank
            ),

            rank_1_hit=(
                rank_1_hit
            ),

            top_2_hit=(
                top_2_hit
            ),

            top_3_hit=(
                top_3_hit
            ),

            primary_hit_count=1,

            all_primary_conditions_ranked=True,

            expected_top_k=3,

            expected_top_k_hit=(
                top_3_hit
            ),

            secondary_hit_count=1,

            candidate_count=(
                candidate_count
            ),

            leading_candidate_category=(
                ranked[0]
            ),

            leading_structural_level=(
                structural_level
            ),

            leading_evidence_quality=(
                evidence_quality
            ),

            leading_explanatory_score=0.8,

            runner_up_explanatory_score=0.6,

            absolute_separation=(
                absolute_separation
            ),

            relative_separation=(
                relative_separation
            ),

            primary_diagnosis_summary_hash=(
                "3" * 64
            ),

            diagnostic_separation_summary_hash=(
                "4" * 64
            ),

            execution_evidence_hash=(
                "5" * 64
            ),

            evaluation_hash=(
                evaluation_hash
            ),

            authority=(
                CALIBRATION_ORACLE_EVALUATION_AUTHORITY
            ),
        )
    )


def build_oracle(
    evaluation: CalibrationOracleEvaluationResult,
    *,
    difficulty: str = "moderate",
    ambiguity: str = "moderate-overlap",
):
    return {
        "scenario_id":
            evaluation.scenario_id,

        "public_hash":
            evaluation.public_hash,

        "oracle_hash":
            evaluation.oracle_hash,

        "intended_difficulty":
            difficulty,

        "intended_ambiguity":
            ambiguity,
    }


def build_observation(
    *,
    scenario_id: str,
    rank_1_hit: bool,
    top_2_hit: bool = True,
    top_3_hit: bool = True,
    reciprocal_rank: float = 1.0,
    candidate_count: int = 3,
    structural_level: str = "HIGH",
    evidence_quality: float = 0.90,
    absolute_separation: float = 0.20,
    relative_separation: float = 0.25,
    difficulty: str = "moderate",
    ambiguity: str = "moderate-overlap",
) -> CalibrationAnalysisObservation:
    evaluation = build_evaluation(
        scenario_id=(
            scenario_id
        ),

        rank_1_hit=(
            rank_1_hit
        ),

        top_2_hit=(
            top_2_hit
        ),

        top_3_hit=(
            top_3_hit
        ),

        reciprocal_rank=(
            reciprocal_rank
        ),

        candidate_count=(
            candidate_count
        ),

        structural_level=(
            structural_level
        ),

        evidence_quality=(
            evidence_quality
        ),

        absolute_separation=(
            absolute_separation
        ),

        relative_separation=(
            relative_separation
        ),
    )

    return SERVICE.observe(
        evaluation=(
            evaluation
        ),
        oracle=(
            build_oracle(
                evaluation,
                difficulty=(
                    difficulty
                ),
                ambiguity=(
                    ambiguity
                ),
            )
        ),
    )


def build_three_observations():
    first = build_observation(
        scenario_id="scenario-001",
        rank_1_hit=True,
        reciprocal_rank=1.0,
        candidate_count=3,
        structural_level="HIGH",
        evidence_quality=0.95,
        absolute_separation=0.30,
        relative_separation=0.40,
        difficulty="low",
        ambiguity="low-overlap",
    )

    second = build_observation(
        scenario_id="scenario-002",
        rank_1_hit=False,
        reciprocal_rank=0.5,
        candidate_count=4,
        structural_level="MODERATE",
        evidence_quality=0.90,
        absolute_separation=0.15,
        relative_separation=0.20,
        difficulty="moderate",
        ambiguity="moderate-overlap",
    )

    third = build_observation(
        scenario_id="scenario-003",
        rank_1_hit=False,
        top_2_hit=False,
        reciprocal_rank=round(
            1 / 3,
            6,
        ),
        candidate_count=5,
        structural_level="LOW",
        evidence_quality=0.85,
        absolute_separation=0.05,
        relative_separation=0.07,
        difficulty="high",
        ambiguity="high-overlap",
    )

    return (
        first,
        second,
        third,
    )


def test_observe_binds_evaluation_identity():
    evaluation = build_evaluation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    observation = SERVICE.observe(
        evaluation=(
            evaluation
        ),
        oracle=(
            build_oracle(
                evaluation
            )
        ),
    )

    assert (
        observation.scenario_id
        == evaluation.scenario_id
    )

    assert (
        observation.evaluation_hash
        == evaluation.evaluation_hash
    )


def test_observe_preserves_difficulty():
    evaluation = build_evaluation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    observation = SERVICE.observe(
        evaluation=(
            evaluation
        ),
        oracle=(
            build_oracle(
                evaluation,
                difficulty="adversarial",
            )
        ),
    )

    assert (
        observation.difficulty
        == "adversarial"
    )


def test_observe_preserves_ambiguity():
    evaluation = build_evaluation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    observation = SERVICE.observe(
        evaluation=(
            evaluation
        ),
        oracle=(
            build_oracle(
                evaluation,
                ambiguity="dual-primary",
            )
        ),
    )

    assert (
        observation.ambiguity
        == "dual-primary"
    )


def test_observe_rejects_wrong_scenario():
    evaluation = build_evaluation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    oracle = build_oracle(
        evaluation
    )

    oracle[
        "scenario_id"
    ] = "wrong"

    with pytest.raises(
        CalibrationCorpusAnalysisError,
        match="scenario_id",
    ):
        SERVICE.observe(
            evaluation=evaluation,
            oracle=oracle,
        )


def test_observe_rejects_wrong_public_hash():
    evaluation = build_evaluation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    oracle = build_oracle(
        evaluation
    )

    oracle[
        "public_hash"
    ] = "x" * 64

    with pytest.raises(
        CalibrationCorpusAnalysisError,
        match="public_hash",
    ):
        SERVICE.observe(
            evaluation=evaluation,
            oracle=oracle,
        )


def test_observe_rejects_wrong_oracle_hash():
    evaluation = build_evaluation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    oracle = build_oracle(
        evaluation
    )

    oracle[
        "oracle_hash"
    ] = "x" * 64

    with pytest.raises(
        CalibrationCorpusAnalysisError,
        match="oracle_hash",
    ):
        SERVICE.observe(
            evaluation=evaluation,
            oracle=oracle,
        )


def test_analysis_requires_observations():
    with pytest.raises(
        CalibrationCorpusAnalysisError,
        match="at least one",
    ):
        SERVICE.analyze(
            observations=()
        )


def test_analysis_counts_scenarios():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.scenario_count
        == 3
    )


def test_analysis_orders_scenario_ids():
    observations = (
        build_three_observations()
    )

    result = SERVICE.analyze(
        observations=(
            tuple(
                reversed(
                    observations
                )
            )
        )
    )

    assert (
        result.scenario_ids
        ==
        (
            "scenario-001",
            "scenario-002",
            "scenario-003",
        )
    )


def test_overall_rank_1_rate():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.overall.rank_1_rate
        == round(
            1 / 3,
            6,
        )
    )


def test_overall_top_2_rate():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.overall.top_2_rate
        == round(
            2 / 3,
            6,
        )
    )


def test_overall_top_3_rate():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.overall.top_3_rate
        == 1.0
    )


def test_overall_mrr():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    expected = round(
        (
            1.0
            + 0.5
            + round(
                1 / 3,
                6,
            )
        )
        / 3,
        6,
    )

    assert (
        result.overall
        .mean_reciprocal_rank
        == expected
    )


def test_overall_mean_candidate_count():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.overall
        .mean_candidate_count
        == 4.0
    )


def test_overall_mean_evidence_quality():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.overall
        .mean_evidence_quality
        == 0.9
    )


def test_overall_mean_relative_separation():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.overall
        .mean_relative_separation
        ==
        round(
            (
                0.40
                + 0.20
                + 0.07
            )
            / 3,
            6,
        )
    )


def test_groups_by_structural_level():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    keys = tuple(
        item.cohort_key
        for item
        in result.by_structural_level
    )

    assert keys == (
        "HIGH",
        "LOW",
        "MODERATE",
    )


def test_groups_by_candidate_count():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    keys = tuple(
        item.cohort_key
        for item
        in result.by_candidate_count
    )

    assert keys == (
        "3",
        "4",
        "5",
    )


def test_groups_by_difficulty():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    keys = tuple(
        item.cohort_key
        for item
        in result.by_difficulty
    )

    assert keys == (
        "high",
        "low",
        "moderate",
    )


def test_groups_by_ambiguity():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    keys = tuple(
        item.cohort_key
        for item
        in result.by_ambiguity
    )

    assert keys == (
        "high-overlap",
        "low-overlap",
        "moderate-overlap",
    )


def test_relative_separation_correlation_is_observational():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.correlations
        .relative_separation_vs_rank_1
        is not None
    )


def test_evidence_quality_correlation_is_observational():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.correlations
        .evidence_quality_vs_reciprocal_rank
        is not None
    )


def test_candidate_count_correlation_is_observational():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.correlations
        .candidate_count_vs_reciprocal_rank
        is not None
    )


def test_constant_outcome_correlation_is_none():
    observations = (
        build_observation(
            scenario_id="scenario-a",
            rank_1_hit=True,
        ),
        build_observation(
            scenario_id="scenario-b",
            rank_1_hit=True,
            relative_separation=0.5,
        ),
    )

    result = SERVICE.analyze(
        observations=observations
    )

    assert (
        result.correlations
        .relative_separation_vs_rank_1
        is None
    )


def test_duplicate_scenario_is_rejected():
    observation = build_observation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    with pytest.raises(
        CalibrationCorpusAnalysisError,
        match="duplicate scenario_id",
    ):
        SERVICE.analyze(
            observations=(
                observation,
                replace(
                    observation,
                    evaluation_hash=(
                        "z" * 64
                    ),
                ),
            )
        )


def test_duplicate_evaluation_hash_is_rejected():
    first = build_observation(
        scenario_id="scenario-001",
        rank_1_hit=True,
    )

    second = replace(
        first,
        scenario_id="scenario-002",
    )

    with pytest.raises(
        CalibrationCorpusAnalysisError,
        match="duplicate evaluation hashes",
    ):
        SERVICE.analyze(
            observations=(
                first,
                second,
            )
        )


def test_analysis_hash_is_deterministic():
    observations = (
        build_three_observations()
    )

    first = SERVICE.analyze(
        observations=(
            observations
        )
    )

    second = SERVICE.analyze(
        observations=(
            tuple(
                reversed(
                    observations
                )
            )
        )
    )

    assert (
        first.analysis_hash
        == second.analysis_hash
    )


def test_analysis_binds_source_evaluation_hashes():
    observations = (
        build_three_observations()
    )

    result = SERVICE.analyze(
        observations=(
            observations
        )
    )

    assert (
        set(
            result.source_evaluation_hashes
        )
        ==
        {
            item.evaluation_hash
            for item
            in observations
        }
    )


def test_analysis_uses_calibration_only_authority():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    assert (
        result.authority
        ==
        CALIBRATION_CORPUS_ANALYSIS_AUTHORITY
    )


def test_result_creates_no_confidence_threshold():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    payload = result.to_dict()

    assert (
        "confidence"
        not in payload
    )

    assert (
        "confidence_band"
        not in payload
    )

    assert (
        "confidence_threshold"
        not in payload
    )


def test_result_creates_no_root_cause_or_authorization():
    result = SERVICE.analyze(
        observations=(
            build_three_observations()
        )
    )

    payload = result.to_dict()

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "intervention_authority"
        not in payload
    )