from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    ALLOWED_PILOT_CLASSIFICATIONS,
    RealPaidAssessmentIntake,
)


REAL_PAID_ASSESSMENT_EXECUTION_EVIDENCE_ID = (
    "governance-real-paid-assessment-execution-evidence"
)
REAL_PAID_ASSESSMENT_EXECUTION_EVIDENCE_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_EXECUTION_EVIDENCE_SCHEMA_VERSION = "1.0.0"

EXECUTION_EVIDENCE_STATUS_APPROVED = (
    "execution_evidence_approved"
)


class RealPaidAssessmentExecutionEvidenceError(ValueError):
    """Raised when execution evidence cannot be bound safely."""


def _require_text(value: str, field_name: str) -> str:
    normalized = str(value).strip()

    if not normalized:
        raise RealPaidAssessmentExecutionEvidenceError(
            f"{field_name} is required"
        )

    return normalized


def _sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class RealAssessmentExecutionEvidenceApproval:
    evidence_id: str
    approved_content_sha256: str
    approved_by: str
    approved_at: str
    execution_evidence_approved: bool

    def __post_init__(self) -> None:
        _require_text(
            self.evidence_id,
            "evidence_id",
        )
        digest = _require_text(
            self.approved_content_sha256,
            "approved_content_sha256",
        )
        _require_text(
            self.approved_by,
            "approved_by",
        )
        approved_at = _require_text(
            self.approved_at,
            "approved_at",
        )

        if len(digest) != 64:
            raise RealPaidAssessmentExecutionEvidenceError(
                "approved_content_sha256 must be a SHA-256 hex digest"
            )

        try:
            int(digest, 16)
        except ValueError as exc:
            raise RealPaidAssessmentExecutionEvidenceError(
                "approved_content_sha256 must be hexadecimal"
            ) from exc

        try:
            datetime.fromisoformat(
                approved_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise RealPaidAssessmentExecutionEvidenceError(
                "approved_at must be ISO-8601"
            ) from exc

        if self.execution_evidence_approved is not True:
            raise RealPaidAssessmentExecutionEvidenceError(
                "execution evidence approval must be affirmative"
            )


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentExecutionEvidenceBinding:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    approved_evidence_ids: tuple[str, ...]
    evidence_content_hashes: tuple[str, ...]

    binding_status: str
    binding_type: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_EVIDENCE_ID
    )
    version: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_EVIDENCE_VERSION
    )
    schema_version: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_EVIDENCE_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_type": self.binding_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "approved_evidence_ids": (
                self.approved_evidence_ids
            ),
            "evidence_content_hashes": (
                self.evidence_content_hashes
            ),
            "binding_status": self.binding_status,
            "boundaries": {
                "evidence_hash_approval_is_not_paid_work_authorization": True,
                "evidence_hash_approval_is_not_execution": True,
                "content_hash_match_is_not_evidence_truth": True,
                "content_hash_match_is_not_compliance_certification": True,
                "execution_evidence_approval_is_not_production_onboarding": True,
            },
        }


class GovernanceRealPaidAssessmentExecutionEvidenceService:
    """
    Bind the exact evidence bytes about to be executed to the evidence
    declarations that passed PILOT-002 readiness.

    PILOT-003 supports only the currently implemented CSV demonstration
    evidence input path.
    """

    def bind(
        self,
        *,
        intake: RealPaidAssessmentIntake,
        request: AssessmentExecutionRequest,
        approvals: tuple[
            RealAssessmentExecutionEvidenceApproval, ...
        ],
    ) -> RealPaidAssessmentExecutionEvidenceBinding:
        if not isinstance(
            intake,
            RealPaidAssessmentIntake,
        ):
            raise RealPaidAssessmentExecutionEvidenceError(
                "intake must be a RealPaidAssessmentIntake"
            )

        if not isinstance(
            request,
            AssessmentExecutionRequest,
        ):
            raise RealPaidAssessmentExecutionEvidenceError(
                "request must be an AssessmentExecutionRequest"
            )

        if not approvals:
            raise RealPaidAssessmentExecutionEvidenceError(
                "at least one execution evidence approval is required"
            )

        expected_hierarchy = (
            intake.tenant_id,
            intake.client_id,
            intake.engagement_id,
            intake.assessment_id,
        )

        request_hierarchy = (
            request.context.tenant_id,
            request.context.client_id,
            request.context.engagement_id,
            request.context.assessment_id,
        )

        if request_hierarchy != expected_hierarchy:
            raise RealPaidAssessmentExecutionEvidenceError(
                "assessment execution request hierarchy does not match intake"
            )

        if request.assessment_name != intake.assessment_name:
            raise RealPaidAssessmentExecutionEvidenceError(
                "assessment execution request name does not match intake"
            )

        if request.client_display_name != intake.client_display_name:
            raise RealPaidAssessmentExecutionEvidenceError(
                "client display name does not match intake"
            )

        declarations = {
            declaration.evidence_id: declaration
            for declaration in intake.evidence
        }

        if len(declarations) != len(intake.evidence):
            raise RealPaidAssessmentExecutionEvidenceError(
                "intake contains duplicate evidence_id values"
            )

        approval_map = {
            approval.evidence_id: approval
            for approval in approvals
        }

        if len(approval_map) != len(approvals):
            raise RealPaidAssessmentExecutionEvidenceError(
                "duplicate execution evidence approvals"
            )

        execution_inputs = {
            evidence_input.source.source_id: evidence_input
            for evidence_input in request.evidence_inputs
        }

        if len(execution_inputs) != len(request.evidence_inputs):
            raise RealPaidAssessmentExecutionEvidenceError(
                "assessment request contains duplicate evidence source IDs"
            )

        declaration_ids = set(declarations)
        approval_ids = set(approval_map)
        execution_ids = set(execution_inputs)

        if declaration_ids != execution_ids:
            raise RealPaidAssessmentExecutionEvidenceError(
                "executed evidence IDs do not exactly match intake declarations"
            )

        if declaration_ids != approval_ids:
            raise RealPaidAssessmentExecutionEvidenceError(
                "execution evidence approvals do not exactly match declarations"
            )

        hashes: list[str] = []

        for evidence_id in sorted(declaration_ids):
            declaration = declarations[evidence_id]
            approval = approval_map[evidence_id]
            execution_input = execution_inputs[evidence_id]

            if (
                declaration.classification
                not in ALLOWED_PILOT_CLASSIFICATIONS
            ):
                raise RealPaidAssessmentExecutionEvidenceError(
                    "evidence classification is not permitted for PILOT-003: "
                    f"{evidence_id}:"
                    f"{declaration.classification.value}"
                )

            execution_kind = (
                execution_input.source.kind.value
                if hasattr(execution_input.source.kind, "value")
                else str(execution_input.source.kind)
            )

            if (
                execution_kind.strip().lower()
                != declaration.source_kind.strip().lower()
            ):
                raise RealPaidAssessmentExecutionEvidenceError(
                    "executed evidence source kind does not match declaration: "
                    f"{evidence_id}"
                )

            actual_hash = _sha256_text(
                execution_input.csv_text
            )

            if (
                actual_hash.lower()
                != approval.approved_content_sha256.lower()
            ):
                raise RealPaidAssessmentExecutionEvidenceError(
                    "executed evidence content hash does not match approval: "
                    f"{evidence_id}"
                )

            hashes.append(actual_hash)

        return RealPaidAssessmentExecutionEvidenceBinding(
            tenant_id=intake.tenant_id,
            client_id=intake.client_id,
            engagement_id=intake.engagement_id,
            assessment_id=intake.assessment_id,
            approved_evidence_ids=tuple(
                sorted(declaration_ids)
            ),
            evidence_content_hashes=tuple(hashes),
            binding_status=EXECUTION_EVIDENCE_STATUS_APPROVED,
        )


SERVICE_TYPE = (
    GovernanceRealPaidAssessmentExecutionEvidenceService
)