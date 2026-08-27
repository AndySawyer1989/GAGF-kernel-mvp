from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_primary_diagnosis_evidence import (
    AssessmentPrimaryDiagnosisEvidenceSummary,
    GovernanceAssessmentPrimaryDiagnosisEvidenceService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    canonical_json,
)
from backend.app.gagf.governance_assessment_structural_importance_classification import (
    AssessmentStructuralImportanceClassificationSummary,
    GovernanceAssessmentStructuralImportanceClassificationService,
)
from backend.app.gagf.governance_assessment_structural_importance_projection import (
    GovernanceAssessmentStructuralImportanceProjectionResult,
    GovernanceAssessmentStructuralImportanceProjectionService,
)


PRIMARY_DIAGNOSIS_EVIDENCE_ARTIFACT_TYPE = (
    "primary-diagnosis-evidence"
)

PRIMARY_DIAGNOSIS_PROJECTION_VERSION = (
    "1.0.0"
)


class PrimaryDiagnosisProjectionError(
    RuntimeError
):
    """
    Raised when governed primary-diagnosis evidence
    cannot be projected safely.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceAssessmentPrimaryDiagnosisProjectionResult:
    hierarchy_key: str

    primary_diagnosis_summary: (
        AssessmentPrimaryDiagnosisEvidenceSummary
    )

    structural_classification_summary: (
        AssessmentStructuralImportanceClassificationSummary
    )

    artifact_id: str
    artifact_hash: str
    sequence_number: int

    repository_chain_valid: bool
    reused_existing: bool

    structural_projection_verified: bool
    structural_classification_verified: bool

    projection_version: str = (
        PRIMARY_DIAGNOSIS_PROJECTION_VERSION
    )

    @property
    def condition_count(
        self,
    ) -> int:
        return (
            self.primary_diagnosis_summary
            .condition_count
        )

    @property
    def highest_ranked_condition(
        self,
    ) -> str | None:
        return (
            self.primary_diagnosis_summary
            .highest_ranked_condition
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "hierarchy_key":
                self.hierarchy_key,

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary
                .summary_hash,

            "structural_classification_summary_hash":
                self.structural_classification_summary
                .summary_hash,

            "condition_count":
                self.condition_count,

            "highest_ranked_condition":
                self.highest_ranked_condition,

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

            "structural_projection_verified":
                self.structural_projection_verified,

            "structural_classification_verified":
                self.structural_classification_verified,

            "projection_version":
                self.projection_version,
        }


class GovernanceAssessmentPrimaryDiagnosisProjectionService:
    """
    Project relative primary-diagnosis evidence from the
    governed structural-importance stack.

    Projection sequence:

    1. Verify the assessment repository chain.
    2. Run the governed structural-importance projection.
    3. Require structural projection hierarchy integrity.
    4. Require structural repository-chain integrity.
    5. Require structural diagnostic-integrity verification.
    6. Freshly classify structural-importance evidence.
    7. Require classification hierarchy integrity.
    8. Derive relative primary-diagnosis evidence.
    9. Require primary-diagnosis evidence hierarchy integrity.
    10. Append or deterministically reuse one immutable
        primary-diagnosis-evidence artifact.
    11. Verify the assessment repository chain again.

    This service does not:

    - inspect PRELIVE oracle information;
    - establish causation;
    - label root cause;
    - declare the highest-ranked condition to be a
      final primary diagnosis;
    - authorize intervention;
    - modify source evidence.
    """

    def __init__(
        self,
        *,
        structural_projection_service: (
            GovernanceAssessmentStructuralImportanceProjectionService
            | None
        ) = None,
        structural_classification_service: (
            GovernanceAssessmentStructuralImportanceClassificationService
            | None
        ) = None,
        primary_diagnosis_service: (
            GovernanceAssessmentPrimaryDiagnosisEvidenceService
            | None
        ) = None,
    ) -> None:
        self._structural_projection_service = (
            structural_projection_service
            or
            GovernanceAssessmentStructuralImportanceProjectionService()
        )

        self._structural_classification_service = (
            structural_classification_service
            or
            GovernanceAssessmentStructuralImportanceClassificationService()
        )

        self._primary_diagnosis_service = (
            primary_diagnosis_service
            or
            GovernanceAssessmentPrimaryDiagnosisEvidenceService()
        )

    def project(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
    ) -> GovernanceAssessmentPrimaryDiagnosisProjectionResult:
        repository = (
            GovernanceAssessmentRepository(
                database_path
            )
        )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise PrimaryDiagnosisProjectionError(
                "assessment repository chain is invalid "
                "before primary-diagnosis projection"
            )

        structural_projection = (
            self._structural_projection_service
            .project(
                database_path=database_path,
                context=context,
            )
        )

        self._validate_structural_projection(
            projection=structural_projection,
            context=context,
        )

        structural_projection_verified = True

        structural_classification = (
            self._structural_classification_service
            .classify(
                structural_summary=(
                    structural_projection
                    .structural_summary
                )
            )
        )

        if (
            structural_classification.hierarchy_key
            != context.hierarchy_key
        ):
            raise PrimaryDiagnosisProjectionError(
                "structural classification hierarchy "
                "does not match assessment"
            )

        structural_classification_verified = True

        primary_diagnosis_summary = (
            self._primary_diagnosis_service
            .analyze(
                structural_classification_summary=(
                    structural_classification
                )
            )
        )

        if (
            primary_diagnosis_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise PrimaryDiagnosisProjectionError(
                "primary-diagnosis evidence hierarchy "
                "does not match assessment"
            )

        payload = (
            primary_diagnosis_summary
            .to_dict()
        )

        existing = (
            repository.list_artifacts(
                context=context,
                artifact_type=(
                    PRIMARY_DIAGNOSIS_EVIDENCE_ARTIFACT_TYPE
                ),
            )
        )

        if existing:
            if len(
                existing
            ) != 1:
                raise PrimaryDiagnosisProjectionError(
                    "assessment contains multiple "
                    "primary-diagnosis-evidence artifacts"
                )

            artifact = existing[0]

            if canonical_json(
                artifact.payload
            ) != canonical_json(
                payload
            ):
                raise PrimaryDiagnosisProjectionError(
                    "existing primary-diagnosis-evidence "
                    "artifact does not match deterministic "
                    "projection"
                )

            reused_existing = True

        else:
            artifact = (
                repository.append_artifact(
                    context=context,
                    artifact_type=(
                        PRIMARY_DIAGNOSIS_EVIDENCE_ARTIFACT_TYPE
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
            raise PrimaryDiagnosisProjectionError(
                "assessment repository chain is invalid "
                "after primary-diagnosis projection"
            )

        return (
            GovernanceAssessmentPrimaryDiagnosisProjectionResult(
                hierarchy_key=(
                    context.hierarchy_key
                ),

                primary_diagnosis_summary=(
                    primary_diagnosis_summary
                ),

                structural_classification_summary=(
                    structural_classification
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

                structural_projection_verified=(
                    structural_projection_verified
                ),

                structural_classification_verified=(
                    structural_classification_verified
                ),
            )
        )

    def _validate_structural_projection(
        self,
        *,
        projection: (
            GovernanceAssessmentStructuralImportanceProjectionResult
        ),
        context: CommercialHierarchyContext,
    ) -> None:
        if (
            projection.hierarchy_key
            != context.hierarchy_key
        ):
            raise PrimaryDiagnosisProjectionError(
                "structural projection hierarchy "
                "does not match assessment"
            )

        if (
            projection.repository_chain_valid
            is not True
        ):
            raise PrimaryDiagnosisProjectionError(
                "structural projection did not "
                "preserve repository chain validity"
            )

        if (
            projection.diagnostic_integrity_verified
            is not True
        ):
            raise PrimaryDiagnosisProjectionError(
                "structural projection did not verify "
                "diagnostic integrity"
            )