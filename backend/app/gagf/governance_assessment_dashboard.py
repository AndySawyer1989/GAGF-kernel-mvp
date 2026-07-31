from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_audit import (
    AssessmentCheckpointKeyAuditStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)


GOVERNANCE_ASSESSMENT_DASHBOARD_VERSION = "1.0.0"


@dataclass(frozen=True)
class GovernanceAssessmentDashboardSummary:
    tenant_id: str
    audit_event_count: int
    audit_chain_valid: bool
    checkpoint_count: int
    signed_checkpoint_count: int
    active_signing_key_id: str | None
    signing_key_count: int
    key_activation_event_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "audit_event_count": self.audit_event_count,
            "audit_chain_valid": self.audit_chain_valid,
            "checkpoint_count": self.checkpoint_count,
            "signed_checkpoint_count": (
                self.signed_checkpoint_count
            ),
            "active_signing_key_id": (
                self.active_signing_key_id
            ),
            "signing_key_count": self.signing_key_count,
            "key_activation_event_count": (
                self.key_activation_event_count
            ),
        }


class GovernanceAssessmentDashboardService:
    def __init__(
        self,
        *,
        audit_ledger: AssessmentAuditLedger,
        checkpoint_store: AssessmentAuditCheckpointStore,
        signed_checkpoint_store: (
            SignedAssessmentAuditCheckpointStore
        ),
        key_metadata_store: (
            AssessmentCheckpointSigningKeyMetadataStore | None
        ) = None,
        key_audit_store: (
            AssessmentCheckpointKeyAuditStore | None
        ) = None,
    ) -> None:
        self.audit_ledger = audit_ledger
        self.checkpoint_store = checkpoint_store
        self.signed_checkpoint_store = signed_checkpoint_store
        self.key_metadata_store = key_metadata_store
        self.key_audit_store = key_audit_store

    def build_summary(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceAssessmentDashboardSummary:
        audit_events = self.audit_ledger.list_events(
            tenant_id=tenant_id,
            limit=500,
        )
        audit_verification = (
            self.audit_ledger.verify_tenant_chain(
                tenant_id=tenant_id
            )
        )
        checkpoints = self.checkpoint_store.list_checkpoints(
            tenant_id=tenant_id,
            limit=500,
        )
        signed_checkpoints = (
            self.signed_checkpoint_store.list_signed_checkpoints(
                tenant_id=tenant_id,
                limit=500,
            )
        )

        active_signing_key_id = None
        signing_key_count = 0

        if self.key_metadata_store is not None:
            keys = self.key_metadata_store.list_keys(
                tenant_id=tenant_id
            )
            signing_key_count = len(keys)

            try:
                active = self.key_metadata_store.get_active_key(
                    tenant_id=tenant_id
                )
            except KeyError:
                active = None

            if active is not None:
                active_signing_key_id = active.key_id

        key_activation_event_count = 0

        if self.key_audit_store is not None:
            key_activation_event_count = len(
                self.key_audit_store.list_events(
                    tenant_id=tenant_id,
                    limit=500,
                )
            )

        return GovernanceAssessmentDashboardSummary(
            tenant_id=tenant_id,
            audit_event_count=len(audit_events),
            audit_chain_valid=audit_verification.valid,
            checkpoint_count=len(checkpoints),
            signed_checkpoint_count=len(signed_checkpoints),
            active_signing_key_id=active_signing_key_id,
            signing_key_count=signing_key_count,
            key_activation_event_count=(
                key_activation_event_count
            ),
        )
