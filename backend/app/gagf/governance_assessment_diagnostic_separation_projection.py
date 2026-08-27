from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_diagnostic_separation import (
    AssessmentDiagnosticSeparationEvidenceSummary,
    GovernanceAssessmentDiagnosticSeparationService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_primary_diagnosis_projection import (
    GovernanceAssessmentPrimaryDiagnosisProjectionResult,
    GovernanceAssessmentPrimaryDiagnosisProjectionService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    canonical_json,
)


DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE = (
    "diagnostic-separation-evidence"
)

DIAGNOSTIC_SEPARATION_PROJECTION_VERSION = (
    "1.0.0"
)


class DiagnosticSeparationProjectionError(
    RuntimeError
):
    """
    Raised when governed diagnostic-separation
    evidence cannot be projected safely.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceAssessmentDiagnosticSeparationProjectionResult:
    hierarchy_key: str

    separation_summary: (
        AssessmentDiagnosticSeparationEvidenceSummary
    )

    artifact_id: str
    artifact_hash: str
    sequence_number: int

    repository_chain_valid: bool
    reused_existing: bool

    primary_projection_verified: bool
    structural_projection_verified: bool
    structural_classification_verified: bool

    projection_version: str = (
        DIAGNOSTIC_SEPARATION_PROJECTION_VERSION
    )

    @property
    def leading_candidate_category(
        self,
    ) -> str | None:
        return (
            self.separation_summary
            .leading_candidate_category
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "hierarchy_key":
                self.hierarchy_key,

            "separation_summary_hash":
                self.separation_summary
                .summary_hash,

            "primary_diagnosis_summary_hash":
                self.separation_summary
                .primary_diagnosis_summary_hash,

            "leading_candidate_category":
                self.leading_candidate_category,

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

            "primary_projection_verified":
                self.primary_projection_verified,

            "structural_projection_verified":
                self.structural_projection_verified,

            "structural_classification_verified":
                self.structural_classification_verified,

            "projection_version":
                self.projection_version,
        }


class GovernanceAssessmentDiagnosticSeparationProjectionService:
    """
    Persist threshold-free diagnostic-separation evidence
    derived from the governed primary-diagnosis stack.

    Projection sequence:

    1. Verify the assessment repository chain.
    2. Run the governed primary-diagnosis projection.
    3. Require primary projection hierarchy integrity.
    4. Require primary repository-chain integrity.
    5. Require structural projection verification.
    6. Require structural classification verification.
    7. Derive threshold-free separation evidence.
    8. Require separation hierarchy integrity.
    9. Bind separation evidence to the primary summary hash.
    10. Append or deterministically reuse one immutable
        diagnostic-separation-evidence artifact.
    11. Verify the repository chain again.

    This service does not:

    - classify confidence;
    - establish correctness;
    - establish causation;
    - label root cause;
    - declare a final primary diagnosis;
    - authorize intervention;
    - modify source evidence.

    Separation != Confidence.
    Confidence != Correctness.
    """

    def __init__(
        self,
        *,
        primary_projection_service: (
            GovernanceAssessmentPrimaryDiagnosisProjectionService
            | None
        ) = None,
        separation_service: (
            GovernanceAssessmentDiagnosticSeparationService
            | None
        ) = None,
    ) -> None:
        self._primary_projection_service = (
            primary_projection_service
            or
            GovernanceAssessmentPrimaryDiagnosisProjectionService()
        )

        self._separation_service = (
            separation_service
            or
            GovernanceAssessmentDiagnosticSeparationService()
        )

    def project(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
    ) -> GovernanceAssessmentDiagnosticSeparationProjectionResult:
        repository = (
            GovernanceAssessmentRepository(
                database_path
            )
        )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise (
                DiagnosticSeparationProjectionError(
                    "assessment repository chain is invalid "
                    "before diagnostic-separation projection"
                )
            )

        primary_projection = (
            self._primary_projection_service
            .project(
                database_path=database_path,
                context=context,
            )
        )

        self._validate_primary_projection(
            projection=primary_projection,
            context=context,
        )

        primary_projection_verified = True

        separation_summary = (
            self._separation_service
            .analyze(
                primary_diagnosis_summary=(
                    primary_projection
                    .primary_diagnosis_summary
                )
            )
        )

        if (
            separation_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "diagnostic-separation hierarchy "
                    "does not match assessment"
                )
            )

        if (
            separation_summary
            .primary_diagnosis_summary_hash
            != primary_projection
            .primary_diagnosis_summary
            .summary_hash
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "diagnostic-separation evidence is "
                    "not bound to the projected "
                    "primary-diagnosis summary"
                )
            )

        payload = (
            separation_summary
            .to_dict()
        )

        existing = (
            repository.list_artifacts(
                context=context,
                artifact_type=(
                    DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE
                ),
            )
        )

        if existing:
            if len(
                existing
            ) != 1:
                raise (
                    DiagnosticSeparationProjectionError(
                        "assessment contains multiple "
                        "diagnostic-separation-evidence "
                        "artifacts"
                    )
                )

            artifact = (
                existing[0]
            )

            if canonical_json(
                artifact.payload
            ) != canonical_json(
                payload
            ):
                raise (
                    DiagnosticSeparationProjectionError(
                        "existing diagnostic-separation-"
                        "evidence artifact does not match "
                        "deterministic projection"
                    )
                )

            reused_existing = True

        else:
            artifact = (
                repository.append_artifact(
                    context=context,
                    artifact_type=(
                        DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE
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
            raise (
                DiagnosticSeparationProjectionError(
                    "assessment repository chain is invalid "
                    "after diagnostic-separation projection"
                )
            )

        return (
            GovernanceAssessmentDiagnosticSeparationProjectionResult(
                hierarchy_key=(
                    context.hierarchy_key
                ),

                separation_summary=(
                    separation_summary
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

                primary_projection_verified=(
                    primary_projection_verified
                ),

                structural_projection_verified=(
                    primary_projection
                    .structural_projection_verified
                ),

                structural_classification_verified=(
                    primary_projection
                    .structural_classification_verified
                ),
            )
        )

    def _validate_primary_projection(
        self,
        *,
        projection: (
            GovernanceAssessmentPrimaryDiagnosisProjectionResult
        ),
        context: CommercialHierarchyContext,
    ) -> None:
        if (
            projection.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "primary-diagnosis projection hierarchy "
                    "does not match assessment"
                )
            )

        if (
            projection.repository_chain_valid
            is not True
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "primary-diagnosis projection did not "
                    "preserve repository chain validity"
                )
            )

        if (
            projection.structural_projection_verified
            is not True
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "primary-diagnosis projection did not "
                    "verify structural projection"
                )
            )

        if (
            projection.structural_classification_verified
            is not True
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "primary-diagnosis projection did not "
                    "verify structural classification"
                )
            )

        if (
            projection.primary_diagnosis_summary
            .hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                DiagnosticSeparationProjectionError(
                    "projected primary-diagnosis evidence "
                    "hierarchy does not match assessment"
                )
            )