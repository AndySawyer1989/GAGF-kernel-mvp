from __future__ import annotations

import json

import pytest

from backend.app.gagf.prelive_multimodel_structural_importance_comparison import (
    PRELIVE_STRUCTURAL_COMPARISON_AUTHORITY,
    PRELIVE_STRUCTURAL_COMPARISON_STATUS,
    PRELIVE_STRUCTURAL_COMPARISON_VERSION,
    STRUCTURAL_COMPARISON_FILENAME,
    PreliveMultimodelStructuralImportanceComparisonService,
    PreliveStructuralImportanceComparisonError,
)
from backend.app.gagf.prelive_multimodel_structural_importance_replay import (
    STRUCTURAL_REPLAY_FILENAME,
)


def write_json(
    path,
    payload,
):
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_model(
    root,
    *,
    model_label,
    scenario_id,
    expected,
    high,
    moderate,
    low=None,
    limited=None,
):
    directory = (
        root
        / model_label
    )

    directory.mkdir(
        parents=True,
    )

    hierarchy_key = (
        f"tenant-{model_label}/"
        f"client-{model_label}/"
        f"engagement-{model_label}/"
        f"assessment-{model_label}"
    )

    benchmark_hash = (
        f"{model_label}-benchmark-hash"
    )

    write_json(
        directory
        / "benchmark_summary.json",
        {
            "model_label":
                model_label,
            "scenario_id":
                scenario_id,
            "scenario_sha256":
                f"{model_label}-scenario-hash",
            "hierarchy_key":
                hierarchy_key,
            "benchmark_hash":
                benchmark_hash,
        },
    )

    write_json(
        directory
        / "systemic_scoring.json",
        {
            "expected_conditions":
                list(
                    expected
                ),
        },
    )

    classification_payload = {
        "hierarchy_key":
            hierarchy_key,
        "summary_hash":
            f"{model_label}-classification-hash",
    }

    write_json(
        directory
        / STRUCTURAL_REPLAY_FILENAME,
        {
            "model_label":
                model_label,
            "scenario_id":
                scenario_id,
            "scenario_sha256":
                f"{model_label}-scenario-hash",
            "hierarchy_key":
                hierarchy_key,
            "source_benchmark_hash":
                benchmark_hash,

            "high_conditions":
                list(
                    high
                ),
            "moderate_conditions":
                list(
                    moderate
                ),
            "low_conditions":
                list(
                    low
                    or ()
                ),
            "limited_conditions":
                list(
                    limited
                    or ()
                ),

            "projection": {
                "repository_chain_valid":
                    True,
                "diagnostic_integrity_verified":
                    True,
            },

            "classification":
                classification_payload,

            "replay_hash":
                f"{model_label}-replay-hash",
        },
    )

    return directory


def build_three_models(
    tmp_path,
):
    gemini = build_model(
        tmp_path,
        model_label="gemini",
        scenario_id="scenario-gemini",
        expected=(
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ),
        high=(
            "APPROVAL_DELAYED",
        ),
        moderate=(
            "SECURITY_REVIEW",
        ),
        low=(
            "OVERRIDE",
        ),
    )

    claude = build_model(
        tmp_path,
        model_label="claude",
        scenario_id="scenario-claude",
        expected=(
            "APPROVAL_DELAYED",
            "DEPENDENCY_WAIT",
        ),
        high=(
            "DEPENDENCY_WAIT",
            "ESCALATION",
        ),
        moderate=(
            "APPROVAL_DELAYED",
        ),
        limited=(
            "OWNERSHIP_GAP",
        ),
    )

    copilot = build_model(
        tmp_path,
        model_label="copilot",
        scenario_id="scenario-copilot",
        expected=(
            "APPROVAL_REQUIRED",
            "WORK_BLOCKED",
        ),
        high=(
            "APPROVAL_REQUIRED",
            "WORK_BLOCKED",
        ),
        moderate=(),
        low=(
            "ENVIRONMENT_FAILURE",
        ),
    )

    return (
        gemini,
        claude,
        copilot,
    )


def test_compare_requires_directory():
    service = (
        PreliveMultimodelStructuralImportanceComparisonService()
    )

    with pytest.raises(
        PreliveStructuralImportanceComparisonError,
        match="At least one",
    ):
        service.compare(
            benchmark_directories=[]
        )


def test_compare_orders_models_deterministically(
    tmp_path,
):
    gemini, claude, copilot = (
        build_three_models(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=[
                gemini,
                copilot,
                claude,
            ]
        )
    )

    assert (
        tuple(
            model.model_label
            for model
            in result.models
        )
        == (
            "claude",
            "copilot",
            "gemini",
        )
    )


def test_compare_calculates_high_metrics(
    tmp_path,
):
    directories = (
        build_three_models(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    # HIGH:
    # Gemini 1 TP
    # Claude 1 TP + 1 FP
    # Copilot 2 TP
    #
    # 4 TP / 5 HIGH detections
    assert (
        result.high_precision
        == 0.8
    )

    # 4 of 6 planted conditions are HIGH.
    assert (
        result.high_recall
        == pytest.approx(
            4 / 6
        )
    )


def test_compare_calculates_high_or_moderate_metrics(
    tmp_path,
):
    directories = (
        build_three_models(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    # All six expected conditions appear in HIGH
    # or MODERATE.
    assert (
        result.high_or_moderate_recall
        == 1.0
    )

    # One additional false-positive ESCALATION.
    assert (
        result.high_or_moderate_precision
        == pytest.approx(
            6 / 7
        )
    )


def test_primary_hit_rates_are_explicit(
    tmp_path,
):
    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                build_three_models(
                    tmp_path
                )
            )
        )
    )

    assert (
        result.primary_high_hit_rate
        == result.high_recall
    )

    assert (
        result.primary_high_or_moderate_hit_rate
        == result.high_or_moderate_recall
    )


def test_compare_calculates_false_high_rate(
    tmp_path,
):
    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                build_three_models(
                    tmp_path
                )
            )
        )
    )

    assert (
        result.false_high_rate
        == 0.2
    )


def test_compare_calculates_limited_rate(
    tmp_path,
):
    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                build_three_models(
                    tmp_path
                )
            )
        )
    )

    # Gemini: 3 classified
    # Claude: 4 classified
    # Copilot: 3 classified
    # 1 LIMITED / 10 total
    assert (
        result.limited_rate
        == 0.1
    )


def test_per_model_preserves_four_levels(
    tmp_path,
):
    gemini = build_model(
        tmp_path,
        model_label="gemini",
        scenario_id="scenario-gemini",
        expected=(
            "A",
        ),
        high=(
            "A",
        ),
        moderate=(
            "B",
        ),
        low=(
            "C",
        ),
        limited=(
            "D",
        ),
    )

    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=[
                gemini,
            ]
        )
    )

    model = result.models[0]

    assert model.high_conditions == ("A",)
    assert model.moderate_conditions == ("B",)
    assert model.low_conditions == ("C",)
    assert model.limited_conditions == ("D",)


def test_compare_tracks_false_highs(
    tmp_path,
):
    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                build_three_models(
                    tmp_path
                )
            )
        )
    )

    assert (
        result.models_with_false_highs
        == (
            "claude",
        )
    )


def test_compare_tracks_limited_models(
    tmp_path,
):
    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                build_three_models(
                    tmp_path
                )
            )
        )
    )

    assert (
        result.models_with_limited_conditions
        == (
            "claude",
        )
    )


def test_compare_rejects_overlapping_buckets(
    tmp_path,
):
    directory = build_model(
        tmp_path,
        model_label="gemini",
        scenario_id="scenario-gemini",
        expected=(
            "A",
        ),
        high=(
            "A",
        ),
        moderate=(
            "B",
        ),
    )

    replay_path = (
        directory
        / STRUCTURAL_REPLAY_FILENAME
    )

    payload = json.loads(
        replay_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "moderate_conditions"
    ] = [
        "A",
        "B",
    ]

    write_json(
        replay_path,
        payload,
    )

    with pytest.raises(
        PreliveStructuralImportanceComparisonError,
        match="buckets overlap",
    ):
        (
            PreliveMultimodelStructuralImportanceComparisonService()
            .compare(
                benchmark_directories=[
                    directory,
                ]
            )
        )


def test_compare_rejects_benchmark_hash_drift(
    tmp_path,
):
    directory = build_model(
        tmp_path,
        model_label="gemini",
        scenario_id="scenario-gemini",
        expected=(
            "A",
        ),
        high=(
            "A",
        ),
        moderate=(),
    )

    replay_path = (
        directory
        / STRUCTURAL_REPLAY_FILENAME
    )

    payload = json.loads(
        replay_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "source_benchmark_hash"
    ] = "wrong-hash"

    write_json(
        replay_path,
        payload,
    )

    with pytest.raises(
        PreliveStructuralImportanceComparisonError,
        match="benchmark hash",
    ):
        (
            PreliveMultimodelStructuralImportanceComparisonService()
            .compare(
                benchmark_directories=[
                    directory,
                ]
            )
        )


def test_compare_rejects_duplicate_model_labels(
    tmp_path,
):
    first = build_model(
        tmp_path / "first",
        model_label="gemini",
        scenario_id="scenario-1",
        expected=("A",),
        high=("A",),
        moderate=(),
    )

    second = build_model(
        tmp_path / "second",
        model_label="gemini",
        scenario_id="scenario-2",
        expected=("A",),
        high=("A",),
        moderate=(),
    )

    with pytest.raises(
        PreliveStructuralImportanceComparisonError,
        match="model labels",
    ):
        (
            PreliveMultimodelStructuralImportanceComparisonService()
            .compare(
                benchmark_directories=[
                    first,
                    second,
                ]
            )
        )


def test_comparison_hash_is_deterministic(
    tmp_path,
):
    directories = (
        build_three_models(
            tmp_path
        )
    )

    service = (
        PreliveMultimodelStructuralImportanceComparisonService()
    )

    first = service.compare(
        benchmark_directories=(
            directories
        )
    )

    second = service.compare(
        benchmark_directories=(
            reversed(
                directories
            )
        )
    )

    assert (
        first.comparison_hash
        == second.comparison_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )


def test_write_receipt_is_deterministic(
    tmp_path,
):
    benchmark_root = (
        tmp_path
        / "benchmarks"
    )

    benchmark_root.mkdir()

    directories = (
        build_three_models(
            benchmark_root
        )
    )

    service = (
        PreliveMultimodelStructuralImportanceComparisonService()
    )

    result = service.compare(
        benchmark_directories=(
            directories
        )
    )

    output = (
        tmp_path
        / "comparison"
    )

    first_path = service.write_receipt(
        output_directory=output,
        result=result,
    )

    first_text = (
        first_path.read_text(
            encoding="utf-8"
        )
    )

    second_path = service.write_receipt(
        output_directory=output,
        result=result,
    )

    second_text = (
        second_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        first_path
        == second_path
    )

    assert (
        first_text
        == second_text
    )

    assert (
        first_path.name
        == STRUCTURAL_COMPARISON_FILENAME
    )


def test_receipt_preserves_governance_boundary(
    tmp_path,
):
    result = (
        PreliveMultimodelStructuralImportanceComparisonService()
        .compare(
            benchmark_directories=(
                build_three_models(
                    tmp_path
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
        == PRELIVE_STRUCTURAL_COMPARISON_AUTHORITY
    )

    assert (
        payload[
            "status"
        ]
        == PRELIVE_STRUCTURAL_COMPARISON_STATUS
    )

    assert (
        payload[
            "version"
        ]
        == PRELIVE_STRUCTURAL_COMPARISON_VERSION
    )

    assert "root_cause" not in payload
    assert "primary_condition" not in payload
    assert "intervention" not in payload