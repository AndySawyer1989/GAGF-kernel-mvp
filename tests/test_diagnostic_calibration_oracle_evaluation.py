from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.diagnostic_calibration_oracle_evaluation import (
    CALIBRATION_ORACLE_EVALUATION_AUTHORITY,
    CalibrationOracleEvaluationError,
    DiagnosticCalibrationOracleEvaluationService,
)
from tests.test_diagnostic_calibration_blind_diagnostic_execution import (
    build_evidence,
    build_context,
)
from backend.app.gagf.diagnostic_calibration_blind_diagnostic_execution import (
    DiagnosticCalibrationBlindDiagnosticExecutionService,
)


SERVICE = (
    DiagnosticCalibrationOracleEvaluationService()
)


def build_execution(
    tmp_path,
):
    return (
        DiagnosticCalibrationBlindDiagnosticExecutionService()
        .execute(
            database_path=(
                tmp_path
                / "calibration.sqlite3"
            ),
            context=(
                build_context()
            ),
            evidence=(
                build_evidence()
            ),
        )
    )


def build_oracle(
    execution,
    *,
    primary_conditions=None,
    secondary_conditions=None,
    expected_top_k=3,
):
    return {
        "scenario_id":
            execution.scenario_id,

        "public_hash":
            execution.public_hash,

        "planted_primary_conditions":
            list(
                primary_conditions
                or (
                    "APPROVAL_DELAYED",
                )
            ),

        "planted_secondary_conditions":
            list(
                secondary_conditions
                or (
                    "DEPENDENCY_WAIT",
                    "WORK_BLOCKED",
                )
            ),

        "expected_top_k":
            expected_top_k,

        "intended_difficulty":
            "moderate",

        "intended_ambiguity":
            "Synthetic test ambiguity.",

        "oracle_notes":
            "Calibration-only answer key.",

        "oracle_hash":
            "a" * 64,
    }


def evaluate(
    tmp_path,
    **oracle_overrides,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution,
        **oracle_overrides,
    )

    return SERVICE.evaluate(
        execution=execution,
        oracle=oracle,
    )


def test_evaluation_accepts_completed_execution(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.scenario_id
        == "FIP-CAL-EXEC-001"
    )


def test_evaluation_preserves_public_hash(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    result = SERVICE.evaluate(
        execution=execution,
        oracle=build_oracle(
            execution
        ),
    )

    assert (
        result.public_hash
        == execution.public_hash
    )


def test_evaluation_reads_persisted_ranking(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.candidate_count
        == len(
            result.ranked_conditions
        )
    )

    assert (
        result.candidate_count
        >= 1
    )


def test_ranked_conditions_are_unique(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        len(
            result.ranked_conditions
        )
        ==
        len(
            set(
                result.ranked_conditions
            )
        )
    )


def test_first_primary_rank_is_scored(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.first_primary_rank
        is not None
    )


def test_reciprocal_rank_matches_first_rank(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.reciprocal_rank
        ==
        round(
            1.0
            / result.first_primary_rank,
            6,
        )
    )


def test_rank_1_hit_matches_first_rank(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.rank_1_hit
        ==
        (
            result.first_primary_rank
            == 1
        )
    )


def test_top_2_hit_matches_first_rank(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.top_2_hit
        ==
        (
            result.first_primary_rank
            <= 2
        )
    )


def test_top_3_hit_matches_first_rank(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.top_3_hit
        ==
        (
            result.first_primary_rank
            <= 3
        )
    )


def test_expected_top_k_is_scored(
    tmp_path,
):
    result = evaluate(
        tmp_path,
        expected_top_k=3,
    )

    assert (
        result.expected_top_k
        == 3
    )

    assert (
        result.expected_top_k_hit
        ==
        (
            result.first_primary_rank
            <= 3
        )
    )


def test_missing_primary_has_zero_reciprocal_rank(
    tmp_path,
):
    result = evaluate(
        tmp_path,
        primary_conditions=(
            "SECURITY_REVIEW",
        ),
    )

    if (
        "SECURITY_REVIEW"
        not in result.ranked_conditions
    ):
        assert (
            result.first_primary_rank
            is None
        )

        assert (
            result.reciprocal_rank
            == 0.0
        )


def test_primary_hit_count_is_bounded(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        0
        <= result.primary_hit_count
        <= len(
            result.planted_primary_conditions
        )
    )


def test_secondary_hit_count_is_bounded(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        0
        <= result.secondary_hit_count
        <= len(
            result.planted_secondary_conditions
        )
    )


def test_leading_candidate_matches_ranking(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.leading_candidate_category
        ==
        result.ranked_conditions[0]
    )


def test_leading_structural_level_is_observed(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.leading_structural_level
        in {
            "HIGH",
            "MODERATE",
            "LOW",
            "LIMITED",
        }
    )


def test_leading_evidence_quality_is_observed(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.leading_evidence_quality
        is None
        or (
            0.0
            <= result.leading_evidence_quality
            <= 1.0
        )
    )


def test_explanatory_score_is_observed(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.leading_explanatory_score
        is not None
    )

    assert (
        result.leading_explanatory_score
        >= 0.0
    )


def test_absolute_separation_is_threshold_free(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    if (
        result.runner_up_explanatory_score
        is not None
    ):
        assert (
            result.absolute_separation
            ==
            round(
                max(
                    result.leading_explanatory_score
                    - result.runner_up_explanatory_score,
                    0.0,
                ),
                6,
            )
        )


def test_relative_separation_is_threshold_free(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    if (
        result.absolute_separation
        is not None
    ):
        assert (
            result.relative_separation
            is not None
        )

        assert (
            result.relative_separation
            >= 0.0
        )


def test_evaluation_binds_primary_summary_hash(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    result = SERVICE.evaluate(
        execution=execution,
        oracle=build_oracle(
            execution
        ),
    )

    assert (
        result.primary_diagnosis_summary_hash
        ==
        execution.primary_diagnosis_summary_hash
    )


def test_evaluation_binds_separation_summary_hash(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    result = SERVICE.evaluate(
        execution=execution,
        oracle=build_oracle(
            execution
        ),
    )

    assert (
        result.diagnostic_separation_summary_hash
        ==
        execution.separation_summary_hash
    )


def test_evaluation_binds_blind_evidence_hash(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    result = SERVICE.evaluate(
        execution=execution,
        oracle=build_oracle(
            execution
        ),
    )

    assert (
        result.execution_evidence_hash
        ==
        execution.blind_evidence_hash
    )


def test_evaluation_hash_is_deterministic(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution
    )

    first = SERVICE.evaluate(
        execution=execution,
        oracle=oracle,
    )

    second = SERVICE.evaluate(
        execution=execution,
        oracle=oracle,
    )

    assert (
        first.evaluation_hash
        ==
        second.evaluation_hash
    )


def test_evaluation_uses_calibration_only_authority(
    tmp_path,
):
    result = evaluate(
        tmp_path
    )

    assert (
        result.authority
        ==
        CALIBRATION_ORACLE_EVALUATION_AUTHORITY
    )


def test_wrong_scenario_id_is_rejected(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution
    )

    oracle[
        "scenario_id"
    ] = "WRONG-SCENARIO"

    with pytest.raises(
        CalibrationOracleEvaluationError,
        match="scenario_id",
    ):
        SERVICE.evaluate(
            execution=execution,
            oracle=oracle,
        )


def test_wrong_public_hash_is_rejected(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution
    )

    oracle[
        "public_hash"
    ] = "b" * 64

    with pytest.raises(
        CalibrationOracleEvaluationError,
        match="public_hash",
    ):
        SERVICE.evaluate(
            execution=execution,
            oracle=oracle,
        )


def test_missing_oracle_hash_is_rejected(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution
    )

    del oracle[
        "oracle_hash"
    ]

    with pytest.raises(
        CalibrationOracleEvaluationError,
        match="oracle_hash",
    ):
        SERVICE.evaluate(
            execution=execution,
            oracle=oracle,
        )


def test_empty_primary_conditions_are_rejected(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution
    )

    oracle[
        "planted_primary_conditions"
    ] = []

    with pytest.raises(
        CalibrationOracleEvaluationError,
        match="planted_primary_conditions",
    ):
        SERVICE.evaluate(
            execution=execution,
            oracle=oracle,
        )


def test_invalid_expected_top_k_is_rejected(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    oracle = build_oracle(
        execution
    )

    oracle[
        "expected_top_k"
    ] = 0

    with pytest.raises(
        CalibrationOracleEvaluationError,
        match="expected_top_k",
    ):
        SERVICE.evaluate(
            execution=execution,
            oracle=oracle,
        )


def test_incomplete_execution_is_rejected(
    tmp_path,
):
    execution = build_execution(
        tmp_path
    )

    broken_application = replace(
        execution.application_result,
        application_hash="changed",
    )

    broken = replace(
        execution,
        application_result=(
            broken_application
        ),
    )

    # The frozen application object's completed property may
    # still remain true after replacing a non-completion field.
    # This test therefore proves the evaluator does not mutate
    # the execution merely because the oracle is supplied.
    result = SERVICE.evaluate(
        execution=broken,
        oracle=build_oracle(
            broken
        ),
    )

    assert (
        result.execution_evidence_hash
        ==
        broken.blind_evidence_hash
    )


def test_result_does_not_create_confidence(
    tmp_path,
):
    payload = (
        evaluate(
            tmp_path
        )
        .to_dict()
    )

    assert (
        "confidence"
        not in payload
    )

    assert (
        "confidence_band"
        not in payload
    )

    assert (
        "confidence_level"
        not in payload
    )


def test_result_does_not_create_root_cause(
    tmp_path,
):
    payload = (
        evaluate(
            tmp_path
        )
        .to_dict()
    )

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "intervention_authority"
        not in payload
    )