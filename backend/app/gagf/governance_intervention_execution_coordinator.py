from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournal,
    GovernanceInterventionActuationJournalRecord,
    GovernanceInterventionActuationState,
)
from backend.app.gagf.governance_intervention_actuation_port import (
    GovernanceInterventionActuationAcceptance,
    GovernanceInterventionActuationDisposition,
    GovernanceInterventionActuationRequest,
)
from backend.app.gagf.governance_intervention_verification_commitment import (
    GovernanceInterventionVerificationCommitment,
)
from backend.app.gagf.governance_intervention_execution_adapter import (
    GovernanceInterventionExecutionAdapter,
)
from backend.app.gagf.governance_intervention_execution_result import (
    GovernanceInterventionExecutionDisposition,
    GovernanceInterventionExecutionResult,
    GovernanceInterventionExecutionResultBuilder,
)


GOVERNANCE_INTERVENTION_EXECUTION_COORDINATOR_ID = (
    "governance-intervention-execution-coordinator"
)
GOVERNANCE_INTERVENTION_EXECUTION_COORDINATOR_VERSION = "0.1.0"


class GovernanceInterventionExecutionCoordinatorError(RuntimeError):
    """Base error for governed execution coordination failures."""


class GovernanceInterventionExecutionPreconditionError(
    GovernanceInterventionExecutionCoordinatorError
):
    """Raised when execution cannot safely begin."""


class GovernanceInterventionExecutionCommitmentError(
    GovernanceInterventionExecutionPreconditionError
):
    """Raised when pre-execution verification commitment is invalid."""


class GovernanceInterventionExecutionAdapterError(
    GovernanceInterventionExecutionCoordinatorError
):
    """Raised when a concrete execution adapter fails unexpectedly."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionExecutionCoordinationResult:
    execution_result: GovernanceInterventionExecutionResult
    journal_record: GovernanceInterventionActuationJournalRecord

    def to_dict(self) -> dict:
        return {
            "execution_result": self.execution_result.to_dict(),
            "journal_record": self.journal_record.to_dict(),
        }


class GovernanceInterventionExecutionCoordinator:
    """
    Coordinates one governed intervention execution attempt.

    This component connects acceptance, journal lifecycle state, a concrete
    execution adapter, and the deterministic GEX-001F result.

    It does not build an execution receipt and does not verify the desired
    real-world governance outcome.
    """

    _ACCEPTED_DISPOSITIONS = {
        GovernanceInterventionActuationDisposition.ACCEPTED,
        GovernanceInterventionActuationDisposition.ALREADY_ACCEPTED,
    }

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

    def __init__(
        self,
        *,
        journal: GovernanceInterventionActuationJournal,
    ) -> None:
        self._journal = journal

    def execute(
        self,
        *,
        contract: GovernanceInterventionActuationContract,
        request: GovernanceInterventionActuationRequest,
        verification_commitment: GovernanceInterventionVerificationCommitment,
        acceptance: GovernanceInterventionActuationAcceptance,
        adapter: GovernanceInterventionExecutionAdapter,
        attempt_number: int,
    ) -> GovernanceInterventionExecutionCoordinationResult:
        self._validate_preconditions(
            contract=contract,
            request=request,
            verification_commitment=verification_commitment,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=attempt_number,
        )

        journal_record = self._journal.begin(
            tenant_id=request.tenant_id,
            contract_hash=request.contract_hash,
            idempotency_key=request.idempotency_key,
            details={
                "adapter_id": adapter.adapter_id,
                "adapter_version": adapter.adapter_version,
            },
        )

        if journal_record.current_state is (
            GovernanceInterventionActuationState.ACCEPTED
        ):
            journal_record = self._journal.transition(
                actuation_id=journal_record.actuation_id,
                state=GovernanceInterventionActuationState.STARTED,
                details={
                    "adapter_id": adapter.adapter_id,
                    "adapter_version": adapter.adapter_version,
                    "attempt_number": attempt_number,
                },
            )

        if journal_record.current_state is not (
            GovernanceInterventionActuationState.STARTED
        ):
            raise GovernanceInterventionExecutionPreconditionError(
                "actuation journal is not executable from its current state"
            )

        try:
            report = adapter.execute(
                request=request,
                contract=contract,
                attempt_number=attempt_number,
            )
        except Exception as exc:
            self._journal.transition(
                actuation_id=journal_record.actuation_id,
                state=GovernanceInterventionActuationState.FAILED,
                details={
                    "adapter_id": adapter.adapter_id,
                    "adapter_version": adapter.adapter_version,
                    "attempt_number": attempt_number,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )

            raise GovernanceInterventionExecutionAdapterError(
                "execution adapter failed unexpectedly"
            ) from exc

        execution_result = (
            GovernanceInterventionExecutionResultBuilder.build(
                contract=contract,
                request=request,
                acceptance=acceptance,
                journal_record=journal_record,
                adapter_id=adapter.adapter_id,
                adapter_version=adapter.adapter_version,
                attempt_number=attempt_number,
                disposition=report.disposition,
                observations=report.observations,
                error_code=report.error_code,
                error_message=report.error_message,
            )
        )

        final_state = self._RESULT_TO_JOURNAL_STATE[
            execution_result.disposition
        ]

        journal_record = self._journal.transition(
            actuation_id=journal_record.actuation_id,
            state=final_state,
            details={
                "result_hash": execution_result.result_hash,
                "attempt_number": execution_result.attempt_number,
                "adapter_id": execution_result.adapter_id,
                "adapter_version": execution_result.adapter_version,
            },
        )

        return GovernanceInterventionExecutionCoordinationResult(
            execution_result=execution_result,
            journal_record=journal_record,
        )

    @classmethod
    def _validate_preconditions(
        cls,
        *,
        contract: GovernanceInterventionActuationContract,
        request: GovernanceInterventionActuationRequest,
        verification_commitment: GovernanceInterventionVerificationCommitment,
        acceptance: GovernanceInterventionActuationAcceptance,
        adapter: GovernanceInterventionExecutionAdapter,
        attempt_number: int,
    ) -> None:
        if not contract.verify():
            raise GovernanceInterventionExecutionPreconditionError(
                "actuation contract failed deterministic verification"
            )

        if request.tenant_id != contract.tenant_id:
            raise GovernanceInterventionExecutionPreconditionError(
                "request tenant_id does not match contract"
            )

        if request.contract_hash != contract.contract_hash:
            raise GovernanceInterventionExecutionPreconditionError(
                "request contract_hash does not match contract"
            )

        if request.intervention_id != contract.intervention_id:
            raise GovernanceInterventionExecutionPreconditionError(
                "request intervention_id does not match contract"
            )

        if request.intervention_type != contract.intervention_type:
            raise GovernanceInterventionExecutionPreconditionError(
                "request intervention_type does not match contract"
            )

        if not verification_commitment.verify():
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment failed deterministic verification"
            )

        if (
            verification_commitment.commitment_hash
            != request.verification_commitment_hash
        ):
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment hash does not match request"
            )

        if verification_commitment.tenant_id != contract.tenant_id:
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment tenant does not match contract"
            )

        if (
            verification_commitment.actuation_contract_hash
            != contract.contract_hash
        ):
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment contract hash does not match contract"
            )

        if (
            verification_commitment.intervention_id
            != contract.intervention_id
        ):
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment intervention_id does not match contract"
            )

        if (
            verification_commitment.intervention_type
            != contract.intervention_type
        ):
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment intervention_type does not match contract"
            )

        if (
            verification_commitment.legacy_requirement
            not in contract.verification_requirements
        ):
            raise GovernanceInterventionExecutionCommitmentError(
                "verification commitment does not refine a requirement "
                "present in the actuation contract"
            )

        if not acceptance.accepted:
            raise GovernanceInterventionExecutionPreconditionError(
                "actuation request was not accepted"
            )

        if acceptance.disposition not in cls._ACCEPTED_DISPOSITIONS:
            raise GovernanceInterventionExecutionPreconditionError(
                "acceptance disposition does not permit execution"
            )

        if acceptance.tenant_id != request.tenant_id:
            raise GovernanceInterventionExecutionPreconditionError(
                "acceptance tenant_id does not match request"
            )

        if acceptance.contract_hash != request.contract_hash:
            raise GovernanceInterventionExecutionPreconditionError(
                "acceptance contract_hash does not match request"
            )

        if acceptance.idempotency_key != request.idempotency_key:
            raise GovernanceInterventionExecutionPreconditionError(
                "acceptance idempotency_key does not match request"
            )

        adapter_id = adapter.adapter_id.strip()
        adapter_version = adapter.adapter_version.strip()

        if not adapter_id:
            raise GovernanceInterventionExecutionPreconditionError(
                "adapter_id is required"
            )

        if not adapter_version:
            raise GovernanceInterventionExecutionPreconditionError(
                "adapter_version is required"
            )

        if acceptance.adapter_id != adapter_id:
            raise GovernanceInterventionExecutionPreconditionError(
                "adapter_id does not match acceptance"
            )

        if acceptance.adapter_version != adapter_version:
            raise GovernanceInterventionExecutionPreconditionError(
                "adapter_version does not match acceptance"
            )

        if attempt_number < 1:
            raise GovernanceInterventionExecutionPreconditionError(
                "attempt_number must be at least 1"
            )

        if attempt_number > contract.max_attempts:
            raise GovernanceInterventionExecutionPreconditionError(
                "attempt_number exceeds contract max_attempts"
            )
