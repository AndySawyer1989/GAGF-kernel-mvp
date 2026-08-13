from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_outcome_verification_result import (
    GovernanceInterventionOutcomeVerificationResult,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_SET_ID = (
    "governance-intervention-verification-set"
)
GOVERNANCE_INTERVENTION_VERIFICATION_SET_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_VERIFICATION_SET_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionVerificationSetError(ValueError):
    """Base error for governed verification-set construction."""


class GovernanceInterventionVerificationSetIntegrityError(
    GovernanceInterventionVerificationSetError
):
    """Raised when a supplied governed artifact fails verification."""


class GovernanceInterventionVerificationSetLineageError(
    GovernanceInterventionVerificationSetError
):
    """Raised when verification artifacts do not share exact lineage."""


class GovernanceInterventionVerificationSetCompletenessError(
    GovernanceInterventionVerificationSetError
):
    """Raised when required verification coverage is incomplete or ambiguous."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationSetEntry:
    """
    One exact contract obligation, its structured verification requirement,
    and its governed I-D verification result.

    Entries contain identity and lineage only. They do not aggregate verdicts.
    """

    ordinal: int
    legacy_requirement: str
    requirement_id: str
    requirement_hash: str
    verification_hash: str
    verification_disposition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "legacy_requirement": self.legacy_requirement,
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "verification_hash": self.verification_hash,
            "verification_disposition": self.verification_disposition,
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationSet:
    """
    Immutable proof that every verification obligation declared in one
    actuation contract is represented exactly once by:
    - one verified structured requirement; and
    - one verified governed outcome-verification result.

    The set is ordered by the original actuation-contract obligation order.

    This artifact proves completeness and lineage only.

    It does not:
    - aggregate individual verdicts into an intervention-level verdict;
    - determine intervention success or failure;
    - establish causation;
    - authorize execution or future action;
    - order rollback or continuation.
    """

    verification_set_id: str
    version: str
    schema_version: str

    tenant_id: str
    contract_hash: str
    intervention_id: str
    intervention_type: str

    required_count: int
    result_count: int

    entries: tuple[GovernanceInterventionVerificationSetEntry, ...]

    verification_set_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "verification_set_id": self.verification_set_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "required_count": self.required_count,
            "result_count": self.result_count,
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ],
        }

    def verify(self) -> bool:
        return self.verification_set_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_set_hash": self.verification_set_hash,
        }


class GovernanceInterventionVerificationSetBuilder:
    """
    Constructs the completeness boundary for one governed intervention.

    Completeness means that the actuation contract's verification obligations
    form an exact one-to-one correspondence with structured requirements and
    governed verification results.

    No favorable result may be selectively omitted, duplicated, substituted,
    or imported from another intervention.
    """

    @classmethod
    def build(
        cls,
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        requirements: tuple[
            GovernanceInterventionVerificationRequirement,
            ...,
        ],
        verification_results: tuple[
            GovernanceInterventionOutcomeVerificationResult,
            ...,
        ],
    ) -> GovernanceInterventionVerificationSet:
        if not actuation_contract.verify():
            raise GovernanceInterventionVerificationSetIntegrityError(
                "actuation contract failed deterministic verification"
            )

        contract_obligations = tuple(
            actuation_contract.verification_requirements
        )

        if not contract_obligations:
            raise GovernanceInterventionVerificationSetCompletenessError(
                "actuation contract contains no verification obligations"
            )

        if len(set(contract_obligations)) != len(contract_obligations):
            raise GovernanceInterventionVerificationSetCompletenessError(
                "actuation contract contains duplicate verification obligations"
            )

        if len(requirements) != len(contract_obligations):
            raise GovernanceInterventionVerificationSetCompletenessError(
                "structured requirement count does not match contract "
                "verification-obligation count"
            )

        if len(verification_results) != len(contract_obligations):
            raise GovernanceInterventionVerificationSetCompletenessError(
                "verification-result count does not match contract "
                "verification-obligation count"
            )

        requirements_by_legacy: dict[
            str,
            GovernanceInterventionVerificationRequirement,
        ] = {}

        requirement_ids: set[str] = set()
        requirement_hashes: set[str] = set()

        for requirement in requirements:
            if not requirement.verify():
                raise GovernanceInterventionVerificationSetIntegrityError(
                    "structured verification requirement failed "
                    "deterministic verification"
                )

            cls._validate_requirement_lineage(
                actuation_contract=actuation_contract,
                requirement=requirement,
            )

            if requirement.legacy_requirement in requirements_by_legacy:
                raise GovernanceInterventionVerificationSetCompletenessError(
                    "multiple structured requirements refine the same "
                    "contract verification obligation"
                )

            if requirement.requirement_id in requirement_ids:
                raise GovernanceInterventionVerificationSetCompletenessError(
                    "duplicate structured requirement_id"
                )

            if requirement.requirement_hash in requirement_hashes:
                raise GovernanceInterventionVerificationSetCompletenessError(
                    "duplicate structured requirement_hash"
                )

            requirements_by_legacy[
                requirement.legacy_requirement
            ] = requirement

            requirement_ids.add(requirement.requirement_id)
            requirement_hashes.add(requirement.requirement_hash)

        if set(requirements_by_legacy) != set(contract_obligations):
            raise GovernanceInterventionVerificationSetCompletenessError(
                "structured requirements do not exactly cover the "
                "actuation contract verification obligations"
            )

        results_by_requirement_hash: dict[
            str,
            GovernanceInterventionOutcomeVerificationResult,
        ] = {}

        result_requirement_ids: set[str] = set()
        verification_hashes: set[str] = set()

        for result in verification_results:
            if not result.verify():
                raise GovernanceInterventionVerificationSetIntegrityError(
                    "governed outcome verification result failed "
                    "deterministic verification"
                )

            cls._validate_result_lineage(
                actuation_contract=actuation_contract,
                result=result,
            )

            if result.requirement_id in result_requirement_ids:
                raise GovernanceInterventionVerificationSetCompletenessError(
                    "duplicate verification result requirement_id"
                )

            if result.requirement_hash in results_by_requirement_hash:
                raise GovernanceInterventionVerificationSetCompletenessError(
                    "duplicate verification result requirement_hash"
                )

            if result.verification_hash in verification_hashes:
                raise GovernanceInterventionVerificationSetCompletenessError(
                    "duplicate verification_hash"
                )

            results_by_requirement_hash[
                result.requirement_hash
            ] = result

            result_requirement_ids.add(result.requirement_id)
            verification_hashes.add(result.verification_hash)

        if set(results_by_requirement_hash) != requirement_hashes:
            raise GovernanceInterventionVerificationSetCompletenessError(
                "verification results do not exactly cover the structured "
                "requirements"
            )

        entries: list[GovernanceInterventionVerificationSetEntry] = []

        for ordinal, legacy_requirement in enumerate(
            contract_obligations
        ):
            requirement = requirements_by_legacy[
                legacy_requirement
            ]

            result = results_by_requirement_hash[
                requirement.requirement_hash
            ]

            if result.requirement_id != requirement.requirement_id:
                raise GovernanceInterventionVerificationSetLineageError(
                    "verification result requirement_id does not match "
                    "its structured requirement"
                )

            entries.append(
                GovernanceInterventionVerificationSetEntry(
                    ordinal=ordinal,
                    legacy_requirement=legacy_requirement,
                    requirement_id=requirement.requirement_id,
                    requirement_hash=requirement.requirement_hash,
                    verification_hash=result.verification_hash,
                    verification_disposition=(
                        result.verification_disposition.value
                    ),
                )
            )

        payload: dict[str, Any] = {
            "verification_set_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_SET_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_SET_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_SET_SCHEMA_VERSION
            ),
            "tenant_id": actuation_contract.tenant_id,
            "contract_hash": actuation_contract.contract_hash,
            "intervention_id": actuation_contract.intervention_id,
            "intervention_type": actuation_contract.intervention_type,
            "required_count": len(contract_obligations),
            "result_count": len(entries),
            "entries": [
                entry.to_dict()
                for entry in entries
            ],
        }

        return GovernanceInterventionVerificationSet(
            verification_set_id=payload["verification_set_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            contract_hash=payload["contract_hash"],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            required_count=payload["required_count"],
            result_count=payload["result_count"],
            entries=tuple(entries),
            verification_set_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_requirement_lineage(
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        requirement: GovernanceInterventionVerificationRequirement,
    ) -> None:
        if requirement.tenant_id != actuation_contract.tenant_id:
            raise GovernanceInterventionVerificationSetLineageError(
                "structured requirement tenant does not match contract"
            )

        if (
            requirement.actuation_contract_hash
            != actuation_contract.contract_hash
        ):
            raise GovernanceInterventionVerificationSetLineageError(
                "structured requirement contract hash does not match contract"
            )

        if (
            requirement.intervention_id
            != actuation_contract.intervention_id
        ):
            raise GovernanceInterventionVerificationSetLineageError(
                "structured requirement intervention_id does not match contract"
            )

        if (
            requirement.intervention_type
            != actuation_contract.intervention_type
        ):
            raise GovernanceInterventionVerificationSetLineageError(
                "structured requirement intervention_type does not match contract"
            )

        if (
            requirement.legacy_requirement
            not in actuation_contract.verification_requirements
        ):
            raise GovernanceInterventionVerificationSetLineageError(
                "structured requirement does not refine a contract obligation"
            )

    @staticmethod
    def _validate_result_lineage(
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        result: GovernanceInterventionOutcomeVerificationResult,
    ) -> None:
        if result.tenant_id != actuation_contract.tenant_id:
            raise GovernanceInterventionVerificationSetLineageError(
                "verification result tenant does not match contract"
            )

        if result.contract_hash != actuation_contract.contract_hash:
            raise GovernanceInterventionVerificationSetLineageError(
                "verification result contract hash does not match contract"
            )

        if result.intervention_id != actuation_contract.intervention_id:
            raise GovernanceInterventionVerificationSetLineageError(
                "verification result intervention_id does not match contract"
            )

        if (
            result.intervention_type
            != actuation_contract.intervention_type
        ):
            raise GovernanceInterventionVerificationSetLineageError(
                "verification result intervention_type does not match contract"
            )