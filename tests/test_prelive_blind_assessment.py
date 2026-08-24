from __future__ import annotations

import csv
import io
import json

import pytest

from backend.app.gagf.prelive_blind_assessment import (
    PRELIVE_PROGRAM,
    PreliveScenarioError,
    build_pre_live_manifest,
    canonical_sha256,
    parse_pre_live_scenario_json,
    scenario_to_governed_csv,
    validate_pre_live_scenario,
)


def build_scenario(
    *,
    event_count: int = 100,
) -> dict:
    events = []

    for index in range(event_count):
        events.append(
            {
                "event_id":
                    f"evt-{index + 1:04d}",
                "timestamp":
                    (
                        "2026-08-01T"
                        f"{index % 24:02d}:"
                        f"{index % 60:02d}:00Z"
                    ),
                "source":
                    (
                        "workflow"
                        if index % 2 == 0
                        else "security"
                    ),
                "source_event_id":
                    f"source-{index + 1:04d}",
                "tenant_id":
                    "synthetic-tenant",
                "lifecycle_instance_id":
                    f"lifecycle-{index // 5:03d}",
                "actor_id":
                    f"actor-{index % 20:02d}",
                "actor_role":
                    (
                        "operator"
                        if index % 3
                        else "approver"
                    ),
                "team_id":
                    f"team-{index % 5}",
                "work_item_id":
                    f"work-{index:04d}",
                "work_item_type":
                    "ticket",
                "constraint_type":
                    (
                        "APPROVAL_DELAYED"
                        if index % 2 == 0
                        else "WORK_BLOCKED"
                    ),
                "state":
                    "blocked",
                "previous_state":
                    "active",
                "duration_minutes":
                    30 + index,
                "evidence_quality":
                    0.90,
                "metadata":
                    {
                        "priority": "normal",
                        "sequence": index,
                    },
            }
        )

    return {
        "schema_version": "1.0",
        "test_program":
            PRELIVE_PROGRAM,
        "scenario_id":
            "PRELIVE-001-TEST-A",
        "generator": {
            "type": "external_ai",
            "model_label":
                "test-generator",
        },
        "organization": {
            "name":
                "Synthetic Test Organization",
            "industry":
                "technology",
            "employee_count":
                250,
        },
        "actors": [],
        "teams": [],
        "systems": [],
        "events": events,
    }


def test_valid_blind_scenario_passes():
    scenario = build_scenario()

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is True
    assert result.scenario is not None
    assert result.issues == ()

    assert (
        result.summary.event_count
        == 100
    )

    assert (
        result.summary.source_count
        == 2
    )

    assert (
        result.summary.actor_count
        == 20
    )

    assert (
        result.summary.team_count
        == 5
    )

    assert result.scenario_sha256
    assert (
        len(result.scenario_sha256)
        == 64
    )


def test_json_parser_accepts_valid_scenario():
    scenario = build_scenario()

    result = parse_pre_live_scenario_json(
        json.dumps(scenario)
    )

    assert result.valid is True
    assert (
        result.scenario["scenario_id"]
        == "PRELIVE-001-TEST-A"
    )


def test_invalid_json_is_rejected():
    result = parse_pre_live_scenario_json(
        "{not-json"
    )

    assert result.valid is False

    assert any(
        issue.code == "INVALID_JSON"
        for issue in result.issues
    )


def test_expected_conditions_are_rejected():
    scenario = build_scenario()

    scenario["expected_conditions"] = [
        {
            "condition":
                "approval bottleneck",
            "should_be_detected":
                True,
        }
    ]

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "ORACLE_LEAKAGE"
        for issue in result.issues
    )


def test_nested_oracle_is_rejected():
    scenario = build_scenario()

    scenario["organization"][
        "private_test"
    ] = {
        "oracle": {
            "root_cause":
                "approval bottleneck"
        }
    }

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "ORACLE_LEAKAGE"
        for issue in result.issues
    )


def test_ai_kernel_decision_is_rejected():
    scenario = build_scenario()

    scenario["events"][0][
        "kernel_decision"
    ] = "approve"

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "ORACLE_LEAKAGE"
        for issue in result.issues
    )


def test_ai_assessment_result_is_rejected():
    scenario = build_scenario()

    scenario["events"][0][
        "assessment_result"
    ] = {
        "finding": "high friction"
    }

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False


def test_duplicate_event_id_is_rejected():
    scenario = build_scenario()

    scenario["events"][1][
        "event_id"
    ] = scenario["events"][0][
        "event_id"
    ]

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code
        == "DUPLICATE_EVENT_ID"
        for issue in result.issues
    )


def test_unsupported_constraint_is_rejected():
    scenario = build_scenario()

    scenario["events"][0][
        "constraint_type"
    ] = "AI_DISCOVERED_BAD_THING"

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "CONSTRAINT_TYPE"
        for issue in result.issues
    )


def test_bad_evidence_quality_is_rejected():
    scenario = build_scenario()

    scenario["events"][0][
        "evidence_quality"
    ] = 1.1

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code
        == "EVIDENCE_QUALITY"
        for issue in result.issues
    )


def test_negative_duration_is_rejected():
    scenario = build_scenario()

    scenario["events"][0][
        "duration_minutes"
    ] = -1

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "DURATION"
        for issue in result.issues
    )


def test_invalid_timestamp_is_rejected():
    scenario = build_scenario()

    scenario["events"][0][
        "timestamp"
    ] = "not-a-date"

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "TIMESTAMP"
        for issue in result.issues
    )


def test_too_few_events_is_rejected():
    scenario = build_scenario(
        event_count=99
    )

    result = validate_pre_live_scenario(
        scenario
    )

    assert result.valid is False

    assert any(
        issue.code == "EVENT_COUNT_LOW"
        for issue in result.issues
    )


def test_canonical_hash_is_deterministic():
    left = {
        "b": 2,
        "a": 1,
    }

    right = {
        "a": 1,
        "b": 2,
    }

    assert (
        canonical_sha256(left)
        == canonical_sha256(right)
    )


def test_valid_scenario_hash_is_reproducible():
    scenario = build_scenario()

    first = validate_pre_live_scenario(
        scenario
    )

    second = validate_pre_live_scenario(
        json.loads(
            json.dumps(scenario)
        )
    )

    assert (
        first.scenario_sha256
        == second.scenario_sha256
    )


def test_scenario_converts_to_governed_csv():
    scenario = build_scenario()

    csv_text = scenario_to_governed_csv(
        scenario
    )

    reader = csv.DictReader(
        io.StringIO(csv_text)
    )

    rows = list(reader)

    assert len(rows) == 100

    assert rows[0]["event_id"] == (
        "evt-0001"
    )

    assert rows[0]["event_type"] == (
        "APPROVAL_DELAYED"
    )

    assert rows[0]["occurred_at"].endswith(
        "Z"
    )

    assert rows[0]["work_item_id"] == (
        "work-0000"
    )

    assert rows[0]["source"] == (
        "workflow"
    )

    assert rows[0][
        "evidence_quality"
    ] == "0.9"


def test_metadata_survives_csv_conversion():
    scenario = build_scenario()

    csv_text = scenario_to_governed_csv(
        scenario
    )

    rows = list(
        csv.DictReader(
            io.StringIO(csv_text)
        )
    )

    metadata = json.loads(
        rows[0]["metadata"]
    )

    assert metadata == {
        "priority": "normal",
        "sequence": 0,
    }


def test_invalid_scenario_cannot_convert():
    scenario = build_scenario()

    scenario["expected_conditions"] = [
        {
            "correct_answer":
                "approval bottleneck"
        }
    ]

    with pytest.raises(
        PreliveScenarioError
    ):
        scenario_to_governed_csv(
            scenario
        )


def test_manifest_keeps_oracle_sealed():
    scenario = build_scenario()

    manifest = build_pre_live_manifest(
        scenario
    )

    assert manifest[
        "test_program"
    ] == "PRELIVE-001"

    assert manifest[
        "scenario_id"
    ] == "PRELIVE-001-TEST-A"

    assert manifest[
        "generator"
    ] == "test-generator"

    assert manifest[
        "event_count"
    ] == 100

    assert manifest[
        "oracle_status"
    ] == "SEALED"

    assert manifest[
        "authority"
    ] == "GAGF_FIP_ONLY"

    assert len(
        manifest["scenario_sha256"]
    ) == 64


def test_manifest_contains_no_oracle():
    scenario = build_scenario()

    manifest = build_pre_live_manifest(
        scenario
    )

    serialized = json.dumps(
        manifest
    ).lower()

    assert "expected_conditions" not in serialized
    assert "ground_truth" not in serialized
    assert '"oracle":' not in serialized
    assert "kernel_decision" not in serialized