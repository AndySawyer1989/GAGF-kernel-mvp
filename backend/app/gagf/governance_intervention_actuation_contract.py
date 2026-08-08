from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_intervention_execution_authorization import (
    GovernanceInterventionExecutionAuthorization,
)
from backend.app.gagf.governance_intervention_execution_binding import (
    GovernanceInterventionExecutionBinding,
)


GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_ID = (
    "governance-intervention-actuation-contract"
)
GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_SCHEMA_VERSION = "1"


class GovernanceInterventionActuationContractError(RuntimeError):
    """Base error for invalid governed actuation contracts."""


class InvalidGovernanceInterventionAuthorizationError(
    GovernanceInterventionActuationContractError
):
    """Raised when execution authorization cannot support actuation."""


class GovernanceInterventionActuationLineageError(
    GovernanceInterventionActuationContractError
):
    """Raised when binding and authorization lineage diverge."""


class UnboundedGovernanceInterventionError(
    GovernanceInterventionActuationContractError
):
    """Raised when an actuation request lacks constitutional bounds."""


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _normalize_required_strings(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(
        value.strip()
        for value in values
        if value.strip()
    )

    if not normalized:
        raise UnboundedGovernanceInterventionError(
            f"{field_name} must contain at least one non-empty value"
        )

    if len(normalized) != len(values):
        raise UnboundedGovernanceInterventionError(
            f"{field_name} cannot contain blank values"
        )

    return normalized


@dataclass(frozen=True)
class GovernanceInterventionActuationContract:
    contract_id: str
    contract_version: str
    schema_version: str

    tenant_id: str

    binding_hash: str
    authorization_receipt_hash: str
    execution_context_hash: str

    intervention_id: str
    intervention_type: str

    requested_effect: str
    effect_boundary: str

    preconditions: tuple[str, ...]
    abort_criteria: tuple[str, ...]

    rollback_strategy: str

    max_attempts: int
    timeout_seconds: int

    verification_requirements: tuple[str, ...]

    contract_hash: str

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "binding_hash": self.binding_hash,
            "authorization_receipt_hash": (
                self.authorization_receipt_hash
            ),
            "execution_context_hash": (
                self.execution_context_hash
            ),
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "requested_effect": self.requested_effect,
            "effect_boundary": self.effect_boundary,
            "preconditions": list(self.preconditions),
            "abort_criteria": list(self.abort_criteria),
            "rollback_strategy": self.rollback_strategy,
            "max_attempts": self.max_attempts,
            "timeout_seconds": self.timeout_seconds,
            "verification_requirements": list(
                self.verification_requirements
            ),
        }

    def verify(self) -> bool:
        expected_hash = _sha256_hex(
            _canonical_json(
                self._hash_payload()
            )
        )

        return self.contract_hash == expected_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._hash_payload(),
            "contract_hash": self.contract_hash,
        }


class GovernanceInterventionActuationContractBuilder:
    """
    Builds a bounded actuation contract from previously established
    execution binding and authorization artifacts.

    This builder does not execute, dispatch, actuate, journal, or verify
    a real-world intervention.
    """

    def build(
        self,
        *,
        binding: GovernanceInterventionExecutionBinding,
        authorization: GovernanceInterventionExecutionAuthorization,
        requested_effect: str,
        effect_boundary: str,
        preconditions: tuple[str, ...],
        abort_criteria: tuple[str, ...],
        rollback_strategy: str,
        max_attempts: int,
        timeout_seconds: int,
        verification_requirements: tuple[str, ...],
    ) -> GovernanceInterventionActuationContract:
        self._validate_lineage(
            binding=binding,
            authorization=authorization,
        )

        requested_effect = requested_effect.strip()
        effect_boundary = effect_boundary.strip()
        rollback_strategy = rollback_strategy.strip()

        if not requested_effect:
            raise UnboundedGovernanceInterventionError(
                "requested_effect is required"
            )

        if not effect_boundary:
            raise UnboundedGovernanceInterventionError(
                "effect_boundary is required"
            )

        if not rollback_strategy:
            raise UnboundedGovernanceInterventionError(
                "rollback_strategy is required"
            )

        if max_attempts < 1:
            raise UnboundedGovernanceInterventionError(
                "max_attempts must be at least 1"
            )

        if timeout_seconds < 1:
            raise UnboundedGovernanceInterventionError(
                "timeout_seconds must be at least 1"
            )

        normalized_preconditions = (
            _normalize_required_strings(
                preconditions,
                field_name="preconditions",
            )
        )

        normalized_abort_criteria = (
            _normalize_required_strings(
                abort_criteria,
                field_name="abort_criteria",
            )
        )

        normalized_verification_requirements = (
            _normalize_required_strings(
                verification_requirements,
                field_name="verification_requirements",
            )
        )

        payload: dict[str, Any] = {
            "contract_id": (
                GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_ID
            ),
            "contract_version": (
                GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_SCHEMA_VERSION
            ),
            "tenant_id": binding.tenant_id,
            "binding_hash": binding.binding_hash,
            "authorization_receipt_hash": (
                authorization.authorization_receipt.receipt_hash
            ),
            "execution_context_hash": (
                authorization.execution_context_hash
            ),
            "intervention_id": binding.intervention_id,
            "intervention_type": binding.intervention_type,
            "requested_effect": requested_effect,
            "effect_boundary": effect_boundary,
            "preconditions": list(
                normalized_preconditions
            ),
            "abort_criteria": list(
                normalized_abort_criteria
            ),
            "rollback_strategy": rollback_strategy,
            "max_attempts": max_attempts,
            "timeout_seconds": timeout_seconds,
            "verification_requirements": list(
                normalized_verification_requirements
            ),
        }

        contract_hash = _sha256_hex(
            _canonical_json(payload)
        )

        return GovernanceInterventionActuationContract(
            contract_id=payload["contract_id"],
            contract_version=payload["contract_version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            binding_hash=payload["binding_hash"],
            authorization_receipt_hash=(
                payload["authorization_receipt_hash"]
            ),
            execution_context_hash=(
                payload["execution_context_hash"]
            ),
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            requested_effect=payload["requested_effect"],
            effect_boundary=payload["effect_boundary"],
            preconditions=normalized_preconditions,
            abort_criteria=normalized_abort_criteria,
            rollback_strategy=payload["rollback_strategy"],
            max_attempts=payload["max_attempts"],
            timeout_seconds=payload["timeout_seconds"],
            verification_requirements=(
                normalized_verification_requirements
            ),
            contract_hash=contract_hash,
        )

    @staticmethod
    def _validate_lineage(
        *,
        binding: GovernanceInterventionExecutionBinding,
        authorization: GovernanceInterventionExecutionAuthorization,
    ) -> None:
        if not binding.verify():
            raise GovernanceInterventionActuationLineageError(
                "execution binding failed hash verification"
            )

        if not authorization.allowed:
            raise InvalidGovernanceInterventionAuthorizationError(
                "intervention execution authorization is not allowed"
            )

        if not authorization.authorization_receipt.verify():
            raise InvalidGovernanceInterventionAuthorizationError(
                "authorization receipt failed verification"
            )

        if authorization.binding_hash != binding.binding_hash:
            raise GovernanceInterventionActuationLineageError(
                "authorization binding hash does not match execution binding"
            )

        if (
            authorization.execution_context_hash
            != binding.execution_context_hash
        ):
            raise GovernanceInterventionActuationLineageError(
                "authorization execution context does not match binding"
            )
