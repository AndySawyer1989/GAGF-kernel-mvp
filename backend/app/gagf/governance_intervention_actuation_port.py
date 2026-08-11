from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_verification_commitment import (
    GovernanceInterventionVerificationCommitment,
)


GOVERNANCE_INTERVENTION_ACTUATION_PORT_ID = (
    "governance-intervention-actuation-port"
)
GOVERNANCE_INTERVENTION_ACTUATION_PORT_VERSION = "0.1.0"


class GovernanceInterventionActuationPortError(RuntimeError):
    """Base error for governed actuation port failures."""


class InvalidGovernanceInterventionActuationContractError(
    GovernanceInterventionActuationPortError
):
    """Raised when an actuator receives an invalid contract."""


class InvalidGovernanceInterventionVerificationCommitmentError(
    GovernanceInterventionActuationPortError
):
    """Raised when actuation lacks a valid verification commitment."""


class GovernanceInterventionActuationDisposition(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ALREADY_ACCEPTED = "ALREADY_ACCEPTED"


@dataclass(frozen=True)
class GovernanceInterventionActuationRequest:
    port_id: str
    port_version: str

    tenant_id: str
    contract_hash: str
    intervention_id: str
    intervention_type: str

    verification_commitment_hash: str
    idempotency_key: str

    def to_dict(self) -> dict[str, str]:
        return {
            "port_id": self.port_id,
            "port_version": self.port_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "verification_commitment_hash": (
                self.verification_commitment_hash
            ),
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True)
class GovernanceInterventionActuationAcceptance:
    disposition: GovernanceInterventionActuationDisposition

    tenant_id: str
    contract_hash: str
    idempotency_key: str

    adapter_id: str
    adapter_version: str

    accepted: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "disposition": self.disposition.value,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "idempotency_key": self.idempotency_key,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "accepted": self.accepted,
        }


class GovernanceInterventionActuationRequestBuilder:
    def build(
        self,
        *,
        contract: GovernanceInterventionActuationContract,
        verification_commitment: GovernanceInterventionVerificationCommitment,
        idempotency_key: str,
    ) -> GovernanceInterventionActuationRequest:
        if not contract.verify():
            raise InvalidGovernanceInterventionActuationContractError(
                "actuation contract failed hash verification"
            )

        if not verification_commitment.verify():
            raise InvalidGovernanceInterventionVerificationCommitmentError(
                "verification commitment failed deterministic verification"
            )

        if verification_commitment.tenant_id != contract.tenant_id:
            raise InvalidGovernanceInterventionVerificationCommitmentError(
                "verification commitment tenant does not match contract"
            )

        if (
            verification_commitment.actuation_contract_hash
            != contract.contract_hash
        ):
            raise InvalidGovernanceInterventionVerificationCommitmentError(
                "verification commitment contract hash does not match contract"
            )

        if (
            verification_commitment.intervention_id
            != contract.intervention_id
        ):
            raise InvalidGovernanceInterventionVerificationCommitmentError(
                "verification commitment intervention_id does not match contract"
            )

        if (
            verification_commitment.intervention_type
            != contract.intervention_type
        ):
            raise InvalidGovernanceInterventionVerificationCommitmentError(
                "verification commitment intervention_type does not match contract"
            )

        normalized_key = idempotency_key.strip()

        if not normalized_key:
            raise InvalidGovernanceInterventionActuationContractError(
                "idempotency_key is required"
            )

        return GovernanceInterventionActuationRequest(
            port_id=GOVERNANCE_INTERVENTION_ACTUATION_PORT_ID,
            port_version=GOVERNANCE_INTERVENTION_ACTUATION_PORT_VERSION,
            tenant_id=contract.tenant_id,
            contract_hash=contract.contract_hash,
            intervention_id=contract.intervention_id,
            intervention_type=contract.intervention_type,
            verification_commitment_hash=(
                verification_commitment.commitment_hash
            ),
            idempotency_key=normalized_key,
        )


@runtime_checkable
class GovernanceInterventionActuationPort(Protocol):
    """
    Boundary implemented by future concrete intervention adapters.

    Accepting a request means the adapter has accepted responsibility
    for a validated bounded actuation contract.

    Acceptance does not itself prove that the intervention executed,
    succeeded, rolled back, or passed outcome verification.
    """

    @property
    def adapter_id(self) -> str:
        ...

    @property
    def adapter_version(self) -> str:
        ...

    def accept(
        self,
        *,
        request: GovernanceInterventionActuationRequest,
        contract: GovernanceInterventionActuationContract,
    ) -> GovernanceInterventionActuationAcceptance:
        ...
