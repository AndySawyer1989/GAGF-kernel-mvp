from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_repository import (
    AssessmentRepositoryError,
    GovernanceAssessmentRepository,
)
from backend.app.gagf.prelive_blind_assessment import (
    PRELIVE_PROGRAM,
    PRELIVE_SCHEMA_VERSION,
    SUPPORTED_CONSTRAINT_TYPES,
    PreliveScenarioError,
    canonical_sha256,
)
from backend.app.gagf.prelive_operator_execution_rehearsal import (
    PreliveOperatorExecutionRehearsalResult,
)
from backend.app.gagf.prelive_rehearsal_result_verification import (
    PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY,
    PRELIVE_REHEARSAL_VERIFICATION_STATUS,
    PreliveRehearsalVerificationResult,
)


PRELIVE_ORACLE_SCORING_VERSION = "1.0.0"

PRELIVE_ORACLE_SCORING_STATUS = (
    "oracle_unsealed_and_scored"
)

PRELIVE_ORACLE_SCORING_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

VALID_FRICTION_BANDS = frozenset(
    {
        "low",
        "moderate",
        "high",
        "severe",
    }
)


@dataclass(frozen=True, slots=True)
class PreliveOracleCondition:
    constraint_type: str
    expected_event_count: int | None = None
    expected_band: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_type":
                self.constraint_type,
            "expected_event_count":
                self.expected_event_count,
            "expected_band":
                self.expected_band,
        }


@dataclass(frozen=True, slots=True)
class PreliveDetectedCondition:
    constraint_type: str
    event_count: int
    unique_work_item_count: int
    friction_score: float
    event_share: float
    band: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_type":
                self.constraint_type,
            "event_count":
                self.event_count,
            "unique_work_item_count":
                self.unique_work_item_count,
            "friction_score":
                self.friction_score,
            "event_share":
                self.event_share,
            "band":
                self.band,
        }


@dataclass(frozen=True, slots=True)
class PreliveOracleScoringResult:
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    oracle_sha256: str
    verification_hash: str

    expected_conditions: tuple[
        PreliveOracleCondition, ...
    ]

    detected_conditions: tuple[
        PreliveDetectedCondition, ...
    ]

    true_positives: tuple[str, ...]
    false_positives: tuple[str, ...]
    false_negatives: tuple[str, ...]

    precision: float
    recall: float
    f1: float

    exact_condition_match: bool

    event_count_accuracy: float | None
    band_accuracy: float | None

    expected_dominant_constraint: str | None
    detected_dominant_constraint: str | None
    dominant_constraint_match: bool | None

    scoring_hash: str

    scoring_status: str = (
        PRELIVE_ORACLE_SCORING_STATUS
    )

    authority: str = (
        PRELIVE_ORACLE_SCORING_AUTHORITY
    )

    scoring_version: str = (
        PRELIVE_ORACLE_SCORING_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scoring_status":
                self.scoring_status,
            "authority":
                self.authority,
            "scoring_version":
                self.scoring_version,
            "scenario_id":
                self.scenario_id,
            "scenario_sha256":
                self.scenario_sha256,
            "hierarchy_key":
                self.hierarchy_key,
            "oracle_sha256":
                self.oracle_sha256,
            "verification_hash":
                self.verification_hash,
            "expected_conditions": [
                condition.to_dict()
                for condition
                in self.expected_conditions
            ],
            "detected_conditions": [
                condition.to_dict()
                for condition
                in self.detected_conditions
            ],
            "true_positives":
                list(self.true_positives),
            "false_positives":
                list(self.false_positives),
            "false_negatives":
                list(self.false_negatives),
            "precision":
                self.precision,
            "recall":
                self.recall,
            "f1":
                self.f1,
            "exact_condition_match":
                self.exact_condition_match,
            "event_count_accuracy":
                self.event_count_accuracy,
            "band_accuracy":
                self.band_accuracy,
            "expected_dominant_constraint": (
                self.expected_dominant_constraint
            ),
            "detected_dominant_constraint": (
                self.detected_dominant_constraint
            ),
            "dominant_constraint_match": (
                self.dominant_constraint_match
            ),
            "scoring_hash":
                self.scoring_hash,
        }


class PreliveOracleScoringService:
    """
    Unseal and score a PRELIVE oracle only after the
    completed blind rehearsal has independently passed
    01K result verification.

    This service does not execute an assessment and does
    not modify persisted assessment artifacts.
    """

    def score(
        self,
        *,
        database_path: str | Path,
        rehearsal_result:
            PreliveOperatorExecutionRehearsalResult,
        verification:
            PreliveRehearsalVerificationResult,
        oracle: Mapping[str, Any],
    ) -> PreliveOracleScoringResult:
        self._validate_rehearsal(
            rehearsal_result
        )

        self._validate_verification(
            rehearsal_result=rehearsal_result,
            verification=verification,
        )

        expected_conditions, expected_dominant = (
            self._validate_oracle(
                rehearsal_result=(
                    rehearsal_result
                ),
                oracle=oracle,
            )
        )

        request = (
            rehearsal_result
            .handoff_bridge
            .request_bridge
            .request
        )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        try:
            if repository.verify_chain(
                context=request.context
            ) is not True:
                raise PreliveScenarioError(
                    "PRELIVE oracle scoring requires "
                    "a valid persisted artifact chain."
                )

            friction_artifacts = (
                repository.list_artifacts(
                    context=request.context,
                    artifact_type=(
                        "friction-summary"
                    ),
                )
            )
        except AssessmentRepositoryError as exc:
            raise PreliveScenarioError(
                "PRELIVE oracle scoring could not "
                f"read persisted assessment data: {exc}"
            ) from exc

        if len(friction_artifacts) != 1:
            raise PreliveScenarioError(
                "PRELIVE oracle scoring requires "
                "exactly one persisted friction-summary."
            )

        friction_payload = (
            friction_artifacts[0].payload
        )

        detected_conditions = (
            self._detected_conditions(
                friction_payload
            )
        )

        detected_dominant = (
            friction_payload.get(
                "dominant_constraint"
            )
        )

        if (
            detected_dominant is not None
            and not isinstance(
                detected_dominant,
                str,
            )
        ):
            raise PreliveScenarioError(
                "Persisted PRELIVE dominant constraint "
                "has an invalid type."
            )

        expected_types = {
            condition.constraint_type
            for condition
            in expected_conditions
        }

        detected_types = {
            condition.constraint_type
            for condition
            in detected_conditions
        }

        true_positives = tuple(
            sorted(
                expected_types
                & detected_types
            )
        )

        false_positives = tuple(
            sorted(
                detected_types
                - expected_types
            )
        )

        false_negatives = tuple(
            sorted(
                expected_types
                - detected_types
            )
        )

        precision = self._precision(
            true_positive_count=(
                len(true_positives)
            ),
            false_positive_count=(
                len(false_positives)
            ),
        )

        recall = self._recall(
            true_positive_count=(
                len(true_positives)
            ),
            false_negative_count=(
                len(false_negatives)
            ),
        )

        f1 = self._f1(
            precision=precision,
            recall=recall,
        )

        event_count_accuracy = (
            self._event_count_accuracy(
                expected_conditions=(
                    expected_conditions
                ),
                detected_conditions=(
                    detected_conditions
                ),
            )
        )

        band_accuracy = self._band_accuracy(
            expected_conditions=(
                expected_conditions
            ),
            detected_conditions=(
                detected_conditions
            ),
        )

        dominant_match = (
            None
            if expected_dominant is None
            else (
                expected_dominant
                == detected_dominant
            )
        )

        bridge_result = (
            rehearsal_result
            .handoff_bridge
            .request_bridge
        )

        oracle_sha256 = canonical_sha256(
            dict(oracle)
        )

        scoring_payload = {
            "scenario_id":
                bridge_result.scenario_id,
            "scenario_sha256":
                bridge_result.scenario_sha256,
            "hierarchy_key":
                request.context.hierarchy_key,
            "oracle_sha256":
                oracle_sha256,
            "verification_hash":
                verification.verification_hash,
            "expected_conditions": [
                condition.to_dict()
                for condition
                in expected_conditions
            ],
            "detected_conditions": [
                condition.to_dict()
                for condition
                in detected_conditions
            ],
            "true_positives":
                list(true_positives),
            "false_positives":
                list(false_positives),
            "false_negatives":
                list(false_negatives),
            "precision":
                precision,
            "recall":
                recall,
            "f1":
                f1,
            "exact_condition_match": (
                expected_types
                == detected_types
            ),
            "event_count_accuracy":
                event_count_accuracy,
            "band_accuracy":
                band_accuracy,
            "expected_dominant_constraint":
                expected_dominant,
            "detected_dominant_constraint":
                detected_dominant,
            "dominant_constraint_match":
                dominant_match,
            "scoring_status":
                PRELIVE_ORACLE_SCORING_STATUS,
            "authority":
                PRELIVE_ORACLE_SCORING_AUTHORITY,
            "scoring_version":
                PRELIVE_ORACLE_SCORING_VERSION,
        }

        return PreliveOracleScoringResult(
            scenario_id=(
                bridge_result.scenario_id
            ),
            scenario_sha256=(
                bridge_result.scenario_sha256
            ),
            hierarchy_key=(
                request.context.hierarchy_key
            ),
            oracle_sha256=oracle_sha256,
            verification_hash=(
                verification.verification_hash
            ),
            expected_conditions=(
                expected_conditions
            ),
            detected_conditions=(
                detected_conditions
            ),
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1=f1,
            exact_condition_match=(
                expected_types
                == detected_types
            ),
            event_count_accuracy=(
                event_count_accuracy
            ),
            band_accuracy=band_accuracy,
            expected_dominant_constraint=(
                expected_dominant
            ),
            detected_dominant_constraint=(
                detected_dominant
            ),
            dominant_constraint_match=(
                dominant_match
            ),
            scoring_hash=canonical_sha256(
                scoring_payload
            ),
        )

    def _validate_rehearsal(
        self,
        rehearsal_result: Any,
    ) -> None:
        if not isinstance(
            rehearsal_result,
            PreliveOperatorExecutionRehearsalResult,
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle scoring requires "
                "a completed operator execution "
                "rehearsal result."
            )

        if (
            rehearsal_result
            .execution_result
            .application_completed
            is not True
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle scoring requires "
                "completed assessment execution."
            )

    def _validate_verification(
        self,
        *,
        rehearsal_result:
            PreliveOperatorExecutionRehearsalResult,
        verification: Any,
    ) -> None:
        if not isinstance(
            verification,
            PreliveRehearsalVerificationResult,
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle scoring requires "
                "an 01K verification receipt."
            )

        if (
            verification.verification_status
            != PRELIVE_REHEARSAL_VERIFICATION_STATUS
            or verification.authority
            != PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY
            or verification.repository_chain_valid
            is not True
            or verification.oracle_leakage_detected
            is not False
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle cannot be unsealed "
                "before blind verification passes."
            )

        request = (
            rehearsal_result
            .handoff_bridge
            .request_bridge
            .request
        )

        if (
            verification.hierarchy_key
            != request.context.hierarchy_key
        ):
            raise PreliveScenarioError(
                "PRELIVE verification hierarchy "
                "does not match the rehearsal."
            )

        if (
            verification.handoff_hash
            != rehearsal_result
            .handoff_bridge
            .handoff
            .handoff_hash
        ):
            raise PreliveScenarioError(
                "PRELIVE verification handoff hash "
                "does not match the rehearsal."
            )

        if (
            verification.request_hash
            != rehearsal_result
            .execution_result
            .assessment_execution_request_hash
        ):
            raise PreliveScenarioError(
                "PRELIVE verification request hash "
                "does not match the rehearsal."
            )

    def _validate_oracle(
        self,
        *,
        rehearsal_result:
            PreliveOperatorExecutionRehearsalResult,
        oracle: Mapping[str, Any],
    ) -> tuple[
        tuple[PreliveOracleCondition, ...],
        str | None,
    ]:
        if not isinstance(
            oracle,
            Mapping,
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle must be an object."
            )

        if (
            oracle.get("schema_version")
            != PRELIVE_SCHEMA_VERSION
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle schema_version "
                f"must equal {PRELIVE_SCHEMA_VERSION!r}."
            )

        if (
            oracle.get("test_program")
            != PRELIVE_PROGRAM
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle test_program "
                f"must equal {PRELIVE_PROGRAM!r}."
            )

        if (
            oracle.get("oracle_status")
            != "SEALED"
        ):
            raise PreliveScenarioError(
                "PRELIVE scoring accepts only an "
                "oracle marked SEALED."
            )

        bridge_result = (
            rehearsal_result
            .handoff_bridge
            .request_bridge
        )

        if (
            oracle.get("scenario_id")
            != bridge_result.scenario_id
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle scenario_id does "
                "not match the blind scenario."
            )

        if (
            oracle.get("scenario_sha256")
            != bridge_result.scenario_sha256
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle scenario SHA-256 "
                "does not match the blind scenario."
            )

        raw_conditions = oracle.get(
            "expected_conditions"
        )

        if (
            not isinstance(
                raw_conditions,
                list,
            )
            or not raw_conditions
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle requires at least "
                "one expected condition."
            )

        conditions: list[
            PreliveOracleCondition
        ] = []

        seen_types: set[str] = set()

        for index, raw_condition in enumerate(
            raw_conditions
        ):
            if not isinstance(
                raw_condition,
                Mapping,
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle expected "
                    f"condition {index} must be "
                    "an object."
                )

            constraint_type = (
                raw_condition.get(
                    "constraint_type"
                )
            )

            if (
                not isinstance(
                    constraint_type,
                    str,
                )
                or constraint_type
                not in SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle contains an "
                    "unsupported constraint type."
                )

            if constraint_type in seen_types:
                raise PreliveScenarioError(
                    "PRELIVE oracle contains "
                    "duplicate expected conditions."
                )

            seen_types.add(
                constraint_type
            )

            expected_event_count = (
                raw_condition.get(
                    "expected_event_count"
                )
            )

            if (
                expected_event_count
                is not None
                and (
                    not isinstance(
                        expected_event_count,
                        int,
                    )
                    or isinstance(
                        expected_event_count,
                        bool,
                    )
                    or expected_event_count < 0
                )
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle expected_event_count "
                    "must be a non-negative integer."
                )

            expected_band = (
                raw_condition.get(
                    "expected_band"
                )
            )

            if (
                expected_band is not None
                and (
                    not isinstance(
                        expected_band,
                        str,
                    )
                    or expected_band
                    not in VALID_FRICTION_BANDS
                )
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle expected_band "
                    "is invalid."
                )

            conditions.append(
                PreliveOracleCondition(
                    constraint_type=(
                        constraint_type
                    ),
                    expected_event_count=(
                        expected_event_count
                    ),
                    expected_band=(
                        expected_band
                    ),
                )
            )

        expected_dominant = oracle.get(
            "expected_dominant_constraint"
        )

        if (
            expected_dominant is not None
            and (
                not isinstance(
                    expected_dominant,
                    str,
                )
                or expected_dominant
                not in SUPPORTED_CONSTRAINT_TYPES
            )
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle expected dominant "
                "constraint is invalid."
            )

        return (
            tuple(
                sorted(
                    conditions,
                    key=lambda item: (
                        item.constraint_type
                    ),
                )
            ),
            expected_dominant,
        )

    def _detected_conditions(
        self,
        friction_payload: Any,
    ) -> tuple[
        PreliveDetectedCondition, ...
    ]:
        if not isinstance(
            friction_payload,
            Mapping,
        ):
            raise PreliveScenarioError(
                "Persisted PRELIVE friction summary "
                "is not an object."
            )

        raw_aggregations = (
            friction_payload.get(
                "constraint_aggregations"
            )
        )

        if not isinstance(
            raw_aggregations,
            list,
        ):
            raise PreliveScenarioError(
                "Persisted PRELIVE friction summary "
                "does not contain constraint "
                "aggregations."
            )

        detected: list[
            PreliveDetectedCondition
        ] = []

        seen_types: set[str] = set()

        for raw in raw_aggregations:
            if not isinstance(
                raw,
                Mapping,
            ):
                raise PreliveScenarioError(
                    "Persisted PRELIVE constraint "
                    "aggregation is invalid."
                )

            constraint_type = raw.get(
                "category"
            )

            if (
                not isinstance(
                    constraint_type,
                    str,
                )
                or constraint_type
                not in SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "Persisted PRELIVE constraint "
                    "aggregation contains an "
                    "unsupported category."
                )

            if constraint_type in seen_types:
                raise PreliveScenarioError(
                    "Persisted PRELIVE friction "
                    "summary contains duplicate "
                    "constraint categories."
                )

            seen_types.add(
                constraint_type
            )

            detected.append(
                PreliveDetectedCondition(
                    constraint_type=(
                        constraint_type
                    ),
                    event_count=int(
                        raw["event_count"]
                    ),
                    unique_work_item_count=int(
                        raw[
                            "unique_work_item_count"
                        ]
                    ),
                    friction_score=float(
                        raw["friction_score"]
                    ),
                    event_share=float(
                        raw["event_share"]
                    ),
                    band=str(
                        raw["band"]
                    ),
                )
            )

        return tuple(
            sorted(
                detected,
                key=lambda item: (
                    item.constraint_type
                ),
            )
        )

    def _precision(
        self,
        *,
        true_positive_count: int,
        false_positive_count: int,
    ) -> float:
        denominator = (
            true_positive_count
            + false_positive_count
        )

        if denominator == 0:
            return 1.0

        return round(
            true_positive_count
            / denominator,
            4,
        )

    def _recall(
        self,
        *,
        true_positive_count: int,
        false_negative_count: int,
    ) -> float:
        denominator = (
            true_positive_count
            + false_negative_count
        )

        if denominator == 0:
            return 1.0

        return round(
            true_positive_count
            / denominator,
            4,
        )

    def _f1(
        self,
        *,
        precision: float,
        recall: float,
    ) -> float:
        if precision + recall == 0:
            return 0.0

        return round(
            (
                2
                * precision
                * recall
            )
            / (
                precision
                + recall
            ),
            4,
        )

    def _event_count_accuracy(
        self,
        *,
        expected_conditions:
            tuple[
                PreliveOracleCondition,
                ...,
            ],
        detected_conditions:
            tuple[
                PreliveDetectedCondition,
                ...,
            ],
    ) -> float | None:
        expected = {
            condition.constraint_type:
                condition.expected_event_count
            for condition
            in expected_conditions
            if (
                condition.expected_event_count
                is not None
            )
        }

        if not expected:
            return None

        detected = {
            condition.constraint_type:
                condition.event_count
            for condition
            in detected_conditions
        }

        matches = sum(
            1
            for constraint_type, count
            in expected.items()
            if (
                detected.get(
                    constraint_type
                )
                == count
            )
        )

        return round(
            matches
            / len(expected),
            4,
        )

    def _band_accuracy(
        self,
        *,
        expected_conditions:
            tuple[
                PreliveOracleCondition,
                ...,
            ],
        detected_conditions:
            tuple[
                PreliveDetectedCondition,
                ...,
            ],
    ) -> float | None:
        expected = {
            condition.constraint_type:
                condition.expected_band
            for condition
            in expected_conditions
            if (
                condition.expected_band
                is not None
            )
        }

        if not expected:
            return None

        detected = {
            condition.constraint_type:
                condition.band
            for condition
            in detected_conditions
        }

        matches = sum(
            1
            for constraint_type, band
            in expected.items()
            if (
                detected.get(
                    constraint_type
                )
                == band
            )
        )

        return round(
            matches
            / len(expected),
            4,
        )