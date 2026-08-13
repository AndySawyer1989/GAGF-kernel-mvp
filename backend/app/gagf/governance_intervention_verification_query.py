from __future__ import annotations

from pathlib import Path

from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationLedger,
    GovernanceInterventionVerificationLedgerVerification,
    GovernanceInterventionVerificationRecord,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleEvent,
    GovernanceInterventionVerificationLifecycleLedger,
    GovernanceInterventionVerificationLifecycleState,
)


class GovernanceInterventionVerificationQueryError(ValueError):
    """Base error for governed verification queries."""


class GovernanceInterventionVerificationQueryService:
    """
    Read-only operational query boundary over the I-G verification ledger.

    This service:
    - never creates a verification disposition;
    - never mutates verification history;
    - never authorizes future intervention activity;
    - never performs causal inference.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self._ledger = GovernanceInterventionVerificationLedger(
            database_path
        )

        self._lifecycle_ledger = (
            GovernanceInterventionVerificationLifecycleLedger(
                database_path=database_path
            )
        )

    def get_by_summary_hash(
        self,
        *,
        tenant_id: str,
        verification_summary_hash: str,
    ) -> GovernanceInterventionVerificationRecord | None:
        return self._ledger.get_by_summary_hash(
            tenant_id=tenant_id,
            verification_summary_hash=(
                verification_summary_hash
            ),
        )

    def list_for_intervention(
        self,
        *,
        tenant_id: str,
        intervention_id: str,
    ) -> tuple[
        GovernanceInterventionVerificationRecord,
        ...,
    ]:
        return self._ledger.list_for_intervention(
            tenant_id=tenant_id,
            intervention_id=intervention_id,
        )

    def verify_tenant_ledger(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionVerificationLedgerVerification:
        return self._ledger.verify_tenant_chain(
            tenant_id=tenant_id
        )

    def get_lifecycle_state(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> (
        GovernanceInterventionVerificationLifecycleState
        | None
    ):
        return self._lifecycle_ledger.get_current_state(
            tenant_id=tenant_id,
            verification_record_hash=(
                verification_record_hash
            ),
        )

    def list_lifecycle_history(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> tuple[
        GovernanceInterventionVerificationLifecycleEvent,
        ...,
    ]:
        return self._lifecycle_ledger.list_history(
            tenant_id=tenant_id,
            verification_record_hash=(
                verification_record_hash
            ),
        )