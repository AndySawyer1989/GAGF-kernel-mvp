from __future__ import annotations

import json

import pytest

from backend.app.gagf.prelive_multimodel_primary_diagnosis_comparison import (
    PRIMARY_DIAGNOSIS_COMPARISON_FILENAME,
    PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_AUTHORITY,
    PreliveMultimodelPrimaryDiagnosisComparisonService,
    PrelivePrimaryDiagnosisComparisonError,
)


def build_structural_model(
    *,
    model_label,
    scenario_id,
    scenario_sha256,
    hierarchy_key,
    benchmark_hash,
    structural_replay_hash,
    expected_conditions,
):
    return {
        "model_label":
            model_label,

        "scenario_id":
            scenario_id,

        "scenario_sha256":
            scenario_sha256,

        "hierarchy_key":
            hierarchy_key,

        "benchmark_hash":
            benchmark_hash,

        "structural_replay_hash":
            structural_replay_hash,

        "expected_conditions":
            list(
                expected_conditions
            ),
    }


def build_ranking_item(
    *,
    category,
    rank,
    score,
    structural_level="HIGH",
):
    return {
        "category":
            category,

        "rank":
            rank,

        "explanatory_score":
            score,

        "relative_to_highest":
            (
                1.0
                if rank == 1
                else score
            ),

        "structural_level":
            structural_level,

        "evidence_hash":
            f"{category}-evidence",
    }


def write_model(
    tmp_path,
    *,
    model_label,
    expected_conditions,
    ranked_conditions,
    scores,
):
    slug = (
        model_label.lower()
    )

    directory = (
        tmp_path
        / f"{slug}-benchmark"
    )

    directory.mkdir()

    hierarchy = (
        f"{slug}-tenant/"
        "client/"
        f"{slug}-engagement/"
        f"{slug}-assessment"
    )

    scenario_id = (
        f"{model_label.upper()}-001"
    )

    scenario_sha = (
        f"{slug}-scenario-sha"
    )

    benchmark_hash = (
        f"{slug}-benchmark-hash"
    )

    replay_hash = (
        f"{slug}-primary-replay-hash"
    )

    ranking = [
        build_ranking_item(
            category=category,
            rank=index,
            score=scores[index - 1],
            structural_level=(
                "MODERATE"
                if category
                == "WORK_BLOCKED"
                else "HIGH"
            ),
        )
        for index, category
        in enumerate(
            ranked_conditions,
            start=1,
        )
    ]

    replay = {
        "status":
            "primary_diagnosis_ranking_replay_complete",

        "authority":
            "GAGF_FIP_ONLY",

        "version":
            "1.0.0",

        "model_label":
            model_label,

        "scenario_id":
            scenario_id,

        "scenario_sha256":
            scenario_sha,

        "hierarchy_key":
            hierarchy,

        "source_benchmark_hash":
            benchmark_hash,

        "ranked_conditions":
            list(
                ranked_conditions
            ),

        "highest_ranked_condition":
            ranked_conditions[0],

        "ranking":
            ranking,

        "replay_hash":
            replay_hash,
    }

    (
        directory
        / "primary_diagnosis_ranking_replay.json"
    ).write_text(
        json.dumps(
            replay
        ),
        encoding="utf-8",
    )

    structural = build_structural_model(
        model_label=model_label,
        scenario_id=scenario_id,
        scenario_sha256=scenario_sha,
        hierarchy_key=hierarchy,
        benchmark_hash=benchmark_hash,
        structural_replay_hash=(
            f"{slug}-structural-replay-hash"
        ),
        expected_conditions=(
            expected_conditions
        ),
    )

    return directory, structural


def build_fixture(
    tmp_path,
):
    gemini_directory, gemini = (
        write_model(
            tmp_path,
            model_label="Gemini",
            expected_conditions=(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
            ),
            ranked_conditions=(
                "SECURITY_REVIEW",
                "APPROVAL_DELAYED",
                "OTHER",
            ),
            scores=(
                0.90,
                0.80,
                0.40,
            ),
        )
    )

    claude_directory, claude = (
        write_model(
            tmp_path,
            model_label="Claude",
            expected_conditions=(
                "APPROVAL_DELAYED",
                "DEPENDENCY_WAIT",
            ),
            ranked_conditions=(
                "DEPENDENCY_WAIT",
                "APPROVAL_DELAYED",
                "OTHER",
            ),
            scores=(
                0.95,
                0.85,
                0.30,
            ),
        )
    )

    copilot_directory, copilot = (
        write_model(
            tmp_path,
            model_label="Copilot",
            expected_conditions=(
                "APPROVAL_REQUIRED",
                "WORK_BLOCKED",
            ),
            ranked_conditions=(
                "APPROVAL_REQUIRED",
                "OTHER",
                "WORK_BLOCKED",
            ),
            scores=(
                0.92,
                0.75,
                0.65,
            ),
        )
    )

    structural_path = (
        tmp_path
        / "structural_importance_comparison.json"
    )

    structural_path.write_text(
        json.dumps(
            {
                "models": [
                    claude,
                    copilot,
                    gemini,
                ]
            }
        ),
        encoding="utf-8",
    )

    return (
        structural_path,
        (
            gemini_directory,
            claude_directory,
            copilot_directory,
        ),
    )


def run_comparison(
    tmp_path,
):
    structural_path, directories = (
        build_fixture(
            tmp_path
        )
    )

    return (
        PreliveMultimodelPrimaryDiagnosisComparisonService()
        .compare(
            structural_comparison_path=(
                structural_path
            ),
            benchmark_directories=(
                directories
            ),
            output_directory=(
                tmp_path
                / "comparison"
            ),
        )
    )


def test_comparison_has_three_models(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.model_count
        == 3
    )


def test_comparison_has_six_expected_conditions(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.total_expected_conditions
        == 6
    )


def test_expected_rank_1_count(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.expected_at_rank_1_count
        == 3
    )

    assert (
        result.expected_rank_1_rate
        == 0.5
    )


def test_expected_top_2_count(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.expected_within_top_2_count
        == 5
    )

    assert (
        result.expected_top_2_rate
        == 0.8333333333
    )


def test_expected_top_3_count(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.expected_within_top_3_count
        == 6
    )

    assert (
        result.expected_top_3_rate
        == 1.0
    )


def test_every_model_has_expected_at_rank_1(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.models_with_expected_at_rank_1
        == (
            "Claude",
            "Copilot",
            "Gemini",
        )
    )


def test_two_models_have_all_expected_top_2(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.models_with_all_expected_top_2
        == (
            "Claude",
            "Gemini",
        )
    )


def test_all_models_have_all_expected_top_3(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.models_with_all_expected_top_3
        == (
            "Claude",
            "Copilot",
            "Gemini",
        )
    )


def test_expected_mean_reciprocal_rank(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.mean_expected_reciprocal_rank
        == 0.7222222222
    )


def test_copilot_expected_ranks_are_one_and_three(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    copilot = next(
        model
        for model
        in result.models
        if model.model_label
        == "Copilot"
    )

    ranks = {
        item.category:
            item.rank
        for item
        in copilot.expected_results
    }

    assert ranks == {
        "APPROVAL_REQUIRED":
            1,

        "WORK_BLOCKED":
            3,
    }


def test_score_margin_is_preserved(
    tmp_path,
):
    result = run_comparison(
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
        gemini.rank_1_to_rank_2_margin
        == 0.1
    )


def test_expected_score_deficit_is_measured(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    gemini = next(
        model
        for model
        in result.models
        if model.model_label
        == "Gemini"
    )

    delayed = next(
        item
        for item
        in gemini.expected_results
        if item.category
        == "APPROVAL_DELAYED"
    )

    assert (
        delayed.score_deficit_from_highest
        == 0.1
    )


def test_benchmark_binding_is_valid(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert all(
        model.benchmark_binding_valid
        for model
        in result.models
    )


def test_hierarchy_binding_is_valid(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert all(
        model.hierarchy_binding_valid
        for model
        in result.models
    )


def test_scenario_binding_is_valid(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert all(
        model.scenario_binding_valid
        for model
        in result.models
    )


def test_comparison_writes_deterministic_receipt(
    tmp_path,
):
    structural_path, directories = (
        build_fixture(
            tmp_path
        )
    )

    output_directory = (
        tmp_path
        / "comparison"
    )

    service = (
        PreliveMultimodelPrimaryDiagnosisComparisonService()
    )

    first = service.compare(
        structural_comparison_path=(
            structural_path
        ),
        benchmark_directories=(
            directories
        ),
        output_directory=(
            output_directory
        ),
    )

    second = service.compare(
        structural_comparison_path=(
            structural_path
        ),
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
        first.comparison_hash
        == second.comparison_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )

    assert (
        output_directory
        / PRIMARY_DIAGNOSIS_COMPARISON_FILENAME
    ).is_file()


def test_comparison_uses_gagf_fip_authority(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    assert (
        result.authority
        == PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_AUTHORITY
    )


def test_comparison_rejects_benchmark_binding_mismatch(
    tmp_path,
):
    structural_path, directories = (
        build_fixture(
            tmp_path
        )
    )

    gemini_path = (
        directories[0]
        / "primary_diagnosis_ranking_replay.json"
    )

    payload = json.loads(
        gemini_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "source_benchmark_hash"
    ] = "wrong-hash"

    gemini_path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PrelivePrimaryDiagnosisComparisonError,
        match="benchmark binding mismatch",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisComparisonService()
            .compare(
                structural_comparison_path=(
                    structural_path
                ),
                benchmark_directories=(
                    directories
                ),
                output_directory=(
                    tmp_path
                    / "comparison"
                ),
            )
        )


def test_comparison_does_not_claim_causation(
    tmp_path,
):
    result = run_comparison(
        tmp_path
    )

    payload = (
        result.to_dict()
    )

    assert "root_cause" not in payload
    assert "causal_condition" not in payload
    assert "authorized_action" not in payload
    assert "intervention" not in payload