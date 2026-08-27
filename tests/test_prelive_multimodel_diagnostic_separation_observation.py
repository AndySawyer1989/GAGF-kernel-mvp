from __future__ import annotations

import json

import pytest

from backend.app.gagf.prelive_multimodel_diagnostic_separation_observation import (
    DIAGNOSTIC_SEPARATION_OBSERVATION_FILENAME,
    PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_AUTHORITY,
    PreliveDiagnosticSeparationObservationError,
    PreliveMultimodelDiagnosticSeparationObservationService,
)


def write_replay(
    tmp_path,
    *,
    model_label,
    absolute,
    relative,
    rank_1_to_3_absolute,
    rank_1_to_3_relative,
    top_3_spread,
    leading_quality,
    runner_quality,
    candidate_count,
):
    slug = model_label.lower()

    directory = (
        tmp_path
        / slug
    )

    directory.mkdir()

    hierarchy = (
        f"{slug}-tenant/"
        "client/"
        f"{slug}-engagement/"
        f"{slug}-assessment"
    )

    separation_summary_hash = (
        f"{slug}-separation-summary"
    )

    primary_summary_hash = (
        f"{slug}-primary-summary"
    )

    payload = {
        "status":
            "diagnostic_separation_replay_complete",

        "authority":
            "GAGF_FIP_ONLY",

        "version":
            "1.0.0",

        "model_label":
            model_label,

        "scenario_id":
            f"{model_label.upper()}-001",

        "scenario_sha256":
            f"{slug}-scenario-sha",

        "hierarchy_key":
            hierarchy,

        "source_benchmark_hash":
            f"{slug}-benchmark-hash",

        "primary_diagnosis_replay_hash":
            f"{slug}-primary-replay-hash",

        "primary_diagnosis_summary_hash":
            primary_summary_hash,

        "separation_summary_hash":
            separation_summary_hash,

        "replay_hash":
            f"{slug}-separation-replay-hash",

        "leading_candidate":
            "LEADER",

        "runner_up_candidate":
            "RUNNER",

        "rank_1_score":
            0.8,

        "rank_2_score":
            (
                0.8 - absolute
            ),

        "rank_1_to_rank_2_absolute":
            absolute,

        "rank_1_to_rank_2_relative":
            relative,

        "rank_1_to_rank_3_absolute":
            rank_1_to_3_absolute,

        "rank_1_to_rank_3_relative":
            rank_1_to_3_relative,

        "top_3_score_spread":
            top_3_spread,

        "projection": {
            "hierarchy_key":
                hierarchy,

            "separation_summary_hash":
                separation_summary_hash,

            "primary_diagnosis_summary_hash":
                primary_summary_hash,

            "repository_chain_valid":
                True,

            "primary_projection_verified":
                True,

            "structural_projection_verified":
                True,

            "structural_classification_verified":
                True,
        },

        "support": {
            "candidate_count":
                candidate_count,

            "ranked_candidate_count":
                candidate_count,

            "evidence_quality_observed_count":
                candidate_count,

            "leading_evidence_quality":
                leading_quality,

            "runner_up_evidence_quality":
                runner_quality,

            "leading_structural_level":
                "HIGH",

            "runner_up_structural_level":
                "MODERATE",

            "leading_event_count":
                10,

            "runner_up_event_count":
                8,

            "leading_unique_work_item_count":
                5,

            "runner_up_unique_work_item_count":
                4,

            "leading_active_day_count":
                6,

            "runner_up_active_day_count":
                5,
        },
    }

    (
        directory
        / "diagnostic_separation_replay.json"
    ).write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    return directory


def build_fixture(
    tmp_path,
):
    gemini = write_replay(
        tmp_path,
        model_label="Gemini",
        absolute=0.0055,
        relative=0.0094,
        rank_1_to_3_absolute=0.0817,
        rank_1_to_3_relative=0.1394,
        top_3_spread=0.0817,
        leading_quality=0.9449,
        runner_quality=0.9027,
        candidate_count=8,
    )

    claude = write_replay(
        tmp_path,
        model_label="Claude",
        absolute=0.0682,
        relative=0.0798,
        rank_1_to_3_absolute=0.20,
        rank_1_to_3_relative=0.23,
        top_3_spread=0.20,
        leading_quality=0.93,
        runner_quality=0.91,
        candidate_count=10,
    )

    copilot = write_replay(
        tmp_path,
        model_label="Copilot",
        absolute=0.2706,
        relative=0.3314,
        rank_1_to_3_absolute=0.3235,
        rank_1_to_3_relative=0.3961,
        top_3_spread=0.3235,
        leading_quality=0.95,
        runner_quality=0.89,
        candidate_count=8,
    )

    return (
        gemini,
        claude,
        copilot,
    )


def run_observation(
    tmp_path,
):
    directories = (
        build_fixture(
            tmp_path
        )
    )

    return (
        PreliveMultimodelDiagnosticSeparationObservationService()
        .observe(
            benchmark_directories=(
                directories
            ),
            output_directory=(
                tmp_path
                / "comparison"
            ),
        )
    )


def test_observation_has_three_models(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.model_count
        == 3
    )


def test_models_are_sorted_deterministically(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert tuple(
        model.model_label
        for model
        in result.models
    ) == (
        "Claude",
        "Copilot",
        "Gemini",
    )


def test_absolute_separation_mean(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .mean_rank_1_to_rank_2_absolute
        == 0.1147666667
    )


def test_absolute_separation_median(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .median_rank_1_to_rank_2_absolute
        == 0.0682
    )


def test_absolute_separation_minimum(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .min_rank_1_to_rank_2_absolute
        == 0.0055
    )


def test_absolute_separation_maximum(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .max_rank_1_to_rank_2_absolute
        == 0.2706
    )


def test_relative_separation_mean(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .mean_rank_1_to_rank_2_relative
        == 0.1402
    )


def test_relative_separation_median(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .median_rank_1_to_rank_2_relative
        == 0.0798
    )


def test_relative_separation_minimum(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .min_rank_1_to_rank_2_relative
        == 0.0094
    )


def test_relative_separation_maximum(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.aggregate
        .max_rank_1_to_rank_2_relative
        == 0.3314
    )


def test_preserves_replay_hash_bindings(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    gemini = next(
        model
        for model
        in result.models
        if model.model_label
        == "Gemini"
    )

    assert (
        gemini.separation_replay_hash
        == "gemini-separation-replay-hash"
    )

    assert (
        gemini.primary_diagnosis_replay_hash
        == "gemini-primary-replay-hash"
    )


def test_preserves_support_evidence(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    gemini = next(
        model
        for model
        in result.models
        if model.model_label
        == "Gemini"
    )

    assert (
        gemini.leading_evidence_quality
        == 0.9449
    )

    assert (
        gemini.runner_up_evidence_quality
        == 0.9027
    )

    assert (
        gemini.candidate_count
        == 8
    )


def test_integrity_flags_are_preserved(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert all(
        model.repository_chain_valid
        and model.primary_projection_verified
        and model.structural_projection_verified
        and model.structural_classification_verified
        for model
        in result.models
    )


def test_rejects_unverified_integrity(
    tmp_path,
):
    directories = list(
        build_fixture(
            tmp_path
        )
    )

    path = (
        directories[0]
        / "diagnostic_separation_replay.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "projection"
    ][
        "repository_chain_valid"
    ] = False

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveDiagnosticSeparationObservationError,
        match="not fully verified",
    ):
        (
            PreliveMultimodelDiagnosticSeparationObservationService()
            .observe(
                benchmark_directories=(
                    directories
                ),
                output_directory=(
                    tmp_path
                    / "comparison"
                ),
            )
        )


def test_rejects_summary_hash_binding_mismatch(
    tmp_path,
):
    directories = list(
        build_fixture(
            tmp_path
        )
    )

    path = (
        directories[0]
        / "diagnostic_separation_replay.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "projection"
    ][
        "separation_summary_hash"
    ] = "wrong"

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveDiagnosticSeparationObservationError,
        match="summary hash binding mismatch",
    ):
        (
            PreliveMultimodelDiagnosticSeparationObservationService()
            .observe(
                benchmark_directories=(
                    directories
                ),
                output_directory=(
                    tmp_path
                    / "comparison"
                ),
            )
        )


def test_rejects_duplicate_model_labels(
    tmp_path,
):
    first = write_replay(
        tmp_path,
        model_label="Gemini",
        absolute=0.1,
        relative=0.1,
        rank_1_to_3_absolute=0.2,
        rank_1_to_3_relative=0.2,
        top_3_spread=0.2,
        leading_quality=0.9,
        runner_quality=0.8,
        candidate_count=3,
    )

    second = (
        tmp_path
        / "duplicate"
    )

    second.mkdir()

    payload = json.loads(
        (
            first
            / "diagnostic_separation_replay.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    (
        second
        / "diagnostic_separation_replay.json"
    ).write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveDiagnosticSeparationObservationError,
        match="duplicate model labels",
    ):
        (
            PreliveMultimodelDiagnosticSeparationObservationService()
            .observe(
                benchmark_directories=(
                    first,
                    second,
                ),
                output_directory=(
                    tmp_path
                    / "comparison"
                ),
            )
        )


def test_observation_receipt_is_deterministic(
    tmp_path,
):
    directories = (
        build_fixture(
            tmp_path
        )
    )

    service = (
        PreliveMultimodelDiagnosticSeparationObservationService()
    )

    output_directory = (
        tmp_path
        / "comparison"
    )

    first = service.observe(
        benchmark_directories=(
            directories
        ),
        output_directory=(
            output_directory
        ),
    )

    second = service.observe(
        benchmark_directories=(
            reversed(
                directories
            )
        ),
        output_directory=(
            output_directory
        ),
    )

    assert (
        first.observation_hash
        == second.observation_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )

    assert (
        output_directory
        / DIAGNOSTIC_SEPARATION_OBSERVATION_FILENAME
    ).is_file()


def test_authority_is_gagf_fip_only(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    assert (
        result.authority
        == PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_AUTHORITY
    )


def test_output_does_not_classify_confidence_or_correctness(
    tmp_path,
):
    result = run_observation(
        tmp_path
    )

    payload = (
        result.to_dict()
    )

    forbidden = (
        "confidence",
        "confidence_level",
        "threshold",
        "correct",
        "correctness",
        "expected_conditions",
        "oracle",
        "root_cause",
        "primary_diagnosis",
        "intervention",
    )

    for field in forbidden:
        assert field not in payload