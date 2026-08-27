from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.diagnostic_calibration_blind_evidence import (
    BlindEvidenceGenerationResult,
    DiagnosticCalibrationBlindEvidenceService,
)
from backend.app.gagf.diagnostic_calibration_blind_evidence_intake_bridge import (
    BlindEvidenceIntakeBridgeResult,
    DiagnosticCalibrationBlindEvidenceIntakeBridgeService,
)
from backend.app.gagf.governance_assessment_application import (
    AssessmentApplicationResult,
    AssessmentExecutionRequest,
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_diagnostic_projection import (
    GovernanceAssessmentDiagnosticProjectionService,
)
from backend.app.gagf.governance_assessment_diagnostic_separation_projection import (
    GovernanceAssessmentDiagnosticSeparationProjectionResult,
    GovernanceAssessmentDiagnosticSeparationProjectionService,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)


BLIND_CALIBRATION_DIAGNOSTIC_EXECUTION_VERSION = "1.0.0"

BLIND_CALIBRATION_DIAGNOSTIC_EXECUTION_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_DIAGNOSTIC_ONLY"
)


class BlindCalibrationDiagnosticExecutionError(
    RuntimeError
):
    """
    Raised when blind calibration evidence cannot be
    executed safely through the real FIP assessment and
    diagnostic stack.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class BlindCalibrationDiagnosticExecutionResult:
    scenario_id: str
    public_hash: str

    generator_id: str
    generation_id: str

    hierarchy_key: str
    database_path: str

    blind_evidence_hash: str
    preflight_intake_hash: str

    assessment_execution_request_hash: str

    application_result: AssessmentApplicationResult

    separation_projection: (
        GovernanceAssessmentDiagnosticSeparationProjectionResult
    )

    repository_chain_valid: bool

    authority: str = (
        BLIND_CALIBRATION_DIAGNOSTIC_EXECUTION_AUTHORITY
    )

    version: str = (
        BLIND_CALIBRATION_DIAGNOSTIC_EXECUTION_VERSION
    )

    @property
    def application_completed(
        self,
    ) -> bool:
        return (
            self.application_result
            .completed
        )

    @property
    def leading_candidate_category(
        self,
    ) -> str | None:
        return (
            self.separation_projection
            .leading_candidate_category
        )

    @property
    def separation_summary_hash(
        self,
    ) -> str:
        return (
            self.separation_projection
            .separation_summary
            .summary_hash
        )

    @property
    def primary_diagnosis_summary_hash(
        self,
    ) -> str:
        return (
            self.separation_projection
            .separation_summary
            .primary_diagnosis_summary_hash
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

            "database_path":
                self.database_path,

            "blind_evidence_hash":
                self.blind_evidence_hash,

            "preflight_intake_hash":
                self.preflight_intake_hash,

            "assessment_execution_request_hash":
                self.assessment_execution_request_hash,

            "application_completed":
                self.application_completed,

            "leading_candidate_category":
                self.leading_candidate_category,

            "separation_summary_hash":
                self.separation_summary_hash,

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary_hash,

            "repository_chain_valid":
                self.repository_chain_valid,

            "diagnostic_projection": {
                "artifact_id":
                    self.separation_projection
                    .artifact_id,

                "artifact_hash":
                    self.separation_projection
                    .artifact_hash,

                "sequence_number":
                    self.separation_projection
                    .sequence_number,

                "primary_projection_verified":
                    self.separation_projection
                    .primary_projection_verified,

                "structural_projection_verified":
                    self.separation_projection
                    .structural_projection_verified,

                "structural_classification_verified":
                    self.separation_projection
                    .structural_classification_verified,
            },

            "authority":
                self.authority,

            "version":
                self.version,
        }


class DiagnosticCalibrationBlindDiagnosticExecutionService:
    """
    Execute already-validated blind calibration evidence
    through the real Governance Assessment application and
    frozen diagnostic-separation stack.

    Constitutional boundary:

    Calibration Diagnostic Execution
        != Paid Work Authorization

    Calibration Diagnostic Execution
        != Customer Assessment Execution

    Diagnostic Separation
        != Confidence

    This service never accepts:

    - a sealed oracle;
    - planted expected conditions;
    - expected rank;
    - confidence thresholds;
    - root-cause labels;
    - intervention authority.

    Execution sequence:

    1. Require a fresh assessment database.
    2. Run blind evidence through the existing real intake
       bridge as an exact preflight.
    3. Convert the same validated evidence into canonical CSV.
    4. Construct the real AssessmentExecutionRequest.
    5. Execute the real GovernanceAssessmentApplicationService.
    6. Verify the application's persisted repository chain.
    7. Require persisted evidence-intake and friction artifacts.
    8. Run deterministic diagnostic-significance projection.
    9. Require exactly one diagnostic-significance artifact.
    10. Run the frozen structural / primary / separation chain.
    11. Verify the repository chain again.
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
        diagnostic_projection_service: (
            GovernanceAssessmentDiagnosticProjectionService
            | None
        ) = None,
        separation_projection_service: (
            GovernanceAssessmentDiagnosticSeparationProjectionService
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

        self._diagnostic_projection_service = (
            diagnostic_projection_service
            or
            GovernanceAssessmentDiagnosticProjectionService()
        )

        self._separation_projection_service = (
            separation_projection_service
            or
            GovernanceAssessmentDiagnosticSeparationProjectionService()
        )

    def execute(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
        evidence: BlindEvidenceGenerationResult,
    ) -> BlindCalibrationDiagnosticExecutionResult:
        path = Path(
            database_path
        )

        if path.exists():
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind calibration diagnostic execution "
                    "requires a fresh database path."
                )
            )

        if context.engagement_id is None:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Calibration diagnostic execution "
                    "requires engagement_id."
                )
            )

        if context.assessment_id is None:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Calibration diagnostic execution "
                    "requires assessment_id."
                )
            )

        preflight = (
            self._intake_bridge_service
            .ingest(
                context=context,
                evidence=evidence,
            )
        )

        self._validate_preflight(
            context=context,
            evidence=evidence,
            preflight=preflight,
        )

        csv_text = (
            self._blind_evidence_service
            .to_csv(
                result=evidence
            )
        )

        source = (
            EvidenceSourceReference(
                source_id=(
                    preflight.source_id
                ),

                kind=(
                    EvidenceSourceKind.CSV
                ),

                display_name=(
                    "Blind Calibration Evidence "
                    f"{evidence.scenario_id}"
                ),

                source_location=(
                    "calibration://"
                    f"{evidence.scenario_id}/"
                    f"{evidence.generation_id}"
                ),
            )
        )

        workflow_names = (
            evidence.lifecycle_instance_ids
        )

        organizational_units = (
            evidence.team_ids
        )

        if not workflow_names:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind calibration evidence must contain "
                    "at least one lifecycle_instance_id."
                )
            )

        if not organizational_units:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind calibration evidence must contain "
                    "at least one team_id."
                )
            )

        timestamps = tuple(
            record.occurred_at
            for record
            in evidence.records
        )

        if not timestamps:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind calibration evidence must contain "
                    "at least one timestamp."
                )
            )

        period_start = min(
            timestamps
        ).date()

        period_end = max(
            timestamps
        ).date()

        request = (
            AssessmentExecutionRequest(
                context=context,

                assessment_name=(
                    "Blind Calibration Diagnostic "
                    f"{evidence.scenario_id}"
                ),

                workflow_names=(
                    workflow_names
                ),

                organizational_units=(
                    organizational_units
                ),

                period_start=(
                    period_start
                ),

                period_end=(
                    period_end
                ),

                objectives=(
                    (
                        "Evaluate blind deterministic "
                        "FIP diagnostic behavior."
                    ),
                ),

                expected_outcomes=(
                    (
                        "Produce governed diagnostic evidence "
                        "without oracle access."
                    ),
                ),

                evidence_requirements=(
                    EvidenceRequirement(
                        requirement_id=(
                            "blind-calibration-csv"
                        ),

                        source_kind=(
                            EvidenceSourceKind.CSV
                        ),

                        description=(
                            "Blind calibration operational "
                            "evidence."
                        ),

                        required=True,

                        minimum_record_count=(
                            evidence.event_count
                        ),
                    ),
                ),

                evidence_inputs=(
                    DemonstrationEvidenceInput(
                        source=(
                            source
                        ),

                        csv_text=(
                            csv_text
                        ),
                    ),
                ),

                client_display_name=(
                    "Synthetic Calibration Organization"
                ),

                prepared_by=(
                    "GAGF FIP Calibration"
                ),

                exclusions=(
                    (
                        "Sealed oracle excluded from "
                        "diagnostic execution."
                    ),
                ),

                maximum_priorities=3,
            )
        )

        request_hash = sha256_text(
            canonical_json(
                request.to_dict()
            )
        )

        repository = (
            GovernanceAssessmentRepository(
                path
            )
        )

        application_service = (
            GovernanceAssessmentApplicationService(
                repository=repository
            )
        )

        application_result = (
            application_service
            .execute(
                request=request
            )
        )

        if (
            application_result.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Governance Assessment application "
                    "returned the wrong hierarchy."
                )
            )

        if (
            application_result.completed
            is not True
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Governance Assessment application "
                    "did not complete."
                )
            )

        chain_valid = (
            repository.verify_chain(
                context=context
            )
        )

        if chain_valid is not True:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Assessment repository chain is invalid "
                    "after application execution."
                )
            )

        self._require_core_diagnostic_artifacts(
            repository=repository,
            context=context,
        )

        diagnostic_projection = (
            self._diagnostic_projection_service
            .project(
                database_path=path,
                context=context,
            )
        )

        if (
            diagnostic_projection.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Diagnostic-significance projection "
                    "returned the wrong hierarchy."
                )
            )

        if (
            diagnostic_projection
            .repository_chain_valid
            is not True
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Diagnostic-significance projection "
                    "did not preserve repository integrity."
                )
            )

        significance_artifacts = (
            repository.list_artifacts(
                context=context,
                artifact_type=(
                    "diagnostic-significance"
                ),
            )
        )

        if len(
            significance_artifacts
        ) != 1:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Calibration execution requires exactly "
                    "one persisted diagnostic-significance "
                    "artifact before structural projection."
                )
            )

        separation_projection = (
            self._separation_projection_service
            .project(
                database_path=path,
                context=context,
            )
        )

        if (
            separation_projection.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Diagnostic-separation projection "
                    "returned the wrong hierarchy."
                )
            )

        if (
            separation_projection
            .repository_chain_valid
            is not True
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Diagnostic-separation projection "
                    "did not preserve repository integrity."
                )
            )

        if (
            separation_projection
            .primary_projection_verified
            is not True
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Primary-diagnosis projection was "
                    "not verified."
                )
            )

        if (
            separation_projection
            .structural_projection_verified
            is not True
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Structural-importance projection was "
                    "not verified."
                )
            )

        if (
            separation_projection
            .structural_classification_verified
            is not True
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Structural-importance classification "
                    "was not verified."
                )
            )

        final_chain_valid = (
            repository.verify_chain(
                context=context
            )
        )

        if final_chain_valid is not True:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Assessment repository chain is invalid "
                    "after diagnostic projection."
                )
            )

        return (
            BlindCalibrationDiagnosticExecutionResult(
                scenario_id=(
                    evidence.scenario_id
                ),

                public_hash=(
                    evidence.public_hash
                ),

                generator_id=(
                    evidence.generator_id
                ),

                generation_id=(
                    evidence.generation_id
                ),

                hierarchy_key=(
                    context.hierarchy_key
                ),

                database_path=str(
                    path
                ),

                blind_evidence_hash=(
                    evidence.evidence_hash
                ),

                preflight_intake_hash=(
                    preflight
                    .intake_result
                    .intake_hash
                ),

                assessment_execution_request_hash=(
                    request_hash
                ),

                application_result=(
                    application_result
                ),

                separation_projection=(
                    separation_projection
                ),

                repository_chain_valid=(
                    final_chain_valid
                ),
            )
        )

    def _validate_preflight(
        self,
        *,
        context: CommercialHierarchyContext,
        evidence: BlindEvidenceGenerationResult,
        preflight: BlindEvidenceIntakeBridgeResult,
    ) -> None:
        if (
            preflight.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind intake preflight hierarchy "
                    "does not match execution hierarchy."
                )
            )

        if (
            preflight.evidence_hash
            != evidence.evidence_hash
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind intake preflight evidence hash "
                    "does not match execution evidence."
                )
            )

        if preflight.valid is not True:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind intake preflight is invalid."
                )
            )

        if (
            preflight.accepted_count
            != evidence.event_count
        ):
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Blind intake preflight accepted count "
                    "does not match evidence event count."
                )
            )

    def _require_core_diagnostic_artifacts(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
    ) -> None:
        artifacts = (
            repository.list_artifacts(
                context=context
            )
        )

        artifact_types = {
            artifact.artifact_type
            for artifact
            in artifacts
        }

        required_types = {
            "evidence-intake-batch",
            "friction-summary",
        }

        missing = (
            required_types
            - artifact_types
        )

        if missing:
            raise (
                BlindCalibrationDiagnosticExecutionError(
                    "Governance Assessment application "
                    "did not persist required diagnostic "
                    "artifacts: "
                    + ", ".join(
                        sorted(
                            missing
                        )
                    )
                )
            )