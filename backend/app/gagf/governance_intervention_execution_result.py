from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournalRecord,
    GovernanceInterventionActuationState,
)
from backend.app.gagf.governance_intervention_actuation_port import (
    GovernanceInterventionActuationAcceptance,
    GovernanceInterventionActuationDisposition,
    GovernanceInterventionActuationRequest,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_EXECUTION_RESULT_ID = (
    "governance-intervention-execution-result"
)
GOVERNANCE_INTERVENTION_EXECUTION_RESULT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_EXECUTION_RESULT_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionExecutionResultError(RuntimeError):
    """Base error for invalid governed intervention execution results."""


class InvalidGovernanceInterventionExecutionLineageError(
    GovernanceInterventionExecutionResultError
):
    """Raised when execution-result lineage does not match governed inputs."""


class InvalidGovernanceInterventionExecutionDispositionError(
    GovernanceInterventionExecutionResultError
):
    """Raised when execution disposition semantics are invalid."""


class GovernanceInterventionExecutionDisposition(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"


@dataclass(frozen=True, slots=True)
class GovernanceInterventionExecutionResult:
    result_id: str
    version: str
    schema_version: str

    tenant_id: str
    actuation_id: str
    contract_hash: str
    idempotency_key: str

    intervention_id: str
    intervention_type: str

    adapter_id: str
    adapter_version: str
    attempt_number: int

    disposition: GovernanceInterventionExecutionDisposition

    observations: tuple[str, ...]
    error_code: str | None
    error_message: str | None

    result_hash: str

    def payload(self) -> dict:
        return {
            "result_id": self.result_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "actuation_id": self.actuation_id,
            "contract_hash": self.contract_hash,
            "idempotency_key": self.idempotency_key,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "attempt_number": self.attempt_number,
            "disposition": self.disposition.value,
            "observations": list(self.observations),
            "error_code": self.error_code,
            "error_message": self.error_message,
        }

    def verify(self) -> bool:
        return self.result_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "result_hash": self.result_hash,
        }


class GovernanceInterventionExecutionResultBuilder:
    """
    Builds deterministic evidence describing one governed actuation attempt.

    This builder does not execute, dispatch, actuate, roll back, verify an
    external outcome, or create an execution receipt.

    A COMPLETED disposition means only that the concrete adapter reported its
    bounded execution attempt as completed. It does not mean that the desired
    real-world governance outcome has been independently verified.
    """

    _ACCEPTED_DISPOSITIONS = {
        GovernanceInterventionActuationDisposition.ACCEPTED,
        GovernanceInterventionActuationDisposition.ALREADY_ACCEPTED,
    }

    @staticmethod
    def _required(value: str, field_name: str) -> str:
        normalized = value.strip()

        if not normalized:
            raise InvalidGovernanceInterventionExecutionLineageError(
                f"{field_name} is required"
            )

        return normalized

    @classmethod
    def _normalize_observations(
        cls,
        observations: Iterable[str],
    ) -> tuple[str, ...]:
        normalized: list[str] = []

        for observation in observations:
            value = observation.strip()

            if not value:
                raise InvalidGovernanceInterventionExecutionDispositionError(
                    "observations cannot contain blank values"
                )

            normalized.append(value)

        return tuple(normalized)

    @classmethod
    def build(
        cls,
        *,
        contract: GovernanceInterventionActuationContract,
        request: GovernanceInterventionActuationRequest,
        acceptance: GovernanceInterventionActuationAcceptance,
        journal_record: GovernanceInterventionActuationJournalRecord,
        adapter_id: str,
        adapter_version: str,
        attempt_number: int,
        disposition: GovernanceInterventionExecutionDisposition,
        observations: Iterable[str] = (),
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> GovernanceInterventionExecutionResult:
        if not contract.verify():
            raise InvalidGovernanceInterventionExecutionLineageError(
                "actuation contract failed deterministic verification"
            )

        normalized_adapter_id = cls._required(
            adapter_id,
            "adapter_id",
        )
        normalized_adapter_version = cls._required(
            adapter_version,
            "adapter_version",
        )

        if attempt_number < 1:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "attempt_number must be at least 1"
            )

        if attempt_number > contract.max_attempts:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "attempt_number exceeds contract max_attempts"
            )

        if request.tenant_id != contract.tenant_id:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "request tenant_id does not match contract"
            )

        if request.contract_hash != contract.contract_hash:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "request contract_hash does not match contract"
            )

        if request.intervention_id != contract.intervention_id:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "request intervention_id does not match contract"
            )

        if request.intervention_type != contract.intervention_type:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "request intervention_type does not match contract"
            )

        if not acceptance.accepted:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "actuation request was not accepted"
            )

        if acceptance.disposition not in cls._ACCEPTED_DISPOSITIONS:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "acceptance disposition does not authorize adapter work"
            )

        if acceptance.tenant_id != request.tenant_id:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "acceptance tenant_id does not match request"
            )

        if acceptance.contract_hash != request.contract_hash:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "acceptance contract_hash does not match request"
            )

        if acceptance.idempotency_key != request.idempotency_key:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "acceptance idempotency_key does not match request"
            )

        if acceptance.adapter_id != normalized_adapter_id:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "adapter_id does not match acceptance"
            )

        if acceptance.adapter_version != normalized_adapter_version:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "adapter_version does not match acceptance"
            )

        if journal_record.current_state is not (
            GovernanceInterventionActuationState.STARTED
        ):
            raise InvalidGovernanceInterventionExecutionLineageError(
                "actuation journal must be STARTED before result creation"
            )

        if journal_record.tenant_id != request.tenant_id:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "journal tenant_id does not match request"
            )

        if journal_record.contract_hash != request.contract_hash:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "journal contract_hash does not match request"
            )

        if journal_record.idempotency_key != request.idempotency_key:
            raise InvalidGovernanceInterventionExecutionLineageError(
                "journal idempotency_key does not match request"
            )

        normalized_observations = cls._normalize_observations(
            observations
        )

        normalized_error_code = (
            error_code.strip()
            if error_code is not None
            else None
        )
        normalized_error_message = (
            error_message.strip()
            if error_message is not None
            else None
        )

        if normalized_error_code == "":
            normalized_error_code = None

        if normalized_error_message == "":
            normalized_error_message = None

        if disposition is GovernanceInterventionExecutionDisposition.COMPLETED:
            if normalized_error_code is not None:
                raise (
                    InvalidGovernanceInterventionExecutionDispositionError(
                        "COMPLETED execution cannot contain error_code"
                    )
                )

            if normalized_error_message is not None:
                raise (
                    InvalidGovernanceInterventionExecutionDispositionError(
                        "COMPLETED execution cannot contain error_message"
                    )
                )
        else:
            if normalized_error_code is None:
                raise (
                    InvalidGovernanceInterventionExecutionDispositionError(
                        f"{disposition.value} execution requires error_code"
                    )
                )

        payload = {
            "result_id": (
                GOVERNANCE_INTERVENTION_EXECUTION_RESULT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_EXECUTION_RESULT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_EXECUTION_RESULT_SCHEMA_VERSION
            ),
            "tenant_id": request.tenant_id,
            "actuation_id": journal_record.actuation_id,
            "contract_hash": request.contract_hash,
            "idempotency_key": request.idempotency_key,
            "intervention_id": request.intervention_id,
            "intervention_type": request.intervention_type,
            "adapter_id": normalized_adapter_id,
            "adapter_version": normalized_adapter_version,
            "attempt_number": attempt_number,
            "disposition": disposition.value,
            "observations": list(normalized_observations),
            "error_code": normalized_error_code,
            "error_message": normalized_error_message,
        }

        return GovernanceInterventionExecutionResult(
            result_id=payload["result_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            actuation_id=payload["actuation_id"],
            contract_hash=payload["contract_hash"],
            idempotency_key=payload["idempotency_key"],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            adapter_id=payload["adapter_id"],
            adapter_version=payload["adapter_version"],
            attempt_number=payload["attempt_number"],
            disposition=disposition,
            observations=normalized_observations,
            error_code=normalized_error_code,
            error_message=normalized_error_message,
            result_hash=sha256_hex(canonical_json(payload)),
        )