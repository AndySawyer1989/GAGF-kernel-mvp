from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationDifficulty,
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    DiagnosticCalibrationScenarioError,
    DiagnosticCalibrationScenarioService,
)


def build_organization():
    return (
        CalibrationOrganizationContext(
            organization_type=(
                "Synthetic Enterprise"
            ),
            operating_model=(
                "Cross-functional delivery"
            ),
            business_domain=(
                "Professional Services"
            ),
            team_count=4,
            actor_count=18,
            workflow_count=6,
            observation_days=30,
        )
    )


def build_evidence_contract():
    return (
        CalibrationEvidenceGenerationContract(
            allowed_constraint_categories=(
                "APPROVAL_DELAYED",
                "DEPENDENCY_WAIT",
                "WORK_BLOCKED",
                "SECURITY_REVIEW",
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
    )


def build_bundle():
    return (
        DiagnosticCalibrationScenarioService()
        .build(
            scenario_id=(
                "FIP-CAL-001-001"
            ),
            scenario_name=(
                "Approval Friction With "
                "Dependency Competition"
            ),
            organization=(
                build_organization()
            ),
            evidence_contract=(
                build_evidence_contract()
            ),
            narrative_seed=(
                "A synthetic organization experiences "
                "recurring delays across multiple "
                "delivery workflows."
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
                "Dependency waiting should appear "
                "plausible but remain secondary."
            ),
            oracle_notes=(
                "Approval delay is intentionally planted "
                "as the strongest explanatory condition."
            ),
        )
    )


def test_builds_public_scenario():
    bundle = build_bundle()

    assert (
        bundle.public_scenario.scenario_id
        == "FIP-CAL-001-001"
    )

    assert (
        bundle.public_scenario.public_hash
    )


def test_builds_sealed_oracle():
    bundle = build_bundle()

    assert (
        bundle.oracle
        .planted_primary_conditions
        == (
            "APPROVAL_DELAYED",
        )
    )

    assert (
        bundle.oracle.oracle_hash
    )


def test_public_and_oracle_share_public_hash():
    bundle = build_bundle()

    assert (
        bundle.public_scenario.public_hash
        == bundle.oracle.public_hash
    )


def test_public_payload_excludes_oracle_fields():
    service = (
        DiagnosticCalibrationScenarioService()
    )

    payload = (
        service.public_payload(
            bundle=(
                build_bundle()
            )
        )
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

    for field in forbidden:
        assert field not in payload


def test_public_payload_contains_evidence_contract():
    service = (
        DiagnosticCalibrationScenarioService()
    )

    payload = (
        service.public_payload(
            bundle=(
                build_bundle()
            )
        )
    )

    assert (
        "evidence_contract"
        in payload
    )

    assert (
        payload[
            "evidence_contract"
        ][
            "minimum_event_count"
        ]
        == 80
    )


def test_bundle_verifies():
    service = (
        DiagnosticCalibrationScenarioService()
    )

    bundle = build_bundle()

    assert (
        service.verify_bundle(
            bundle=bundle
        )
        is True
    )


def test_public_hash_is_deterministic():
    first = build_bundle()
    second = build_bundle()

    assert (
        first.public_scenario.public_hash
        ==
        second.public_scenario.public_hash
    )


def test_oracle_hash_is_deterministic():
    first = build_bundle()
    second = build_bundle()

    assert (
        first.oracle.oracle_hash
        ==
        second.oracle.oracle_hash
    )


def test_bundle_hash_is_deterministic():
    first = build_bundle()
    second = build_bundle()

    assert (
        first.bundle_hash
        ==
        second.bundle_hash
    )


def test_public_change_changes_public_hash():
    service = (
        DiagnosticCalibrationScenarioService()
    )

    first = build_bundle()

    second = service.build(
        scenario_id=(
            "FIP-CAL-001-001"
        ),
        scenario_name=(
            "Approval Friction With "
            "Dependency Competition"
        ),
        organization=(
            build_organization()
        ),
        evidence_contract=(
            build_evidence_contract()
        ),
        narrative_seed=(
            "A materially different synthetic "
            "organization narrative."
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
            "Dependency waiting should appear "
            "plausible but remain secondary."
        ),
        oracle_notes=(
            "Approval delay remains primary."
        ),
    )

    assert (
        first.public_scenario.public_hash
        !=
        second.public_scenario.public_hash
    )


def test_oracle_change_does_not_change_public_hash():
    service = (
        DiagnosticCalibrationScenarioService()
    )

    first = build_bundle()

    second = service.build(
        scenario_id=(
            "FIP-CAL-001-001"
        ),
        scenario_name=(
            "Approval Friction With "
            "Dependency Competition"
        ),
        organization=(
            build_organization()
        ),
        evidence_contract=(
            build_evidence_contract()
        ),
        narrative_seed=(
            "A synthetic organization experiences "
            "recurring delays across multiple "
            "delivery workflows."
        ),
        planted_primary_conditions=(
            "DEPENDENCY_WAIT",
        ),
        planted_secondary_conditions=(
            "APPROVAL_DELAYED",
            "WORK_BLOCKED",
        ),
        expected_top_k=2,
        intended_difficulty=(
            CalibrationDifficulty.HIGH
        ),
        intended_ambiguity=(
            "Approval delay should appear plausible."
        ),
        oracle_notes=(
            "Dependency waiting is now primary."
        ),
    )

    assert (
        first.public_scenario.public_hash
        ==
        second.public_scenario.public_hash
    )

    assert (
        first.oracle.oracle_hash
        !=
        second.oracle.oracle_hash
    )


def test_rejects_empty_primary_conditions():
    with pytest.raises(
        DiagnosticCalibrationScenarioError,
        match="At least one planted primary",
    ):
        (
            DiagnosticCalibrationScenarioService()
            .build(
                scenario_id="scenario",
                scenario_name="name",
                organization=build_organization(),
                evidence_contract=(
                    build_evidence_contract()
                ),
                narrative_seed="seed",
                planted_primary_conditions=(),
                planted_secondary_conditions=(),
                expected_top_k=1,
                intended_difficulty=(
                    CalibrationDifficulty.LOW
                ),
                intended_ambiguity="ambiguity",
                oracle_notes="notes",
            )
        )


def test_rejects_overlapping_primary_secondary():
    with pytest.raises(
        DiagnosticCalibrationScenarioError,
        match="must be unique",
    ):
        (
            DiagnosticCalibrationScenarioService()
            .build(
                scenario_id="scenario",
                scenario_name="name",
                organization=build_organization(),
                evidence_contract=(
                    build_evidence_contract()
                ),
                narrative_seed="seed",
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                ),
                planted_secondary_conditions=(
                    "APPROVAL_DELAYED",
                ),
                expected_top_k=1,
                intended_difficulty=(
                    CalibrationDifficulty.LOW
                ),
                intended_ambiguity="ambiguity",
                oracle_notes="notes",
            )
        )


def test_rejects_invalid_top_k():
    with pytest.raises(
        DiagnosticCalibrationScenarioError,
        match="expected_top_k",
    ):
        (
            DiagnosticCalibrationScenarioService()
            .build(
                scenario_id="scenario",
                scenario_name="name",
                organization=build_organization(),
                evidence_contract=(
                    build_evidence_contract()
                ),
                narrative_seed="seed",
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                    "DEPENDENCY_WAIT",
                ),
                planted_secondary_conditions=(),
                expected_top_k=1,
                intended_difficulty=(
                    CalibrationDifficulty.HIGH
                ),
                intended_ambiguity="ambiguity",
                oracle_notes="notes",
            )
        )


def test_rejects_invalid_event_range():
    contract = replace(
        build_evidence_contract(),
        minimum_event_count=100,
        maximum_event_count=50,
    )

    with pytest.raises(
        DiagnosticCalibrationScenarioError,
        match="maximum_event_count",
    ):
        (
            DiagnosticCalibrationScenarioService()
            .build(
                scenario_id="scenario",
                scenario_name="name",
                organization=build_organization(),
                evidence_contract=contract,
                narrative_seed="seed",
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                ),
                planted_secondary_conditions=(),
                expected_top_k=1,
                intended_difficulty=(
                    CalibrationDifficulty.LOW
                ),
                intended_ambiguity="ambiguity",
                oracle_notes="notes",
            )
        )


def test_rejects_invalid_quality_bounds():
    contract = replace(
        build_evidence_contract(),
        evidence_quality_floor=0.95,
        evidence_quality_ceiling=0.80,
    )

    with pytest.raises(
        DiagnosticCalibrationScenarioError,
        match="quality bounds",
    ):
        (
            DiagnosticCalibrationScenarioService()
            .build(
                scenario_id="scenario",
                scenario_name="name",
                organization=build_organization(),
                evidence_contract=contract,
                narrative_seed="seed",
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                ),
                planted_secondary_conditions=(),
                expected_top_k=1,
                intended_difficulty=(
                    CalibrationDifficulty.LOW
                ),
                intended_ambiguity="ambiguity",
                oracle_notes="notes",
            )
        )


def test_rejects_duplicate_allowed_categories():
    contract = replace(
        build_evidence_contract(),
        allowed_constraint_categories=(
            "APPROVAL_DELAYED",
            "APPROVAL_DELAYED",
        ),
    )

    with pytest.raises(
        DiagnosticCalibrationScenarioError,
        match="cannot contain duplicates",
    ):
        (
            DiagnosticCalibrationScenarioService()
            .build(
                scenario_id="scenario",
                scenario_name="name",
                organization=build_organization(),
                evidence_contract=contract,
                narrative_seed="seed",
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                ),
                planted_secondary_conditions=(),
                expected_top_k=1,
                intended_difficulty=(
                    CalibrationDifficulty.LOW
                ),
                intended_ambiguity="ambiguity",
                oracle_notes="notes",
            )
        )