from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature import (
    SignedAssessmentAuditCheckpoint,
    sign_assessment_audit_checkpoint,
    verify_assessment_audit_checkpoint_signature,
)
from backend.app.gagf.governance_assessment_checkpoint_key_registry import (
    AssessmentCheckpointSigningKeyRegistry,
)


ASSESSMENT_CHECKPOINT_KEY_SERVICE_VERSION = "1.0.0"


@dataclass(frozen=True)
class AssessmentCheckpointSignatureVerification:
    valid: bool
    tenant_id: str
    key_id: str
    reason_code: str | None = None


class AssessmentCheckpointKeyService:
    def __init__(
        self,
        *,
        registry: AssessmentCheckpointSigningKeyRegistry,
    ) -> None:
        self.registry = registry

    def sign_checkpoint(
        self,
        *,
        checkpoint: AssessmentAuditCheckpoint,
    ) -> SignedAssessmentAuditCheckpoint:
        key = self.registry.get_active_key(
            tenant_id=checkpoint.tenant_id
        )

        if not key.active:
            raise ValueError(
                "retired checkpoint signing key cannot sign"
            )

        return sign_assessment_audit_checkpoint(
            checkpoint=checkpoint,
            key_id=key.key_id,
            secret=key.secret,
        )

    def verify_signed_checkpoint(
        self,
        *,
        signed_checkpoint: SignedAssessmentAuditCheckpoint,
    ) -> AssessmentCheckpointSignatureVerification:
        tenant_id = signed_checkpoint.checkpoint.tenant_id
        key_id = signed_checkpoint.key_id

        try:
            key = self.registry.get_key(
                tenant_id=tenant_id,
                key_id=key_id,
            )
        except KeyError:
            return AssessmentCheckpointSignatureVerification(
                valid=False,
                tenant_id=tenant_id,
                key_id=key_id,
                reason_code="ASSESSMENT_CHECKPOINT_KEY_NOT_FOUND",
            )

        valid = verify_assessment_audit_checkpoint_signature(
            signed_checkpoint=signed_checkpoint,
            secret=key.secret,
        )

        return AssessmentCheckpointSignatureVerification(
            valid=valid,
            tenant_id=tenant_id,
            key_id=key_id,
            reason_code=(
                None
                if valid
                else "ASSESSMENT_CHECKPOINT_SIGNATURE_INVALID"
            ),
        )
