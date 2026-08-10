from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_execution_receipt import (
    GovernanceInterventionExecutionReceipt,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_ID = (
    "governance-intervention-outcome-observation"
)
GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionOutcomeObservationError(ValueError):
    """Base error for governed outcome-observation evidence."""


class GovernanceInterventionOutcomeObservationLineageError(
    GovernanceInterventionOutcomeObservationError
):
    """Raised when observation lineage does not match governed execution."""


class GovernanceInterventionOutcomeObservationRequirementError(
    GovernanceInterventionOutcomeObservationError
):
    """Raised when an observation targets a non-contractual requirement."""


class GovernanceInterventionOutcomeObservationIndependenceError(
    GovernanceInterventionOutcomeObservationError
):
    """Raised when the observation source is the execution adapter itself."""


class GovernanceInterventionOutcomeObservationEvidenceError(
    GovernanceInterventionOutcomeObservationError
):
    """Raised when observation evidence is incomplete or invalid."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionOutcomeObservation:
    """
    Immutable post-execution observation evidence for one precommitted
    verification requirement.

    An observation records what an independent source observed after a
    governed execution attempt. It does not determine whether the desired
    governance outcome was achieved.

    In particular, this artifact is not:
    - an execution result;
    - an execution receipt;
    - a verification judgment;
    - evidence of causation by itself.
    """

    observation_id: str
    version: str
    schema_version: str

    tenant_id: str
    contract_hash: str
    execution_receipt_hash: str
    execution_result_hash: str
    actuation_id: str

    intervention_id: str
    intervention_type: str

    verification_requirement: str

    execution_adapter_id: str
    execution_adapter_version: str

    source_id: str
    source_kind: str
    observed_at: str

    observation_summary: str
    evidence_references: tuple[str, ...]
    record_count: int

    observation_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "execution_receipt_hash": self.execution_receipt_hash,
            "execution_result_hash": self.execution_result_hash,
            "actuation_id": self.actuation_id,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "verification_requirement": self.verification_requirement,
            "execution_adapter_id": self.execution_adapter_id,
            "execution_adapter_version": self.execution_adapter_version,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "observed_at": self.observed_at,
            "observation_summary": self.observation_summary,
            "evidence_references": list(self.evidence_references),
            "record_count": self.record_count,
        }

    def verify(self) -> bool:
        return self.observation_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "observation_hash": self.observation_hash,
        }


class GovernanceInterventionOutcomeObservationBuilder:
    """
    Builds deterministic GEX-001I-A observation evidence.

    The builder binds independent post-execution observations to:
    - a verified GEX-001C actuation contract;
    - a verified GEX-001H execution receipt; and
    - one verification requirement fixed before execution.

    It performs no success evaluation and emits no VERIFIED,
    NOT_VERIFIED, or INCONCLUSIVE judgment.
    """

    @staticmethod
    def _required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise GovernanceInterventionOutcomeObservationEvidenceError(
                f"{field_name} is required"
            )

        return normalized

    @classmethod
    def _normalize_references(
        cls,
        values: Iterable[str],
    ) -> tuple[str, ...]:
        normalized = tuple(
            cls._required(
                value,
                "evidence_references",
            )
            for value in values
        )

        if not normalized:
            raise GovernanceInterventionOutcomeObservationEvidenceError(
                "at least one evidence reference is required"
            )

        if len(normalized) != len(set(normalized)):
            raise GovernanceInterventionOutcomeObservationEvidenceError(
                "evidence_references must not contain duplicates"
            )

        return normalized

    @classmethod
    def build(
        cls,
        *,
        contract: GovernanceInterventionActuationContract,
        execution_receipt: GovernanceInterventionExecutionReceipt,
        verification_requirement: str,
        source_id: str,
        source_kind: str,
        observed_at: str,
        observation_summary: str,
        evidence_references: Iterable[str],
        record_count: int,
    ) -> GovernanceInterventionOutcomeObservation:
        if not contract.verify():
            raise GovernanceInterventionOutcomeObservationLineageError(
                "actuation contract failed deterministic verification"
            )

        if not execution_receipt.verify():
            raise GovernanceInterventionOutcomeObservationLineageError(
                "execution receipt failed deterministic verification"
            )

        cls._validate_lineage(
            contract=contract,
            execution_receipt=execution_receipt,
        )

        requirement = cls._required(
            verification_requirement,
            "verification_requirement",
        )

        if requirement not in contract.verification_requirements:
            raise GovernanceInterventionOutcomeObservationRequirementError(
                "verification requirement was not precommitted "
                "in the actuation contract"
            )

        normalized_source_id = cls._required(
            source_id,
            "source_id",
        )

        normalized_source_kind = cls._required(
            source_kind,
            "source_kind",
        )

        normalized_observed_at = cls._required(
            observed_at,
            "observed_at",
        )

        normalized_summary = cls._required(
            observation_summary,
            "observation_summary",
        )

        normalized_references = cls._normalize_references(
            evidence_references
        )

        if record_count < 1:
            raise GovernanceInterventionOutcomeObservationEvidenceError(
                "record_count must be at least 1"
            )

        if normalized_source_id == execution_receipt.adapter_id:
            raise GovernanceInterventionOutcomeObservationIndependenceError(
                "outcome observation source must not be "
                "the execution adapter"
            )

        payload: dict[str, Any] = {
            "observation_id": (
                GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_SCHEMA_VERSION
            ),
            "tenant_id": contract.tenant_id,
            "contract_hash": contract.contract_hash,
            "execution_receipt_hash": execution_receipt.receipt_hash,
            "execution_result_hash": execution_receipt.result_hash,
            "actuation_id": execution_receipt.actuation_id,
            "intervention_id": contract.intervention_id,
            "intervention_type": contract.intervention_type,
            "verification_requirement": requirement,
            "execution_adapter_id": execution_receipt.adapter_id,
            "execution_adapter_version": execution_receipt.adapter_version,
            "source_id": normalized_source_id,
            "source_kind": normalized_source_kind,
            "observed_at": normalized_observed_at,
            "observation_summary": normalized_summary,
            "evidence_references": list(normalized_references),
            "record_count": record_count,
        }

        return GovernanceInterventionOutcomeObservation(
            observation_id=payload["observation_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            contract_hash=payload["contract_hash"],
            execution_receipt_hash=payload[
                "execution_receipt_hash"
            ],
            execution_result_hash=payload[
                "execution_result_hash"
            ],
            actuation_id=payload["actuation_id"],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            verification_requirement=payload[
                "verification_requirement"
            ],
            execution_adapter_id=payload[
                "execution_adapter_id"
            ],
            execution_adapter_version=payload[
                "execution_adapter_version"
            ],
            source_id=payload["source_id"],
            source_kind=payload["source_kind"],
            observed_at=payload["observed_at"],
            observation_summary=payload[
                "observation_summary"
            ],
            evidence_references=normalized_references,
            record_count=payload["record_count"],
            observation_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        contract: GovernanceInterventionActuationContract,
        execution_receipt: GovernanceInterventionExecutionReceipt,
    ) -> None:
        if execution_receipt.tenant_id != contract.tenant_id:
            raise GovernanceInterventionOutcomeObservationLineageError(
                "execution receipt tenant_id does not match contract"
            )

        if execution_receipt.contract_hash != contract.contract_hash:
            raise GovernanceInterventionOutcomeObservationLineageError(
                "execution receipt contract_hash does not match contract"
            )

        if execution_receipt.intervention_id != contract.intervention_id:
            raise GovernanceInterventionOutcomeObservationLineageError(
                "execution receipt intervention_id does not match contract"
            )

        if (
            execution_receipt.intervention_type
            != contract.intervention_type
        ):
            raise GovernanceInterventionOutcomeObservationLineageError(
                "execution receipt intervention_type does not match contract"
            )