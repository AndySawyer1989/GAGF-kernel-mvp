from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_diagnostic_scope import (
    GovernanceAssessmentDiagnosticScopeService,
)
from backend.app.gagf.governance_assessment_diagnostic_significance import (
    GovernanceAssessmentDiagnosticSignificanceService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_persisted_reconstruction import (
    GovernanceAssessmentPersistedReconstructionService,
    PersistedAssessmentReconstructionError,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
    canonical_json,
)
from backend.app.gagf.governance_assessment_structural_importance import (
    AssessmentStructuralImportanceEvidenceSummary,
    GovernanceAssessmentStructuralImportanceService,
)


DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE = (
    "diagnostic-significance"
)

STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE = (
    "structural-importance-evidence"
)

STRUCTURAL_IMPORTANCE_PROJECTION_VERSION = (
    "1.0.0"
)


class StructuralImportanceProjectionError(
    RuntimeError
):
    """
    Raised when governed structural-importance
    evidence cannot be projected safely.
    """


@dataclass(frozen=True, slots=True)
class GovernanceAssessmentStructuralImportanceProjectionResult:
    hierarchy_key: str
    structural_summary: (
        AssessmentStructuralImportanceEvidenceSummary
    )
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    repository_chain_valid: bool
    reused_existing: bool
    diagnostic_integrity_verified: bool
    projection_version: str = (
        STRUCTURAL_IMPORTANCE_PROJECTION_VERSION
    )

    @property
    def condition_count(
        self,
    ) -> int:
        return len(
            self.structural_summary.conditions
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "structural_summary_hash":
                self.structural_summary.summary_hash,
            "condition_count":
                self.condition_count,
            "artifact_id":
                self.artifact_id,
            "artifact_hash":
                self.artifact_hash,
            "sequence_number":
                self.sequence_number,
            "repository_chain_valid":
                self.repository_chain_valid,
            "reused_existing":
                self.reused_existing,
            "diagnostic_integrity_verified":
                self.diagnostic_integrity_verified,
            "projection_version":
                self.projection_version,
        }


class GovernanceAssessmentStructuralImportanceProjectionService:
    """
    Project structural-importance evidence from
    already-persisted governed assessment evidence.

    Projection sequence:

    1. Verify the immutable repository chain.
    2. Require evidence-intake-batch.
    3. Require friction-summary.
    4. Require diagnostic-significance.
    5. Reconstruct governed intake and friction
       through the canonical persisted
       reconstruction service.
    6. Recompute diagnostic significance.
    7. Require exact deterministic equality with
       persisted diagnostic-significance.
    8. Recompute diagnostic scope.
    9. Compute structural-importance evidence.
    10. Append or deterministically reuse one
        structural-importance-evidence artifact.
    11. Verify the repository chain again.

    The service does not:

    - inspect PRELIVE oracle information;
    - assign root cause;
    - assign primary diagnosis;
    - authorize an intervention;
    - modify source evidence.
    """

    def __init__(
        self,
        *,
        reconstruction_service: (
            GovernanceAssessmentPersistedReconstructionService
            | None
        ) = None,
        significance_service: (
            GovernanceAssessmentDiagnosticSignificanceService
            | None
        ) = None,
        scope_service: (
            GovernanceAssessmentDiagnosticScopeService
            | None
        ) = None,
        structural_service: (
            GovernanceAssessmentStructuralImportanceService
            | None
        ) = None,
    ) -> None:
        self._reconstruction_service = (
            reconstruction_service
            or
            GovernanceAssessmentPersistedReconstructionService()
        )

        self._significance_service = (
            significance_service
            or
            GovernanceAssessmentDiagnosticSignificanceService()
        )

        self._scope_service = (
            scope_service
            or
            GovernanceAssessmentDiagnosticScopeService()
        )

        self._structural_service = (
            structural_service
            or
            GovernanceAssessmentStructuralImportanceService()
        )

    def project(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
    ) -> GovernanceAssessmentStructuralImportanceProjectionResult:
        repository = (
            GovernanceAssessmentRepository(
                database_path
            )
        )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise StructuralImportanceProjectionError(
                "assessment repository chain is invalid "
                "before structural-importance projection"
            )

        intake_artifact = (
            self._require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    "evidence-intake-batch"
                ),
            )
        )

        friction_artifact = (
            self._require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    "friction-summary"
                ),
            )
        )

        diagnostic_artifact = (
            self._require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
                ),
            )
        )

        try:
            intake_results = (
                self._reconstruction_service
                .reconstruct_intake_results(
                    payload=(
                        intake_artifact.payload
                    ),
                    expected_hierarchy=(
                        context.hierarchy_key
                    ),
                )
            )

            friction_summary = (
                self._reconstruction_service
                .reconstruct_friction_summary(
                    payload=(
                        friction_artifact.payload
                    ),
                    expected_hierarchy=(
                        context.hierarchy_key
                    ),
                )
            )

        except (
            PersistedAssessmentReconstructionError
        ) as exc:
            raise StructuralImportanceProjectionError(
                str(
                    exc
                )
            ) from exc

        significance_summary = (
            self._significance_service.classify(
                friction_summary=(
                    friction_summary
                ),
                intake_results=(
                    intake_results
                ),
            )
        )

        if (
            significance_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise StructuralImportanceProjectionError(
                "recomputed diagnostic significance "
                "hierarchy does not match assessment"
            )

        recomputed_diagnostic_payload = (
            significance_summary.to_dict()
        )

        if canonical_json(
            diagnostic_artifact.payload
        ) != canonical_json(
            recomputed_diagnostic_payload
        ):
            raise StructuralImportanceProjectionError(
                "persisted diagnostic-significance "
                "artifact does not match deterministic "
                "recomputation"
            )

        diagnostic_integrity_verified = True

        scope_summary = (
            self._scope_service.classify(
                significance_summary=(
                    significance_summary
                )
            )
        )

        if (
            scope_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise StructuralImportanceProjectionError(
                "diagnostic scope hierarchy does not "
                "match assessment"
            )

        structural_summary = (
            self._structural_service.analyze(
                friction_summary=(
                    friction_summary
                ),
                significance_summary=(
                    significance_summary
                ),
                scope_summary=(
                    scope_summary
                ),
                intake_results=(
                    intake_results
                ),
            )
        )

        if (
            structural_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise StructuralImportanceProjectionError(
                "structural-importance hierarchy does "
                "not match assessment"
            )

        payload = (
            structural_summary.to_dict()
        )

        existing = repository.list_artifacts(
            context=context,
            artifact_type=(
                STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE
            ),
        )

        if existing:
            if len(
                existing
            ) != 1:
                raise StructuralImportanceProjectionError(
                    "assessment contains multiple "
                    "structural-importance-evidence "
                    "artifacts"
                )

            artifact = existing[0]

            if canonical_json(
                artifact.payload
            ) != canonical_json(
                payload
            ):
                raise StructuralImportanceProjectionError(
                    "existing structural-importance-"
                    "evidence artifact does not match "
                    "deterministic projection"
                )

            reused_existing = True

        else:
            artifact = (
                repository.append_artifact(
                    context=context,
                    artifact_type=(
                        STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE
                    ),
                    payload=payload,
                )
            )

            reused_existing = False

        chain_valid = (
            repository.verify_chain(
                context=context
            )
        )

        if chain_valid is not True:
            raise StructuralImportanceProjectionError(
                "assessment repository chain is invalid "
                "after structural-importance projection"
            )

        return (
            GovernanceAssessmentStructuralImportanceProjectionResult(
                hierarchy_key=(
                    context.hierarchy_key
                ),
                structural_summary=(
                    structural_summary
                ),
                artifact_id=(
                    artifact.artifact_id
                ),
                artifact_hash=(
                    artifact.artifact_hash
                ),
                sequence_number=(
                    artifact.sequence_number
                ),
                repository_chain_valid=(
                    chain_valid
                ),
                reused_existing=(
                    reused_existing
                ),
                diagnostic_integrity_verified=(
                    diagnostic_integrity_verified
                ),
            )
        )

    def _require_single_artifact(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        artifact_type: str,
    ) -> ImmutableAssessmentArtifact:
        try:
            return (
                self._reconstruction_service
                .require_single_artifact(
                    repository=repository,
                    context=context,
                    artifact_type=(
                        artifact_type
                    ),
                )
            )

        except (
            PersistedAssessmentReconstructionError
        ) as exc:
            raise StructuralImportanceProjectionError(
                str(
                    exc
                )
            ) from exc