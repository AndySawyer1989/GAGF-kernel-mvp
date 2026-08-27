from __future__ import annotations

import pytest

from backend.app.gagf.diagnostic_calibration_blind_evidence import (
    DiagnosticCalibrationBlindEvidenceService,
)
from backend.app.gagf.diagnostic_calibration_blind_evidence_intake_bridge import (
    BLIND_EVIDENCE_INTAKE_BRIDGE_AUTHORITY,
    BlindEvidenceIntakeBridgeError,
    DiagnosticCalibrationBlindEvidenceIntakeBridgeService,
)
from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationDifficulty,
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    DiagnosticCalibrationScenarioService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


def build_public_scenario():
    return (
        DiagnosticCalibrationScenarioService()
        .build(
            scenario_id="FIP-CAL-BRIDGE-001",
            scenario_name="Bridge Test",
            organization=(
                CalibrationOrganizationContext(
                    organization_type="Synthetic",
                    operating_model="Cross-functional",
                    business_domain="Services",
                    team_count=3,
                    actor_count=8,
                    workflow_count=3,
                    observation_days=10,
                )
            ),
            evidence_contract=(
                CalibrationEvidenceGenerationContract(
                    allowed_constraint_categories=(
                        "APPROVAL_DELAYED",
                        "DEPENDENCY_WAIT",
                    ),
                    minimum_event_count=4,
                    maximum_event_count=6,
                    minimum_work_item_count=2,
                    maximum_work_item_count=4,
                    require_multiple_teams=True,
                    require_multiple_lifecycles=True,
                    require_temporal_ordering=True,
                    evidence_quality_floor=0.75,
                    evidence_quality_ceiling=0.98,
                )
            ),
            narrative_seed="Synthetic bridge scenario.",
            planted_primary_conditions=(
                "APPROVAL_DELAYED",
            ),
            planted_secondary_conditions=(
                "DEPENDENCY_WAIT",
            ),
            expected_top_k=2,
            intended_difficulty=(
                CalibrationDifficulty.MODERATE
            ),
            intended_ambiguity="Hidden.",
            oracle_notes="Hidden.",
        )
        .public_scenario
    )


def build_payload():
    public = build_public_scenario()

    return {
        "scenario_id":
            public.scenario_id,

        "public_hash":
            public.public_hash,

        "generator_id":
            "blind-generator",

        "generation_id":
            "generation-001",

        "evidence_records": [
            {
                "event_id":
                    "event-1",

                "event_type":
                    "APPROVAL_DELAYED",

                "occurred_at":
                    "2026-01-01T12:00:00Z",

                "attributes": {
                    "work_item_id":
                        "work-1",

                    "actor_id":
                        "actor-1",

                    "team_id":
                        "team-1",

                    "lifecycle_instance_id":
                        "life-1",

                    "duration_minutes":
                        "15",

                    "evidence_quality":
                        "0.90",
                },
            },

            {
                "event_id":
                    "event-2",

                "event_type":
                    "DEPENDENCY_WAIT",

                "occurred_at":
                    "2026-01-02T12:00:00Z",

                "attributes": {
                    "work_item_id":
                        "work-2",

                    "actor_id":
                        "actor-2",

                    "team_id":
                        "team-2",

                    "lifecycle_instance_id":
                        "life-2",

                    "duration_minutes":
                        "30",

                    "evidence_quality":
                        "0.91",
                },
            },

            {
                "event_id":
                    "event-3",

                "event_type":
                    "APPROVAL_DELAYED",

                "occurred_at":
                    "2026-01-03T12:00:00Z",

                "attributes": {
                    "work_item_id":
                        "work-1",

                    "actor_id":
                        "actor-3",

                    "team_id":
                        "team-1",

                    "lifecycle_instance_id":
                        "life-1",

                    "duration_minutes":
                        "45",

                    "evidence_quality":
                        "0.92",
                },
            },

            {
                "event_id":
                    "event-4",

                "event_type":
                    "APPROVAL_DELAYED",

                "occurred_at":
                    "2026-01-04T12:00:00Z",

                "attributes": {
                    "work_item_id":
                        "work-2",

                    "actor_id":
                        "actor-4",

                    "team_id":
                        "team-2",

                    "lifecycle_instance_id":
                        "life-2",

                    "duration_minutes":
                        "60",

                    "evidence_quality":
                        "0.93",
                },
            },
        ],
    }


def build_evidence():
    public = build_public_scenario()

    return (
        DiagnosticCalibrationBlindEvidenceService()
        .validate(
            public_scenario=public,
            generator_payload=build_payload(),
        )
    )


def build_context():
    return (
        CommercialHierarchyContext(
            tenant_id="calibration-tenant",
            client_id="calibration-client",
            engagement_id="calibration-engagement",
            assessment_id="calibration-assessment",
        )
    )


def ingest():
    return (
        DiagnosticCalibrationBlindEvidenceIntakeBridgeService()
        .ingest(
            context=build_context(),
            evidence=build_evidence(),
        )
    )


def test_bridge_accepts_all_validated_events():
    result = ingest()

    assert result.accepted_count == 4
    assert result.rejected_count == 0
    assert result.valid is True


def test_bridge_preserves_hierarchy():
    result = ingest()

    assert (
        result.hierarchy_key
        ==
        (
            "calibration-tenant/"
            "calibration-client/"
            "calibration-engagement/"
            "calibration-assessment"
        )
    )

    assert (
        result.intake_result.hierarchy_key
        == result.hierarchy_key
    )


def test_bridge_creates_deterministic_source_id():
    result = ingest()

    assert (
        result.source_id
        ==
        (
            "calibration:"
            "FIP-CAL-BRIDGE-001:"
            "blind-generator:"
            "generation-001"
        )
    )


def test_bridge_uses_csv_source():
    result = ingest()

    assert (
        result.intake_result
        .source
        .kind
        .value
        == "csv"
    )


def test_bridge_preserves_event_ids():
    result = ingest()

    assert tuple(
        record.event_id
        for record
        in result.intake_result.accepted_records
    ) == (
        "event-1",
        "event-2",
        "event-3",
        "event-4",
    )


def test_bridge_preserves_event_types():
    result = ingest()

    assert tuple(
        record.event_type
        for record
        in result.intake_result.accepted_records
    ) == (
        "APPROVAL_DELAYED",
        "DEPENDENCY_WAIT",
        "APPROVAL_DELAYED",
        "APPROVAL_DELAYED",
    )


def test_bridge_preserves_attributes():
    result = ingest()

    first = (
        result.intake_result
        .accepted_records[0]
    )

    assert (
        first.attributes[
            "work_item_id"
        ]
        == "work-1"
    )

    assert (
        first.attributes[
            "team_id"
        ]
        == "team-1"
    )

    assert (
        first.attributes[
            "evidence_quality"
        ]
        == "0.90"
    )


def test_bridge_normalizes_timestamp_via_real_intake():
    result = ingest()

    assert (
        result.intake_result
        .accepted_records[0]
        .occurred_at
        .isoformat()
        ==
        "2026-01-01T12:00:00+00:00"
    )


def test_bridge_produces_real_evidence_hashes():
    result = ingest()

    assert all(
        record.evidence_hash
        for record
        in result.intake_result.accepted_records
    )

    assert len(
        {
            record.evidence_hash
            for record
            in result.intake_result.accepted_records
        }
    ) == 4


def test_bridge_intake_hash_is_deterministic():
    first = ingest()
    second = ingest()

    assert (
        first.intake_result.intake_hash
        == second.intake_result.intake_hash
    )


def test_bridge_preserves_blind_evidence_hash():
    evidence = build_evidence()

    result = (
        DiagnosticCalibrationBlindEvidenceIntakeBridgeService()
        .ingest(
            context=build_context(),
            evidence=evidence,
        )
    )

    assert (
        result.evidence_hash
        == evidence.evidence_hash
    )


def test_bridge_uses_calibration_authority():
    result = ingest()

    assert (
        result.authority
        ==
        BLIND_EVIDENCE_INTAKE_BRIDGE_AUTHORITY
    )


def test_bridge_result_exposes_real_intake_hash():
    result = ingest()

    payload = result.to_dict()

    assert (
        payload[
            "intake_hash"
        ]
        ==
        result.intake_result.intake_hash
    )


def test_bridge_requires_engagement_id():
    context = (
        CommercialHierarchyContext(
            tenant_id="tenant",
            client_id="client",
            engagement_id=None,
            assessment_id=None,
        )
    )

    with pytest.raises(
        BlindEvidenceIntakeBridgeError,
        match="engagement_id",
    ):
        (
            DiagnosticCalibrationBlindEvidenceIntakeBridgeService()
            .ingest(
                context=context,
                evidence=build_evidence(),
            )
        )


def test_bridge_requires_assessment_id():
    context = (
        CommercialHierarchyContext(
            tenant_id="tenant",
            client_id="client",
            engagement_id="engagement",
            assessment_id=None,
        )
    )

    with pytest.raises(
        BlindEvidenceIntakeBridgeError,
        match="assessment_id",
    ):
        (
            DiagnosticCalibrationBlindEvidenceIntakeBridgeService()
            .ingest(
                context=context,
                evidence=build_evidence(),
            )
        )


def test_bridge_output_contains_no_oracle_fields():
    payload = ingest().to_dict()

    forbidden = (
        "oracle",
        "expected_conditions",
        "planted_primary_conditions",
        "root_cause",
        "primary_diagnosis",
        "confidence",
    )

    for field in forbidden:
        assert field not in payload