from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_ID = (
    "governance-intervention-verification-commitment"
)
GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionVerificationCommitmentError(ValueError):
    """Base error for governed verification commitments."""


class GovernanceInterventionVerificationCommitmentLineageError(
    GovernanceInterventionVerificationCommitmentError
):
    """Raised when contract and verification requirement lineage diverge."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationCommitment:
    """
    Immutable commitment to one structured verification requirement.

    This artifact binds a verified GEX-001I-B structured requirement to the
    exact GEX-001C actuation contract that the requirement refines.

    The artifact alone does not prove temporal ordering. Pre-execution
    commitment is established when a governed execution boundary requires a
    valid commitment before allowing execution to advance.

    This artifact does not:
    - authorize execution;
    - create an actuation request;
    - accept an intervention;
    - start or execute an intervention;
    - collect outcome evidence;
    - evaluate a verification requirement;
    - declare VERIFIED, NOT_VERIFIED, or INCONCLUSIVE.
    """

    commitment_id: str
    version: str
    schema_version: str

    tenant_id: str
    actuation_contract_hash: str
    intervention_id: str
    intervention_type: str

    requirement_id: str
    legacy_requirement: str
    requirement_hash: str

    commitment_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "commitment_id": self.commitment_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "actuation_contract_hash": self.actuation_contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "requirement_id": self.requirement_id,
            "legacy_requirement": self.legacy_requirement,
            "requirement_hash": self.requirement_hash,
        }

    def verify(self) -> bool:
        return self.commitment_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "commitment_hash": self.commitment_hash,
        }


class GovernanceInterventionVerificationCommitmentBuilder:
    """
    Builds a deterministic commitment from verified GEX-001C and GEX-001I-B
    artifacts.

    The builder establishes artifact lineage only. A later execution-boundary
    guard establishes the pre-execution ordering invariant.
    """

    @classmethod
    def build(
        cls,
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        requirement: GovernanceInterventionVerificationRequirement,
    ) -> GovernanceInterventionVerificationCommitment:
        cls._validate_lineage(
            actuation_contract=actuation_contract,
            requirement=requirement,
        )

        payload: dict[str, Any] = {
            "commitment_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_SCHEMA_VERSION
            ),
            "tenant_id": actuation_contract.tenant_id,
            "actuation_contract_hash": actuation_contract.contract_hash,
            "intervention_id": actuation_contract.intervention_id,
            "intervention_type": actuation_contract.intervention_type,
            "requirement_id": requirement.requirement_id,
            "legacy_requirement": requirement.legacy_requirement,
            "requirement_hash": requirement.requirement_hash,
        }

        return GovernanceInterventionVerificationCommitment(
            **payload,
            commitment_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        requirement: GovernanceInterventionVerificationRequirement,
    ) -> None:
        if not actuation_contract.verify():
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "actuation contract failed deterministic verification"
            )

        if not requirement.verify():
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "verification requirement failed deterministic verification"
            )

        if requirement.tenant_id != actuation_contract.tenant_id:
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "verification requirement tenant does not match "
                "actuation contract"
            )

        if (
            requirement.actuation_contract_hash
            != actuation_contract.contract_hash
        ):
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "verification requirement actuation contract hash "
                "does not match actuation contract"
            )

        if (
            requirement.intervention_id
            != actuation_contract.intervention_id
        ):
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "verification requirement intervention_id does not match "
                "actuation contract"
            )

        if (
            requirement.intervention_type
            != actuation_contract.intervention_type
        ):
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "verification requirement intervention_type does not match "
                "actuation contract"
            )

        if (
            requirement.legacy_requirement
            not in actuation_contract.verification_requirements
        ):
            raise GovernanceInterventionVerificationCommitmentLineageError(
                "verification requirement does not refine a requirement "
                "present in the actuation contract"
            )