from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_oracle_scoring import (
    PRELIVE_ORACLE_SCORING_AUTHORITY,
    PRELIVE_ORACLE_SCORING_STATUS,
    PreliveOracleScoringService,
)
from backend.app.gagf.prelive_rehearsal_result_verification import (
    PreliveRehearsalResultVerifier,
)
from tests.test_prelive_rehearsal_result_verification import (
    execute_blind_rehearsal,
)


def execute_verify_and_build_oracle(
    tmp_path: Path,
):
    (
        database_path,
        prepared,
        execution,
    ) = execute_blind_rehearsal(
        tmp_path
    )

    verification = (
        PreliveRehearsalResultVerifier()
        .verify(
            database_path=database_path,
            rehearsal_result=execution,
        )
    )

    oracle = {
        "schema_version": "1.0",
        "test_program": "PRELIVE-001",
        "oracle_status": "SEALED",
        "scenario_id": (
            prepared.request_bridge
            .scenario_id
        ),
        "scenario_sha256": (
            prepared.request_bridge
            .scenario_sha256
        ),
        "expected_conditions": [
            {
                "constraint_type":
                    "APPROVAL_DELAYED",
                "expected_event_count":
                    50,
                "expected_band":
                    "severe",
            },
            {
                "constraint_type":
                    "WORK_BLOCKED",
                "expected_event_count":
                    50,
                "expected_band":
                    "severe",
            },
        ],
        "expected_dominant_constraint":
            "WORK_BLOCKED",
    }

    return (
        database_path,
        prepared,
        execution,
        verification,
        oracle,
    )


def score_rehearsal(
    tmp_path: Path,
):
    (
        database_path,
        prepared,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    score = (
        PreliveOracleScoringService()
        .score(
            database_path=database_path,
            rehearsal_result=execution,
            verification=verification,
            oracle=oracle,
        )
    )

    return (
        database_path,
        prepared,
        execution,
        verification,
        oracle,
        score,
    )


def test_scores_exact_blind_diagnostic_match(
    tmp_path,
):
    *_, score = score_rehearsal(
        tmp_path
    )

    assert (
        score.scoring_status
        == PRELIVE_ORACLE_SCORING_STATUS
    )

    assert (
        score.authority
        == PRELIVE_ORACLE_SCORING_AUTHORITY
    )

    assert score.true_positives == (
        "APPROVAL_DELAYED",
        "WORK_BLOCKED",
    )

    assert score.false_positives == ()
    assert score.false_negatives == ()

    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1 == 1.0

    assert (
        score.exact_condition_match
        is True
    )


def test_scores_exact_event_counts(
    tmp_path,
):
    *_, score = score_rehearsal(
        tmp_path
    )

    assert (
        score.event_count_accuracy
        == 1.0
    )


def test_scores_exact_friction_bands(
    tmp_path,
):
    *_, score = score_rehearsal(
        tmp_path
    )

    assert score.band_accuracy == 1.0


def test_scores_dominant_constraint(
    tmp_path,
):
    *_, score = score_rehearsal(
        tmp_path
    )

    assert (
        score.expected_dominant_constraint
        == "WORK_BLOCKED"
    )

    assert (
        score.detected_dominant_constraint
        == "WORK_BLOCKED"
    )

    assert (
        score.dominant_constraint_match
        is True
    )


def test_detected_conditions_come_from_persistence(
    tmp_path,
):
    *_, score = score_rehearsal(
        tmp_path
    )

    detected = {
        condition.constraint_type:
            condition
        for condition
        in score.detected_conditions
    }

    assert (
        detected[
            "APPROVAL_DELAYED"
        ].event_count
        == 50
    )

    assert (
        detected[
            "WORK_BLOCKED"
        ].event_count
        == 50
    )

    assert (
        detected[
            "APPROVAL_DELAYED"
        ].band
        == "severe"
    )

    assert (
        detected[
            "WORK_BLOCKED"
        ].band
        == "severe"
    )


def test_scores_false_negative(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle[
        "expected_conditions"
    ].append(
        {
            "constraint_type":
                "OWNERSHIP_GAP",
        }
    )

    score = (
        PreliveOracleScoringService()
        .score(
            database_path=database_path,
            rehearsal_result=execution,
            verification=verification,
            oracle=oracle,
        )
    )

    assert score.false_negatives == (
        "OWNERSHIP_GAP",
    )

    assert score.precision == 1.0

    assert score.recall == round(
        2 / 3,
        4,
    )

    assert score.f1 < 1.0


def test_scores_false_positive(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle["expected_conditions"] = [
        {
            "constraint_type":
                "WORK_BLOCKED",
        }
    ]

    oracle[
        "expected_dominant_constraint"
    ] = "WORK_BLOCKED"

    score = (
        PreliveOracleScoringService()
        .score(
            database_path=database_path,
            rehearsal_result=execution,
            verification=verification,
            oracle=oracle,
        )
    )

    assert score.true_positives == (
        "WORK_BLOCKED",
    )

    assert score.false_positives == (
        "APPROVAL_DELAYED",
    )

    assert score.false_negatives == ()

    assert score.precision == 0.5
    assert score.recall == 1.0


def test_rejects_wrong_scenario_id(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle["scenario_id"] = (
        "WRONG-SCENARIO"
    )

    with pytest.raises(
        PreliveScenarioError,
        match="scenario_id",
    ):
        (
            PreliveOracleScoringService()
            .score(
                database_path=database_path,
                rehearsal_result=execution,
                verification=verification,
                oracle=oracle,
            )
        )


def test_rejects_wrong_scenario_hash(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle["scenario_sha256"] = (
        "0" * 64
    )

    with pytest.raises(
        PreliveScenarioError,
        match="SHA-256",
    ):
        (
            PreliveOracleScoringService()
            .score(
                database_path=database_path,
                rehearsal_result=execution,
                verification=verification,
                oracle=oracle,
            )
        )


def test_rejects_unsealed_oracle_marker(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle["oracle_status"] = (
        "UNSEALED"
    )

    with pytest.raises(
        PreliveScenarioError,
        match="marked SEALED",
    ):
        (
            PreliveOracleScoringService()
            .score(
                database_path=database_path,
                rehearsal_result=execution,
                verification=verification,
                oracle=oracle,
            )
        )


def test_rejects_duplicate_expected_condition(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle[
        "expected_conditions"
    ].append(
        {
            "constraint_type":
                "WORK_BLOCKED",
        }
    )

    with pytest.raises(
        PreliveScenarioError,
        match="duplicate expected",
    ):
        (
            PreliveOracleScoringService()
            .score(
                database_path=database_path,
                rehearsal_result=execution,
                verification=verification,
                oracle=oracle,
            )
        )


def test_rejects_unsupported_oracle_condition(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    oracle["expected_conditions"] = [
        {
            "constraint_type":
                "AI_MADE_UP_PROBLEM",
        }
    ]

    with pytest.raises(
        PreliveScenarioError,
        match="unsupported constraint",
    ):
        (
            PreliveOracleScoringService()
            .score(
                database_path=database_path,
                rehearsal_result=execution,
                verification=verification,
                oracle=oracle,
            )
        )


def test_scoring_is_deterministic(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        verification,
        oracle,
    ) = execute_verify_and_build_oracle(
        tmp_path
    )

    service = (
        PreliveOracleScoringService()
    )

    first = service.score(
        database_path=database_path,
        rehearsal_result=execution,
        verification=verification,
        oracle=oracle,
    )

    second = service.score(
        database_path=database_path,
        rehearsal_result=execution,
        verification=verification,
        oracle=oracle,
    )

    assert first == second

    assert (
        first.scoring_hash
        == second.scoring_hash
    )

    assert len(first.scoring_hash) == 64

    assert len(first.oracle_sha256) == 64


def test_scoring_receipt_binds_verification(
    tmp_path,
):
    (
        _,
        _,
        _,
        verification,
        _,
        score,
    ) = score_rehearsal(
        tmp_path
    )

    assert (
        score.verification_hash
        == verification.verification_hash
    )

    assert (
        score.hierarchy_key
        == verification.hierarchy_key
    )


def test_scoring_receipt_is_immutable(
    tmp_path,
):
    *_, score = score_rehearsal(
        tmp_path
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        score.authority = "changed"