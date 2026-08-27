from __future__ import annotations

import json

import pytest

from backend.app.gagf.diagnostic_calibration_corpus_generator import (
    CALIBRATION_CORPUS_MANIFEST_FILENAME,
    DiagnosticCalibrationCorpusGeneratorError,
    DiagnosticCalibrationCorpusGeneratorService,
)


def generate(
    tmp_path,
):
    return (
        DiagnosticCalibrationCorpusGeneratorService()
        .generate_default_corpus(
            corpus_root=(
                tmp_path
                / "corpus"
            )
        )
    )


def test_default_corpus_contains_eight_scenarios(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    assert (
        result.scenario_count
        == 8
    )


def test_default_scenario_ids_are_deterministic(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    assert (
        result.scenario_ids
        == (
            "FIP-CAL-001-001",
            "FIP-CAL-001-002",
            "FIP-CAL-001-003",
            "FIP-CAL-001-004",
            "FIP-CAL-001-005",
            "FIP-CAL-001-006",
            "FIP-CAL-001-007",
            "FIP-CAL-001-008",
        )
    )


def test_each_scenario_has_package_directory(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    for scenario in result.scenarios:
        directory = (
            tmp_path
            / "corpus"
            / scenario.scenario_id
        )

        assert directory.is_dir()

        assert (
            directory
            / "public_scenario.json"
        ).is_file()

        assert (
            directory
            / "sealed_oracle.json"
        ).is_file()

        assert (
            directory
            / "manifest.json"
        ).is_file()


def test_corpus_manifest_is_written(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    path = (
        tmp_path
        / "corpus"
        / CALIBRATION_CORPUS_MANIFEST_FILENAME
    )

    assert path.is_file()

    assert (
        result.manifest_path
        == str(
            path
        )
    )


def test_corpus_hash_is_deterministic(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusGeneratorService()
    )

    root = (
        tmp_path
        / "corpus"
    )

    first = (
        service.generate_default_corpus(
            corpus_root=root
        )
    )

    second = (
        service.generate_default_corpus(
            corpus_root=root
        )
    )

    assert (
        first.corpus_hash
        == second.corpus_hash
    )


def test_second_generation_reuses_scenario_packages(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusGeneratorService()
    )

    root = (
        tmp_path
        / "corpus"
    )

    first = (
        service.generate_default_corpus(
            corpus_root=root
        )
    )

    second = (
        service.generate_default_corpus(
            corpus_root=root
        )
    )

    assert all(
        scenario.reused_existing
        is False
        for scenario
        in first.scenarios
    )

    assert all(
        scenario.reused_existing
        is True
        for scenario
        in second.scenarios
    )


def test_corpus_manifest_ignores_reuse_state(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusGeneratorService()
    )

    root = (
        tmp_path
        / "corpus"
    )

    first = (
        service.generate_default_corpus(
            corpus_root=root
        )
    )

    path = (
        root
        / CALIBRATION_CORPUS_MANIFEST_FILENAME
    )

    first_payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    second = (
        service.generate_default_corpus(
            corpus_root=root
        )
    )

    second_payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        first.corpus_hash
        == second.corpus_hash
    )

    assert (
        first_payload
        == second_payload
    )

    for scenario in (
        second_payload[
            "scenarios"
        ]
    ):
        assert (
            "reused_existing"
            not in scenario
        )


def test_public_scenarios_do_not_expose_oracle_fields(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    forbidden = (
        "planted_primary_conditions",
        "planted_secondary_conditions",
        "expected_top_k",
        "intended_difficulty",
        "intended_ambiguity",
        "oracle_notes",
        "oracle_hash",
    )

    for scenario in result.scenarios:
        path = (
            tmp_path
            / "corpus"
            / scenario.scenario_id
            / "public_scenario.json"
        )

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        for field in forbidden:
            assert field not in payload


def test_oracles_are_present_but_separate(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    for scenario in result.scenarios:
        public_path = (
            tmp_path
            / "corpus"
            / scenario.scenario_id
            / "public_scenario.json"
        )

        oracle_path = (
            tmp_path
            / "corpus"
            / scenario.scenario_id
            / "sealed_oracle.json"
        )

        public_payload = json.loads(
            public_path.read_text(
                encoding="utf-8"
            )
        )

        oracle_payload = json.loads(
            oracle_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            public_payload[
                "public_hash"
            ]
            ==
            oracle_payload[
                "public_hash"
            ]
        )

        assert (
            "planted_primary_conditions"
            not in public_payload
        )

        assert (
            "planted_primary_conditions"
            in oracle_payload
        )


def test_default_corpus_contains_multiple_difficulty_levels(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    difficulties = set()

    for scenario in result.scenarios:
        oracle_path = (
            tmp_path
            / "corpus"
            / scenario.scenario_id
            / "sealed_oracle.json"
        )

        payload = json.loads(
            oracle_path.read_text(
                encoding="utf-8"
            )
        )

        difficulties.add(
            payload[
                "intended_difficulty"
            ]
        )

    assert (
        "LOW"
        in difficulties
    )

    assert (
        "MODERATE"
        in difficulties
    )

    assert (
        "HIGH"
        in difficulties
    )

    assert (
        "ADVERSARIAL"
        in difficulties
    )


def test_default_corpus_contains_dual_primary_scenario(
    tmp_path,
):
    generate(
        tmp_path
    )

    path = (
        tmp_path
        / "corpus"
        / "FIP-CAL-001-008"
        / "sealed_oracle.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload[
            "planted_primary_conditions"
        ]
        == [
            "APPROVAL_DELAYED",
            "DEPENDENCY_WAIT",
        ]
    )


def test_rejects_empty_templates(
    tmp_path,
):
    with pytest.raises(
        DiagnosticCalibrationCorpusGeneratorError,
        match="At least one",
    ):
        (
            DiagnosticCalibrationCorpusGeneratorService()
            .generate(
                corpus_root=(
                    tmp_path
                ),
                corpus_id=(
                    "CORPUS"
                ),
                templates=(),
            )
        )


def test_rejects_duplicate_scenario_ids(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusGeneratorService()
    )

    templates = (
        service.default_templates()
    )

    duplicate = (
        templates[0],
        templates[0],
    )

    with pytest.raises(
        DiagnosticCalibrationCorpusGeneratorError,
        match="duplicate scenario_id",
    ):
        service.generate(
            corpus_root=(
                tmp_path
            ),
            corpus_id=(
                "CORPUS"
            ),
            templates=(
                duplicate
            ),
        )


def test_corpus_authority_is_calibration_only(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    assert (
        result.authority
        == "GAGF_FIP_CALIBRATION_ONLY"
    )


def test_generated_corpus_has_no_confidence_thresholds(
    tmp_path,
):
    result = generate(
        tmp_path
    )

    payload = (
        result.to_dict()
    )

    forbidden = (
        "confidence",
        "confidence_level",
        "threshold",
        "correctness",
        "root_cause",
        "intervention",
    )

    for field in forbidden:
        assert field not in payload