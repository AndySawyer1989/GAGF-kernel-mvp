from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from backend.app.gagf.governance_intervention_execution_receipt import (
    GovernanceInterventionExecutionReceipt,
)
from backend.app.gagf.governance_intervention_outcome_observation import (
    GovernanceInterventionOutcomeObservation,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_ID = (
    "governance-intervention-outcome-measurement"
)
GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionOutcomeMeasurementError(ValueError):
    """Base error for governed outcome measurements."""


class GovernanceInterventionOutcomeMeasurementLineageError(
    GovernanceInterventionOutcomeMeasurementError
):
    """Raised when measurement lineage diverges from governed evidence."""


class GovernanceInterventionOutcomeMeasurementValueError(
    GovernanceInterventionOutcomeMeasurementError
):
    """Raised when governed measurement values are invalid."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionOutcomeMeasurement:
    """
    Immutable quantitative measurement for one precommitted verification rule.

    This artifact records a typed measured value derived from governed
    post-execution observation evidence.

    It does not:
    - evaluate the requirement operator;
    - determine whether the requirement is satisfied;
    - declare VERIFIED, NOT_VERIFIED, or INCONCLUSIVE;
    - determine intervention success;
    - prove causation.
    """

    measurement_id: str
    version: str
    schema_version: str

    tenant_id: str
    contract_hash: str
    execution_receipt_hash: str
    observation_hash: str

    intervention_id: str
    intervention_type: str

    requirement_id: str
    requirement_hash: str
    metric_id: str

    observed_value: float
    unit: str
    measurement_window_seconds: int
    record_count: int

    measurement_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "execution_receipt_hash": self.execution_receipt_hash,
            "observation_hash": self.observation_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "metric_id": self.metric_id,
            "observed_value": self.observed_value,
            "unit": self.unit,
            "measurement_window_seconds": self.measurement_window_seconds,
            "record_count": self.record_count,
        }

    def verify(self) -> bool:
        return self.measurement_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "measurement_hash": self.measurement_hash,
        }


class GovernanceInterventionOutcomeMeasurementBuilder:
    """
    Builds deterministic quantitative evidence for GEX-001I-C.

    The measurement must remain bound to a verified requirement, execution
    receipt, and independent outcome observation.

    No comparison with the requirement target occurs here.
    """

    @staticmethod
    def _required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise GovernanceInterventionOutcomeMeasurementValueError(
                f"{field_name} is required"
            )

        return normalized

    @classmethod
    def build(
        cls,
        *,
        requirement: GovernanceInterventionVerificationRequirement,
        execution_receipt: GovernanceInterventionExecutionReceipt,
        observation: GovernanceInterventionOutcomeObservation,
        observed_value: float,
        unit: str,
        measurement_window_seconds: int,
    ) -> GovernanceInterventionOutcomeMeasurement:
        if not requirement.verify():
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "verification requirement failed deterministic verification"
            )

        if not execution_receipt.verify():
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "execution receipt failed deterministic verification"
            )

        if not observation.verify():
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "outcome observation failed deterministic verification"
            )

        cls._validate_lineage(
            requirement=requirement,
            execution_receipt=execution_receipt,
            observation=observation,
        )

        normalized_value = float(observed_value)

        if not isfinite(normalized_value):
            raise GovernanceInterventionOutcomeMeasurementValueError(
                "observed_value must be finite"
            )

        normalized_unit = cls._required(
            unit,
            "unit",
        )

        if normalized_unit != requirement.unit:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "measurement unit does not match verification requirement"
            )

        if measurement_window_seconds < 1:
            raise GovernanceInterventionOutcomeMeasurementValueError(
                "measurement_window_seconds must be at least 1"
            )

        payload: dict[str, Any] = {
            "measurement_id": (
                GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_SCHEMA_VERSION
            ),
            "tenant_id": requirement.tenant_id,
            "contract_hash": requirement.actuation_contract_hash,
            "execution_receipt_hash": execution_receipt.receipt_hash,
            "observation_hash": observation.observation_hash,
            "intervention_id": requirement.intervention_id,
            "intervention_type": requirement.intervention_type,
            "requirement_id": requirement.requirement_id,
            "requirement_hash": requirement.requirement_hash,
            "metric_id": requirement.metric_id,
            "observed_value": normalized_value,
            "unit": normalized_unit,
            "measurement_window_seconds": measurement_window_seconds,
            "record_count": observation.record_count,
        }

        return GovernanceInterventionOutcomeMeasurement(
            **payload,
            measurement_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        requirement: GovernanceInterventionVerificationRequirement,
        execution_receipt: GovernanceInterventionExecutionReceipt,
        observation: GovernanceInterventionOutcomeObservation,
    ) -> None:
        if execution_receipt.tenant_id != requirement.tenant_id:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "execution receipt tenant does not match requirement"
            )

        if (
            execution_receipt.contract_hash
            != requirement.actuation_contract_hash
        ):
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "execution receipt contract hash does not match requirement"
            )

        if execution_receipt.intervention_id != requirement.intervention_id:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "execution receipt intervention_id does not match requirement"
            )

        if (
            execution_receipt.intervention_type
            != requirement.intervention_type
        ):
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "execution receipt intervention_type does not match requirement"
            )

        if observation.tenant_id != requirement.tenant_id:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "observation tenant does not match requirement"
            )

        if (
            observation.contract_hash
            != requirement.actuation_contract_hash
        ):
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "observation contract hash does not match requirement"
            )

        if observation.execution_receipt_hash != execution_receipt.receipt_hash:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "observation execution receipt hash does not match receipt"
            )

        if observation.intervention_id != requirement.intervention_id:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "observation intervention_id does not match requirement"
            )

        if observation.intervention_type != requirement.intervention_type:
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "observation intervention_type does not match requirement"
            )

        if (
            observation.verification_requirement
            != requirement.legacy_requirement
        ):
            raise GovernanceInterventionOutcomeMeasurementLineageError(
                "observation requirement does not match structured requirement"
            )