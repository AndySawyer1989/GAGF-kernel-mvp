from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.gagf.prelive_multimodel_benchmark_comparison import (
    PRELIVE_MULTIMODEL_COMPARISON_AUTHORITY,
    PRELIVE_MULTIMODEL_COMPARISON_STATUS,
    PreliveMultimodelBenchmarkComparisonService,
    PreliveMultimodelComparisonError,
)


def write_json(
    path: Path,
    payload: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_benchmark_fixture(
    tmp_path: Path,
    *,
    model_label: str,
    scenario_id: str,
    scenario_sha256: str,
    event_count: int,
    expected_conditions: list[str],
    raw_true_positives: list[str],
    raw_false_positives: list[str],
    raw_precision: float,
    raw_recall: float,
    raw_f1: float,
    raw_exact: bool,
    raw_dominant_match: bool,
    projection_dominant: str | None,
    systemic_conditions: list[str],
    systemic_true_positives: list[str],
    systemic_false_positives: list[str],
    systemic_false_negatives: list[str],
    systemic_precision: float,
    systemic_recall: float,
    systemic_f1: float,
    systemic_exact: bool,
    systemic_dominant_match: bool,
    expected_dominant: str,
    detected_dominant: str | None,
) -> Path:
    safe_model = (
        model_label
        .strip()
        .lower()
        .replace(" ", "-")
    )

    safe_scenario = (
        scenario_id
        .strip()
        .lower()
        .replace(" ", "-")
    )

    fixture_key = (
        f"{safe_model}-{safe_scenario}"
    )

    source_directory = (
        tmp_path
        / f"{fixture_key}_source"
    )

    benchmark_directory = (
        tmp_path
        / f"{fixture_key}_benchmark"
    )

    source_directory.mkdir()
    benchmark_directory.mkdir()

    source_database = (
        source_directory
        / "prelive.sqlite3"
    )

    source_database.write_bytes(
        b"synthetic-database"
    )

    events = [
        {
            "event_id":
                f"{fixture_key}-event-{index}",
        }
        for index
        in range(
            1,
            event_count + 1,
        )
    ]

    write_json(
        source_directory
        / "scenario_input.json",
        {
            "scenario_id":
                scenario_id,
            "events":
                events,
        },
    )

    write_json(
        source_directory
        / "run_summary.json",
        {
            "precision":
                raw_precision,
            "recall":
                raw_recall,
            "f1":
                raw_f1,
            "exact_condition_match":
                raw_exact,
            "dominant_constraint_match":
                raw_dominant_match,
            "repository_chain_valid":
                True,
            "oracle_leakage_detected":
                False,
        },
    )

    write_json(
        source_directory
        / "scoring.json",
        {
            "true_positives":
                raw_true_positives,
            "false_positives":
                raw_false_positives,
        },
    )

    benchmark_payload = {
        "model_label":
            model_label,
        "scenario_id":
            scenario_id,
        "scenario_sha256":
            scenario_sha256,
        "source_database_path":
            str(
                source_database
            ),
        "benchmark_hash":
            f"{fixture_key}-benchmark-hash",
        "projection": {
            "dominant_condition":
                projection_dominant,
        },
        "scope": {
            "scope_hash":
                f"{fixture_key}-scope-hash",
        },
    }

    write_json(
        benchmark_directory
        / "benchmark_summary.json",
        benchmark_payload,
    )

    write_json(
        benchmark_directory
        / "systemic_scoring.json",
        {
            "expected_conditions":
                expected_conditions,
            "systemic_conditions":
                systemic_conditions,
            "true_positives":
                systemic_true_positives,
            "false_positives":
                systemic_false_positives,
            "false_negatives":
                systemic_false_negatives,
            "precision":
                systemic_precision,
            "recall":
                systemic_recall,
            "f1":
                systemic_f1,
            "exact_condition_match":
                systemic_exact,
            "dominant_constraint_match":
                systemic_dominant_match,
            "expected_dominant_constraint":
                expected_dominant,
            "detected_dominant_constraint":
                detected_dominant,
        },
    )

    return benchmark_directory


def build_three_models(
    tmp_path: Path,
) -> tuple[
    Path,
    Path,
    Path,
]:
    gemini = build_benchmark_fixture(
        tmp_path,
        model_label="Gemini",
        scenario_id="PRELIVE-GEMINI",
        scenario_sha256="g" * 64,
        event_count=140,
        expected_conditions=[
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ],
        raw_true_positives=[
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ],
        raw_false_positives=[
            "ESCALATION",
            "WORK_BLOCKED",
        ],
        raw_precision=0.5,
        raw_recall=1.0,
        raw_f1=0.6667,
        raw_exact=False,
        raw_dominant_match=True,
        projection_dominant=(
            "SECURITY_REVIEW"
        ),
        systemic_conditions=[
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ],
        systemic_true_positives=[
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ],
        systemic_false_positives=[],
        systemic_false_negatives=[],
        systemic_precision=1.0,
        systemic_recall=1.0,
        systemic_f1=1.0,
        systemic_exact=True,
        systemic_dominant_match=True,
        expected_dominant=(
            "SECURITY_REVIEW"
        ),
        detected_dominant=(
            "SECURITY_REVIEW"
        ),
    )

    claude = build_benchmark_fixture(
        tmp_path,
        model_label="Claude",
        scenario_id="PRELIVE-CLAUDE",
        scenario_sha256="c" * 64,
        event_count=156,
        expected_conditions=[
            "APPROVAL_DELAYED",
            "DEPENDENCY_WAIT",
        ],
        raw_true_positives=[
            "APPROVAL_DELAYED",
            "DEPENDENCY_WAIT",
        ],
        raw_false_positives=[
            "ESCALATION",
        ],
        raw_precision=0.6667,
        raw_recall=1.0,
        raw_f1=0.8,
        raw_exact=False,
        raw_dominant_match=True,
        projection_dominant=(
            "DEPENDENCY_WAIT"
        ),
        systemic_conditions=[
            "APPROVAL_DELAYED",
            "DEPENDENCY_WAIT",
            "ESCALATION",
        ],
        systemic_true_positives=[
            "APPROVAL_DELAYED",
            "DEPENDENCY_WAIT",
        ],
        systemic_false_positives=[
            "ESCALATION",
        ],
        systemic_false_negatives=[],
        systemic_precision=0.6667,
        systemic_recall=1.0,
        systemic_f1=0.8,
        systemic_exact=False,
        systemic_dominant_match=True,
        expected_dominant=(
            "DEPENDENCY_WAIT"
        ),
        detected_dominant=(
            "DEPENDENCY_WAIT"
        ),
    )

    copilot = build_benchmark_fixture(
        tmp_path,
        model_label="Copilot",
        scenario_id="PRELIVE-COPILOT",
        scenario_sha256="p" * 64,
        event_count=130,
        expected_conditions=[
            "APPROVAL_REQUIRED",
            "WORK_BLOCKED",
        ],
        raw_true_positives=[
            "APPROVAL_REQUIRED",
            "WORK_BLOCKED",
        ],
        raw_false_positives=[
            "APPROVAL_DELAYED",
        ],
        raw_precision=0.6667,
        raw_recall=1.0,
        raw_f1=0.8,
        raw_exact=False,
        raw_dominant_match=False,
        projection_dominant=(
            "WORK_BLOCKED"
        ),
        systemic_conditions=[
            "APPROVAL_DELAYED",
            "APPROVAL_REQUIRED",
        ],
        systemic_true_positives=[
            "APPROVAL_REQUIRED",
        ],
        systemic_false_positives=[
            "APPROVAL_DELAYED",
        ],
        systemic_false_negatives=[
            "WORK_BLOCKED",
        ],
        systemic_precision=0.5,
        systemic_recall=0.5,
        systemic_f1=0.5,
        systemic_exact=False,
        systemic_dominant_match=False,
        expected_dominant=(
            "APPROVAL_REQUIRED"
        ),
        detected_dominant=None,
    )

    return (
        gemini,
        claude,
        copilot,
    )


def test_compare_requires_at_least_one_directory(
    tmp_path,
):
    service = (
        PreliveMultimodelBenchmarkComparisonService()
    )

    with pytest.raises(
        PreliveMultimodelComparisonError,
        match="At least one",
    ):
        service.compare(
            benchmark_directories=[],
        )


def test_compare_rejects_missing_directory(
    tmp_path,
):
    service = (
        PreliveMultimodelBenchmarkComparisonService()
    )

    with pytest.raises(
        PreliveMultimodelComparisonError,
        match="does not exist",
    ):
        service.compare(
            benchmark_directories=[
                tmp_path / "missing",
            ],
        )


def test_compare_aggregates_three_models(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert result.model_count == 3
    assert result.total_scenarios == 3

    assert result.total_events == (
        140
        + 156
        + 130
    )


def test_compare_orders_models_deterministically(
    tmp_path,
):
    (
        gemini,
        claude,
        copilot,
    ) = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=[
                gemini,
                copilot,
                claude,
            ]
        )
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


def test_compare_calculates_raw_primary_recall(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.raw_primary_recall_rate
        == 1.0
    )


def test_compare_calculates_systemic_primary_recall(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.systemic_primary_recall_rate
        == pytest.approx(
            5 / 6,
            abs=0.0001,
        )
    )


def test_compare_tracks_exact_matches(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.models_with_raw_exact_match
        == ()
    )

    assert (
        result.models_with_systemic_exact_match
        == (
            "Gemini",
        )
    )


def test_compare_tracks_dominant_matches(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.models_with_raw_dominant_match
        == (
            "Claude",
            "Gemini",
        )
    )

    assert (
        result.models_with_systemic_dominant_match
        == (
            "Claude",
            "Gemini",
        )
    )


def test_compare_tracks_systemic_false_negatives(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.models_with_systemic_false_negatives
        == (
            "Copilot",
        )
    )


def test_compare_tracks_systemic_false_positives(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.models_with_systemic_false_positives
        == (
            "Claude",
            "Copilot",
        )
    )


def test_compare_preserves_authority_boundary(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert (
        result.authority
        == PRELIVE_MULTIMODEL_COMPARISON_AUTHORITY
    )

    assert (
        result.status
        == PRELIVE_MULTIMODEL_COMPARISON_STATUS
    )


def test_compare_preserves_repository_verification(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    assert all(
        model.repository_chain_valid
        for model
        in result.models
    )

    assert all(
        not model.oracle_leakage_detected
        for model
        in result.models
    )


def test_compare_preserves_raw_detected_conditions(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    copilot = next(
        model
        for model
        in result.models
        if model.model_label
        == "Copilot"
    )

    assert (
        copilot.raw_detected_conditions
        == (
            "APPROVAL_DELAYED",
            "APPROVAL_REQUIRED",
            "WORK_BLOCKED",
        )
    )


def test_compare_preserves_projection_dominant(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    result = (
        PreliveMultimodelBenchmarkComparisonService()
        .compare(
            benchmark_directories=(
                directories
            )
        )
    )

    copilot = next(
        model
        for model
        in result.models
        if model.model_label
        == "Copilot"
    )

    assert (
        copilot.dominant_raw
        == "WORK_BLOCKED"
    )

    assert (
        copilot.dominant_systemic
        is None
    )


def test_comparison_hash_is_deterministic(
    tmp_path,
):
    (
        gemini,
        claude,
        copilot,
    ) = build_three_models(
        tmp_path
    )

    service = (
        PreliveMultimodelBenchmarkComparisonService()
    )

    first = service.compare(
        benchmark_directories=[
            gemini,
            claude,
            copilot,
        ]
    )

    second = service.compare(
        benchmark_directories=[
            copilot,
            gemini,
            claude,
        ]
    )

    assert (
        first.comparison_hash
        == second.comparison_hash
    )


def test_compare_rejects_duplicate_model_labels(
    tmp_path,
):
    first = build_benchmark_fixture(
        tmp_path,
        model_label="Gemini",
        scenario_id="SCENARIO-1",
        scenario_sha256="a" * 64,
        event_count=1,
        expected_conditions=[
            "APPROVAL_REQUIRED",
        ],
        raw_true_positives=[
            "APPROVAL_REQUIRED",
        ],
        raw_false_positives=[],
        raw_precision=1.0,
        raw_recall=1.0,
        raw_f1=1.0,
        raw_exact=True,
        raw_dominant_match=True,
        projection_dominant=(
            "APPROVAL_REQUIRED"
        ),
        systemic_conditions=[
            "APPROVAL_REQUIRED",
        ],
        systemic_true_positives=[
            "APPROVAL_REQUIRED",
        ],
        systemic_false_positives=[],
        systemic_false_negatives=[],
        systemic_precision=1.0,
        systemic_recall=1.0,
        systemic_f1=1.0,
        systemic_exact=True,
        systemic_dominant_match=True,
        expected_dominant=(
            "APPROVAL_REQUIRED"
        ),
        detected_dominant=(
            "APPROVAL_REQUIRED"
        ),
    )

    second = build_benchmark_fixture(
        tmp_path,
        model_label="Gemini",
        scenario_id="SCENARIO-2",
        scenario_sha256="b" * 64,
        event_count=1,
        expected_conditions=[
            "WORK_BLOCKED",
        ],
        raw_true_positives=[
            "WORK_BLOCKED",
        ],
        raw_false_positives=[],
        raw_precision=1.0,
        raw_recall=1.0,
        raw_f1=1.0,
        raw_exact=True,
        raw_dominant_match=True,
        projection_dominant=(
            "WORK_BLOCKED"
        ),
        systemic_conditions=[
            "WORK_BLOCKED",
        ],
        systemic_true_positives=[
            "WORK_BLOCKED",
        ],
        systemic_false_positives=[],
        systemic_false_negatives=[],
        systemic_precision=1.0,
        systemic_recall=1.0,
        systemic_f1=1.0,
        systemic_exact=True,
        systemic_dominant_match=True,
        expected_dominant=(
            "WORK_BLOCKED"
        ),
        detected_dominant=(
            "WORK_BLOCKED"
        ),
    )

    service = (
        PreliveMultimodelBenchmarkComparisonService()
    )

    with pytest.raises(
        PreliveMultimodelComparisonError,
        match="model labels",
    ):
        service.compare(
            benchmark_directories=[
                first,
                second,
            ]
        )


def test_write_receipt_creates_json(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    service = (
        PreliveMultimodelBenchmarkComparisonService()
    )

    result = service.compare(
        benchmark_directories=(
            directories
        )
    )

    output_path = (
        tmp_path
        / "comparison"
        / "receipt.json"
    )

    service.write_receipt(
        result=result,
        output_path=output_path,
    )

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload[
        "comparison_hash"
    ] == result.comparison_hash

    assert payload[
        "model_count"
    ] == 3


def test_write_receipt_refuses_overwrite(
    tmp_path,
):
    directories = build_three_models(
        tmp_path
    )

    service = (
        PreliveMultimodelBenchmarkComparisonService()
    )

    result = service.compare(
        benchmark_directories=(
            directories
        )
    )

    output_path = (
        tmp_path
        / "receipt.json"
    )

    output_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveMultimodelComparisonError,
        match="already exists",
    ):
        service.write_receipt(
            result=result,
            output_path=output_path,
        )