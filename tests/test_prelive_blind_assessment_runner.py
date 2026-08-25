from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_blind_assessment_runner import (
    PRELIVE_BLIND_RUNNER_AUTHORITY,
    PRELIVE_BLIND_RUNNER_STATUS,
    PreliveBlindAssessmentRunner,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)
from tests.test_prelive_rehearsal_result_verification import (
    execute_blind_rehearsal,
)
from backend.app.gagf.prelive_rehearsal_result_verification import (
    PreliveRehearsalResultVerifier,
)


def build_external_oracle(
    scenario: dict,
) -> dict:
    from backend.app.gagf.prelive_blind_assessment import (
        canonical_sha256,
    )

    return {
        "schema_version": "1.0",
        "test_program": "PRELIVE-001",
        "oracle_status": "SEALED",
        "scenario_id": scenario["scenario_id"],
        "scenario_sha256": canonical_sha256(
            scenario
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


def run_blind_assessment(
    tmp_path: Path,
):
    scenario = build_scenario()

    oracle = build_external_oracle(
        scenario
    )

    output_directory = (
        tmp_path
        / "prelive_run_001"
    )

    result = (
        PreliveBlindAssessmentRunner()
        .run(
            scenario=scenario,
            oracle=oracle,
            output_directory=(
                output_directory
            ),
            operator_id=(
                "PRELIVE Test Operator"
            ),
            execution_confirmed=True,
            confirmed_at=(
                "2026-08-25T00:30:00-04:00"
            ),
        )
    )

    return (
        scenario,
        oracle,
        output_directory,
        result,
    )


def test_runner_completes_full_blind_rehearsal(
    tmp_path,
):
    (
        _,
        _,
        _,
        result,
    ) = run_blind_assessment(
        tmp_path
    )

    assert (
        result.run_status
        == PRELIVE_BLIND_RUNNER_STATUS
    )

    assert (
        result.authority
        == PRELIVE_BLIND_RUNNER_AUTHORITY
    )

    assert (
        result.execution
        .execution_result
        .application_completed
        is True
    )

    assert (
        result.verification
        .repository_chain_valid
        is True
    )

    assert (
        result.verification
        .oracle_leakage_detected
        is False
    )


def test_runner_scores_oracle_after_verification(
    tmp_path,
):
    (
        _,
        _,
        _,
        result,
    ) = run_blind_assessment(
        tmp_path
    )

    score = result.scoring

    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1 == 1.0

    assert (
        score.exact_condition_match
        is True
    )

    assert (
        score.event_count_accuracy
        == 1.0
    )

    assert (
        score.band_accuracy
        == 1.0
    )

    assert (
        score.dominant_constraint_match
        is True
    )


def test_runner_writes_expected_output_files(
    tmp_path,
):
    (
        _,
        _,
        output_directory,
        _,
    ) = run_blind_assessment(
        tmp_path
    )

    expected_files = {
        "scenario_input.json",
        "oracle_unsealed.json",
        "execution_result.json",
        "verification.json",
        "scoring.json",
        "run_summary.json",
        "prelive.sqlite3",
    }

    actual_files = {
        path.name
        for path
        in output_directory.iterdir()
    }

    assert expected_files.issubset(
        actual_files
    )


def test_runner_summary_contains_scoring_metrics(
    tmp_path,
):
    (
        _,
        _,
        output_directory,
        _,
    ) = run_blind_assessment(
        tmp_path
    )

    summary = json.loads(
        (
            output_directory
            / "run_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        summary["run_status"]
        == PRELIVE_BLIND_RUNNER_STATUS
    )

    assert (
        summary["authority"]
        == PRELIVE_BLIND_RUNNER_AUTHORITY
    )

    assert (
        summary["repository_chain_valid"]
        is True
    )

    assert (
        summary["oracle_leakage_detected"]
        is False
    )

    assert summary["precision"] == 1.0
    assert summary["recall"] == 1.0
    assert summary["f1"] == 1.0

    assert (
        summary["exact_condition_match"]
        is True
    )

    assert (
        summary["customer_outcome_verified"]
        is False
    )

    assert (
        summary[
            "production_onboarding_authorized"
        ]
        is False
    )


def test_runner_output_preserves_scenario_hash(
    tmp_path,
):
    (
        _,
        _,
        output_directory,
        result,
    ) = run_blind_assessment(
        tmp_path
    )

    summary = json.loads(
        (
            output_directory
            / "run_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        summary["scenario_sha256"]
        == result.scenario_sha256
    )

    assert len(
        result.scenario_sha256
    ) == 64


def test_runner_persists_verification_receipt(
    tmp_path,
):
    (
        _,
        _,
        output_directory,
        result,
    ) = run_blind_assessment(
        tmp_path
    )

    payload = json.loads(
        (
            output_directory
            / "verification.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload["verification_hash"]
        == result.verification
        .verification_hash
    )

    assert (
        payload["repository_chain_valid"]
        is True
    )

    assert (
        payload["oracle_leakage_detected"]
        is False
    )


def test_runner_persists_scoring_receipt(
    tmp_path,
):
    (
        _,
        _,
        output_directory,
        result,
    ) = run_blind_assessment(
        tmp_path
    )

    payload = json.loads(
        (
            output_directory
            / "scoring.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload["scoring_hash"]
        == result.scoring.scoring_hash
    )

    assert payload["precision"] == 1.0
    assert payload["recall"] == 1.0
    assert payload["f1"] == 1.0


def test_runner_rejects_execution_without_confirmation(
    tmp_path,
):
    scenario = build_scenario()

    oracle = build_external_oracle(
        scenario
    )

    output_directory = (
        tmp_path
        / "should_not_execute"
    )

    with pytest.raises(
        PreliveScenarioError,
        match=(
            "requires explicit human "
            "confirmation"
        ),
    ):
        (
            PreliveBlindAssessmentRunner()
            .run(
                scenario=scenario,
                oracle=oracle,
                output_directory=(
                    output_directory
                ),
                operator_id=(
                    "PRELIVE Test Operator"
                ),
                execution_confirmed=False,
                confirmed_at=(
                    "2026-08-25T00:30:00-04:00"
                ),
            )
        )

    assert not (
        output_directory
        / "prelive.sqlite3"
    ).exists()


def test_runner_rejects_empty_operator_id(
    tmp_path,
):
    scenario = build_scenario()

    oracle = build_external_oracle(
        scenario
    )

    with pytest.raises(
        PreliveScenarioError,
        match="operator_id",
    ):
        (
            PreliveBlindAssessmentRunner()
            .run(
                scenario=scenario,
                oracle=oracle,
                output_directory=(
                    tmp_path
                    / "invalid_operator"
                ),
                operator_id="",
                execution_confirmed=True,
                confirmed_at=(
                    "2026-08-25T00:30:00-04:00"
                ),
            )
        )


def test_runner_rejects_nonempty_output_directory(
    tmp_path,
):
    scenario = build_scenario()

    oracle = build_external_oracle(
        scenario
    )

    output_directory = (
        tmp_path
        / "existing_run"
    )

    output_directory.mkdir()

    (
        output_directory
        / "existing.txt"
    ).write_text(
        "already used",
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveScenarioError,
        match="must be empty",
    ):
        (
            PreliveBlindAssessmentRunner()
            .run(
                scenario=scenario,
                oracle=oracle,
                output_directory=(
                    output_directory
                ),
                operator_id=(
                    "PRELIVE Test Operator"
                ),
                execution_confirmed=True,
                confirmed_at=(
                    "2026-08-25T00:30:00-04:00"
                ),
            )
        )


def test_runner_rejects_wrong_oracle_hash(
    tmp_path,
):
    scenario = build_scenario()

    oracle = build_external_oracle(
        scenario
    )

    oracle["scenario_sha256"] = (
        "0" * 64
    )

    with pytest.raises(
        PreliveScenarioError,
        match="scenario SHA-256",
    ):
        (
            PreliveBlindAssessmentRunner()
            .run(
                scenario=scenario,
                oracle=oracle,
                output_directory=(
                    tmp_path
                    / "wrong_oracle"
                ),
                operator_id=(
                    "PRELIVE Test Operator"
                ),
                execution_confirmed=True,
                confirmed_at=(
                    "2026-08-25T00:30:00-04:00"
                ),
            )
        )


def test_runner_rejects_invalid_blind_scenario(
    tmp_path,
):
    scenario = build_scenario()

    scenario[
        "expected_conditions"
    ] = [
        "WORK_BLOCKED"
    ]

    oracle = {
        "schema_version": "1.0",
        "test_program": "PRELIVE-001",
        "oracle_status": "SEALED",
        "scenario_id": (
            scenario["scenario_id"]
        ),
        "scenario_sha256": (
            "0" * 64
        ),
        "expected_conditions": [
            {
                "constraint_type":
                    "WORK_BLOCKED",
            }
        ],
    }

    with pytest.raises(
        PreliveScenarioError,
        match=(
            "blind scenario validation "
            "failed"
        ),
    ):
        (
            PreliveBlindAssessmentRunner()
            .run(
                scenario=scenario,
                oracle=oracle,
                output_directory=(
                    tmp_path
                    / "invalid_scenario"
                ),
                operator_id=(
                    "PRELIVE Test Operator"
                ),
                execution_confirmed=True,
                confirmed_at=(
                    "2026-08-25T00:30:00-04:00"
                ),
            )
        )


def test_runner_result_is_immutable(
    tmp_path,
):
    (
        _,
        _,
        _,
        result,
    ) = run_blind_assessment(
        tmp_path
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.authority = "changed"


def test_cli_help_runs_successfully():
    completed = subprocess.run(
        [
            sys.executable,
            (
                "scripts/"
                "run_prelive_blind_assessment.py"
            ),
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0

    assert (
        "--scenario"
        in completed.stdout
    )

    assert (
        "--oracle"
        in completed.stdout
    )

    assert (
        "--output"
        in completed.stdout
    )


def test_cli_refuses_missing_scenario_file(
    tmp_path,
):
    completed = subprocess.run(
        [
            sys.executable,
            (
                "scripts/"
                "run_prelive_blind_assessment.py"
            ),
            "--scenario",
            str(
                tmp_path
                / "missing_scenario.json"
            ),
            "--oracle",
            str(
                tmp_path
                / "missing_oracle.json"
            ),
            "--output",
            str(
                tmp_path
                / "output"
            ),
        ],
        input="EXECUTE PRELIVE\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1

    assert (
        "Scenario file does not exist"
        in completed.stderr
    )