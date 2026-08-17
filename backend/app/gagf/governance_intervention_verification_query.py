from __future__ import annotations

from pathlib import Path

from backend.app.gagf.governance_intervention_reverification_request import (
    GovernanceInterventionReverificationRequest,
)
from backend.app.gagf.governance_intervention_reverification_request_ledger import (
    GovernanceInterventionReverificationRequestLedger,
    GovernanceInterventionReverificationRequestLedgerVerification,
)
from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.governance_intervention_reverification_work_order_ledger import (
    GovernanceInterventionReverificationWorkOrderLedger,
    GovernanceInterventionReverificationWorkOrderLedgerVerification,
)
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
    Read-only operational query boundary over governed intervention
    verification and reverification ledgers.

    This service:
    - never creates a verification disposition;
    - never creates a reverification request;
    - never creates a reverification work order;
    - never starts or executes reverification;
    - never performs measurement or observation;
    - never mutates verification or lifecycle history;
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

        self._reverification_request_ledger = (
            GovernanceInterventionReverificationRequestLedger(
                database_path
            )
        )

        self._reverification_work_order_ledger = (
            GovernanceInterventionReverificationWorkOrderLedger(
                database_path
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
    ) -> GovernanceInterventionVerificationLifecycleState | None:
        return self._lifecycle_ledger.get_current_state(
            tenant_id=tenant_id,
            verification_record_hash=verification_record_hash,
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
            verification_record_hash=verification_record_hash,
        )

    def get_reverification_request(
        self,
        *,
        tenant_id: str,
        request_hash: str,
    ) -> GovernanceInterventionReverificationRequest | None:
        return (
            self._reverification_request_ledger.get_by_request_hash(
                tenant_id=tenant_id,
                request_hash=request_hash,
            )
        )

    def list_reverification_requests_for_record(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> tuple[
        GovernanceInterventionReverificationRequest,
        ...,
    ]:
        return (
            self._reverification_request_ledger
            .list_for_verification_record(
                tenant_id=tenant_id,
                verification_record_hash=verification_record_hash,
            )
        )

    def verify_reverification_request_ledger(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionReverificationRequestLedgerVerification:
        return (
            self._reverification_request_ledger.verify_tenant_chain(
                tenant_id=tenant_id
            )
        )

    def get_reverification_work_order(
        self,
        *,
        tenant_id: str,
        work_order_hash: str,
    ) -> GovernanceInterventionReverificationWorkOrder | None:
        return (
            self._reverification_work_order_ledger
            .get_by_work_order_hash(
                tenant_id=tenant_id,
                work_order_hash=work_order_hash,
            )
        )

    def list_reverification_work_orders_for_request(
        self,
        *,
        tenant_id: str,
        request_hash: str,
    ) -> tuple[
        GovernanceInterventionReverificationWorkOrder,
        ...,
    ]:
        return (
            self._reverification_work_order_ledger.list_for_request(
                tenant_id=tenant_id,
                request_hash=request_hash,
            )
        )

    def verify_reverification_work_order_ledger(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionReverificationWorkOrderLedgerVerification:
        return (
            self._reverification_work_order_ledger.verify_tenant_chain(
                tenant_id=tenant_id
            )
        )