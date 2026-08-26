from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_diagnostic_significance import (
    AssessmentDiagnosticSignificanceSummary,
    GovernanceAssessmentDiagnosticSignificanceService,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
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


DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE = (
    "diagnostic-significance"
)

DIAGNOSTIC_PROJECTION_VERSION = "1.0.0"


DiagnosticProjectionError = (
    PersistedAssessmentReconstructionError
)


@dataclass(frozen=True, slots=True)
class GovernanceAssessmentDiagnosticProjectionResult:
    hierarchy_key: str
    diagnostic_summary: AssessmentDiagnosticSignificanceSummary
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    repository_chain_valid: bool
    reused_existing: bool
    projection_version: str = DIAGNOSTIC_PROJECTION_VERSION

    @property
    def diagnosed_conditions(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            category.value
            for category
            in self.diagnostic_summary.diagnosed_conditions
        )

    @property
    def dominant_condition(
        self,
    ) -> str | None:
        value = self.diagnostic_summary.dominant_condition

        return (
            value.value
            if value is not None
            else None
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "diagnosed_conditions":
                list(
                    self.diagnosed_conditions
                ),
            "dominant_condition":
                self.dominant_condition,
            "diagnostic_summary_hash":
                self.diagnostic_summary.summary_hash,
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
            "projection_version":
                self.projection_version,
        }


class GovernanceAssessmentDiagnosticProjectionService:
    """
    Build diagnostic significance from already-persisted governed
    assessment evidence.

    Persisted artifact reconstruction is delegated to the shared
    GovernanceAssessmentPersistedReconstructionService.

    The projection:

    1. Verifies the immutable assessment artifact chain.
    2. Reads evidence-intake-batch.
    3. Reads friction-summary.
    4. Reconstructs both through the canonical reconstruction service.
    5. Computes diagnostic significance deterministically.
    6. Appends or reuses one immutable diagnostic-significance artifact.
    7. Verifies the repository chain after projection.

    It does not alter or reinterpret original evidence artifacts.
    """

    def __init__(
        self,
        *,
        significance_service: (
            GovernanceAssessmentDiagnosticSignificanceService
            | None
        ) = None,
        reconstruction_service: (
            GovernanceAssessmentPersistedReconstructionService
            | None
        ) = None,
    ) -> None:
        self._significance_service = (
            significance_service
            or GovernanceAssessmentDiagnosticSignificanceService()
        )

        self._reconstruction_service = (
            reconstruction_service
            or GovernanceAssessmentPersistedReconstructionService()
        )

    def project(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
    ) -> GovernanceAssessmentDiagnosticProjectionResult:
        repository = GovernanceAssessmentRepository(
            database_path
        )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise DiagnosticProjectionError(
                "assessment repository chain is invalid before "
                "diagnostic projection"
            )

        intake_artifact = (
            self._reconstruction_service
            .require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    "evidence-intake-batch"
                ),
            )
        )

        friction_artifact = (
            self._reconstruction_service
            .require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=(
                    "friction-summary"
                ),
            )
        )

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

        diagnostic_summary = (
            self._significance_service.classify(
                friction_summary=friction_summary,
                intake_results=intake_results,
            )
        )

        if (
            diagnostic_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise DiagnosticProjectionError(
                "diagnostic significance hierarchy does not match "
                "the persisted assessment"
            )

        payload = (
            diagnostic_summary.to_dict()
        )

        existing = repository.list_artifacts(
            context=context,
            artifact_type=(
                DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
            ),
        )

        if existing:
            if len(existing) != 1:
                raise DiagnosticProjectionError(
                    "assessment contains multiple "
                    "diagnostic-significance artifacts"
                )

            artifact = existing[0]

            if canonical_json(
                artifact.payload
            ) != canonical_json(
                payload
            ):
                raise DiagnosticProjectionError(
                    "existing diagnostic-significance artifact does not "
                    "match deterministic projection"
                )

            reused_existing = True

        else:
            artifact = (
                repository.append_artifact(
                    context=context,
                    artifact_type=(
                        DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
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
            raise DiagnosticProjectionError(
                "assessment repository chain is invalid after "
                "diagnostic projection"
            )

        return (
            GovernanceAssessmentDiagnosticProjectionResult(
                hierarchy_key=(
                    context.hierarchy_key
                ),
                diagnostic_summary=(
                    diagnostic_summary
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
            )
        )

    def _require_single_artifact(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        artifact_type: str,
    ) -> ImmutableAssessmentArtifact:
        """
        Compatibility wrapper retained for callers/tests that relied on
        the former projection-local helper.
        """

        return (
            self._reconstruction_service
            .require_single_artifact(
                repository=repository,
                context=context,
                artifact_type=artifact_type,
            )
        )

    def reconstruct_intake_results(
        self,
        *,
        payload: Any,
        expected_hierarchy: str,
    ) -> tuple[
        AssessmentEvidenceIntakeResult,
        ...,
    ]:
        """
        Compatibility wrapper over the canonical persisted
        reconstruction service.
        """

        return (
            self._reconstruction_service
            .reconstruct_intake_results(
                payload=payload,
                expected_hierarchy=(
                    expected_hierarchy
                ),
            )
        )

    def _reconstruct_intake_results(
        self,
        *,
        payload: Any,
        expected_hierarchy: str,
    ) -> tuple[
        AssessmentEvidenceIntakeResult,
        ...,
    ]:
        """
        Private compatibility wrapper retained while downstream callers
        migrate to the shared reconstruction service.
        """

        return self.reconstruct_intake_results(
            payload=payload,
            expected_hierarchy=expected_hierarchy,
        )

    def reconstruct_friction_summary(
        self,
        *,
        payload: Any,
        expected_hierarchy: str,
    ) -> AssessmentFrictionSummary:
        """
        Compatibility wrapper over the canonical persisted
        reconstruction service.
        """

        return (
            self._reconstruction_service
            .reconstruct_friction_summary(
                payload=payload,
                expected_hierarchy=(
                    expected_hierarchy
                ),
            )
        )

    def _reconstruct_friction_summary(
        self,
        *,
        payload: Any,
        expected_hierarchy: str,
    ) -> AssessmentFrictionSummary:
        """
        Private compatibility wrapper retained while downstream callers
        migrate to the shared reconstruction service.
        """

        return self.reconstruct_friction_summary(
            payload=payload,
            expected_hierarchy=expected_hierarchy,
        )