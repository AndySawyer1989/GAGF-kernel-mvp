from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.gagf.diagnostic_calibration_blind_diagnostic_execution import (
    BlindCalibrationDiagnosticExecutionResult,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    canonical_json,
    sha256_text,
)


CALIBRATION_ORACLE_EVALUATION_VERSION = "1.0.0"

CALIBRATION_ORACLE_EVALUATION_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_EVALUATION_ONLY"
)

PRIMARY_DIAGNOSIS_ARTIFACT_TYPE = (
    "primary-diagnosis-evidence"
)

DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE = (
    "diagnostic-separation-evidence"
)


class CalibrationOracleEvaluationError(
    RuntimeError
):
    """
    Raised when a completed blind diagnostic execution
    cannot be safely evaluated against a sealed oracle.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationOracleEvaluationResult:
    scenario_id: str
    public_hash: str
    oracle_hash: str

    hierarchy_key: str

    ranked_conditions: tuple[str, ...]

    planted_primary_conditions: tuple[str, ...]
    planted_secondary_conditions: tuple[str, ...]

    first_primary_rank: int | None
    reciprocal_rank: float

    rank_1_hit: bool
    top_2_hit: bool
    top_3_hit: bool

    primary_hit_count: int
    all_primary_conditions_ranked: bool

    expected_top_k: int
    expected_top_k_hit: bool

    secondary_hit_count: int

    candidate_count: int

    leading_candidate_category: str | None
    leading_structural_level: str | None
    leading_evidence_quality: float | None

    leading_explanatory_score: float | None
    runner_up_explanatory_score: float | None

    absolute_separation: float | None
    relative_separation: float | None

    primary_diagnosis_summary_hash: str
    diagnostic_separation_summary_hash: str

    execution_evidence_hash: str

    evaluation_hash: str

    authority: str = (
        CALIBRATION_ORACLE_EVALUATION_AUTHORITY
    )

    version: str = (
        CALIBRATION_ORACLE_EVALUATION_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "public_hash":
                self.public_hash,

            "oracle_hash":
                self.oracle_hash,

            "hierarchy_key":
                self.hierarchy_key,

            "ranked_conditions":
                list(
                    self.ranked_conditions
                ),

            "planted_primary_conditions":
                list(
                    self.planted_primary_conditions
                ),

            "planted_secondary_conditions":
                list(
                    self.planted_secondary_conditions
                ),

            "first_primary_rank":
                self.first_primary_rank,

            "reciprocal_rank":
                self.reciprocal_rank,

            "rank_1_hit":
                self.rank_1_hit,

            "top_2_hit":
                self.top_2_hit,

            "top_3_hit":
                self.top_3_hit,

            "primary_hit_count":
                self.primary_hit_count,

            "all_primary_conditions_ranked":
                self.all_primary_conditions_ranked,

            "expected_top_k":
                self.expected_top_k,

            "expected_top_k_hit":
                self.expected_top_k_hit,

            "secondary_hit_count":
                self.secondary_hit_count,

            "candidate_count":
                self.candidate_count,

            "leading_candidate_category":
                self.leading_candidate_category,

            "leading_structural_level":
                self.leading_structural_level,

            "leading_evidence_quality":
                self.leading_evidence_quality,

            "leading_explanatory_score":
                self.leading_explanatory_score,

            "runner_up_explanatory_score":
                self.runner_up_explanatory_score,

            "absolute_separation":
                self.absolute_separation,

            "relative_separation":
                self.relative_separation,

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary_hash,

            "diagnostic_separation_summary_hash":
                self.diagnostic_separation_summary_hash,

            "execution_evidence_hash":
                self.execution_evidence_hash,

            "evaluation_hash":
                self.evaluation_hash,

            "authority":
                self.authority,

            "version":
                self.version,
        }


class DiagnosticCalibrationOracleEvaluationService:
    """
    Compare a completed blind calibration execution with
    its separately sealed oracle.

    Constitutional boundary:

    Evaluation happens only after diagnostic execution.

    The oracle may score the completed execution.

    The oracle may not:

    - alter evidence;
    - alter ranking;
    - alter structural importance;
    - alter diagnostic separation;
    - create confidence;
    - establish causation;
    - establish root cause;
    - authorize intervention.

    Rank metrics use the first planted-primary condition
    encountered in the frozen FIP ranking.

    MRR semantics:

        reciprocal_rank = 1 / first_primary_rank

    when a planted primary is present, otherwise 0.
    """

    def evaluate(
        self,
        *,
        execution: (
            BlindCalibrationDiagnosticExecutionResult
        ),
        oracle: Mapping[str, Any],
    ) -> CalibrationOracleEvaluationResult:
        if (
            execution.application_completed
            is not True
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Oracle evaluation requires a "
                    "completed blind diagnostic execution."
                )
            )

        if (
            execution.repository_chain_valid
            is not True
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Oracle evaluation requires a valid "
                    "assessment repository chain."
                )
            )

        oracle_payload = dict(
            oracle
        )

        scenario_id = self._required_text(
            oracle_payload,
            "scenario_id",
        )

        public_hash = self._required_text(
            oracle_payload,
            "public_hash",
        )

        oracle_hash = self._required_text(
            oracle_payload,
            "oracle_hash",
        )

        if (
            scenario_id
            != execution.scenario_id
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Oracle scenario_id does not match "
                    "blind execution."
                )
            )

        if (
            public_hash
            != execution.public_hash
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Oracle public_hash does not match "
                    "blind execution."
                )
            )

        planted_primary = (
            self._required_string_tuple(
                oracle_payload,
                "planted_primary_conditions",
            )
        )

        planted_secondary = (
            self._required_string_tuple(
                oracle_payload,
                "planted_secondary_conditions",
                allow_empty=True,
            )
        )

        expected_top_k = (
            self._required_positive_int(
                oracle_payload,
                "expected_top_k",
            )
        )

        context = (
            self._context_from_hierarchy(
                execution.hierarchy_key
            )
        )

        repository = (
            GovernanceAssessmentRepository(
                execution.database_path
            )
        )

        if (
            repository.verify_chain(
                context=context
            )
            is not True
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Assessment repository chain is invalid "
                    "at oracle evaluation time."
                )
            )

        primary_artifact = (
            self._require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    PRIMARY_DIAGNOSIS_ARTIFACT_TYPE
                ),
            )
        )

        separation_artifact = (
            self._require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE
                ),
            )
        )

        primary_payload = (
            self._required_mapping_payload(
                primary_artifact.payload,
                PRIMARY_DIAGNOSIS_ARTIFACT_TYPE,
            )
        )

        separation_payload = (
            self._required_mapping_payload(
                separation_artifact.payload,
                DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE,
            )
        )

        primary_summary_hash = (
            self._required_text(
                primary_payload,
                "summary_hash",
            )
        )

        separation_summary_hash = (
            self._required_text(
                separation_payload,
                "summary_hash",
            )
        )

        separation_primary_hash = (
            self._required_text(
                separation_payload,
                "primary_diagnosis_summary_hash",
            )
        )

        if (
            separation_primary_hash
            != primary_summary_hash
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Diagnostic separation is not bound "
                    "to the persisted primary diagnosis "
                    "summary."
                )
            )

        if (
            primary_summary_hash
            != execution
            .primary_diagnosis_summary_hash
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Execution primary diagnosis hash does "
                    "not match persisted evaluation input."
                )
            )

        if (
            separation_summary_hash
            != execution
            .separation_summary_hash
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Execution separation hash does not "
                    "match persisted evaluation input."
                )
            )

        ranked_conditions = (
            self._ranked_conditions(
                primary_payload
            )
        )

        conditions = (
            self._condition_payloads(
                primary_payload
            )
        )

        candidate_count = len(
            ranked_conditions
        )

        first_primary_rank = (
            self._first_relevant_rank(
                ranked_conditions=(
                    ranked_conditions
                ),
                relevant_conditions=(
                    planted_primary
                ),
            )
        )

        reciprocal_rank = (
            round(
                1.0
                / float(
                    first_primary_rank
                ),
                6,
            )
            if first_primary_rank
            is not None
            else 0.0
        )

        rank_1_hit = (
            first_primary_rank
            == 1
        )

        top_2_hit = (
            first_primary_rank
            is not None
            and first_primary_rank <= 2
        )

        top_3_hit = (
            first_primary_rank
            is not None
            and first_primary_rank <= 3
        )

        primary_hit_count = len(
            set(
                ranked_conditions
            ).intersection(
                planted_primary
            )
        )

        all_primary_ranked = (
            primary_hit_count
            == len(
                set(
                    planted_primary
                )
            )
        )

        expected_top_k_hit = (
            first_primary_rank
            is not None
            and first_primary_rank
            <= expected_top_k
        )

        secondary_hit_count = len(
            set(
                ranked_conditions
            ).intersection(
                planted_secondary
            )
        )

        leading = (
            conditions[0]
            if conditions
            else None
        )

        runner_up = (
            conditions[1]
            if len(
                conditions
            ) >= 2
            else None
        )

        leading_category = (
            self._optional_text(
                leading,
                "category",
            )
            if leading
            is not None
            else None
        )

        leading_structural_level = (
            self._optional_text(
                leading,
                "structural_level",
            )
            if leading
            is not None
            else None
        )

        leading_evidence_quality = (
            self._optional_float(
                leading,
                "evidence_quality",
            )
            if leading
            is not None
            else None
        )

        leading_score = (
            self._explanatory_score(
                leading
            )
            if leading
            is not None
            else None
        )

        runner_up_score = (
            self._explanatory_score(
                runner_up
            )
            if runner_up
            is not None
            else None
        )

        absolute_separation = (
            self._absolute_separation(
                leading_score,
                runner_up_score,
            )
        )

        relative_separation = (
            self._relative_separation(
                leading_score,
                absolute_separation,
            )
        )

        evaluation_payload = {
            "scenario_id":
                scenario_id,

            "public_hash":
                public_hash,

            "oracle_hash":
                oracle_hash,

            "hierarchy_key":
                execution.hierarchy_key,

            "ranked_conditions":
                list(
                    ranked_conditions
                ),

            "planted_primary_conditions":
                list(
                    planted_primary
                ),

            "planted_secondary_conditions":
                list(
                    planted_secondary
                ),

            "first_primary_rank":
                first_primary_rank,

            "reciprocal_rank":
                reciprocal_rank,

            "rank_1_hit":
                rank_1_hit,

            "top_2_hit":
                top_2_hit,

            "top_3_hit":
                top_3_hit,

            "primary_hit_count":
                primary_hit_count,

            "all_primary_conditions_ranked":
                all_primary_ranked,

            "expected_top_k":
                expected_top_k,

            "expected_top_k_hit":
                expected_top_k_hit,

            "secondary_hit_count":
                secondary_hit_count,

            "candidate_count":
                candidate_count,

            "leading_candidate_category":
                leading_category,

            "leading_structural_level":
                leading_structural_level,

            "leading_evidence_quality":
                leading_evidence_quality,

            "leading_explanatory_score":
                leading_score,

            "runner_up_explanatory_score":
                runner_up_score,

            "absolute_separation":
                absolute_separation,

            "relative_separation":
                relative_separation,

            "primary_diagnosis_summary_hash":
                primary_summary_hash,

            "diagnostic_separation_summary_hash":
                separation_summary_hash,

            "execution_evidence_hash":
                execution
                .blind_evidence_hash,

            "authority":
                CALIBRATION_ORACLE_EVALUATION_AUTHORITY,

            "version":
                CALIBRATION_ORACLE_EVALUATION_VERSION,
        }

        evaluation_hash = sha256_text(
            canonical_json(
                evaluation_payload
            )
        )

        return (
            CalibrationOracleEvaluationResult(
                scenario_id=(
                    scenario_id
                ),

                public_hash=(
                    public_hash
                ),

                oracle_hash=(
                    oracle_hash
                ),

                hierarchy_key=(
                    execution.hierarchy_key
                ),

                ranked_conditions=(
                    ranked_conditions
                ),

                planted_primary_conditions=(
                    planted_primary
                ),

                planted_secondary_conditions=(
                    planted_secondary
                ),

                first_primary_rank=(
                    first_primary_rank
                ),

                reciprocal_rank=(
                    reciprocal_rank
                ),

                rank_1_hit=(
                    rank_1_hit
                ),

                top_2_hit=(
                    top_2_hit
                ),

                top_3_hit=(
                    top_3_hit
                ),

                primary_hit_count=(
                    primary_hit_count
                ),

                all_primary_conditions_ranked=(
                    all_primary_ranked
                ),

                expected_top_k=(
                    expected_top_k
                ),

                expected_top_k_hit=(
                    expected_top_k_hit
                ),

                secondary_hit_count=(
                    secondary_hit_count
                ),

                candidate_count=(
                    candidate_count
                ),

                leading_candidate_category=(
                    leading_category
                ),

                leading_structural_level=(
                    leading_structural_level
                ),

                leading_evidence_quality=(
                    leading_evidence_quality
                ),

                leading_explanatory_score=(
                    leading_score
                ),

                runner_up_explanatory_score=(
                    runner_up_score
                ),

                absolute_separation=(
                    absolute_separation
                ),

                relative_separation=(
                    relative_separation
                ),

                primary_diagnosis_summary_hash=(
                    primary_summary_hash
                ),

                diagnostic_separation_summary_hash=(
                    separation_summary_hash
                ),

                execution_evidence_hash=(
                    execution
                    .blind_evidence_hash
                ),

                evaluation_hash=(
                    evaluation_hash
                ),
            )
        )

    def _require_single_artifact(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        artifact_type: str,
    ):
        artifacts = (
            repository.list_artifacts(
                context=context,
                artifact_type=(
                    artifact_type
                ),
            )
        )

        if len(
            artifacts
        ) != 1:
            raise (
                CalibrationOracleEvaluationError(
                    "Oracle evaluation requires exactly "
                    f"one {artifact_type} artifact."
                )
            )

        return artifacts[0]

    def _context_from_hierarchy(
        self,
        hierarchy_key: str,
    ) -> CommercialHierarchyContext:
        parts = hierarchy_key.split(
            "/"
        )

        if len(
            parts
        ) != 4:
            raise (
                CalibrationOracleEvaluationError(
                    "Blind execution hierarchy_key must "
                    "contain exactly four hierarchy levels."
                )
            )

        return (
            CommercialHierarchyContext(
                tenant_id=parts[0],
                client_id=parts[1],
                engagement_id=parts[2],
                assessment_id=parts[3],
            )
        )

    def _ranked_conditions(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[str, ...]:
        value = payload.get(
            "ranked_conditions"
        )

        if not isinstance(
            value,
            list,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Persisted primary diagnosis is missing "
                    "ranked_conditions."
                )
            )

        result = tuple(
            self._normalize_text(
                item,
                "ranked condition",
            )
            for item
            in value
        )

        if not result:
            raise (
                CalibrationOracleEvaluationError(
                    "Persisted primary diagnosis contains "
                    "no ranked conditions."
                )
            )

        if len(
            result
        ) != len(
            set(
                result
            )
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Persisted primary diagnosis contains "
                    "duplicate ranked conditions."
                )
            )

        return result

    def _condition_payloads(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[
        Mapping[str, Any],
        ...,
    ]:
        raw = payload.get(
            "conditions"
        )

        if not isinstance(
            raw,
            list,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Persisted primary diagnosis is missing "
                    "condition evidence."
                )
            )

        normalized = []

        for item in raw:
            if not isinstance(
                item,
                Mapping,
            ):
                raise (
                    CalibrationOracleEvaluationError(
                        "Primary diagnosis condition evidence "
                        "must be an object."
                    )
                )

            normalized.append(
                item
            )

        ordered = tuple(
            sorted(
                normalized,
                key=lambda item: (
                    self._required_rank(
                        item
                    )
                ),
            )
        )

        return ordered

    def _first_relevant_rank(
        self,
        *,
        ranked_conditions: tuple[str, ...],
        relevant_conditions: tuple[str, ...],
    ) -> int | None:
        relevant = set(
            relevant_conditions
        )

        for index, condition in enumerate(
            ranked_conditions,
            start=1,
        ):
            if condition in relevant:
                return index

        return None

    def _explanatory_score(
        self,
        condition: Mapping[str, Any],
    ) -> float:
        axes = condition.get(
            "axes"
        )

        if not isinstance(
            axes,
            Mapping,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Primary diagnosis condition is missing "
                    "explanatory axes."
                )
            )

        value = axes.get(
            "explanatory_score"
        )

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Primary diagnosis explanatory_score "
                    "must be numeric."
                )
            )

        return float(
            value
        )

    def _absolute_separation(
        self,
        leading_score: float | None,
        runner_up_score: float | None,
    ) -> float | None:
        if (
            leading_score
            is None
            or runner_up_score
            is None
        ):
            return None

        return round(
            max(
                leading_score
                - runner_up_score,
                0.0,
            ),
            6,
        )

    def _relative_separation(
        self,
        leading_score: float | None,
        absolute_separation: float | None,
    ) -> float | None:
        if (
            leading_score
            is None
            or absolute_separation
            is None
        ):
            return None

        if leading_score <= 0.0:
            return 0.0

        return round(
            absolute_separation
            / leading_score,
            6,
        )

    def _required_text(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str:
        return self._normalize_text(
            payload.get(
                field_name
            ),
            field_name,
        )

    def _optional_text(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str | None:
        value = payload.get(
            field_name
        )

        if value is None:
            return None

        return self._normalize_text(
            value,
            field_name,
        )

    def _optional_float(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> float | None:
        value = payload.get(
            field_name
        )

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must be numeric."
                )
            )

        return float(
            value
        )

    def _normalize_text(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must be a string."
                )
            )

        normalized = (
            value.strip()
        )

        if not normalized:
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must not be empty."
                )
            )

        return normalized

    def _required_string_tuple(
        self,
        payload: Mapping[str, Any],
        field_name: str,
        *,
        allow_empty: bool = False,
    ) -> tuple[str, ...]:
        raw = payload.get(
            field_name
        )

        if not isinstance(
            raw,
            (
                list,
                tuple,
            ),
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must be an array."
                )
            )

        result = tuple(
            self._normalize_text(
                item,
                field_name,
            )
            for item
            in raw
        )

        if (
            not allow_empty
            and not result
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must not be empty."
                )
            )

        if len(
            result
        ) != len(
            set(
                result
            )
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} contains duplicates."
                )
            )

        return result

    def _required_positive_int(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> int:
        value = payload.get(
            field_name
        )

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must be an integer."
                )
            )

        if value < 1:
            raise (
                CalibrationOracleEvaluationError(
                    f"{field_name} must be at least 1."
                )
            )

        return value

    def _required_rank(
        self,
        payload: Mapping[str, Any],
    ) -> int:
        value = payload.get(
            "rank"
        )

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    "Primary diagnosis condition rank "
                    "must be an integer."
                )
            )

        if value < 1:
            raise (
                CalibrationOracleEvaluationError(
                    "Primary diagnosis condition rank "
                    "must be at least 1."
                )
            )

        return value

    def _required_mapping_payload(
        self,
        value: Any,
        label: str,
    ) -> Mapping[str, Any]:
        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                CalibrationOracleEvaluationError(
                    f"{label} payload must be an object."
                )
            )

        return value