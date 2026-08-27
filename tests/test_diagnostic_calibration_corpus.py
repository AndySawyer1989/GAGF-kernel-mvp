from __future__ import annotations

import json

import pytest

from backend.app.gagf.diagnostic_calibration_corpus import (
    CALIBRATION_MANIFEST_FILENAME,
    PUBLIC_SCENARIO_FILENAME,
    SEALED_ORACLE_FILENAME,
    DiagnosticCalibrationCorpusError,
    DiagnosticCalibrationCorpusService,
)
from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationDifficulty,
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    DiagnosticCalibrationScenarioService,
)


def build_bundle():
    return (
        DiagnosticCalibrationScenarioService()
        .build(
            scenario_id=(
                "FIP-CAL-001-001"
            ),
            scenario_name=(
                "Approval Friction Calibration"
            ),
            organization=(
                CalibrationOrganizationContext(
                    organization_type=(
                        "Synthetic Enterprise"
                    ),
                    operating_model=(
                        "Cross-functional"
                    ),
                    business_domain=(
                        "Professional Services"
                    ),
                    team_count=4,
                    actor_count=18,
                    workflow_count=6,
                    observation_days=30,
                )
            ),
            evidence_contract=(
                CalibrationEvidenceGenerationContract(
                    allowed_constraint_categories=(
                        "APPROVAL_DELAYED",
                        "DEPENDENCY_WAIT",
                        "WORK_BLOCKED",
                    ),
                    minimum_event_count=80,
                    maximum_event_count=160,
                    minimum_work_item_count=20,
                    maximum_work_item_count=60,
                    require_multiple_teams=True,
                    require_multiple_lifecycles=True,
                    require_temporal_ordering=True,
                    evidence_quality_floor=0.75,
                    evidence_quality_ceiling=0.98,
                )
            ),
            narrative_seed=(
                "A synthetic organization experiences "
                "recurring workflow delay."
            ),
            planted_primary_conditions=(
                "APPROVAL_DELAYED",
            ),
            planted_secondary_conditions=(
                "DEPENDENCY_WAIT",
                "WORK_BLOCKED",
            ),
            expected_top_k=2,
            intended_difficulty=(
                CalibrationDifficulty.MODERATE
            ),
            intended_ambiguity=(
                "Dependency waiting competes with "
                "approval delay."
            ),
            oracle_notes=(
                "Approval delay is planted primary."
            ),
        )
    )


def test_writes_three_package_files(
    tmp_path,
):
    result = (
        DiagnosticCalibrationCorpusService()
        .write_bundle(
            bundle=(
                build_bundle()
            ),
            corpus_root=(
                tmp_path
            ),
        )
    )

    directory = (
        tmp_path
        / "FIP-CAL-001-001"
    )

    assert (
        directory
        / PUBLIC_SCENARIO_FILENAME
    ).is_file()

    assert (
        directory
        / SEALED_ORACLE_FILENAME
    ).is_file()

    assert (
        directory
        / CALIBRATION_MANIFEST_FILENAME
    ).is_file()

    assert result.reused_existing is False


def test_public_file_contains_no_oracle_fields(
    tmp_path,
):
    DiagnosticCalibrationCorpusService().write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    payload = json.loads(
        (
            tmp_path
            / "FIP-CAL-001-001"
            / PUBLIC_SCENARIO_FILENAME
        ).read_text(
            encoding="utf-8"
        )
    )

    forbidden = (
        "planted_primary_conditions",
        "planted_secondary_conditions",
        "oracle_hash",
        "oracle_notes",
        "expected_top_k",
    )

    for field in forbidden:
        assert field not in payload


def test_oracle_file_contains_calibration_answer(
    tmp_path,
):
    DiagnosticCalibrationCorpusService().write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    payload = json.loads(
        (
            tmp_path
            / "FIP-CAL-001-001"
            / SEALED_ORACLE_FILENAME
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload[
            "planted_primary_conditions"
        ]
        == [
            "APPROVAL_DELAYED"
        ]
    )


def test_manifest_binds_public_oracle_and_bundle(
    tmp_path,
):
    bundle = build_bundle()

    result = (
        DiagnosticCalibrationCorpusService()
        .write_bundle(
            bundle=bundle,
            corpus_root=tmp_path,
        )
    )

    assert (
        result.manifest.public_hash
        == bundle.public_scenario.public_hash
    )

    assert (
        result.manifest.oracle_hash
        == bundle.oracle.oracle_hash
    )

    assert (
        result.manifest.bundle_hash
        == bundle.bundle_hash
    )


def test_package_verifies(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusService()
    )

    result = service.write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    assert (
        service.verify_package(
            scenario_directory=(
                result.scenario_directory
            )
        )
        is True
    )


def test_second_write_reuses_existing_package(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusService()
    )

    first = service.write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    second = service.write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    assert first.reused_existing is False
    assert second.reused_existing is True

    assert (
        first.manifest.manifest_hash
        == second.manifest.manifest_hash
    )


def test_rejects_different_existing_public_file(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusService()
    )

    result = service.write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    path = (
        tmp_path
        / "FIP-CAL-001-001"
        / PUBLIC_SCENARIO_FILENAME
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "scenario_name"
    ] = "tampered"

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        DiagnosticCalibrationCorpusError,
        match="does not match deterministic content",
    ):
        service.write_bundle(
            bundle=build_bundle(),
            corpus_root=tmp_path,
        )


def test_rejects_partial_existing_package(
    tmp_path,
):
    directory = (
        tmp_path
        / "FIP-CAL-001-001"
    )

    directory.mkdir()

    (
        directory
        / PUBLIC_SCENARIO_FILENAME
    ).write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        DiagnosticCalibrationCorpusError,
        match="partially present",
    ):
        (
            DiagnosticCalibrationCorpusService()
            .write_bundle(
                bundle=build_bundle(),
                corpus_root=tmp_path,
            )
        )


def test_verify_rejects_missing_file(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusService()
    )

    result = service.write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    (
        tmp_path
        / "FIP-CAL-001-001"
        / SEALED_ORACLE_FILENAME
    ).unlink()

    assert (
        service.verify_package(
            scenario_directory=(
                result.scenario_directory
            )
        )
        is False
    )


def test_verify_rejects_manifest_hash_tamper(
    tmp_path,
):
    service = (
        DiagnosticCalibrationCorpusService()
    )

    result = service.write_bundle(
        bundle=build_bundle(),
        corpus_root=tmp_path,
    )

    path = (
        tmp_path
        / "FIP-CAL-001-001"
        / CALIBRATION_MANIFEST_FILENAME
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "manifest_hash"
    ] = "tampered"

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    assert (
        service.verify_package(
            scenario_directory=(
                result.scenario_directory
            )
        )
        is False
    )


def test_result_paths_point_to_scenario_package(
    tmp_path,
):
    result = (
        DiagnosticCalibrationCorpusService()
        .write_bundle(
            bundle=build_bundle(),
            corpus_root=tmp_path,
        )
    )

    assert result.scenario_id == "FIP-CAL-001-001"

    assert result.public_scenario_path.endswith(
        PUBLIC_SCENARIO_FILENAME
    )

    assert result.sealed_oracle_path.endswith(
        SEALED_ORACLE_FILENAME
    )

    assert result.manifest_path.endswith(
        CALIBRATION_MANIFEST_FILENAME
    )