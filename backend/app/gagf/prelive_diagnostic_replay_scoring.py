from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_diagnostic_projection import (
    DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.prelive_blind_assessment import (
    PRELIVE_PROGRAM,
    PRELIVE_SCHEMA_VERSION,
    SUPPORTED_CONSTRAINT_TYPES,
    PreliveScenarioError,
    canonical_sha256,
)


PRELIVE_DIAGNOSTIC_REPLAY_VERSION = "1.0.0"
PRELIVE_DIAGNOSTIC_REPLAY_STATUS = "diagnostic_significance_replayed"
PRELIVE_DIAGNOSTIC_REPLAY_AUTHORITY = "GAGF_FIP_ONLY"


@dataclass(frozen=True, slots=True)
class PreliveDiagnosticReplayResult:
    hierarchy_key: str

    oracle_sha256: str
    diagnostic_summary_hash: str
    diagnostic_artifact_hash: str

    expected_conditions: tuple[str, ...]
    diagnosed_conditions: tuple[str, ...]

    true_positives: tuple[str, ...]
    false_positives: tuple[str, ...]
    false_negatives: tuple[str, ...]

    precision: float
    recall: float
    f1: float
    exact_condition_match: bool

    expected_dominant_constraint: str | None
    detected_dominant_constraint: str | None
    dominant_constraint_match: bool | None

    replay_hash: str

    replay_status: str = PRELIVE_DIAGNOSTIC_REPLAY_STATUS
    authority: str = PRELIVE_DIAGNOSTIC_REPLAY_AUTHORITY
    replay_version: str = PRELIVE_DIAGNOSTIC_REPLAY_VERSION

    def to_dict(self) -> dict[str, Any]:
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
            "diagnostic_summary_hash":
                self.diagnostic_summary_hash,
            "diagnostic_artifact_hash":
                self.diagnostic_artifact_hash,
            "expected_conditions":
                list(self.expected_conditions),
            "diagnosed_conditions":
                list(self.diagnosed_conditions),
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
            "expected_dominant_constraint":
                self.expected_dominant_constraint,
            "detected_dominant_constraint":
                self.detected_dominant_constraint,
            "dominant_constraint_match":
                self.dominant_constraint_match,
            "replay_hash":
                self.replay_hash,
        }


class PreliveDiagnosticReplayScoringService:
    """
    Score a persisted diagnostic-significance projection against
    a previously sealed PRELIVE oracle.

    This is post-hoc benchmark evaluation only.

    It does not:
    - execute an assessment,
    - mutate assessment evidence,
    - authorize intervention,
    - reinterpret OBSERVED or RECURRING categories as diagnoses.
    """

    def score(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
        oracle: Mapping[str, Any],
    ) -> PreliveDiagnosticReplayResult:
        expected_conditions, expected_dominant = (
            self._validate_oracle(
                oracle
            )
        )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise PreliveScenarioError(
                "PRELIVE diagnostic replay requires "
                "a valid repository chain."
            )

        artifacts = repository.list_artifacts(
            context=context,
            artifact_type=(
                DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
            ),
        )

        if len(artifacts) != 1:
            raise PreliveScenarioError(
                "PRELIVE diagnostic replay requires "
                "exactly one diagnostic-significance artifact."
            )

        artifact = artifacts[0]
        payload = artifact.payload

        if not isinstance(
            payload,
            Mapping,
        ):
            raise PreliveScenarioError(
                "Persisted diagnostic-significance artifact "
                "must be an object."
            )

        hierarchy_key = payload.get(
            "hierarchy_key"
        )

        if (
            not isinstance(
                hierarchy_key,
                str,
            )
            or hierarchy_key
            != context.hierarchy_key
        ):
            raise PreliveScenarioError(
                "Diagnostic-significance hierarchy does not "
                "match replay context."
            )

        raw_diagnosed = payload.get(
            "diagnosed_conditions"
        )

        if not isinstance(
            raw_diagnosed,
            list,
        ):
            raise PreliveScenarioError(
                "Diagnostic-significance artifact does not "
                "contain diagnosed_conditions."
            )

        diagnosed_conditions = self._condition_tuple(
            raw_diagnosed,
            label="diagnosed condition",
        )

        detected_dominant = payload.get(
            "dominant_condition"
        )

        if detected_dominant is not None:
            if (
                not isinstance(
                    detected_dominant,
                    str,
                )
                or detected_dominant
                not in SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "Diagnostic-significance dominant condition "
                    "is invalid."
                )

            if (
                detected_dominant
                not in diagnosed_conditions
            ):
                raise PreliveScenarioError(
                    "Diagnostic dominant condition must also "
                    "be a diagnosed condition."
                )

        diagnostic_summary_hash = payload.get(
            "summary_hash"
        )

        if (
            not isinstance(
                diagnostic_summary_hash,
                str,
            )
            or len(
                diagnostic_summary_hash
            )
            != 64
        ):
            raise PreliveScenarioError(
                "Diagnostic-significance summary hash is invalid."
            )

        expected_set = set(
            expected_conditions
        )

        diagnosed_set = set(
            diagnosed_conditions
        )

        true_positives = tuple(
            sorted(
                expected_set
                & diagnosed_set
            )
        )

        false_positives = tuple(
            sorted(
                diagnosed_set
                - expected_set
            )
        )

        false_negatives = tuple(
            sorted(
                expected_set
                - diagnosed_set
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

        dominant_match = (
            None
            if expected_dominant is None
            else (
                expected_dominant
                == detected_dominant
            )
        )

        oracle_sha256 = canonical_sha256(
            dict(oracle)
        )

        replay_payload = {
            "hierarchy_key":
                context.hierarchy_key,
            "oracle_sha256":
                oracle_sha256,
            "diagnostic_summary_hash":
                diagnostic_summary_hash,
            "diagnostic_artifact_hash":
                artifact.artifact_hash,
            "expected_conditions":
                list(expected_conditions),
            "diagnosed_conditions":
                list(diagnosed_conditions),
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
            "exact_condition_match":
                expected_set
                == diagnosed_set,
            "expected_dominant_constraint":
                expected_dominant,
            "detected_dominant_constraint":
                detected_dominant,
            "dominant_constraint_match":
                dominant_match,
            "replay_status":
                PRELIVE_DIAGNOSTIC_REPLAY_STATUS,
            "authority":
                PRELIVE_DIAGNOSTIC_REPLAY_AUTHORITY,
            "replay_version":
                PRELIVE_DIAGNOSTIC_REPLAY_VERSION,
        }

        return PreliveDiagnosticReplayResult(
            hierarchy_key=(
                context.hierarchy_key
            ),
            oracle_sha256=(
                oracle_sha256
            ),
            diagnostic_summary_hash=(
                diagnostic_summary_hash
            ),
            diagnostic_artifact_hash=(
                artifact.artifact_hash
            ),
            expected_conditions=(
                expected_conditions
            ),
            diagnosed_conditions=(
                diagnosed_conditions
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
            precision=precision,
            recall=recall,
            f1=f1,
            exact_condition_match=(
                expected_set
                == diagnosed_set
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
            replay_hash=canonical_sha256(
                replay_payload
            ),
        )

    def _validate_oracle(
        self,
        oracle: Mapping[str, Any],
    ) -> tuple[
        tuple[str, ...],
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
                f"must equal {PRELIVE_SCHEMA_VERSION!r}."
            )

        if (
            oracle.get(
                "test_program"
            )
            != PRELIVE_PROGRAM
        ):
            raise PreliveScenarioError(
                "PRELIVE oracle test_program "
                f"must equal {PRELIVE_PROGRAM!r}."
            )

        if (
            oracle.get(
                "oracle_status"
            )
            != "SEALED"
        ):
            raise PreliveScenarioError(
                "PRELIVE diagnostic replay accepts "
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
                "PRELIVE oracle requires expected_conditions."
            )

        expected: list[str] = []

        for raw_condition in raw_expected:
            if not isinstance(
                raw_condition,
                Mapping,
            ):
                raise PreliveScenarioError(
                    "PRELIVE expected condition must "
                    "be an object."
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

            if constraint_type in expected:
                raise PreliveScenarioError(
                    "PRELIVE oracle contains duplicate "
                    "expected conditions."
                )

            expected.append(
                constraint_type
            )

        expected_dominant = oracle.get(
            "expected_dominant_constraint"
        )

        if expected_dominant is not None:
            if (
                not isinstance(
                    expected_dominant,
                    str,
                )
                or expected_dominant
                not in SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    "PRELIVE oracle expected dominant "
                    "constraint is invalid."
                )

        return (
            tuple(
                sorted(
                    expected
                )
            ),
            expected_dominant,
        )

    def _condition_tuple(
        self,
        values: list[Any],
        *,
        label: str,
    ) -> tuple[str, ...]:
        result: list[str] = []

        for value in values:
            if (
                not isinstance(
                    value,
                    str,
                )
                or value
                not in SUPPORTED_CONSTRAINT_TYPES
            ):
                raise PreliveScenarioError(
                    f"PRELIVE {label} is invalid."
                )

            if value in result:
                raise PreliveScenarioError(
                    f"PRELIVE contains duplicate {label}s."
                )

            result.append(
                value
            )

        return tuple(
            sorted(
                result
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