from __future__ import annotations

import csv
import io

import pytest

from backend.app.gagf.diagnostic_calibration_blind_evidence import (
    BLIND_EVIDENCE_GENERATION_AUTHORITY,
    BlindEvidenceGenerationError,
    DiagnosticCalibrationBlindEvidenceService,
)
from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationDifficulty,
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    DiagnosticCalibrationScenarioService,
)


def build_public_scenario():
    bundle = (
        DiagnosticCalibrationScenarioService()
        .build(
            scenario_id="FIP-CAL-TEST-001",
            scenario_name="Blind Evidence Test",
            organization=(
                CalibrationOrganizationContext(
                    organization_type="Synthetic",
                    operating_model="Cross-functional",
                    business_domain="Services",
                    team_count=3,
                    actor_count=12,
                    workflow_count=4,
                    observation_days=10,
                )
            ),
            evidence_contract=(
                CalibrationEvidenceGenerationContract(
                    allowed_constraint_categories=(
                        "APPROVAL_DELAYED",
                        "DEPENDENCY_WAIT",
                        "WORK_BLOCKED",
                    ),
                    minimum_event_count=4,
                    maximum_event_count=8,
                    minimum_work_item_count=2,
                    maximum_work_item_count=4,
                    require_multiple_teams=True,
                    require_multiple_lifecycles=True,
                    require_temporal_ordering=True,
                    evidence_quality_floor=0.75,
                    evidence_quality_ceiling=0.98,
                )
            ),
            narrative_seed=(
                "Synthetic public narrative."
            ),
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
            intended_ambiguity=(
                "Hidden calibration ambiguity."
            ),
            oracle_notes=(
                "Hidden calibration notes."
            ),
        )
    )

    return (
        bundle.public_scenario
    )


def build_record(
    index,
    *,
    event_type="APPROVAL_DELAYED",
    work_item_id=None,
    team_id=None,
    lifecycle_id=None,
    quality="0.90",
    occurred_at=None,
):
    return {
        "event_id":
            f"event-{index}",

        "event_type":
            event_type,

        "occurred_at":
            (
                occurred_at
                or
                (
                    "2026-01-"
                    f"{index:02d}"
                    "T12:00:00Z"
                )
            ),

        "attributes": {
            "work_item_id":
                (
                    work_item_id
                    or
                    f"work-{((index - 1) % 2) + 1}"
                ),

            "actor_id":
                f"actor-{index}",

            "team_id":
                (
                    team_id
                    or
                    f"team-{((index - 1) % 2) + 1}"
                ),

            "lifecycle_instance_id":
                (
                    lifecycle_id
                    or
                    f"life-{((index - 1) % 2) + 1}"
                ),

            "duration_minutes":
                str(
                    index * 15
                ),

            "evidence_quality":
                quality,
        },
    }


def build_payload():
    public = (
        build_public_scenario()
    )

    return {
        "scenario_id":
            public.scenario_id,

        "public_hash":
            public.public_hash,

        "generator_id":
            "external-ai-test",

        "generation_id":
            "generation-001",

        "evidence_records": [
            build_record(1),
            build_record(
                2,
                event_type="DEPENDENCY_WAIT",
            ),
            build_record(
                3,
                event_type="WORK_BLOCKED",
            ),
            build_record(4),
        ],
    }


def validate(
    payload=None,
):
    public = (
        build_public_scenario()
    )

    return (
        DiagnosticCalibrationBlindEvidenceService()
        .validate(
            public_scenario=public,
            generator_payload=(
                payload
                or
                build_payload()
            ),
        )
    )


def test_valid_blind_evidence_is_accepted():
    result = validate()

    assert (
        result.event_count
        == 4
    )

    assert (
        result.generator_id
        == "external-ai-test"
    )


def test_result_binds_public_hash():
    public = (
        build_public_scenario()
    )

    result = validate()

    assert (
        result.public_hash
        == public.public_hash
    )


def test_result_uses_calibration_evidence_authority():
    result = validate()

    assert (
        result.authority
        ==
        BLIND_EVIDENCE_GENERATION_AUTHORITY
    )


def test_hash_is_deterministic():
    first = validate()
    second = validate()

    assert (
        first.evidence_hash
        == second.evidence_hash
    )


def test_timestamp_is_normalized_to_utc():
    result = validate()

    assert (
        result.records[0]
        .occurred_at_iso
        ==
        "2026-01-01T12:00:00+00:00"
    )


def test_rejects_wrong_scenario_id():
    payload = build_payload()

    payload[
        "scenario_id"
    ] = "wrong"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="scenario_id does not match",
    ):
        validate(
            payload
        )


def test_rejects_wrong_public_hash():
    payload = build_payload()

    payload[
        "public_hash"
    ] = "wrong"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="public_hash does not match",
    ):
        validate(
            payload
        )


def test_rejects_too_few_events():
    payload = build_payload()

    payload[
        "evidence_records"
    ] = (
        payload[
            "evidence_records"
        ][:2]
    )

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="event count",
    ):
        validate(
            payload
        )


def test_rejects_too_many_events():
    payload = build_payload()

    payload[
        "evidence_records"
    ] = [
        build_record(
            index
        )
        for index
        in range(
            1,
            10,
        )
    ]

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="event count",
    ):
        validate(
            payload
        )


def test_rejects_duplicate_event_ids():
    payload = build_payload()

    payload[
        "evidence_records"
    ][1][
        "event_id"
    ] = "event-1"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="duplicate event_id",
    ):
        validate(
            payload
        )


def test_rejects_disallowed_event_type():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "event_type"
    ] = "SECURITY_REVIEW"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="not allowed",
    ):
        validate(
            payload
        )


def test_rejects_too_few_work_items():
    payload = build_payload()

    for record in (
        payload[
            "evidence_records"
        ]
    ):
        record[
            "attributes"
        ][
            "work_item_id"
        ] = "one-work-item"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="work-item count",
    ):
        validate(
            payload
        )


def test_rejects_missing_work_item_id():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "attributes"
    ].pop(
        "work_item_id"
    )

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="work_item_id is required",
    ):
        validate(
            payload
        )


def test_rejects_single_team_when_multiple_required():
    payload = build_payload()

    for record in (
        payload[
            "evidence_records"
        ]
    ):
        record[
            "attributes"
        ][
            "team_id"
        ] = "team-1"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="multiple teams",
    ):
        validate(
            payload
        )


def test_rejects_single_lifecycle_when_multiple_required():
    payload = build_payload()

    for record in (
        payload[
            "evidence_records"
        ]
    ):
        record[
            "attributes"
        ][
            "lifecycle_instance_id"
        ] = "life-1"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="multiple lifecycle",
    ):
        validate(
            payload
        )


def test_rejects_missing_evidence_quality():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "attributes"
    ].pop(
        "evidence_quality"
    )

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="evidence_quality is required",
    ):
        validate(
            payload
        )


def test_rejects_non_numeric_evidence_quality():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "attributes"
    ][
        "evidence_quality"
    ] = "excellent"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="must be numeric",
    ):
        validate(
            payload
        )


def test_rejects_evidence_quality_below_floor():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "attributes"
    ][
        "evidence_quality"
    ] = "0.50"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="outside",
    ):
        validate(
            payload
        )


def test_rejects_evidence_quality_above_ceiling():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "attributes"
    ][
        "evidence_quality"
    ] = "1.00"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="outside",
    ):
        validate(
            payload
        )


def test_rejects_timestamp_without_timezone():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "occurred_at"
    ] = "2026-01-01T12:00:00"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="Invalid occurred_at",
    ):
        validate(
            payload
        )


def test_rejects_no_observable_temporal_ordering():
    payload = build_payload()

    for record in (
        payload[
            "evidence_records"
        ]
    ):
        record[
            "occurred_at"
        ] = (
            "2026-01-01T12:00:00Z"
        )

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="temporal ordering",
    ):
        validate(
            payload
        )


@pytest.mark.parametrize(
    "forbidden_field",
    (
        "oracle",
        "oracle_hash",
        "expected_conditions",
        "primary_diagnosis",
        "planted_primary_conditions",
        "root_cause",
        "confidence_target",
    ),
)
def test_rejects_top_level_oracle_shaped_fields(
    forbidden_field,
):
    payload = build_payload()

    payload[
        forbidden_field
    ] = "forbidden"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="forbidden oracle-shaped field",
    ):
        validate(
            payload
        )


def test_rejects_nested_oracle_shaped_field():
    payload = build_payload()

    payload[
        "evidence_records"
    ][0][
        "attributes"
    ][
        "expected_conditions"
    ] = "APPROVAL_DELAYED"

    with pytest.raises(
        BlindEvidenceGenerationError,
        match="forbidden oracle-shaped field",
    ):
        validate(
            payload
        )


def test_generation_payload_contains_only_public_scenario():
    public = (
        build_public_scenario()
    )

    payload = (
        DiagnosticCalibrationBlindEvidenceService()
        .public_generation_payload(
            public_scenario=public
        )
    )

    text = str(
        payload
    )

    assert (
        "planted_primary_conditions"
        not in text
    )

    assert (
        "oracle_notes"
        not in text
    )

    assert (
        "oracle_hash"
        not in text
    )


def test_generation_payload_includes_public_bounds():
    public = (
        build_public_scenario()
    )

    payload = (
        DiagnosticCalibrationBlindEvidenceService()
        .public_generation_payload(
            public_scenario=public
        )
    )

    assert (
        payload[
            "rules"
        ][
            "minimum_event_count"
        ]
        == 4
    )

    assert (
        payload[
            "rules"
        ][
            "maximum_event_count"
        ]
        == 8
    )


def test_to_csv_has_real_fip_required_columns():
    service = (
        DiagnosticCalibrationBlindEvidenceService()
    )

    result = validate()

    csv_text = service.to_csv(
        result=result
    )

    reader = csv.DictReader(
        io.StringIO(
            csv_text
        )
    )

    assert (
        reader.fieldnames[:3]
        == [
            "event_id",
            "event_type",
            "occurred_at",
        ]
    )


def test_to_csv_flattens_attributes():
    service = (
        DiagnosticCalibrationBlindEvidenceService()
    )

    csv_text = service.to_csv(
        result=(
            validate()
        )
    )

    rows = list(
        csv.DictReader(
            io.StringIO(
                csv_text
            )
        )
    )

    assert (
        rows[0][
            "work_item_id"
        ]
        == "work-1"
    )

    assert (
        rows[0][
            "team_id"
        ]
        == "team-1"
    )

    assert (
        rows[0][
            "evidence_quality"
        ]
        == "0.90"
    )


def test_to_csv_is_deterministic():
    service = (
        DiagnosticCalibrationBlindEvidenceService()
    )

    first = service.to_csv(
        result=(
            validate()
        )
    )

    second = service.to_csv(
        result=(
            validate()
        )
    )

    assert (
        first
        == second
    )