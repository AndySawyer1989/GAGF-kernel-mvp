from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.diagnostic_calibration_blind_diagnostic_execution import (
    BlindCalibrationDiagnosticExecutionResult,
    DiagnosticCalibrationBlindDiagnosticExecutionService,
)
from backend.app.gagf.diagnostic_calibration_blind_evidence import (
    BlindEvidenceGenerationResult,
    DiagnosticCalibrationBlindEvidenceService,
)
from backend.app.gagf.diagnostic_calibration_blind_evidence_intake_bridge import (
    BlindEvidenceIntakeBridgeResult,
    CommercialHierarchyContext,
    DiagnosticCalibrationBlindEvidenceIntakeBridgeService,
)
from backend.app.gagf.diagnostic_calibration_oracle_evaluation import (
    CalibrationOracleEvaluationResult,
    DiagnosticCalibrationOracleEvaluationService,
)
from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    CalibrationPublicScenario,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


CALIBRATION_BLIND_RUN_HARNESS_VERSION = "1.0.0"

CALIBRATION_BLIND_RUN_HARNESS_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_RUN_ONLY"
)


class CalibrationBlindRunHarnessError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationBlindRunPaths:
    public_scenario_path: Path
    generator_payload_path: Path
    sealed_oracle_path: Path
    database_path: Path
    validated_evidence_path: Path
    diagnostic_freeze_path: Path
    evaluation_path: Path

    def to_dict(
        self,
    ) -> dict[str, str]:
        return {
            "public_scenario_path":
                str(
                    self.public_scenario_path
                ),

            "generator_payload_path":
                str(
                    self.generator_payload_path
                ),

            "sealed_oracle_path":
                str(
                    self.sealed_oracle_path
                ),

            "database_path":
                str(
                    self.database_path
                ),

            "validated_evidence_path":
                str(
                    self.validated_evidence_path
                ),

            "diagnostic_freeze_path":
                str(
                    self.diagnostic_freeze_path
                ),

            "evaluation_path":
                str(
                    self.evaluation_path
                ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationDiagnosticFreeze:
    scenario_id: str
    public_hash: str

    generator_id: str
    generation_id: str

    hierarchy_key: str

    blind_evidence_hash: str
    preflight_intake_hash: str
    assessment_execution_request_hash: str

    repository_chain_valid: bool

    leading_candidate_category: str | None

    primary_diagnosis_summary_hash: str
    separation_summary_hash: str

    oracle_opened: bool

    boundary: str

    freeze_hash: str

    authority: str = (
        CALIBRATION_BLIND_RUN_HARNESS_AUTHORITY
    )

    version: str = (
        CALIBRATION_BLIND_RUN_HARNESS_VERSION
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

            "hierarchy_key":
                self.hierarchy_key,

            "blind_evidence_hash":
                self.blind_evidence_hash,

            "preflight_intake_hash":
                self.preflight_intake_hash,

            "assessment_execution_request_hash":
                self.assessment_execution_request_hash,

            "repository_chain_valid":
                self.repository_chain_valid,

            "leading_candidate_category":
                self.leading_candidate_category,

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary_hash,

            "separation_summary_hash":
                self.separation_summary_hash,

            "oracle_opened":
                self.oracle_opened,

            "boundary":
                self.boundary,

            "freeze_hash":
                self.freeze_hash,

            "authority":
                self.authority,

            "version":
                self.version,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationBlindRunResult:
    scenario_id: str

    generator_id: str
    generation_id: str

    evidence: BlindEvidenceGenerationResult

    intake: BlindEvidenceIntakeBridgeResult

    execution: (
        BlindCalibrationDiagnosticExecutionResult
    )

    freeze: CalibrationDiagnosticFreeze

    evaluation: CalibrationOracleEvaluationResult

    paths: CalibrationBlindRunPaths

    authority: str = (
        CALIBRATION_BLIND_RUN_HARNESS_AUTHORITY
    )

    version: str = (
        CALIBRATION_BLIND_RUN_HARNESS_VERSION
    )

    @property
    def rank_1_hit(
        self,
    ) -> bool:
        return (
            self.evaluation.rank_1_hit
        )

    @property
    def top_2_hit(
        self,
    ) -> bool:
        return (
            self.evaluation.top_2_hit
        )

    @property
    def top_3_hit(
        self,
    ) -> bool:
        return (
            self.evaluation.top_3_hit
        )

    @property
    def reciprocal_rank(
        self,
    ) -> float:
        return (
            self.evaluation.reciprocal_rank
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "generator_id":
                self.generator_id,

            "generation_id":
                self.generation_id,

            "rank_1_hit":
                self.rank_1_hit,

            "top_2_hit":
                self.top_2_hit,

            "top_3_hit":
                self.top_3_hit,

            "reciprocal_rank":
                self.reciprocal_rank,

            "leading_candidate_category":
                self.evaluation
                .leading_candidate_category,

            "first_primary_rank":
                self.evaluation
                .first_primary_rank,

            "candidate_count":
                self.evaluation
                .candidate_count,

            "leading_structural_level":
                self.evaluation
                .leading_structural_level,

            "leading_evidence_quality":
                self.evaluation
                .leading_evidence_quality,

            "absolute_separation":
                self.evaluation
                .absolute_separation,

            "relative_separation":
                self.evaluation
                .relative_separation,

            "evidence_hash":
                self.evidence.evidence_hash,

            "freeze_hash":
                self.freeze.freeze_hash,

            "evaluation_hash":
                self.evaluation.evaluation_hash,

            "paths":
                self.paths.to_dict(),

            "authority":
                self.authority,

            "version":
                self.version,
        }


class DiagnosticCalibrationBlindRunHarnessService:
    """
    Execute one independent blind calibration case.

    Authority sequence:

        public scenario
        -> external generator payload
        -> 001D evidence validation
        -> 001E real evidence intake
        -> 001F governed diagnostic execution
        -> diagnostic freeze persisted
        ---------------------------------
        -> sealed oracle opened
        -> 001G calibration evaluation

    The sealed oracle is intentionally not loaded until
    diagnostic execution has completed and the freeze
    artifact has been persisted successfully.

    This service does not:

    - create diagnostic confidence;
    - define confidence thresholds;
    - establish root cause;
    - authorize interventions;
    - alter diagnostic ranking after oracle disclosure.
    """

    def __init__(
        self,
        *,
        blind_evidence_service: (
            DiagnosticCalibrationBlindEvidenceService
            | None
        ) = None,
        intake_bridge_service: (
            DiagnosticCalibrationBlindEvidenceIntakeBridgeService
            | None
        ) = None,
        execution_service: (
            DiagnosticCalibrationBlindDiagnosticExecutionService
            | None
        ) = None,
        evaluation_service: (
            DiagnosticCalibrationOracleEvaluationService
            | None
        ) = None,
    ) -> None:
        self._blind_evidence_service = (
            blind_evidence_service
            or
            DiagnosticCalibrationBlindEvidenceService()
        )

        self._intake_bridge_service = (
            intake_bridge_service
            or
            DiagnosticCalibrationBlindEvidenceIntakeBridgeService()
        )

        self._execution_service = (
            execution_service
            or
            DiagnosticCalibrationBlindDiagnosticExecutionService()
        )

        self._evaluation_service = (
            evaluation_service
            or
            DiagnosticCalibrationOracleEvaluationService()
        )

    def run(
        self,
        *,
        context: CommercialHierarchyContext,
        paths: CalibrationBlindRunPaths,
    ) -> CalibrationBlindRunResult:
        self._validate_context(
            context
        )

        self._validate_input_paths(
            paths
        )

        self._refuse_existing_outputs(
            paths
        )

        public_payload = self._read_json(
            paths.public_scenario_path
        )

        public_scenario = (
            self._build_public_scenario(
                public_payload
            )
        )

        generator_payload = self._read_json(
            paths.generator_payload_path
        )

        evidence = (
            self._blind_evidence_service
            .validate(
                public_scenario=(
                    public_scenario
                ),
                generator_payload=(
                    generator_payload
                ),
            )
        )

        self._write_json(
            paths.validated_evidence_path,
            evidence.to_dict(),
        )

        intake = (
            self._intake_bridge_service
            .ingest(
                context=(
                    context
                ),
                evidence=(
                    evidence
                ),
            )
        )

        execution = (
            self._execution_service
            .execute(
                database_path=(
                    paths.database_path
                ),
                context=(
                    context
                ),
                evidence=(
                    evidence
                ),
            )
        )

        self._validate_execution(
            execution=(
                execution
            ),
            evidence=(
                evidence
            ),
        )

        freeze = self._build_freeze(
            execution
        )

        #
        # CRITICAL ORACLE BOUNDARY:
        #
        # The diagnostic freeze is persisted before
        # sealed_oracle.json is read.
        #
        self._write_json(
            paths.diagnostic_freeze_path,
            freeze.to_dict(),
        )

        if not (
            paths.diagnostic_freeze_path.exists()
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Diagnostic freeze was not persisted "
                    "before oracle disclosure."
                )
            )

        #
        # ==================================================
        # SEALED ORACLE MAY BE OPENED ONLY BELOW THIS LINE.
        # ==================================================
        #

        oracle_payload = self._read_json(
            paths.sealed_oracle_path
        )

        evaluation = (
            self._evaluation_service
            .evaluate(
                execution=(
                    execution
                ),
                oracle=(
                    oracle_payload
                ),
            )
        )

        self._write_json(
            paths.evaluation_path,
            evaluation.to_dict(),
        )

        return (
            CalibrationBlindRunResult(
                scenario_id=(
                    evidence.scenario_id
                ),

                generator_id=(
                    evidence.generator_id
                ),

                generation_id=(
                    evidence.generation_id
                ),

                evidence=(
                    evidence
                ),

                intake=(
                    intake
                ),

                execution=(
                    execution
                ),

                freeze=(
                    freeze
                ),

                evaluation=(
                    evaluation
                ),

                paths=(
                    paths
                ),
            )
        )

    def _build_freeze(
        self,
        execution: (
            BlindCalibrationDiagnosticExecutionResult
        ),
    ) -> CalibrationDiagnosticFreeze:
        payload = {
            "scenario_id":
                execution.scenario_id,

            "public_hash":
                execution.public_hash,

            "generator_id":
                execution.generator_id,

            "generation_id":
                execution.generation_id,

            "hierarchy_key":
                execution.hierarchy_key,

            "blind_evidence_hash":
                execution.blind_evidence_hash,

            "preflight_intake_hash":
                execution.preflight_intake_hash,

            "assessment_execution_request_hash":
                execution
                .assessment_execution_request_hash,

            "repository_chain_valid":
                execution.repository_chain_valid,

            "leading_candidate_category":
                execution.leading_candidate_category,

            "primary_diagnosis_summary_hash":
                execution
                .primary_diagnosis_summary_hash,

            "separation_summary_hash":
                execution.separation_summary_hash,

            "oracle_opened":
                False,

            "boundary":
                "DIAGNOSTIC_FROZEN_BEFORE_ORACLE",

            "authority":
                CALIBRATION_BLIND_RUN_HARNESS_AUTHORITY,

            "version":
                CALIBRATION_BLIND_RUN_HARNESS_VERSION,
        }

        freeze_hash = sha256_text(
            canonical_json(
                payload
            )
        )

        return (
            CalibrationDiagnosticFreeze(
                scenario_id=(
                    execution.scenario_id
                ),

                public_hash=(
                    execution.public_hash
                ),

                generator_id=(
                    execution.generator_id
                ),

                generation_id=(
                    execution.generation_id
                ),

                hierarchy_key=(
                    execution.hierarchy_key
                ),

                blind_evidence_hash=(
                    execution.blind_evidence_hash
                ),

                preflight_intake_hash=(
                    execution.preflight_intake_hash
                ),

                assessment_execution_request_hash=(
                    execution
                    .assessment_execution_request_hash
                ),

                repository_chain_valid=(
                    execution.repository_chain_valid
                ),

                leading_candidate_category=(
                    execution.leading_candidate_category
                ),

                primary_diagnosis_summary_hash=(
                    execution
                    .primary_diagnosis_summary_hash
                ),

                separation_summary_hash=(
                    execution.separation_summary_hash
                ),

                oracle_opened=False,

                boundary=(
                    "DIAGNOSTIC_FROZEN_BEFORE_ORACLE"
                ),

                freeze_hash=(
                    freeze_hash
                ),
            )
        )

    def _validate_execution(
        self,
        *,
        execution: (
            BlindCalibrationDiagnosticExecutionResult
        ),
        evidence: BlindEvidenceGenerationResult,
    ) -> None:
        if not execution.application_completed:
            raise (
                CalibrationBlindRunHarnessError(
                    "Calibration diagnostic application "
                    "did not complete."
                )
            )

        if not execution.repository_chain_valid:
            raise (
                CalibrationBlindRunHarnessError(
                    "Calibration diagnostic repository "
                    "chain is invalid."
                )
            )

        if (
            execution.scenario_id
            != evidence.scenario_id
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution scenario_id does not match "
                    "validated evidence."
                )
            )

        if (
            execution.public_hash
            != evidence.public_hash
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution public_hash does not match "
                    "validated evidence."
                )
            )

        if (
            execution.generator_id
            != evidence.generator_id
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution generator_id does not match "
                    "validated evidence."
                )
            )

        if (
            execution.generation_id
            != evidence.generation_id
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution generation_id does not "
                    "match validated evidence."
                )
            )

        if (
            execution.blind_evidence_hash
            != evidence.evidence_hash
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution evidence hash does not "
                    "match validated evidence."
                )
            )

        if not (
            execution.primary_diagnosis_summary_hash
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution is missing its frozen "
                    "primary-diagnosis summary hash."
                )
            )

        if not (
            execution.separation_summary_hash
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Execution is missing its frozen "
                    "diagnostic-separation summary hash."
                )
            )

    def _validate_context(
        self,
        context: CommercialHierarchyContext,
    ) -> None:
        if not context.engagement_id:
            raise (
                CalibrationBlindRunHarnessError(
                    "Calibration context requires "
                    "engagement_id."
                )
            )

        if not context.assessment_id:
            raise (
                CalibrationBlindRunHarnessError(
                    "Calibration context requires "
                    "assessment_id."
                )
            )

    def _validate_input_paths(
        self,
        paths: CalibrationBlindRunPaths,
    ) -> None:
        for path in (
            paths.public_scenario_path,
            paths.generator_payload_path,
            paths.sealed_oracle_path,
        ):
            if not path.exists():
                raise (
                    CalibrationBlindRunHarnessError(
                        "Required calibration input does "
                        f"not exist: {path}"
                    )
                )

            if not path.is_file():
                raise (
                    CalibrationBlindRunHarnessError(
                        "Calibration input must be a file: "
                        f"{path}"
                    )
                )

    def _refuse_existing_outputs(
        self,
        paths: CalibrationBlindRunPaths,
    ) -> None:
        for path in (
            paths.database_path,
            paths.diagnostic_freeze_path,
            paths.evaluation_path,
        ):
            if path.exists():
                raise (
                    CalibrationBlindRunHarnessError(
                        "Refusing to overwrite an existing "
                        f"calibration output: {path}"
                    )
                )

    def _build_public_scenario(
        self,
        payload: Mapping[
            str,
            Any,
        ],
    ) -> CalibrationPublicScenario:
        organization_payload = (
            self._required_mapping(
                payload,
                "organization",
            )
        )

        contract_payload = (
            self._required_mapping(
                payload,
                "evidence_contract",
            )
        )

        organization = (
            CalibrationOrganizationContext(
                organization_type=(
                    self._required_text(
                        organization_payload,
                        "organization_type",
                    )
                ),

                operating_model=(
                    self._required_text(
                        organization_payload,
                        "operating_model",
                    )
                ),

                business_domain=(
                    self._required_text(
                        organization_payload,
                        "business_domain",
                    )
                ),

                team_count=(
                    self._required_int(
                        organization_payload,
                        "team_count",
                    )
                ),

                actor_count=(
                    self._required_int(
                        organization_payload,
                        "actor_count",
                    )
                ),

                workflow_count=(
                    self._required_int(
                        organization_payload,
                        "workflow_count",
                    )
                ),

                observation_days=(
                    self._required_int(
                        organization_payload,
                        "observation_days",
                    )
                ),
            )
        )

        categories = (
            contract_payload.get(
                "allowed_constraint_categories"
            )
        )

        if not isinstance(
            categories,
            list,
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "allowed_constraint_categories must "
                    "be a JSON array."
                )
            )

        normalized_categories = tuple(
            str(
                value
            ).strip()
            for value
            in categories
            if str(
                value
            ).strip()
        )

        if not normalized_categories:
            raise (
                CalibrationBlindRunHarnessError(
                    "allowed_constraint_categories must "
                    "not be empty."
                )
            )

        evidence_contract = (
            CalibrationEvidenceGenerationContract(
                allowed_constraint_categories=(
                    normalized_categories
                ),

                minimum_event_count=(
                    self._required_int(
                        contract_payload,
                        "minimum_event_count",
                    )
                ),

                maximum_event_count=(
                    self._required_int(
                        contract_payload,
                        "maximum_event_count",
                    )
                ),

                minimum_work_item_count=(
                    self._required_int(
                        contract_payload,
                        "minimum_work_item_count",
                    )
                ),

                maximum_work_item_count=(
                    self._required_int(
                        contract_payload,
                        "maximum_work_item_count",
                    )
                ),

                require_multiple_teams=(
                    self._required_bool(
                        contract_payload,
                        "require_multiple_teams",
                    )
                ),

                require_multiple_lifecycles=(
                    self._required_bool(
                        contract_payload,
                        "require_multiple_lifecycles",
                    )
                ),

                require_temporal_ordering=(
                    self._required_bool(
                        contract_payload,
                        "require_temporal_ordering",
                    )
                ),

                evidence_quality_floor=(
                    self._required_float(
                        contract_payload,
                        "evidence_quality_floor",
                    )
                ),

                evidence_quality_ceiling=(
                    self._required_float(
                        contract_payload,
                        "evidence_quality_ceiling",
                    )
                ),
            )
        )

        return (
            CalibrationPublicScenario(
                scenario_id=(
                    self._required_text(
                        payload,
                        "scenario_id",
                    )
                ),

                scenario_name=(
                    self._required_text(
                        payload,
                        "scenario_name",
                    )
                ),

                organization=(
                    organization
                ),

                evidence_contract=(
                    evidence_contract
                ),

                narrative_seed=(
                    self._required_text(
                        payload,
                        "narrative_seed",
                    )
                ),

                public_hash=(
                    self._required_text(
                        payload,
                        "public_hash",
                    )
                ),

                schema_version=(
                    self._required_text(
                        payload,
                        "schema_version",
                    )
                ),
            )
        )

    def _read_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                payload = json.load(
                    handle
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise (
                CalibrationBlindRunHarnessError(
                    "Unable to read calibration JSON "
                    f"from {path}: {exc}"
                )
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    "Calibration JSON must contain one "
                    f"object: {path}"
                )
            )

        return payload

    def _write_json(
        self,
        path: Path,
        payload: Mapping[
            str,
            Any,
        ],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            path.with_name(
                path.name
                + ".tmp"
            )
        )

        try:
            with temporary_path.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    dict(
                        payload
                    ),
                    handle,
                    indent=2,
                    sort_keys=True,
                )

                handle.write(
                    "\n"
                )

                handle.flush()

            temporary_path.replace(
                path
            )

        except OSError as exc:
            if temporary_path.exists():
                temporary_path.unlink()

            raise (
                CalibrationBlindRunHarnessError(
                    "Unable to persist calibration "
                    f"artifact {path}: {exc}"
                )
            ) from exc

    def _required_mapping(
        self,
        payload: Mapping[
            str,
            Any,
        ],
        field_name: str,
    ) -> Mapping[
        str,
        Any,
    ]:
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    f"{field_name} must be an object."
                )
            )

        return value

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

        if not isinstance(
            value,
            str,
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    f"{field_name} must be a string."
                )
            )

        normalized = value.strip()

        if not normalized:
            raise (
                CalibrationBlindRunHarnessError(
                    f"{field_name} must not be empty."
                )
            )

        return normalized

    def _required_int(
        self,
        payload: Mapping[
            str,
            Any,
        ],
        field_name: str,
    ) -> int:
        value = payload.get(
            field_name
        )

        if (
            isinstance(
                value,
                bool,
            )
            or
            not isinstance(
                value,
                int,
            )
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    f"{field_name} must be an integer."
                )
            )

        return value

    def _required_float(
        self,
        payload: Mapping[
            str,
            Any,
        ],
        field_name: str,
    ) -> float:
        value = payload.get(
            field_name
        )

        if (
            isinstance(
                value,
                bool,
            )
            or
            not isinstance(
                value,
                (
                    int,
                    float,
                ),
            )
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    f"{field_name} must be numeric."
                )
            )

        return float(
            value
        )

    def _required_bool(
        self,
        payload: Mapping[
            str,
            Any,
        ],
        field_name: str,
    ) -> bool:
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            bool,
        ):
            raise (
                CalibrationBlindRunHarnessError(
                    f"{field_name} must be boolean."
                )
            )

        return value