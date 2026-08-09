from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournalRecord,
    GovernanceInterventionActuationState,
)
from backend.app.gagf.governance_intervention_execution_result import (
    GovernanceInterventionExecutionDisposition,
    GovernanceInterventionExecutionResult,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_ID = (
    "governance-intervention-execution-receipt"
)
GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionExecutionReceiptError(ValueError):
    """Base error for governed intervention execution receipts."""


class InvalidGovernanceInterventionExecutionReceiptLineageError(
    GovernanceInterventionExecutionReceiptError
):
    """Raised when result and journal evidence do not share valid lineage."""


class InvalidGovernanceInterventionExecutionReceiptStateError(
    GovernanceInterventionExecutionReceiptError
):
    """Raised when execution state cannot support receipt construction."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionExecutionReceipt:
    """
    Deterministic integrity receipt for a governed execution result.

    The receipt binds a verified GEX-001F execution result to its terminal
    GEX-001E journal state.

    It proves deterministic integrity and lineage of the supplied execution
    evidence. It does not independently prove that an external real-world
    effect occurred, succeeded, or achieved the desired governance outcome.
    """

    receipt_id: str
    receipt_version: str
    schema_version: str

    tenant_id: str
    actuation_id: str
    contract_hash: str
    idempotency_key: str

    result_hash: str

    intervention_id: str
    intervention_type: str

    adapter_id: str
    adapter_version: str
    attempt_number: int

    disposition: GovernanceInterventionExecutionDisposition
    journal_state: GovernanceInterventionActuationState
    journal_transition_count: int

    receipt_hash: str

    def payload(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "receipt_version": self.receipt_version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "actuation_id": self.actuation_id,
            "contract_hash": self.contract_hash,
            "idempotency_key": self.idempotency_key,
            "result_hash": self.result_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "attempt_number": self.attempt_number,
            "disposition": self.disposition.value,
            "journal_state": self.journal_state.value,
            "journal_transition_count": self.journal_transition_count,
        }

    def verify(self) -> bool:
        return self.receipt_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "receipt_hash": self.receipt_hash,
        }


class GovernanceInterventionExecutionReceiptBuilder:
    """
    Builds deterministic GEX-001H execution receipts.

    Receipt construction requires a verified GEX-001F result and matching
    terminal journal evidence. Receipt creation performs no execution,
    dispatch, actuation, rollback, or outcome verification.
    """

    _RESULT_TO_JOURNAL_STATE = {
        GovernanceInterventionExecutionDisposition.COMPLETED: (
            GovernanceInterventionActuationState.COMPLETED
        ),
        GovernanceInterventionExecutionDisposition.FAILED: (
            GovernanceInterventionActuationState.FAILED
        ),
        GovernanceInterventionExecutionDisposition.ABORTED: (
            GovernanceInterventionActuationState.ABORTED
        ),
        GovernanceInterventionExecutionDisposition.ROLLBACK_REQUIRED: (
            GovernanceInterventionActuationState.ROLLBACK_REQUIRED
        ),
    }

    @classmethod
    def build(
        cls,
        *,
        execution_result: GovernanceInterventionExecutionResult,
        journal_record: GovernanceInterventionActuationJournalRecord,
    ) -> GovernanceInterventionExecutionReceipt:
        if not execution_result.verify():
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "execution result failed deterministic verification"
            )

        cls._validate_lineage(
            execution_result=execution_result,
            journal_record=journal_record,
        )

        cls._validate_terminal_state(
            execution_result=execution_result,
            journal_record=journal_record,
        )

        payload = {
            "receipt_id": (
                GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_ID
            ),
            "receipt_version": (
                GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_SCHEMA_VERSION
            ),
            "tenant_id": execution_result.tenant_id,
            "actuation_id": execution_result.actuation_id,
            "contract_hash": execution_result.contract_hash,
            "idempotency_key": execution_result.idempotency_key,
            "result_hash": execution_result.result_hash,
            "intervention_id": execution_result.intervention_id,
            "intervention_type": execution_result.intervention_type,
            "adapter_id": execution_result.adapter_id,
            "adapter_version": execution_result.adapter_version,
            "attempt_number": execution_result.attempt_number,
            "disposition": execution_result.disposition.value,
            "journal_state": journal_record.current_state.value,
            "journal_transition_count": journal_record.transition_count,
        }

        return GovernanceInterventionExecutionReceipt(
            receipt_id=payload["receipt_id"],
            receipt_version=payload["receipt_version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            actuation_id=payload["actuation_id"],
            contract_hash=payload["contract_hash"],
            idempotency_key=payload["idempotency_key"],
            result_hash=payload["result_hash"],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            adapter_id=payload["adapter_id"],
            adapter_version=payload["adapter_version"],
            attempt_number=payload["attempt_number"],
            disposition=execution_result.disposition,
            journal_state=journal_record.current_state,
            journal_transition_count=payload[
                "journal_transition_count"
            ],
            receipt_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        execution_result: GovernanceInterventionExecutionResult,
        journal_record: GovernanceInterventionActuationJournalRecord,
    ) -> None:
        if journal_record.tenant_id != execution_result.tenant_id:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal tenant_id does not match execution result"
            )

        if journal_record.actuation_id != execution_result.actuation_id:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal actuation_id does not match execution result"
            )

        if journal_record.contract_hash != execution_result.contract_hash:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal contract_hash does not match execution result"
            )

        if (
            journal_record.idempotency_key
            != execution_result.idempotency_key
        ):
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal idempotency_key does not match execution result"
            )

        if journal_record.details.get(
            "result_hash"
        ) != execution_result.result_hash:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal result_hash does not match execution result"
            )

        if journal_record.details.get(
            "adapter_id"
        ) != execution_result.adapter_id:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal adapter_id does not match execution result"
            )

        if journal_record.details.get(
            "adapter_version"
        ) != execution_result.adapter_version:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal adapter_version does not match execution result"
            )

        if journal_record.details.get(
            "attempt_number"
        ) != execution_result.attempt_number:
            raise InvalidGovernanceInterventionExecutionReceiptLineageError(
                "journal attempt_number does not match execution result"
            )

    @classmethod
    def _validate_terminal_state(
        cls,
        *,
        execution_result: GovernanceInterventionExecutionResult,
        journal_record: GovernanceInterventionActuationJournalRecord,
    ) -> None:
        expected_state = cls._RESULT_TO_JOURNAL_STATE[
            execution_result.disposition
        ]

        if journal_record.current_state is not expected_state:
            raise InvalidGovernanceInterventionExecutionReceiptStateError(
                "journal terminal state does not match execution disposition"
            )

        if journal_record.transition_count < 3:
            raise InvalidGovernanceInterventionExecutionReceiptStateError(
                "journal does not contain a complete execution lifecycle"
            )