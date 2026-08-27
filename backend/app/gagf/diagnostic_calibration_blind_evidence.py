from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationPublicScenario,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    canonical_json,
    parse_timestamp,
    sha256_text,
)


BLIND_EVIDENCE_GENERATION_VERSION = "1.0.0"

BLIND_EVIDENCE_GENERATION_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_EVIDENCE_ONLY"
)


FORBIDDEN_ORACLE_FIELD_NAMES = frozenset(
    {
        "oracle",
        "oracle_hash",
        "oracle_notes",
        "sealed_oracle",
        "ground_truth",
        "expected_condition",
        "expected_conditions",
        "expected_diagnosis",
        "expected_top_k",
        "expected_rank",
        "expected_confidence",
        "confidence_target",
        "primary_diagnosis",
        "planted_primary_condition",
        "planted_primary_conditions",
        "planted_secondary_condition",
        "planted_secondary_conditions",
        "intended_difficulty",
        "intended_ambiguity",
        "root_cause",
    }
)


class BlindEvidenceGenerationError(
    ValueError
):
    """
    Raised when externally generated calibration evidence
    violates the public-scenario generation boundary.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class BlindGeneratedEvidenceRecord:
    event_id: str
    event_type: str
    occurred_at: datetime
    attributes: dict[str, str]

    @property
    def occurred_at_iso(
        self,
    ) -> str:
        return (
            self.occurred_at
            .isoformat()
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "event_id":
                self.event_id,

            "event_type":
                self.event_type,

            "occurred_at":
                self.occurred_at_iso,

            "attributes":
                dict(
                    self.attributes
                ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class BlindEvidenceGenerationResult:
    scenario_id: str
    public_hash: str

    generator_id: str
    generation_id: str

    records: tuple[
        BlindGeneratedEvidenceRecord,
        ...,
    ]

    evidence_hash: str

    authority: str = (
        BLIND_EVIDENCE_GENERATION_AUTHORITY
    )

    schema_version: str = (
        BLIND_EVIDENCE_GENERATION_VERSION
    )

    @property
    def event_count(
        self,
    ) -> int:
        return len(
            self.records
        )

    @property
    def event_types(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    record.event_type
                    for record
                    in self.records
                }
            )
        )

    @property
    def work_item_ids(
        self,
    ) -> tuple[str, ...]:
        return self._attribute_values(
            "work_item_id"
        )

    @property
    def team_ids(
        self,
    ) -> tuple[str, ...]:
        return self._attribute_values(
            "team_id"
        )

    @property
    def lifecycle_instance_ids(
        self,
    ) -> tuple[str, ...]:
        return self._attribute_values(
            "lifecycle_instance_id"
        )

    def _attribute_values(
        self,
        field_name: str,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    value
                    for record
                    in self.records
                    for value
                    in (
                        record.attributes.get(
                            field_name
                        ),
                    )
                    if value
                }
            )
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "public_hash":
                self.public_hash,

            "generator_id":
                self.generator_id,

            "generation_id":
                self.generation_id,

            "records": [
                record.to_dict()
                for record
                in self.records
            ],

            "event_count":
                self.event_count,

            "event_types":
                list(
                    self.event_types
                ),

            "work_item_count":
                len(
                    self.work_item_ids
                ),

            "team_count":
                len(
                    self.team_ids
                ),

            "lifecycle_count":
                len(
                    self.lifecycle_instance_ids
                ),

            "evidence_hash":
                self.evidence_hash,

            "authority":
                self.authority,

            "schema_version":
                self.schema_version,
        }


class DiagnosticCalibrationBlindEvidenceService:
    """
    Validate blind calibration evidence generated from a
    public calibration scenario.

    The service intentionally knows only the public scenario.

    It does not accept or inspect:

    - sealed oracle information;
    - planted primary conditions;
    - expected diagnostic rank;
    - expected confidence;
    - root-cause labels.

    Valid output can be serialized directly into the CSV
    format consumed by GovernanceAssessmentEvidenceIntakeService.
    """

    def validate(
        self,
        *,
        public_scenario: CalibrationPublicScenario,
        generator_payload: Mapping[
            str,
            Any,
        ],
    ) -> BlindEvidenceGenerationResult:
        self._reject_forbidden_fields(
            generator_payload
        )

        scenario_id = self._required_text(
            generator_payload,
            "scenario_id",
        )

        public_hash = self._required_text(
            generator_payload,
            "public_hash",
        )

        generator_id = self._required_text(
            generator_payload,
            "generator_id",
        )

        generation_id = self._required_text(
            generator_payload,
            "generation_id",
        )

        if (
            scenario_id
            != public_scenario.scenario_id
        ):
            raise (
                BlindEvidenceGenerationError(
                    "scenario_id does not match "
                    "the public calibration scenario"
                )
            )

        if (
            public_hash
            != public_scenario.public_hash
        ):
            raise (
                BlindEvidenceGenerationError(
                    "public_hash does not match "
                    "the public calibration scenario"
                )
            )

        raw_records = (
            generator_payload.get(
                "evidence_records"
            )
        )

        if (
            not isinstance(
                raw_records,
                Sequence,
            )
            or isinstance(
                raw_records,
                (
                    str,
                    bytes,
                    bytearray,
                ),
            )
        ):
            raise (
                BlindEvidenceGenerationError(
                    "evidence_records must be an array"
                )
            )

        records = tuple(
            self._build_record(
                value=value,
                index=index,
            )
            for index, value
            in enumerate(
                raw_records,
                start=1,
            )
        )

        self._validate_records(
            public_scenario=(
                public_scenario
            ),
            records=(
                records
            ),
        )

        hash_payload = {
            "scenario_id":
                scenario_id,

            "public_hash":
                public_hash,

            "generator_id":
                generator_id,

            "generation_id":
                generation_id,

            "records": [
                record.to_dict()
                for record
                in records
            ],

            "authority":
                BLIND_EVIDENCE_GENERATION_AUTHORITY,

            "schema_version":
                BLIND_EVIDENCE_GENERATION_VERSION,
        }

        evidence_hash = sha256_text(
            canonical_json(
                hash_payload
            )
        )

        return (
            BlindEvidenceGenerationResult(
                scenario_id=(
                    scenario_id
                ),

                public_hash=(
                    public_hash
                ),

                generator_id=(
                    generator_id
                ),

                generation_id=(
                    generation_id
                ),

                records=(
                    records
                ),

                evidence_hash=(
                    evidence_hash
                ),
            )
        )

    def to_csv(
        self,
        *,
        result: (
            BlindEvidenceGenerationResult
        ),
    ) -> str:
        attribute_names = tuple(
            sorted(
                {
                    key
                    for record
                    in result.records
                    for key
                    in record.attributes
                }
            )
        )

        fieldnames = (
            "event_id",
            "event_type",
            "occurred_at",
            *attribute_names,
        )

        buffer = io.StringIO(
            newline=""
        )

        writer = csv.DictWriter(
            buffer,
            fieldnames=fieldnames,
            lineterminator="\n",
        )

        writer.writeheader()

        for record in result.records:
            row: dict[
                str,
                str,
            ] = {
                "event_id":
                    record.event_id,

                "event_type":
                    record.event_type,

                "occurred_at":
                    record.occurred_at_iso,
            }

            for attribute_name in (
                attribute_names
            ):
                row[
                    attribute_name
                ] = (
                    record.attributes.get(
                        attribute_name,
                        "",
                    )
                )

            writer.writerow(
                row
            )

        return (
            buffer.getvalue()
        )

    def public_generation_payload(
        self,
        *,
        public_scenario: (
            CalibrationPublicScenario
        ),
    ) -> dict[str, Any]:
        """
        Build the only scenario payload permitted to be sent
        to an external calibration evidence generator.
        """

        return {
            "scenario":
                public_scenario.to_dict(),

            "required_output": {
                "scenario_id":
                    public_scenario.scenario_id,

                "public_hash":
                    public_scenario.public_hash,

                "generator_id":
                    (
                        "REQUIRED_NON_EMPTY_STRING"
                    ),

                "generation_id":
                    (
                        "REQUIRED_NON_EMPTY_STRING"
                    ),

                "evidence_records": [
                    {
                        "event_id":
                            "UNIQUE_STRING",

                        "event_type":
                            (
                                "ONE_ALLOWED_"
                                "CONSTRAINT_CATEGORY"
                            ),

                        "occurred_at":
                            (
                                "ISO_8601_WITH_TIMEZONE"
                            ),

                        "attributes": {
                            "work_item_id":
                                "STRING",

                            "actor_id":
                                "STRING",

                            "team_id":
                                "STRING",

                            "lifecycle_instance_id":
                                "STRING",

                            "duration_minutes":
                                "NUMERIC_STRING",

                            "evidence_quality":
                                "DECIMAL_STRING_0_TO_1",
                        },
                    }
                ],
            },

            "rules": {
                "oracle_information_forbidden":
                    True,

                "minimum_event_count":
                    (
                        public_scenario
                        .evidence_contract
                        .minimum_event_count
                    ),

                "maximum_event_count":
                    (
                        public_scenario
                        .evidence_contract
                        .maximum_event_count
                    ),

                "minimum_work_item_count":
                    (
                        public_scenario
                        .evidence_contract
                        .minimum_work_item_count
                    ),

                "maximum_work_item_count":
                    (
                        public_scenario
                        .evidence_contract
                        .maximum_work_item_count
                    ),

                "allowed_event_types":
                    list(
                        public_scenario
                        .evidence_contract
                        .allowed_constraint_categories
                    ),

                "require_multiple_teams":
                    (
                        public_scenario
                        .evidence_contract
                        .require_multiple_teams
                    ),

                "require_multiple_lifecycles":
                    (
                        public_scenario
                        .evidence_contract
                        .require_multiple_lifecycles
                    ),

                "require_temporal_ordering":
                    (
                        public_scenario
                        .evidence_contract
                        .require_temporal_ordering
                    ),

                "evidence_quality_floor":
                    (
                        public_scenario
                        .evidence_contract
                        .evidence_quality_floor
                    ),

                "evidence_quality_ceiling":
                    (
                        public_scenario
                        .evidence_contract
                        .evidence_quality_ceiling
                    ),
            },
        }

    def _build_record(
        self,
        *,
        value: Any,
        index: int,
    ) -> BlindGeneratedEvidenceRecord:
        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                BlindEvidenceGenerationError(
                    "Each evidence record must "
                    f"be an object; record {index}"
                )
            )

        self._reject_forbidden_fields(
            value
        )

        event_id = self._required_text(
            value,
            "event_id",
        )

        event_type = self._required_text(
            value,
            "event_type",
        )

        raw_occurred_at = (
            self._required_text(
                value,
                "occurred_at",
            )
        )

        try:
            occurred_at = parse_timestamp(
                raw_occurred_at
            )

        except ValueError as exc:
            raise (
                BlindEvidenceGenerationError(
                    "Invalid occurred_at for "
                    f"event {event_id}: {exc}"
                )
            ) from exc

        raw_attributes = (
            value.get(
                "attributes"
            )
        )

        if not isinstance(
            raw_attributes,
            Mapping,
        ):
            raise (
                BlindEvidenceGenerationError(
                    "attributes must be an object "
                    f"for event {event_id}"
                )
            )

        self._reject_forbidden_fields(
            raw_attributes
        )

        attributes: dict[
            str,
            str,
        ] = {}

        for raw_key, raw_value in (
            raw_attributes.items()
        ):
            if (
                not isinstance(
                    raw_key,
                    str,
                )
                or not raw_key.strip()
            ):
                raise (
                    BlindEvidenceGenerationError(
                        "Attribute names must be "
                        "non-empty strings"
                    )
                )

            key = (
                raw_key.strip()
            )

            if isinstance(
                raw_value,
                bool,
            ):
                normalized_value = (
                    "true"
                    if raw_value
                    else "false"
                )

            elif isinstance(
                raw_value,
                (
                    str,
                    int,
                    float,
                ),
            ):
                normalized_value = str(
                    raw_value
                ).strip()

            else:
                raise (
                    BlindEvidenceGenerationError(
                        "Attribute values must be "
                        "scalar strings or numbers; "
                        f"event {event_id}, field {key}"
                    )
                )

            if normalized_value:
                attributes[
                    key
                ] = normalized_value

        return (
            BlindGeneratedEvidenceRecord(
                event_id=(
                    event_id
                ),

                event_type=(
                    event_type
                ),

                occurred_at=(
                    occurred_at
                ),

                attributes=(
                    attributes
                ),
            )
        )

    def _validate_records(
        self,
        *,
        public_scenario: (
            CalibrationPublicScenario
        ),
        records: tuple[
            BlindGeneratedEvidenceRecord,
            ...,
        ],
    ) -> None:
        contract = (
            public_scenario
            .evidence_contract
        )

        event_count = len(
            records
        )

        if not (
            contract.minimum_event_count
            <= event_count
            <= contract.maximum_event_count
        ):
            raise (
                BlindEvidenceGenerationError(
                    "Generated event count is outside "
                    "the public scenario bounds"
                )
            )

        event_ids = [
            record.event_id
            for record
            in records
        ]

        if (
            len(
                event_ids
            )
            != len(
                set(
                    event_ids
                )
            )
        ):
            raise (
                BlindEvidenceGenerationError(
                    "Generated evidence contains "
                    "duplicate event_id values"
                )
            )

        allowed = set(
            contract
            .allowed_constraint_categories
        )

        for record in records:
            if (
                record.event_type
                not in allowed
            ):
                raise (
                    BlindEvidenceGenerationError(
                        "Generated event_type is not "
                        "allowed by the public scenario: "
                        f"{record.event_type}"
                    )
                )

        work_items = self._required_attribute_set(
            records=records,
            field_name="work_item_id",
        )

        if not (
            contract.minimum_work_item_count
            <= len(
                work_items
            )
            <= contract.maximum_work_item_count
        ):
            raise (
                BlindEvidenceGenerationError(
                    "Generated work-item count is outside "
                    "the public scenario bounds"
                )
            )

        teams = self._required_attribute_set(
            records=records,
            field_name="team_id",
        )

        if (
            contract.require_multiple_teams
            and len(
                teams
            ) < 2
        ):
            raise (
                BlindEvidenceGenerationError(
                    "Public scenario requires evidence "
                    "from multiple teams"
                )
            )

        lifecycles = self._required_attribute_set(
            records=records,
            field_name="lifecycle_instance_id",
        )

        if (
            contract.require_multiple_lifecycles
            and len(
                lifecycles
            ) < 2
        ):
            raise (
                BlindEvidenceGenerationError(
                    "Public scenario requires multiple "
                    "lifecycle_instance_id values"
                )
            )

        for record in records:
            self._validate_evidence_quality(
                record=record,
                floor=(
                    contract
                    .evidence_quality_floor
                ),
                ceiling=(
                    contract
                    .evidence_quality_ceiling
                ),
            )

        if (
            contract.require_temporal_ordering
            and len(
                records
            ) > 1
        ):
            timestamps = [
                record.occurred_at
                for record
                in records
            ]

            if (
                len(
                    set(
                        timestamps
                    )
                ) < 2
            ):
                raise (
                    BlindEvidenceGenerationError(
                        "Public scenario requires "
                        "observable temporal ordering"
                    )
                )

    def _required_attribute_set(
        self,
        *,
        records: tuple[
            BlindGeneratedEvidenceRecord,
            ...,
        ],
        field_name: str,
    ) -> set[str]:
        values: set[
            str
        ] = set()

        for record in records:
            value = (
                record.attributes.get(
                    field_name
                )
            )

            if not value:
                raise (
                    BlindEvidenceGenerationError(
                        f"{field_name} is required "
                        "for every generated event"
                    )
                )

            values.add(
                value
            )

        return values

    def _validate_evidence_quality(
        self,
        *,
        record: (
            BlindGeneratedEvidenceRecord
        ),
        floor: float,
        ceiling: float,
    ) -> None:
        raw_value = (
            record.attributes.get(
                "evidence_quality"
            )
        )

        if not raw_value:
            raise (
                BlindEvidenceGenerationError(
                    "evidence_quality is required "
                    f"for event {record.event_id}"
                )
            )

        try:
            value = float(
                raw_value
            )

        except ValueError as exc:
            raise (
                BlindEvidenceGenerationError(
                    "evidence_quality must be numeric "
                    f"for event {record.event_id}"
                )
            ) from exc

        if not (
            floor
            <= value
            <= ceiling
        ):
            raise (
                BlindEvidenceGenerationError(
                    "evidence_quality is outside "
                    "the public scenario bounds "
                    f"for event {record.event_id}"
                )
            )

    def _reject_forbidden_fields(
        self,
        payload: Any,
    ) -> None:
        if isinstance(
            payload,
            Mapping,
        ):
            for key, value in (
                payload.items()
            ):
                if (
                    isinstance(
                        key,
                        str,
                    )
                    and key.strip().lower()
                    in FORBIDDEN_ORACLE_FIELD_NAMES
                ):
                    raise (
                        BlindEvidenceGenerationError(
                            "Generator payload contains "
                            "forbidden oracle-shaped field: "
                            f"{key}"
                        )
                    )

                self._reject_forbidden_fields(
                    value
                )

        elif isinstance(
            payload,
            Sequence,
        ) and not isinstance(
            payload,
            (
                str,
                bytes,
                bytearray,
            ),
        ):
            for value in payload:
                self._reject_forbidden_fields(
                    value
                )

    def _required_text(
        self,
        payload: Mapping[
            str,
            Any,
        ],
        field_name: str,
    ) -> str:
        value = payload.get(
            field_name
        )

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise (
                BlindEvidenceGenerationError(
                    f"{field_name} must be a "
                    "non-empty string"
                )
            )

        return value.strip()