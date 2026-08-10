from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_ID = (
    "governance-intervention-verification-requirement"
)
GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionVerificationOperator(str, Enum):
    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    LTE = "LTE"
    GT = "GT"
    GTE = "GTE"


class GovernanceInterventionVerificationRequirementError(ValueError):
    """Base error for governed verification requirements."""


class GovernanceInterventionVerificationRequirementLineageError(
    GovernanceInterventionVerificationRequirementError
):
    """Raised when a requirement lacks valid actuation-contract lineage."""


class GovernanceInterventionVerificationRequirementValueError(
    GovernanceInterventionVerificationRequirementError
):
    """Raised when a structured verification rule is invalid."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationRequirement:
    """
    Immutable machine-readable requirement associated with one descriptive
    verification requirement already present in a GEX-001C actuation contract.

    This artifact defines comparison semantics only.

    It does not:
    - execute an intervention;
    - observe an outcome;
    - evaluate an observation;
    - declare VERIFIED, NOT_VERIFIED, or INCONCLUSIVE;
    - prove that this requirement was committed before execution.

    Pre-execution commitment is a separate governance step.
    """

    requirement_contract_id: str
    version: str
    schema_version: str

    tenant_id: str
    actuation_contract_hash: str
    intervention_id: str
    intervention_type: str

    legacy_requirement: str
    requirement_id: str
    description: str

    metric_id: str
    operator: GovernanceInterventionVerificationOperator
    target_value: float
    unit: str

    measurement_window_seconds: int
    minimum_record_count: int

    requirement_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "requirement_contract_id": self.requirement_contract_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "actuation_contract_hash": self.actuation_contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "legacy_requirement": self.legacy_requirement,
            "requirement_id": self.requirement_id,
            "description": self.description,
            "metric_id": self.metric_id,
            "operator": self.operator.value,
            "target_value": self.target_value,
            "unit": self.unit,
            "measurement_window_seconds": self.measurement_window_seconds,
            "minimum_record_count": self.minimum_record_count,
        }

    def verify(self) -> bool:
        return self.requirement_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "requirement_hash": self.requirement_hash,
        }


class GovernanceInterventionVerificationRequirementBuilder:
    """
    Builds deterministic GEX-001I-B structured verification requirements.

    The legacy requirement must already exist in the supplied GEX-001C
    actuation contract. This prevents a structured requirement from silently
    changing which descriptive verification obligation it refines.

    This builder does not prove pre-execution commitment. That responsibility
    belongs to the subsequent commitment-binding layer.
    """

    @staticmethod
    def _required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise GovernanceInterventionVerificationRequirementValueError(
                f"{field_name} is required"
            )

        return normalized

    @classmethod
    def build(
        cls,
        *,
        actuation_contract: GovernanceInterventionActuationContract,
        legacy_requirement: str,
        requirement_id: str,
        description: str,
        metric_id: str,
        operator: GovernanceInterventionVerificationOperator,
        target_value: float,
        unit: str,
        measurement_window_seconds: int,
        minimum_record_count: int,
    ) -> GovernanceInterventionVerificationRequirement:
        if not actuation_contract.verify():
            raise GovernanceInterventionVerificationRequirementLineageError(
                "actuation contract failed deterministic verification"
            )

        normalized_legacy_requirement = cls._required(
            legacy_requirement,
            "legacy_requirement",
        )

        if (
            normalized_legacy_requirement
            not in actuation_contract.verification_requirements
        ):
            raise GovernanceInterventionVerificationRequirementLineageError(
                "legacy requirement is not present in the "
                "actuation contract"
            )

        normalized_requirement_id = cls._required(
            requirement_id,
            "requirement_id",
        )

        normalized_description = cls._required(
            description,
            "description",
        )

        normalized_metric_id = cls._required(
            metric_id,
            "metric_id",
        )

        normalized_unit = cls._required(
            unit,
            "unit",
        )

        if not isinstance(
            operator,
            GovernanceInterventionVerificationOperator,
        ):
            raise GovernanceInterventionVerificationRequirementValueError(
                "operator must be a governed verification operator"
            )

        normalized_target_value = float(target_value)

        if not isfinite(normalized_target_value):
            raise GovernanceInterventionVerificationRequirementValueError(
                "target_value must be finite"
            )

        if measurement_window_seconds < 1:
            raise GovernanceInterventionVerificationRequirementValueError(
                "measurement_window_seconds must be at least 1"
            )

        if minimum_record_count < 1:
            raise GovernanceInterventionVerificationRequirementValueError(
                "minimum_record_count must be at least 1"
            )

        payload: dict[str, Any] = {
            "requirement_contract_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_SCHEMA_VERSION
            ),
            "tenant_id": actuation_contract.tenant_id,
            "actuation_contract_hash": (
                actuation_contract.contract_hash
            ),
            "intervention_id": actuation_contract.intervention_id,
            "intervention_type": actuation_contract.intervention_type,
            "legacy_requirement": normalized_legacy_requirement,
            "requirement_id": normalized_requirement_id,
            "description": normalized_description,
            "metric_id": normalized_metric_id,
            "operator": operator.value,
            "target_value": normalized_target_value,
            "unit": normalized_unit,
            "measurement_window_seconds": (
                measurement_window_seconds
            ),
            "minimum_record_count": minimum_record_count,
        }

        return GovernanceInterventionVerificationRequirement(
            requirement_contract_id=payload[
                "requirement_contract_id"
            ],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            actuation_contract_hash=payload[
                "actuation_contract_hash"
            ],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            legacy_requirement=payload["legacy_requirement"],
            requirement_id=payload["requirement_id"],
            description=payload["description"],
            metric_id=payload["metric_id"],
            operator=operator,
            target_value=payload["target_value"],
            unit=payload["unit"],
            measurement_window_seconds=payload[
                "measurement_window_seconds"
            ],
            minimum_record_count=payload[
                "minimum_record_count"
            ],
            requirement_hash=sha256_hex(
                canonical_json(payload)
            ),
        )