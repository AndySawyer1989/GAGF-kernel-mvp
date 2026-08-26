from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_diagnostic_scope import (
    AssessmentDiagnosticScopeSummary,
)
from backend.app.gagf.prelive_blind_assessment import (
    PRELIVE_PROGRAM,
    PRELIVE_SCHEMA_VERSION,
    SUPPORTED_CONSTRAINT_TYPES,
    PreliveScenarioError,
    canonical_sha256,
)


PRELIVE_SYSTEMIC_REPLAY_VERSION = "1.0.0"

PRELIVE_SYSTEMIC_REPLAY_STATUS = (
    "systemic_diagnostic_replayed"
)

PRELIVE_SYSTEMIC_REPLAY_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveSystemicDiagnosticReplayResult:
    hierarchy_key: str

    oracle_sha256: str
    scope_hash: str

    expected_conditions: tuple[
        str,
        ...,
    ]

    systemic_conditions: tuple[
        str,
        ...,
    ]

    true_positives: tuple[
        str,
        ...,
    ]

    false_positives: tuple[
        str,
        ...,
    ]

    false_negatives: tuple[
        str,
        ...,
    ]

    precision: float
    recall: float
    f1: float

    exact_condition_match: bool

    expected_dominant_constraint: (
        str
        | None
    )

    detected_dominant_constraint: (
        str
        | None
    )

    dominant_constraint_match: (
        bool
        | None
    )

    replay_hash: str

    replay_status: str = (
        PRELIVE_SYSTEMIC_REPLAY_STATUS
    )

    authority: str = (
        PRELIVE_SYSTEMIC_REPLAY_AUTHORITY
    )

    replay_version: str = (
        PRELIVE_SYSTEMIC_REPLAY_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "replay_status":
                self.replay_status,
            "authority":
                self.authority,
            "replay_version":
                self.replay_version,
            "hierarchy_key":
                self.hierarchy_key,
            "oracle_sha256":
                self.oracle_sha256,
            "scope_hash":
                self.scope_hash,
            "expected_conditions":
                list(
                    self.expected_conditions
                ),
            "systemic_conditions":
                list(
                    self.systemic_conditions
                ),
            "true_positives":
                list(
                    self.true_positives
                ),
            "false_positives":
                list(
                    self.false_positives
                ),
            "false_negatives":
                list(
                    self.false_negatives
                ),
            "precision":
                self.precision,
            "recall":
                self.recall,
            "f1":
                self.f1,
            "exact_condition_match":
                self.exact_condition_match,
            "expected_dominant_constraint":
                self.expected_dominant_constraint,
            "detected_dominant_constraint":
                self.detected_dominant_constraint,
            "dominant_constraint_match":
                self.dominant_constraint_match,
            "replay_hash":
                self.replay_hash,
        }


class PreliveSystemicDiagnosticReplayScoringService:
    """
    Score systemic diagnostic conditions against a sealed
    PRELIVE oracle.

    This scorer intentionally does not treat localized or
    cross-context friction as false diagnoses.

    It evaluates only the systemic diagnostic layer.

    It does not:
    - execute an assessment,
    - mutate evidence,
    - mutate the assessment repository,
    - authorize an intervention,
    - suppress secondary findings.
    """

    def score(
        self,
        *,
        scope_summary:
            AssessmentDiagnosticScopeSummary,
        oracle:
            Mapping[str, Any],
    ) -> PreliveSystemicDiagnosticReplayResult:
        (
            expected_conditions,
            expected_dominant,
        ) = self._validate_oracle(
            oracle
        )

        self._validate_scope_summary(
            scope_summary
        )

        systemic_conditions = tuple(
            sorted(
                scope_summary
                .systemic_conditions
            )
        )

        expected_set = set(
            expected_conditions
        )

        systemic_set = set(
            systemic_conditions
        )

        true_positives = tuple(
            sorted(
                expected_set
                & systemic_set
            )
        )

        false_positives = tuple(
            sorted(
                systemic_set
                - expected_set
            )
        )

        false_negatives = tuple(
            sorted(
                expected_set
                - systemic_set
            )
        )

        precision = self._precision(
            true_positive_count=(
                len(
                    true_positives
                )
            ),
            false_positive_count=(
                len(
                    false_positives
                )
            ),
        )

        recall = self._recall(
            true_positive_count=(
                len(
                    true_positives
                )
            ),
            false_negative_count=(
                len(
                    false_negatives
                )
            ),
        )

        f1 = self._f1(
            precision=precision,
            recall=recall,
        )

        detected_dominant = (
            scope_summary
            .dominant_systemic_condition
        )

        dominant_match = (
            None
            if expected_dominant
            is None
            else (
                expected_dominant
                == detected_dominant
            )
        )

        oracle_sha256 = canonical_sha256(
            dict(
                oracle
            )
        )

        replay_payload = {
            "hierarchy_key":
                scope_summary
                .hierarchy_key,
            "oracle_sha256":
                oracle_sha256,
            "scope_hash":
                scope_summary
                .scope_hash,
            "expected_conditions":
                list(
                    expected_conditions
                ),
            "systemic_conditions":
                list(
                    systemic_conditions
                ),
            "true_positives":
                list(
                    true_positives
                ),
            "false_positives":
                list(
                    false_positives
                ),
            "false_negatives":
                list(
                    false_negatives
                ),
            "precision":
                precision,
            "recall":
                recall,
            "f1":
                f1,
            "exact_condition_match":
                expected_set
                == systemic_set,
            "expected_dominant_constraint":
                expected_dominant,
            "detected_dominant_constraint":
                detected_dominant,
            "dominant_constraint_match":
                dominant_match,
            "replay_status":
                PRELIVE_SYSTEMIC_REPLAY_STATUS,
            "authority":
                PRELIVE_SYSTEMIC_REPLAY_AUTHORITY,
            "replay_version":
                PRELIVE_SYSTEMIC_REPLAY_VERSION,
        }

        return (
            PreliveSystemicDiagnosticReplayResult(
                hierarchy_key=(
                    scope_summary
                    .hierarchy_key
                ),
                oracle_sha256=(
                    oracle_sha256
                ),
                scope_hash=(
                    scope_summary
                    .scope_hash
                ),
                expected_conditions=(
                    expected_conditions
                ),
                systemic_conditions=(
                    systemic_conditions
                ),
                true_positives=(
                    true_positives
                ),
                false_positives=(
                    false_positives
                ),
                false_negatives=(
                    false_negatives
                ),
                precision=(
                    precision
                ),
                recall=(
                    recall
                ),
                f1=f1,
                exact_condition_match=(
                    expected_set
                    == systemic_set
                ),
                expected_dominant_constraint=(
                    expected_dominant
                ),
                detected_dominant_constraint=(
                    detected_dominant
                ),
                dominant_constraint_match=(
                    dominant_match
                ),
                replay_hash=(
                    canonical_sha256(
                        replay_payload
                    )
                ),
            )
        )

    def _validate_scope_summary(
        self,
        scope_summary:
            AssessmentDiagnosticScopeSummary,
    ) -> None:
        if not isinstance(
            scope_summary,
            AssessmentDiagnosticScopeSummary,
        ):
            raise PreliveScenarioError(
                "PRELIVE systemic replay requires "
                "AssessmentDiagnosticScopeSummary."
            )

        if not scope_summary.hierarchy_key:
            raise PreliveScenarioError(
                "PRELIVE systemic replay requires "
                "a complete hierarchy."
            )

        if (
            not isinstance(
                scope_summary.scope_hash,
                str,
            )
            or len(
                scope_summary.scope_hash
            )
            != 64
        ):
            raise PreliveScenarioError(
                "PRELIVE systemic replay requires "
                "a valid diagnostic scope hash."
            )

        systemic_conditions = (
            scope_summary
            .systemic_conditions
        )

        if (
            len(
                systemic_conditions
            )
            != len(
                set(
                    systemic_conditions
                )
            )
        ):
            raise PreliveScenarioError(
                "Diagnostic scope contains duplicate "
                "systemic conditions."
            )

        for condition in systemic_conditions:
            if (
                condition
                not in
                SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "Diagnostic scope contains an "
                    "unsupported systemic condition."
                )

        dominant = (
            scope_summary
            .dominant_systemic_condition
        )

        if dominant is not None:
            if (
                dominant
                not in
                SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "Diagnostic scope dominant "
                    "systemic condition is invalid."
                )

            if (
                dominant
                not in
                systemic_conditions
            ):
                raise PreliveScenarioError(
                    "Dominant systemic condition "
                    "must also be systemic."
                )

    def _validate_oracle(
        self,
        oracle:
            Mapping[str, Any],
    ) -> tuple[
        tuple[
            str,
            ...,
        ],
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
            oracle.get(
                "schema_version"
            )
            != PRELIVE_SCHEMA_VERSION
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle schema_version "
                f"must equal "
                f"{PRELIVE_SCHEMA_VERSION!r}."
            )

        if (
            oracle.get(
                "test_program"
            )
            != PRELIVE_PROGRAM
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle test_program "
                f"must equal "
                f"{PRELIVE_PROGRAM!r}."
            )

        if (
            oracle.get(
                "oracle_status"
            )
            != "SEALED"
        ):
            raise PreliveScenarioError(
                "PRELIVE systemic replay accepts "
                "only an oracle marked SEALED."
            )

        raw_expected = oracle.get(
            "expected_conditions"
        )

        if (
            not isinstance(
                raw_expected,
                list,
            )
            or not raw_expected
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle requires "
                "expected_conditions."
            )

        expected: list[
            str
        ] = []

        for raw_condition in raw_expected:
            if not isinstance(
                raw_condition,
                Mapping,
            ):
                raise PreliveScenarioError(
                    "PRELIVE expected condition "
                    "must be an object."
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
                not in
                SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle contains an "
                    "unsupported constraint type."
                )

            if (
                constraint_type
                in expected
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle contains duplicate "
                    "expected conditions."
                )

            expected.append(
                constraint_type
            )

        expected_dominant = (
            oracle.get(
                "expected_dominant_constraint"
            )
        )

        if (
            expected_dominant
            is not None
        ):
            if (
                not isinstance(
                    expected_dominant,
                    str,
                )
                or expected_dominant
                not in
                SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle expected dominant "
                    "constraint is invalid."
                )

            if (
                expected_dominant
                not in expected
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle expected dominant "
                    "constraint must also be expected."
                )

        return (
            tuple(
                sorted(
                    expected
                )
            ),
            expected_dominant,
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
        if (
            precision
            + recall
            == 0
        ):
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