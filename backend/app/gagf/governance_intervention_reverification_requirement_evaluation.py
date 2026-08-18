from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_reverification_measurement import (
    GovernanceInterventionReverificationMeasurement,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_ID = (
    "governance-intervention-reverification-requirement-evaluation"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationRequirementEvaluationDisposition(
    str,
    Enum,
):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class GovernanceInterventionReverificationRequirementEvaluationError(
    ValueError
):
    """Base error for deterministic reverification evaluation."""


class GovernanceInterventionReverificationRequirementEvaluationLineageError(
    GovernanceInterventionReverificationRequirementEvaluationError
):
    """Raised when requirement and reverification measurement diverge."""


class GovernanceInterventionReverificationRequirementEvaluationOperatorError(
    GovernanceInterventionReverificationRequirementEvaluationError
):
    """Raised when an unsupported governed operator reaches evaluation."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationRequirementEvaluation:
    """
    Immutable deterministic evaluation of one governed reverification
    measurement against one existing structured verification requirement.

    This artifact answers only whether:
    - the supplied reverification evidence is sufficient; and
    - if sufficient, the measured value satisfies the governed comparison.

    It does not:
    - declare VERIFIED, NOT_VERIFIED, or INCONCLUSIVE;
    - determine intervention success or failure;
    - complete a reverification attempt;
    - supersede a verification record;
    - mutate verification lifecycle state;
    - authorize intervention activity;
    - prove causation.
    """

    evaluation_id: str
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
    measurement_hash: str

    actuation_contract_hash: str
    intervention_type: str

    requirement_id: str
    requirement_hash: str
    metric_id: str

    operator: GovernanceInterventionVerificationOperator
    target_value: float
    observed_value: float
    unit: str

    required_measurement_window_seconds: int
    actual_measurement_window_seconds: int
    minimum_record_count: int
    actual_record_count: int

    evidence_sufficient: bool
    comparison_satisfied: bool | None
    disposition: (
        GovernanceInterventionReverificationRequirementEvaluationDisposition
    )

    evaluation_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
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
            "measurement_hash": (
                self.measurement_hash
            ),
            "actuation_contract_hash": (
                self.actuation_contract_hash
            ),
            "intervention_type": (
                self.intervention_type
            ),
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "metric_id": self.metric_id,
            "operator": self.operator.value,
            "target_value": self.target_value,
            "observed_value": self.observed_value,
            "unit": self.unit,
            "required_measurement_window_seconds": (
                self.required_measurement_window_seconds
            ),
            "actual_measurement_window_seconds": (
                self.actual_measurement_window_seconds
            ),
            "minimum_record_count": (
                self.minimum_record_count
            ),
            "actual_record_count": (
                self.actual_record_count
            ),
            "evidence_sufficient": (
                self.evidence_sufficient
            ),
            "comparison_satisfied": (
                self.comparison_satisfied
            ),
            "disposition": self.disposition.value,
        }

    def verify(self) -> bool:
        return (
            self.evaluation_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "evaluation_hash": self.evaluation_hash,
        }


class GovernanceInterventionReverificationRequirementEvaluator:
    """
    Deterministically evaluates I-P reverification measurement evidence
    against an I-B structured verification requirement.

    Evidence sufficiency is resolved before comparison semantics.

    Insufficient evidence is not converted into failure.

    This evaluator does not issue a final governed verification judgment.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        requirement: (
            GovernanceInterventionVerificationRequirement
        ),
        measurement: (
            GovernanceInterventionReverificationMeasurement
        ),
    ) -> GovernanceInterventionReverificationRequirementEvaluation:
        if not requirement.verify():
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "verification requirement failed "
                    "deterministic verification"
                )
            )

        if not measurement.verify():
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "reverification measurement failed "
                    "deterministic verification"
                )
            )

        cls._validate_lineage(
            requirement=requirement,
            measurement=measurement,
        )

        evidence_sufficient = (
            measurement.measurement_window_seconds
            >= requirement.measurement_window_seconds
            and measurement.record_count
            >= requirement.minimum_record_count
        )

        if not evidence_sufficient:
            comparison_satisfied = None

            disposition = (
                GovernanceInterventionReverificationRequirementEvaluationDisposition
                .INSUFFICIENT_EVIDENCE
            )

        else:
            comparison_satisfied = cls._compare(
                operator=requirement.operator,
                observed_value=(
                    measurement.observed_value
                ),
                target_value=requirement.target_value,
            )

            if comparison_satisfied:
                disposition = (
                    GovernanceInterventionReverificationRequirementEvaluationDisposition
                    .SATISFIED
                )

            else:
                disposition = (
                    GovernanceInterventionReverificationRequirementEvaluationDisposition
                    .NOT_SATISFIED
                )

        payload: dict[str, Any] = {
            "evaluation_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_SCHEMA_VERSION
            ),
            "tenant_id": requirement.tenant_id,
            "intervention_id": (
                requirement.intervention_id
            ),
            "verification_record_hash": (
                measurement.verification_record_hash
            ),
            "request_hash": measurement.request_hash,
            "work_order_hash": (
                measurement.work_order_hash
            ),
            "attempt_id": measurement.attempt_id,
            "attempt_execution_id": (
                measurement.attempt_execution_id
            ),
            "reverification_scope": (
                measurement.reverification_scope
            ),
            "evidence_hash": (
                measurement.evidence_hash
            ),
            "measurement_hash": (
                measurement.measurement_hash
            ),
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
            "operator": requirement.operator.value,
            "target_value": requirement.target_value,
            "observed_value": (
                measurement.observed_value
            ),
            "unit": requirement.unit,
            "required_measurement_window_seconds": (
                requirement.measurement_window_seconds
            ),
            "actual_measurement_window_seconds": (
                measurement.measurement_window_seconds
            ),
            "minimum_record_count": (
                requirement.minimum_record_count
            ),
            "actual_record_count": (
                measurement.record_count
            ),
            "evidence_sufficient": (
                evidence_sufficient
            ),
            "comparison_satisfied": (
                comparison_satisfied
            ),
            "disposition": disposition.value,
        }

        return (
            GovernanceInterventionReverificationRequirementEvaluation(
                evaluation_id=payload[
                    "evaluation_id"
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
                evidence_hash=payload[
                    "evidence_hash"
                ],
                measurement_hash=payload[
                    "measurement_hash"
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
                metric_id=payload[
                    "metric_id"
                ],
                operator=requirement.operator,
                target_value=payload[
                    "target_value"
                ],
                observed_value=payload[
                    "observed_value"
                ],
                unit=payload["unit"],
                required_measurement_window_seconds=payload[
                    "required_measurement_window_seconds"
                ],
                actual_measurement_window_seconds=payload[
                    "actual_measurement_window_seconds"
                ],
                minimum_record_count=payload[
                    "minimum_record_count"
                ],
                actual_record_count=payload[
                    "actual_record_count"
                ],
                evidence_sufficient=payload[
                    "evidence_sufficient"
                ],
                comparison_satisfied=payload[
                    "comparison_satisfied"
                ],
                disposition=disposition,
                evaluation_hash=sha256_hex(
                    canonical_json(payload)
                ),
            )
        )

    @staticmethod
    def _validate_lineage(
        *,
        requirement: (
            GovernanceInterventionVerificationRequirement
        ),
        measurement: (
            GovernanceInterventionReverificationMeasurement
        ),
    ) -> None:
        if (
            measurement.tenant_id
            != requirement.tenant_id
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement tenant does not match requirement"
                )
            )

        if (
            measurement.actuation_contract_hash
            != requirement.actuation_contract_hash
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement actuation contract hash "
                    "does not match requirement"
                )
            )

        if (
            measurement.intervention_id
            != requirement.intervention_id
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement intervention_id does not "
                    "match requirement"
                )
            )

        if (
            measurement.intervention_type
            != requirement.intervention_type
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement intervention_type does not "
                    "match requirement"
                )
            )

        if (
            measurement.requirement_id
            != requirement.requirement_id
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement requirement_id does not "
                    "match requirement"
                )
            )

        if (
            measurement.requirement_hash
            != requirement.requirement_hash
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement requirement hash does not "
                    "match requirement"
                )
            )

        if (
            measurement.metric_id
            != requirement.metric_id
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement metric_id does not "
                    "match requirement"
                )
            )

        if (
            measurement.unit
            != requirement.unit
        ):
            raise (
                GovernanceInterventionReverificationRequirementEvaluationLineageError(
                    "measurement unit does not match requirement"
                )
            )

    @staticmethod
    def _compare(
        *,
        operator: (
            GovernanceInterventionVerificationOperator
        ),
        observed_value: float,
        target_value: float,
    ) -> bool:
        if (
            operator
            is GovernanceInterventionVerificationOperator.EQ
        ):
            return observed_value == target_value

        if (
            operator
            is GovernanceInterventionVerificationOperator.NE
        ):
            return observed_value != target_value

        if (
            operator
            is GovernanceInterventionVerificationOperator.LT
        ):
            return observed_value < target_value

        if (
            operator
            is GovernanceInterventionVerificationOperator.LTE
        ):
            return observed_value <= target_value

        if (
            operator
            is GovernanceInterventionVerificationOperator.GT
        ):
            return observed_value > target_value

        if (
            operator
            is GovernanceInterventionVerificationOperator.GTE
        ):
            return observed_value >= target_value

        raise (
            GovernanceInterventionReverificationRequirementEvaluationOperatorError(
                "unsupported governed verification operator"
            )
        )