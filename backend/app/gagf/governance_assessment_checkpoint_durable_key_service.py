from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature import (
    SignedAssessmentAuditCheckpoint,
    sign_assessment_audit_checkpoint,
    verify_assessment_audit_checkpoint_signature,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadata,
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    AssessmentCheckpointSecretResolver,
)


ASSESSMENT_CHECKPOINT_DURABLE_KEY_SERVICE_VERSION = "1.0.0"


@dataclass(frozen=True)
class DurableCheckpointSignatureVerification:
    valid: bool
    tenant_id: str
    key_id: str
    reason_code: str | None = None


class AssessmentCheckpointDurableKeyService:
    def __init__(
        self,
        *,
        metadata_store: AssessmentCheckpointSigningKeyMetadataStore,
        secret_resolver: AssessmentCheckpointSecretResolver,
    ) -> None:
        self.metadata_store = metadata_store
        self.secret_resolver = secret_resolver

    def register_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
        secret_reference: str,
        make_active: bool = False,
    ) -> AssessmentCheckpointSigningKeyMetadata:
        normalized_tenant_id = tenant_id.strip()
        normalized_key_id = key_id.strip()
        normalized_reference = secret_reference.strip()

        if not normalized_tenant_id:
            raise ValueError("tenant_id is required")

        if not normalized_key_id:
            raise ValueError("key_id is required")

        if not normalized_reference:
            raise ValueError("secret_reference is required")

        self.secret_resolver.resolve_secret(
            secret_reference=normalized_reference
        )

        metadata = AssessmentCheckpointSigningKeyMetadata(
            tenant_id=normalized_tenant_id,
            key_id=normalized_key_id,
            secret_reference=normalized_reference,
            active=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.metadata_store.insert(metadata)

        if make_active:
            return self.activate_key(
                tenant_id=normalized_tenant_id,
                key_id=normalized_key_id,
            )

        return metadata

    def activate_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
    ) -> AssessmentCheckpointSigningKeyMetadata:
        selected = self.metadata_store.get_key(
            tenant_id=tenant_id,
            key_id=key_id,
        )

        try:
            current = self.metadata_store.get_active_key(
                tenant_id=tenant_id
            )
        except KeyError:
            current = None

        if current is not None and current.key_id != key_id:
            retired = replace(
                current,
                active=False,
                retired_at=datetime.now(
                    timezone.utc
                ).isoformat(),
            )
            self.metadata_store.replace(retired)

        activated = replace(
            selected,
            active=True,
            retired_at=None,
        )
        self.metadata_store.replace(activated)
        return activated

    def sign_checkpoint(
        self,
        *,
        checkpoint: AssessmentAuditCheckpoint,
    ) -> SignedAssessmentAuditCheckpoint:
        metadata = self.metadata_store.get_active_key(
            tenant_id=checkpoint.tenant_id
        )
        secret = self.secret_resolver.resolve_secret(
            secret_reference=metadata.secret_reference
        )

        return sign_assessment_audit_checkpoint(
            checkpoint=checkpoint,
            key_id=metadata.key_id,
            secret=secret,
        )

    def verify_signed_checkpoint(
        self,
        *,
        signed_checkpoint: SignedAssessmentAuditCheckpoint,
    ) -> DurableCheckpointSignatureVerification:
        tenant_id = signed_checkpoint.checkpoint.tenant_id
        key_id = signed_checkpoint.key_id

        try:
            metadata = self.metadata_store.get_key(
                tenant_id=tenant_id,
                key_id=key_id,
            )
        except KeyError:
            return DurableCheckpointSignatureVerification(
                valid=False,
                tenant_id=tenant_id,
                key_id=key_id,
                reason_code="ASSESSMENT_CHECKPOINT_KEY_NOT_FOUND",
            )

        try:
            secret = self.secret_resolver.resolve_secret(
                secret_reference=metadata.secret_reference
            )
        except KeyError:
            return DurableCheckpointSignatureVerification(
                valid=False,
                tenant_id=tenant_id,
                key_id=key_id,
                reason_code="ASSESSMENT_CHECKPOINT_SECRET_NOT_FOUND",
            )

        valid = verify_assessment_audit_checkpoint_signature(
            signed_checkpoint=signed_checkpoint,
            secret=secret,
        )

        return DurableCheckpointSignatureVerification(
            valid=valid,
            tenant_id=tenant_id,
            key_id=key_id,
            reason_code=(
                None
                if valid
                else "ASSESSMENT_CHECKPOINT_SIGNATURE_INVALID"
            ),
        )
