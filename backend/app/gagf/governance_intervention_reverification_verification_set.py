from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_reverification_verification_result import (
    GovernanceInterventionReverificationVerificationResult,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_ID = (
    "governance-intervention-reverification-verification-set"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationVerificationSetError(
    ValueError
):
    """Base error for governed reverification verification sets."""


class GovernanceInterventionReverificationVerificationSetIntegrityError(
    GovernanceInterventionReverificationVerificationSetError
):
    """Raised when a supplied governed artifact fails verification."""


class GovernanceInterventionReverificationVerificationSetLineageError(
    GovernanceInterventionReverificationVerificationSetError
):
    """Raised when governed reverification artifacts diverge in lineage."""


class GovernanceInterventionReverificationVerificationSetCompletenessError(
    GovernanceInterventionReverificationVerificationSetError
):
    """Raised when reverification coverage is incomplete or ambiguous."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationVerificationSetEntry:
    """
    One exact contract obligation, its structured requirement, and its
    governed I-R reverification verification result.

    Entries contain identity, lineage, and per-requirement disposition only.

    They do not aggregate verdicts.
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
            "legacy_requirement": (
                self.legacy_requirement
            ),
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "verification_hash": self.verification_hash,
            "verification_disposition": (
                self.verification_disposition
            ),
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationVerificationSet:
    """
    Immutable proof that every verification obligation declared in one
    actuation contract is represented exactly once by:
    - one verified structured verification requirement; and
    - one verified I-R reverification verification result.

    Every result must belong to the same governed reverification attempt.

    Entries are ordered by the original actuation-contract obligation order.

    This artifact proves completeness and lineage only.

    It does not:
    - aggregate individual dispositions into an intervention-level verdict;
    - determine intervention success or failure;
    - complete the reverification attempt;
    - supersede a verification record;
    - mutate verification lifecycle state;
    - establish causation;
    - authorize intervention activity;
    - order rollback, continuation, or remediation.
    """

    verification_set_id: str
    version: str
    schema_version: str

    tenant_id: str
    actuation_contract_hash: str
    intervention_id: str
    intervention_type: str

    verification_record_hash: str
    request_hash: str
    work_order_hash: str
    attempt_id: str
    attempt_execution_id: str
    reverification_scope: str

    required_count: int
    result_count: int

    entries: tuple[
        GovernanceInterventionReverificationVerificationSetEntry,
        ...,
    ]

    verification_set_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "verification_set_id": (
                self.verification_set_id
            ),
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "actuation_contract_hash": (
                self.actuation_contract_hash
            ),
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "request_hash": self.request_hash,
            "work_order_hash": self.work_order_hash,
            "attempt_id": self.attempt_id,
            "attempt_execution_id": (
                self.attempt_execution_id
            ),
            "reverification_scope": (
                self.reverification_scope
            ),
            "required_count": self.required_count,
            "result_count": self.result_count,
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ],
        }

    def verify(self) -> bool:
        return (
            self.verification_set_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_set_hash": (
                self.verification_set_hash
            ),
        }


class GovernanceInterventionReverificationVerificationSetBuilder:
    """
    Constructs the completeness boundary for one governed reverification
    attempt.

    Completeness means the actuation contract verification obligations form
    an exact one-to-one correspondence with:
    - structured I-B requirements; and
    - governed I-R reverification verification results.

    No result may be omitted, duplicated, substituted, imported from another
    intervention, or imported from another reverification attempt.

    This builder does not aggregate the per-requirement verification
    dispositions.
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
            GovernanceInterventionReverificationVerificationResult,
            ...,
        ],
    ) -> GovernanceInterventionReverificationVerificationSet:
        if not actuation_contract.verify():
            raise (
                GovernanceInterventionReverificationVerificationSetIntegrityError(
                    "actuation contract failed deterministic verification"
                )
            )

        contract_obligations = tuple(
            actuation_contract.verification_requirements
        )

        if not contract_obligations:
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "actuation contract contains no verification obligations"
                )
            )

        if (
            len(set(contract_obligations))
            != len(contract_obligations)
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "actuation contract contains duplicate "
                    "verification obligations"
                )
            )

        if (
            len(requirements)
            != len(contract_obligations)
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "structured requirement count does not match "
                    "contract verification-obligation count"
                )
            )

        if (
            len(verification_results)
            != len(contract_obligations)
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "reverification-result count does not match "
                    "contract verification-obligation count"
                )
            )

        requirements_by_legacy: dict[
            str,
            GovernanceInterventionVerificationRequirement,
        ] = {}

        requirement_ids: set[str] = set()
        requirement_hashes: set[str] = set()

        for requirement in requirements:
            if not requirement.verify():
                raise (
                    GovernanceInterventionReverificationVerificationSetIntegrityError(
                        "structured verification requirement failed "
                        "deterministic verification"
                    )
                )

            cls._validate_requirement_lineage(
                actuation_contract=actuation_contract,
                requirement=requirement,
            )

            if (
                requirement.legacy_requirement
                in requirements_by_legacy
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetCompletenessError(
                        "multiple structured requirements refine "
                        "the same contract verification obligation"
                    )
                )

            if (
                requirement.requirement_id
                in requirement_ids
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetCompletenessError(
                        "duplicate structured requirement_id"
                    )
                )

            if (
                requirement.requirement_hash
                in requirement_hashes
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetCompletenessError(
                        "duplicate structured requirement_hash"
                    )
                )

            requirements_by_legacy[
                requirement.legacy_requirement
            ] = requirement

            requirement_ids.add(
                requirement.requirement_id
            )

            requirement_hashes.add(
                requirement.requirement_hash
            )

        if (
            set(requirements_by_legacy)
            != set(contract_obligations)
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "structured requirements do not exactly cover "
                    "the actuation contract verification obligations"
                )
            )

        results_by_requirement_hash: dict[
            str,
            GovernanceInterventionReverificationVerificationResult,
        ] = {}

        result_requirement_ids: set[str] = set()
        verification_hashes: set[str] = set()

        attempt_lineage: tuple[
            str,
            str,
            str,
            str,
            str,
            str,
        ] | None = None

        for result in verification_results:
            if not result.verify():
                raise (
                    GovernanceInterventionReverificationVerificationSetIntegrityError(
                        "governed reverification verification result "
                        "failed deterministic verification"
                    )
                )

            cls._validate_result_contract_lineage(
                actuation_contract=actuation_contract,
                result=result,
            )

            current_attempt_lineage = (
                result.verification_record_hash,
                result.request_hash,
                result.work_order_hash,
                result.attempt_id,
                result.attempt_execution_id,
                result.reverification_scope,
            )

            if attempt_lineage is None:
                attempt_lineage = current_attempt_lineage

            elif (
                current_attempt_lineage
                != attempt_lineage
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetLineageError(
                        "reverification results do not share "
                        "one exact attempt lineage"
                    )
                )

            if (
                result.requirement_id
                in result_requirement_ids
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetCompletenessError(
                        "duplicate reverification result requirement_id"
                    )
                )

            if (
                result.requirement_hash
                in results_by_requirement_hash
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetCompletenessError(
                        "duplicate reverification result requirement_hash"
                    )
                )

            if (
                result.verification_hash
                in verification_hashes
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetCompletenessError(
                        "duplicate reverification verification_hash"
                    )
                )

            results_by_requirement_hash[
                result.requirement_hash
            ] = result

            result_requirement_ids.add(
                result.requirement_id
            )

            verification_hashes.add(
                result.verification_hash
            )

        if (
            set(results_by_requirement_hash)
            != requirement_hashes
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "reverification results do not exactly cover "
                    "the structured requirements"
                )
            )

        if attempt_lineage is None:
            raise (
                GovernanceInterventionReverificationVerificationSetCompletenessError(
                    "reverification result set is empty"
                )
            )

        entries: list[
            GovernanceInterventionReverificationVerificationSetEntry
        ] = []

        for ordinal, legacy_requirement in enumerate(
            contract_obligations
        ):
            requirement = requirements_by_legacy[
                legacy_requirement
            ]

            result = results_by_requirement_hash[
                requirement.requirement_hash
            ]

            if (
                result.requirement_id
                != requirement.requirement_id
            ):
                raise (
                    GovernanceInterventionReverificationVerificationSetLineageError(
                        "reverification result requirement_id does not "
                        "match its structured requirement"
                    )
                )

            entries.append(
                GovernanceInterventionReverificationVerificationSetEntry(
                    ordinal=ordinal,
                    legacy_requirement=legacy_requirement,
                    requirement_id=(
                        requirement.requirement_id
                    ),
                    requirement_hash=(
                        requirement.requirement_hash
                    ),
                    verification_hash=(
                        result.verification_hash
                    ),
                    verification_disposition=(
                        result.verification_disposition.value
                    ),
                )
            )

        (
            verification_record_hash,
            request_hash,
            work_order_hash,
            attempt_id,
            attempt_execution_id,
            reverification_scope,
        ) = attempt_lineage

        payload: dict[str, Any] = {
            "verification_set_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_SCHEMA_VERSION
            ),
            "tenant_id": (
                actuation_contract.tenant_id
            ),
            "actuation_contract_hash": (
                actuation_contract.contract_hash
            ),
            "intervention_id": (
                actuation_contract.intervention_id
            ),
            "intervention_type": (
                actuation_contract.intervention_type
            ),
            "verification_record_hash": (
                verification_record_hash
            ),
            "request_hash": request_hash,
            "work_order_hash": work_order_hash,
            "attempt_id": attempt_id,
            "attempt_execution_id": (
                attempt_execution_id
            ),
            "reverification_scope": (
                reverification_scope
            ),
            "required_count": len(
                contract_obligations
            ),
            "result_count": len(entries),
            "entries": [
                entry.to_dict()
                for entry in entries
            ],
        }

        return (
            GovernanceInterventionReverificationVerificationSet(
                verification_set_id=payload[
                    "verification_set_id"
                ],
                version=payload["version"],
                schema_version=payload[
                    "schema_version"
                ],
                tenant_id=payload[
                    "tenant_id"
                ],
                actuation_contract_hash=payload[
                    "actuation_contract_hash"
                ],
                intervention_id=payload[
                    "intervention_id"
                ],
                intervention_type=payload[
                    "intervention_type"
                ],
                verification_record_hash=payload[
                    "verification_record_hash"
                ],
                request_hash=payload[
                    "request_hash"
                ],
                work_order_hash=payload[
                    "work_order_hash"
                ],
                attempt_id=payload[
                    "attempt_id"
                ],
                attempt_execution_id=payload[
                    "attempt_execution_id"
                ],
                reverification_scope=payload[
                    "reverification_scope"
                ],
                required_count=payload[
                    "required_count"
                ],
                result_count=payload[
                    "result_count"
                ],
                entries=tuple(entries),
                verification_set_hash=sha256_hex(
                    canonical_json(payload)
                ),
            )
        )

    @staticmethod
    def _validate_requirement_lineage(
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        requirement: GovernanceInterventionVerificationRequirement,
    ) -> None:
        if (
            requirement.tenant_id
            != actuation_contract.tenant_id
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "structured requirement tenant does not match contract"
                )
            )

        if (
            requirement.actuation_contract_hash
            != actuation_contract.contract_hash
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "structured requirement contract hash does not "
                    "match contract"
                )
            )

        if (
            requirement.intervention_id
            != actuation_contract.intervention_id
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "structured requirement intervention_id does "
                    "not match contract"
                )
            )

        if (
            requirement.intervention_type
            != actuation_contract.intervention_type
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "structured requirement intervention_type does "
                    "not match contract"
                )
            )

        if (
            requirement.legacy_requirement
            not in actuation_contract.verification_requirements
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "structured requirement does not refine "
                    "a contract obligation"
                )
            )

    @staticmethod
    def _validate_result_contract_lineage(
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        result: GovernanceInterventionReverificationVerificationResult,
    ) -> None:
        if (
            result.tenant_id
            != actuation_contract.tenant_id
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "reverification result tenant does not match contract"
                )
            )

        if (
            result.actuation_contract_hash
            != actuation_contract.contract_hash
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "reverification result actuation contract hash "
                    "does not match contract"
                )
            )

        if (
            result.intervention_id
            != actuation_contract.intervention_id
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "reverification result intervention_id does "
                    "not match contract"
                )
            )

        if (
            result.intervention_type
            != actuation_contract.intervention_type
        ):
            raise (
                GovernanceInterventionReverificationVerificationSetLineageError(
                    "reverification result intervention_type does "
                    "not match contract"
                )
            )