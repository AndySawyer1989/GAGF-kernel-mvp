from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.diagnostic_calibration_blind_evidence import (
    BlindEvidenceGenerationResult,
    DiagnosticCalibrationBlindEvidenceService,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    GovernanceAssessmentEvidenceIntakeService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


BLIND_EVIDENCE_INTAKE_BRIDGE_VERSION = "1.0.0"

BLIND_EVIDENCE_INTAKE_BRIDGE_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_EVIDENCE_ONLY"
)


class BlindEvidenceIntakeBridgeError(
    RuntimeError
):
    """
    Raised when validated blind calibration evidence cannot
    be handed into the real governance assessment intake.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class BlindEvidenceIntakeBridgeResult:
    scenario_id: str
    public_hash: str
    generator_id: str
    generation_id: str

    hierarchy_key: str

    source_id: str

    evidence_hash: str

    intake_result: (
        AssessmentEvidenceIntakeResult
    )

    authority: str = (
        BLIND_EVIDENCE_INTAKE_BRIDGE_AUTHORITY
    )

    version: str = (
        BLIND_EVIDENCE_INTAKE_BRIDGE_VERSION
    )

    @property
    def accepted_count(
        self,
    ) -> int:
        return (
            self.intake_result
            .accepted_count
        )

    @property
    def rejected_count(
        self,
    ) -> int:
        return (
            self.intake_result
            .rejected_count
        )

    @property
    def valid(
        self,
    ) -> bool:
        return (
            self.intake_result
            .valid
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

            "source_id":
                self.source_id,

            "evidence_hash":
                self.evidence_hash,

            "accepted_count":
                self.accepted_count,

            "rejected_count":
                self.rejected_count,

            "valid":
                self.valid,

            "intake_hash":
                self.intake_result
                .intake_hash,

            "authority":
                self.authority,

            "version":
                self.version,
        }


class DiagnosticCalibrationBlindEvidenceIntakeBridgeService:
    """
    Convert already-validated blind calibration evidence
    into the real governance assessment CSV intake path.

    The bridge does not:

    - inspect sealed oracle information;
    - modify evidence semantics;
    - infer diagnostic labels;
    - bypass intake validation.

    Validated blind evidence
        -> canonical CSV
        -> existing FIP intake.
    """

    def __init__(
        self,
        *,
        blind_evidence_service: (
            DiagnosticCalibrationBlindEvidenceService
            | None
        ) = None,
        intake_service: (
            GovernanceAssessmentEvidenceIntakeService
            | None
        ) = None,
    ) -> None:
        self._blind_evidence_service = (
            blind_evidence_service
            or
            DiagnosticCalibrationBlindEvidenceService()
        )

        self._intake_service = (
            intake_service
            or
            GovernanceAssessmentEvidenceIntakeService()
        )

    def ingest(
        self,
        *,
        context: CommercialHierarchyContext,
        evidence: BlindEvidenceGenerationResult,
    ) -> BlindEvidenceIntakeBridgeResult:
        if (
            context.engagement_id is None
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Calibration evidence intake requires "
                    "engagement_id."
                )
            )

        if (
            context.assessment_id is None
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Calibration evidence intake requires "
                    "assessment_id."
                )
            )

        csv_text = (
            self._blind_evidence_service
            .to_csv(
                result=evidence
            )
        )

        source_id = (
            "calibration:"
            f"{evidence.scenario_id}:"
            f"{evidence.generator_id}:"
            f"{evidence.generation_id}"
        )

        source = (
            EvidenceSourceReference(
                source_id=(
                    source_id
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

        intake_result = (
            self._intake_service
            .ingest_csv(
                context=(
                    context
                ),

                source=(
                    source
                ),

                csv_text=(
                    csv_text
                ),
            )
        )

        if (
            intake_result.hierarchy_key
            != context.hierarchy_key
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Evidence intake hierarchy does "
                    "not match calibration assessment."
                )
            )

        if (
            intake_result.source.source_id
            != source_id
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Evidence intake source_id does "
                    "not match calibration source."
                )
            )

        if (
            intake_result.total_rows
            != evidence.event_count
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Evidence intake row count does "
                    "not match blind evidence."
                )
            )

        if (
            intake_result.accepted_count
            != evidence.event_count
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Validated blind evidence was "
                    "rejected by governance assessment "
                    "evidence intake."
                )
            )

        if (
            intake_result.rejected_count
            != 0
        ):
            raise (
                BlindEvidenceIntakeBridgeError(
                    "Validated blind evidence produced "
                    "rejected intake rows."
                )
            )

        return (
            BlindEvidenceIntakeBridgeResult(
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

                source_id=(
                    source_id
                ),

                evidence_hash=(
                    evidence.evidence_hash
                ),

                intake_result=(
                    intake_result
                ),
            )
        )