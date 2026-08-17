from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from backend.app.gagf.governance_intervention_reverification_evidence import (
    GovernanceInterventionReverificationEvidence,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_ID = (
    "governance-intervention-reverification-measurement"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationMeasurementError(
    ValueError
):
    """Base error for governed reverification measurements."""


class GovernanceInterventionReverificationMeasurementLineageError(
    GovernanceInterventionReverificationMeasurementError
):
    """Raised when measurement lineage diverges from governed evidence."""


class GovernanceInterventionReverificationMeasurementValueError(
    GovernanceInterventionReverificationMeasurementError
):
    """Raised when governed measurement values are invalid."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationMeasurement:
    """
    Immutable quantitative measurement derived from one governed
    reverification-evidence artifact.

    This artifact records a typed measured value for one existing structured
    verification requirement.

    It does not:
    - evaluate the requirement operator;
    - compare the value with the requirement target;
    - determine whether minimum evidence is sufficient;
    - declare SATISFIED, NOT_SATISFIED, or INSUFFICIENT_EVIDENCE;
    - declare VERIFIED, NOT_VERIFIED, or INCONCLUSIVE;
    - determine intervention success or failure;
    - complete a reverification attempt;
    - supersede a verification record;
    - mutate verification lifecycle state;
    - authorize intervention activity;
    - prove causation.
    """

    measurement_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    request_hash: str
    work_order_hash: str
    attempt_id: str
    attempt_execution_id: str
    reverification_scope: str

    evidence_hash: str

    actuation_contract_hash: str
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
            "intervention_id": self.intervention_id,
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
            "evidence_hash": self.evidence_hash,
            "actuation_contract_hash": (
                self.actuation_contract_hash
            ),
            "intervention_type": (
                self.intervention_type
            ),
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "metric_id": self.metric_id,
            "observed_value": self.observed_value,
            "unit": self.unit,
            "measurement_window_seconds": (
                self.measurement_window_seconds
            ),
            "record_count": self.record_count,
        }

    def verify(self) -> bool:
        return (
            self.measurement_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "measurement_hash": self.measurement_hash,
        }


class GovernanceInterventionReverificationMeasurementBuilder:
    """
    Builds deterministic quantitative evidence from governed I-O evidence.

    Authority ends at measurement.

    The builder does not:
    - evaluate the requirement;
    - enforce the requirement target;
    - turn record-count sufficiency into a disposition;
    - issue verification judgments;
    - mutate I-N or I-I lifecycle state;
    - supersede verification records;
    - authorize intervention activity;
    - infer causation.
    """

    @staticmethod
    def _required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise (
                GovernanceInterventionReverificationMeasurementValueError(
                    f"{field_name} is required"
                )
            )

        if normalized != value:
            raise (
                GovernanceInterventionReverificationMeasurementValueError(
                    f"{field_name} must already be canonical"
                )
            )

        return normalized

    @classmethod
    def build(
        cls,
        *,
        requirement: (
            GovernanceInterventionVerificationRequirement
        ),
        evidence: (
            GovernanceInterventionReverificationEvidence
        ),
        observed_value: float,
        unit: str,
        measurement_window_seconds: int,
    ) -> GovernanceInterventionReverificationMeasurement:
        if not requirement.verify():
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "verification requirement failed "
                    "deterministic verification"
                )
            )

        if not evidence.verify():
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "reverification evidence failed "
                    "deterministic verification"
                )
            )

        cls._validate_lineage(
            requirement=requirement,
            evidence=evidence,
        )

        normalized_value = float(
            observed_value
        )

        if not isfinite(normalized_value):
            raise (
                GovernanceInterventionReverificationMeasurementValueError(
                    "observed_value must be finite"
                )
            )

        normalized_unit = cls._required(
            unit,
            "unit",
        )

        if normalized_unit != requirement.unit:
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "measurement unit does not match "
                    "verification requirement"
                )
            )

        if measurement_window_seconds < 1:
            raise (
                GovernanceInterventionReverificationMeasurementValueError(
                    "measurement_window_seconds must be at least 1"
                )
            )

        payload: dict[str, Any] = {
            "measurement_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_SCHEMA_VERSION
            ),
            "tenant_id": evidence.tenant_id,
            "intervention_id": (
                evidence.intervention_id
            ),
            "verification_record_hash": (
                evidence.verification_record_hash
            ),
            "request_hash": evidence.request_hash,
            "work_order_hash": (
                evidence.work_order_hash
            ),
            "attempt_id": evidence.attempt_id,
            "attempt_execution_id": (
                evidence.attempt_execution_id
            ),
            "reverification_scope": (
                evidence.reverification_scope
            ),
            "evidence_hash": evidence.evidence_hash,
            "actuation_contract_hash": (
                requirement.actuation_contract_hash
            ),
            "intervention_type": (
                requirement.intervention_type
            ),
            "requirement_id": (
                requirement.requirement_id
            ),
            "requirement_hash": (
                requirement.requirement_hash
            ),
            "metric_id": requirement.metric_id,
            "observed_value": normalized_value,
            "unit": normalized_unit,
            "measurement_window_seconds": (
                measurement_window_seconds
            ),
            "record_count": evidence.record_count,
        }

        return GovernanceInterventionReverificationMeasurement(
            measurement_id=payload[
                "measurement_id"
            ],
            version=payload["version"],
            schema_version=payload[
                "schema_version"
            ],
            tenant_id=payload["tenant_id"],
            intervention_id=payload[
                "intervention_id"
            ],
            verification_record_hash=payload[
                "verification_record_hash"
            ],
            request_hash=payload["request_hash"],
            work_order_hash=payload[
                "work_order_hash"
            ],
            attempt_id=payload["attempt_id"],
            attempt_execution_id=payload[
                "attempt_execution_id"
            ],
            reverification_scope=payload[
                "reverification_scope"
            ],
            evidence_hash=payload[
                "evidence_hash"
            ],
            actuation_contract_hash=payload[
                "actuation_contract_hash"
            ],
            intervention_type=payload[
                "intervention_type"
            ],
            requirement_id=payload[
                "requirement_id"
            ],
            requirement_hash=payload[
                "requirement_hash"
            ],
            metric_id=payload["metric_id"],
            observed_value=payload[
                "observed_value"
            ],
            unit=payload["unit"],
            measurement_window_seconds=payload[
                "measurement_window_seconds"
            ],
            record_count=payload["record_count"],
            measurement_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        requirement: (
            GovernanceInterventionVerificationRequirement
        ),
        evidence: (
            GovernanceInterventionReverificationEvidence
        ),
    ) -> None:
        if (
            evidence.tenant_id
            != requirement.tenant_id
        ):
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "reverification evidence tenant does "
                    "not match verification requirement"
                )
            )

        if (
            evidence.intervention_id
            != requirement.intervention_id
        ):
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "reverification evidence intervention_id "
                    "does not match verification requirement"
                )
            )

        if (
            evidence.requirement_id
            != requirement.requirement_id
        ):
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "reverification evidence requirement_id "
                    "does not match verification requirement"
                )
            )

        if (
            evidence.requirement_hash
            != requirement.requirement_hash
        ):
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "reverification evidence requirement_hash "
                    "does not match verification requirement"
                )
            )

        if (
            evidence.metric_id
            != requirement.metric_id
        ):
            raise (
                GovernanceInterventionReverificationMeasurementLineageError(
                    "reverification evidence metric_id "
                    "does not match verification requirement"
                )
            )