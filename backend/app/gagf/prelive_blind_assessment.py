from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


PRELIVE_PROGRAM = "PRELIVE-001"
PRELIVE_SCHEMA_VERSION = "1.0"

SUPPORTED_CONSTRAINT_TYPES = frozenset(
    {
        "APPROVAL_REQUIRED",
        "APPROVAL_DELAYED",
        "APPROVAL_REJECTED",
        "WORK_BLOCKED",
        "DEPENDENCY_WAIT",
        "OWNERSHIP_GAP",
        "SECURITY_REVIEW",
        "ENVIRONMENT_FAILURE",
        "ESCALATION",
        "OVERRIDE",
    }
)

FORBIDDEN_KEYS = frozenset(
    {
        "final_decision",
        "kernel_decision",
        "authorized_intervention",
        "assessment_result",
        "governance_determination",
        "recommended_kernel_action",
        "expected_condition",
        "expected_conditions",
        "expected_result",
        "correct_answer",
        "should_be_detected",
        "ground_truth",
        "oracle",
        "planted_problem",
        "false_positive_test",
    }
)

REQUIRED_EVENT_STRING_FIELDS = (
    "event_id",
    "timestamp",
    "source",
    "source_event_id",
    "tenant_id",
    "lifecycle_instance_id",
    "actor_id",
    "actor_role",
    "team_id",
    "work_item_id",
    "work_item_type",
    "constraint_type",
    "state",
    "previous_state",
)


class PreliveScenarioError(ValueError):
    """Raised when a PRELIVE scenario violates the blind-test contract."""


@dataclass(frozen=True)
class PreliveValidationIssue:
    code: str
    message: str
    event_id: str | None = None
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "event_id": self.event_id,
            "path": self.path,
        }


@dataclass(frozen=True)
class PreliveValidationSummary:
    event_count: int
    source_count: int
    actor_count: int
    team_count: int
    work_item_count: int
    lifecycle_count: int
    start_timestamp: str | None
    end_timestamp: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_count": self.event_count,
            "source_count": self.source_count,
            "actor_count": self.actor_count,
            "team_count": self.team_count,
            "work_item_count": self.work_item_count,
            "lifecycle_count": self.lifecycle_count,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
        }


@dataclass(frozen=True)
class PreliveValidationResult:
    valid: bool
    scenario: dict[str, Any] | None
    issues: tuple[PreliveValidationIssue, ...]
    summary: PreliveValidationSummary
    scenario_sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "scenario": self.scenario,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "summary": self.summary.to_dict(),
            "scenario_sha256": self.scenario_sha256,
        }


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _required_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
    )


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json_bytes(value)
    ).hexdigest()


def _valid_iso_timestamp(value: Any) -> bool:
    if not _required_string(value):
        return False

    candidate = value.strip()

    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False

    return True


def _find_forbidden_keys(
    value: Any,
    *,
    path: str = "$",
) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []

    if isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(
                _find_forbidden_keys(
                    item,
                    path=f"{path}[{index}]",
                )
            )

        return findings

    if not _is_mapping(value):
        return findings

    for raw_key, child in value.items():
        key = str(raw_key)
        normalized = key.strip().lower()
        child_path = f"{path}.{key}"

        if normalized in FORBIDDEN_KEYS:
            findings.append(
                (child_path, normalized)
            )

        findings.extend(
            _find_forbidden_keys(
                child,
                path=child_path,
            )
        )

    return findings


def _empty_summary() -> PreliveValidationSummary:
    return PreliveValidationSummary(
        event_count=0,
        source_count=0,
        actor_count=0,
        team_count=0,
        work_item_count=0,
        lifecycle_count=0,
        start_timestamp=None,
        end_timestamp=None,
    )


def parse_pre_live_scenario_json(
    json_text: str,
) -> PreliveValidationResult:
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return PreliveValidationResult(
            valid=False,
            scenario=None,
            issues=(
                PreliveValidationIssue(
                    code="INVALID_JSON",
                    message=(
                        "The PRELIVE scenario is not valid JSON: "
                        f"{exc.msg}"
                    ),
                ),
            ),
            summary=_empty_summary(),
            scenario_sha256=None,
        )

    return validate_pre_live_scenario(payload)


def validate_pre_live_scenario(
    payload: Any,
) -> PreliveValidationResult:
    issues: list[PreliveValidationIssue] = []

    if not _is_mapping(payload):
        return PreliveValidationResult(
            valid=False,
            scenario=None,
            issues=(
                PreliveValidationIssue(
                    code="INVALID_ROOT",
                    message=(
                        "The PRELIVE scenario root must "
                        "be a JSON object."
                    ),
                ),
            ),
            summary=_empty_summary(),
            scenario_sha256=None,
        )

    scenario = dict(payload)

    for path, key in _find_forbidden_keys(
        scenario
    ):
        issues.append(
            PreliveValidationIssue(
                code="ORACLE_LEAKAGE",
                message=(
                    "Forbidden oracle or governance-authority "
                    f"field detected: {key}"
                ),
                path=path,
            )
        )

    if (
        scenario.get("schema_version")
        != PRELIVE_SCHEMA_VERSION
    ):
        issues.append(
            PreliveValidationIssue(
                code="SCHEMA_VERSION",
                message=(
                    "schema_version must equal "
                    f"{PRELIVE_SCHEMA_VERSION!r}."
                ),
            )
        )

    if (
        scenario.get("test_program")
        != PRELIVE_PROGRAM
    ):
        issues.append(
            PreliveValidationIssue(
                code="TEST_PROGRAM",
                message=(
                    "test_program must equal "
                    f"{PRELIVE_PROGRAM!r}."
                ),
            )
        )

    scenario_id = scenario.get("scenario_id")

    if not _required_string(scenario_id):
        issues.append(
            PreliveValidationIssue(
                code="SCENARIO_ID",
                message="scenario_id is required.",
            )
        )

    generator = scenario.get("generator")

    if not _is_mapping(generator):
        issues.append(
            PreliveValidationIssue(
                code="GENERATOR",
                message="generator must be an object.",
            )
        )
    else:
        if generator.get("type") != "external_ai":
            issues.append(
                PreliveValidationIssue(
                    code="GENERATOR_TYPE",
                    message=(
                        "generator.type must equal "
                        "'external_ai'."
                    ),
                )
            )

        if not _required_string(
            generator.get("model_label")
        ):
            issues.append(
                PreliveValidationIssue(
                    code="GENERATOR_LABEL",
                    message=(
                        "generator.model_label is required."
                    ),
                )
            )

    organization = scenario.get(
        "organization"
    )

    if not _is_mapping(organization):
        issues.append(
            PreliveValidationIssue(
                code="ORGANIZATION",
                message=(
                    "organization must be an object."
                ),
            )
        )
    elif not _required_string(
        organization.get("name")
    ):
        issues.append(
            PreliveValidationIssue(
                code="ORGANIZATION_NAME",
                message=(
                    "organization.name is required."
                ),
            )
        )

    events = scenario.get("events")

    if not isinstance(events, list):
        issues.append(
            PreliveValidationIssue(
                code="EVENTS",
                message="events must be an array.",
            )
        )

        return PreliveValidationResult(
            valid=False,
            scenario=None,
            issues=tuple(issues),
            summary=_empty_summary(),
            scenario_sha256=None,
        )

    if len(events) < 100:
        issues.append(
            PreliveValidationIssue(
                code="EVENT_COUNT_LOW",
                message=(
                    "PRELIVE requires at least "
                    "100 evidence events."
                ),
            )
        )

    if len(events) > 500:
        issues.append(
            PreliveValidationIssue(
                code="EVENT_COUNT_HIGH",
                message=(
                    "PRELIVE accepts no more than "
                    "500 evidence events."
                ),
            )
        )

    event_ids: set[str] = set()
    sources: set[str] = set()
    actors: set[str] = set()
    teams: set[str] = set()
    work_items: set[str] = set()
    lifecycles: set[str] = set()
    timestamps: list[str] = []

    for index, raw_event in enumerate(events):
        if not _is_mapping(raw_event):
            issues.append(
                PreliveValidationIssue(
                    code="INVALID_EVENT",
                    message=(
                        f"events[{index}] must be "
                        "an object."
                    ),
                )
            )
            continue

        event = dict(raw_event)

        raw_event_id = event.get("event_id")

        event_id = (
            raw_event_id.strip()
            if _required_string(raw_event_id)
            else None
        )

        if event_id is None:
            issues.append(
                PreliveValidationIssue(
                    code="EVENT_ID",
                    message=(
                        f"events[{index}].event_id "
                        "is required."
                    ),
                )
            )
        elif event_id in event_ids:
            issues.append(
                PreliveValidationIssue(
                    code="DUPLICATE_EVENT_ID",
                    message=(
                        "Duplicate event_id: "
                        f"{event_id}."
                    ),
                    event_id=event_id,
                )
            )
        else:
            event_ids.add(event_id)

        for field_name in (
            REQUIRED_EVENT_STRING_FIELDS
        ):
            if not _required_string(
                event.get(field_name)
            ):
                issues.append(
                    PreliveValidationIssue(
                        code="REQUIRED_EVENT_FIELD",
                        message=(
                            f"{event_id or f'events[{index}]'} "
                            f"is missing {field_name}."
                        ),
                        event_id=event_id,
                    )
                )

        timestamp = event.get("timestamp")

        if not _valid_iso_timestamp(timestamp):
            issues.append(
                PreliveValidationIssue(
                    code="TIMESTAMP",
                    message=(
                        f"{event_id or f'events[{index}]'} "
                        "has an invalid timestamp."
                    ),
                    event_id=event_id,
                )
            )
        else:
            timestamps.append(
                str(timestamp)
            )

        constraint_type = event.get(
            "constraint_type"
        )

        if (
            not _required_string(
                constraint_type
            )
            or constraint_type
            not in SUPPORTED_CONSTRAINT_TYPES
        ):
            issues.append(
                PreliveValidationIssue(
                    code="CONSTRAINT_TYPE",
                    message=(
                        f"{event_id or f'events[{index}]'} "
                        "has an unsupported "
                        "constraint_type."
                    ),
                    event_id=event_id,
                )
            )

        duration_minutes = event.get(
            "duration_minutes"
        )

        if (
            not isinstance(
                duration_minutes,
                (int, float),
            )
            or isinstance(
                duration_minutes,
                bool,
            )
            or duration_minutes < 0
        ):
            issues.append(
                PreliveValidationIssue(
                    code="DURATION",
                    message=(
                        f"{event_id or f'events[{index}]'} "
                        "has invalid duration_minutes."
                    ),
                    event_id=event_id,
                )
            )

        evidence_quality = event.get(
            "evidence_quality"
        )

        if (
            not isinstance(
                evidence_quality,
                (int, float),
            )
            or isinstance(
                evidence_quality,
                bool,
            )
            or not (
                0.0
                <= float(evidence_quality)
                <= 1.0
            )
        ):
            issues.append(
                PreliveValidationIssue(
                    code="EVIDENCE_QUALITY",
                    message=(
                        f"{event_id or f'events[{index}]'} "
                        "has evidence_quality "
                        "outside 0.0-1.0."
                    ),
                    event_id=event_id,
                )
            )

        metadata = event.get("metadata")

        if not _is_mapping(metadata):
            issues.append(
                PreliveValidationIssue(
                    code="METADATA",
                    message=(
                        f"{event_id or f'events[{index}]'} "
                        "metadata must be an object."
                    ),
                    event_id=event_id,
                )
            )

        if _required_string(
            event.get("source")
        ):
            sources.add(
                str(event["source"])
            )

        if _required_string(
            event.get("actor_id")
        ):
            actors.add(
                str(event["actor_id"])
            )

        if _required_string(
            event.get("team_id")
        ):
            teams.add(
                str(event["team_id"])
            )

        if _required_string(
            event.get("work_item_id")
        ):
            work_items.add(
                str(event["work_item_id"])
            )

        if _required_string(
            event.get(
                "lifecycle_instance_id"
            )
        ):
            lifecycles.add(
                str(
                    event[
                        "lifecycle_instance_id"
                    ]
                )
            )

    timestamps.sort(
        key=lambda value: datetime.fromisoformat(
            value[:-1] + "+00:00"
            if value.endswith("Z")
            else value
        )
    )

    summary = PreliveValidationSummary(
        event_count=len(events),
        source_count=len(sources),
        actor_count=len(actors),
        team_count=len(teams),
        work_item_count=len(work_items),
        lifecycle_count=len(lifecycles),
        start_timestamp=(
            timestamps[0]
            if timestamps
            else None
        ),
        end_timestamp=(
            timestamps[-1]
            if timestamps
            else None
        ),
    )

    valid = not issues

    return PreliveValidationResult(
        valid=valid,
        scenario=scenario if valid else None,
        issues=tuple(issues),
        summary=summary,
        scenario_sha256=(
            canonical_sha256(scenario)
            if valid
            else None
        ),
    )


CSV_COLUMNS = (
    "event_id",
    "event_type",
    "occurred_at",
    "work_item_id",
    "source",
    "source_event_id",
    "lifecycle_instance_id",
    "actor_id",
    "actor_role",
    "team_id",
    "work_item_type",
    "state",
    "previous_state",
    "duration_minutes",
    "evidence_quality",
    "metadata",
)


def scenario_to_governed_csv(
    scenario: Mapping[str, Any],
) -> str:
    validation = validate_pre_live_scenario(
        scenario
    )

    if not validation.valid:
        messages = "; ".join(
            issue.message
            for issue in validation.issues
        )

        raise PreliveScenarioError(
            "Cannot convert invalid PRELIVE "
            f"scenario to CSV: {messages}"
        )

    events = scenario["events"]

    buffer = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_COLUMNS,
        extrasaction="ignore",
        lineterminator="\n",
    )

    writer.writeheader()

    for raw_event in events:
        event = dict(raw_event)

        writer.writerow(
            {
                "event_id":
                    event["event_id"],
                "event_type":
                    event["constraint_type"],
                "occurred_at":
                    event["timestamp"],
                "work_item_id":
                    event["work_item_id"],
                "source":
                    event["source"],
                "source_event_id":
                    event["source_event_id"],
                "lifecycle_instance_id":
                    event[
                        "lifecycle_instance_id"
                    ],
                "actor_id":
                    event["actor_id"],
                "actor_role":
                    event["actor_role"],
                "team_id":
                    event["team_id"],
                "work_item_type":
                    event["work_item_type"],
                "state":
                    event["state"],
                "previous_state":
                    event["previous_state"],
                "duration_minutes":
                    event["duration_minutes"],
                "evidence_quality":
                    event["evidence_quality"],
                "metadata":
                    json.dumps(
                        event["metadata"],
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
            }
        )

    return buffer.getvalue()


def build_pre_live_manifest(
    scenario: Mapping[str, Any],
) -> dict[str, Any]:
    validation = validate_pre_live_scenario(
        scenario
    )

    if not validation.valid:
        raise PreliveScenarioError(
            "Cannot build a manifest for "
            "an invalid PRELIVE scenario."
        )

    generator = scenario["generator"]
    organization = scenario["organization"]

    return {
        "test_program": PRELIVE_PROGRAM,
        "schema_version":
            PRELIVE_SCHEMA_VERSION,
        "scenario_id":
            scenario["scenario_id"],
        "generator":
            generator["model_label"],
        "organization_name":
            organization["name"],
        "event_count":
            validation.summary.event_count,
        "source_count":
            validation.summary.source_count,
        "actor_count":
            validation.summary.actor_count,
        "team_count":
            validation.summary.team_count,
        "work_item_count":
            validation.summary.work_item_count,
        "lifecycle_count":
            validation.summary.lifecycle_count,
        "start_timestamp":
            validation.summary.start_timestamp,
        "end_timestamp":
            validation.summary.end_timestamp,
        "scenario_sha256":
            validation.scenario_sha256,
        "oracle_status": "SEALED",
        "authority": "GAGF_FIP_ONLY",
    }