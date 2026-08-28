from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.diagnostic_calibration_blind_run_cli import (
    SUPPORTED_MODELS,
    build_context,
    build_parser,
    build_paths,
    normalize_scenario_id,
)


def test_supported_models():
    assert (
        SUPPORTED_MODELS
        ==
        (
            "gemini",
            "claude",
            "copilot",
        )
    )


def test_parser_requires_model():
    parser = build_parser()

    with pytest.raises(
        SystemExit
    ):
        parser.parse_args(
            [
                "--scenario",
                "FIP-CAL-001-001",
            ]
        )


def test_parser_requires_scenario():
    parser = build_parser()

    with pytest.raises(
        SystemExit
    ):
        parser.parse_args(
            [
                "--model",
                "gemini",
            ]
        )


def test_parser_accepts_gemini():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--model",
            "gemini",
            "--scenario",
            "FIP-CAL-001-002",
        ]
    )

    assert (
        args.model
        == "gemini"
    )


def test_parser_accepts_claude():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--model",
            "claude",
            "--scenario",
            "FIP-CAL-001-002",
        ]
    )

    assert (
        args.model
        == "claude"
    )


def test_parser_accepts_copilot():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--model",
            "copilot",
            "--scenario",
            "FIP-CAL-001-002",
        ]
    )

    assert (
        args.model
        == "copilot"
    )


def test_parser_rejects_unknown_model():
    parser = build_parser()

    with pytest.raises(
        SystemExit
    ):
        parser.parse_args(
            [
                "--model",
                "unknown",
                "--scenario",
                "FIP-CAL-001-002",
            ]
        )


def test_normalizes_scenario():
    assert (
        normalize_scenario_id(
            "  FIP-CAL-001-002  "
        )
        ==
        "FIP-CAL-001-002"
    )


def test_rejects_empty_scenario():
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        normalize_scenario_id(
            " "
        )


def test_rejects_non_calibration_scenario():
    with pytest.raises(
        ValueError,
        match="FIP calibration",
    ):
        normalize_scenario_id(
            "customer-assessment"
        )


def test_build_paths_public_scenario():
    result = build_paths(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
        corpus_root=Path(
            "corpus"
        ),
        run_root=Path(
            "runs"
        ),
    )

    assert (
        result.public_scenario_path
        ==
        Path(
            "corpus"
        )
        / "FIP-CAL-001-002"
        / "public_scenario.json"
    )


def test_build_paths_generator_payload():
    result = build_paths(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
        corpus_root=Path(
            "corpus"
        ),
        run_root=Path(
            "runs"
        ),
    )

    assert (
        result.generator_payload_path
        ==
        Path(
            "runs"
        )
        / "gemini"
        / "FIP-CAL-001-002.json"
    )


def test_build_paths_oracle():
    result = build_paths(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
        corpus_root=Path(
            "corpus"
        ),
        run_root=Path(
            "runs"
        ),
    )

    assert (
        result.sealed_oracle_path
        ==
        Path(
            "corpus"
        )
        / "FIP-CAL-001-002"
        / "sealed_oracle.json"
    )


def test_build_paths_database():
    result = build_paths(
        model="claude",
        scenario_id="FIP-CAL-001-003",
        corpus_root=Path(
            "corpus"
        ),
        run_root=Path(
            "runs"
        ),
    )

    assert (
        result.database_path
        ==
        Path(
            "runs"
        )
        / "claude"
        / "FIP-CAL-001-003.sqlite3"
    )


def test_build_paths_freeze():
    result = build_paths(
        model="copilot",
        scenario_id="FIP-CAL-001-004",
        corpus_root=Path(
            "corpus"
        ),
        run_root=Path(
            "runs"
        ),
    )

    assert (
        result.diagnostic_freeze_path
        ==
        Path(
            "runs"
        )
        / "copilot"
        / (
            "FIP-CAL-001-004"
            "-diagnostic-freeze.json"
        )
    )


def test_build_paths_evaluation():
    result = build_paths(
        model="gemini",
        scenario_id="FIP-CAL-001-005",
        corpus_root=Path(
            "corpus"
        ),
        run_root=Path(
            "runs"
        ),
    )

    assert (
        result.evaluation_path
        ==
        Path(
            "runs"
        )
        / "gemini"
        / (
            "FIP-CAL-001-005"
            "-evaluation.json"
        )
    )


def test_context_uses_calibration_tenant():
    result = build_context(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
    )

    assert (
        result.tenant_id
        ==
        "fip-calibration"
    )


def test_context_uses_independent_client():
    result = build_context(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
    )

    assert (
        result.client_id
        ==
        "independent-blind-corpus"
    )


def test_context_uses_calibration_engagement():
    result = build_context(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
    )

    assert (
        result.engagement_id
        ==
        "fip-cal-001"
    )


def test_context_assessment_is_model_specific():
    gemini = build_context(
        model="gemini",
        scenario_id="FIP-CAL-001-002",
    )

    claude = build_context(
        model="claude",
        scenario_id="FIP-CAL-001-002",
    )

    assert (
        gemini.assessment_id
        != claude.assessment_id
    )


def test_context_assessment_contains_scenario():
    result = build_context(
        model="gemini",
        scenario_id="FIP-CAL-001-007",
    )

    assert (
        "fip-cal-001-007"
        in result.assessment_id
    )