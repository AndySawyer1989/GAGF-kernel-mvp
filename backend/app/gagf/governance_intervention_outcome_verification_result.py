from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_requirement_evaluation import (
    GovernanceInterventionRequirementEvaluation,
    GovernanceInterventionRequirementEvaluationDisposition,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_ID = (
    "governance-intervention-outcome-verification-result"
)
GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionOutcomeVerificationDisposition(
    str,
    Enum,
):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class GovernanceInterventionOutcomeVerificationResultError(ValueError):
    """Base error for governed outcome verification."""


class GovernanceInterventionOutcomeVerificationResultIntegrityError(
    GovernanceInterventionOutcomeVerificationResultError
):
    """Raised when the supplied deterministic evaluation is invalid."""


class GovernanceInterventionOutcomeVerificationResultDispositionError(
    GovernanceInterventionOutcomeVerificationResultError
):
    """Raised when an unsupported evaluation disposition reaches verification."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionOutcomeVerificationResult:
    """
    Immutable governed verification result for one deterministic requirement
    evaluation.

    VERIFIED means only that sufficient governed evidence deterministically
    satisfied the precommitted verification requirement.

    NOT_VERIFIED means only that sufficient governed evidence deterministically
    did not satisfy the precommitted verification requirement.

    INCONCLUSIVE means the governed evidence was insufficient to resolve the
    requirement.

    This artifact does not:
    - claim intervention success or failure;
    - establish causation;
    - authorize future action;
    - order continuation, rollback, or remediation;
    - alter the requirement, measurement, or evaluation.
    """

    verification_result_id: str
    version: str
    schema_version: str

    tenant_id: str
    contract_hash: str
    intervention_id: str
    intervention_type: str

    requirement_id: str
    requirement_hash: str
    measurement_hash: str
    observation_hash: str
    execution_receipt_hash: str
    evaluation_hash: str

    metric_id: str
    operator: str
    target_value: float
    observed_value: float
    unit: str

    evidence_sufficient: bool
    comparison_satisfied: bool | None
    evaluation_disposition: str
    verification_disposition: (
        GovernanceInterventionOutcomeVerificationDisposition
    )

    verification_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "verification_result_id": self.verification_result_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "measurement_hash": self.measurement_hash,
            "observation_hash": self.observation_hash,
            "execution_receipt_hash": self.execution_receipt_hash,
            "evaluation_hash": self.evaluation_hash,
            "metric_id": self.metric_id,
            "operator": self.operator,
            "target_value": self.target_value,
            "observed_value": self.observed_value,
            "unit": self.unit,
            "evidence_sufficient": self.evidence_sufficient,
            "comparison_satisfied": self.comparison_satisfied,
            "evaluation_disposition": self.evaluation_disposition,
            "verification_disposition": (
                self.verification_disposition.value
            ),
        }

    def verify(self) -> bool:
        return self.verification_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_hash": self.verification_hash,
        }


class GovernanceInterventionOutcomeVerificationResultBuilder:
    """
    Converts one verified deterministic C2 evaluation into one bounded
    governance verification disposition.

    This builder performs no measurement, comparison, causal attribution,
    execution, authorization, rollback, or policy selection.
    """

    @classmethod
    def build(
        cls,
        *,
        evaluation: GovernanceInterventionRequirementEvaluation,
    ) -> GovernanceInterventionOutcomeVerificationResult:
        if not evaluation.verify():
            raise GovernanceInterventionOutcomeVerificationResultIntegrityError(
                "requirement evaluation failed deterministic verification"
            )

        verification_disposition = cls._map_disposition(
            evaluation=evaluation
        )

        cls._validate_semantics(
            evaluation=evaluation,
            verification_disposition=verification_disposition,
        )

        payload: dict[str, Any] = {
            "verification_result_id": (
                GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_SCHEMA_VERSION
            ),
            "tenant_id": evaluation.tenant_id,
            "contract_hash": evaluation.contract_hash,
            "intervention_id": evaluation.intervention_id,
            "intervention_type": evaluation.intervention_type,
            "requirement_id": evaluation.requirement_id,
            "requirement_hash": evaluation.requirement_hash,
            "measurement_hash": evaluation.measurement_hash,
            "observation_hash": evaluation.observation_hash,
            "execution_receipt_hash": evaluation.execution_receipt_hash,
            "evaluation_hash": evaluation.evaluation_hash,
            "metric_id": evaluation.metric_id,
            "operator": evaluation.operator.value,
            "target_value": evaluation.target_value,
            "observed_value": evaluation.observed_value,
            "unit": evaluation.unit,
            "evidence_sufficient": evaluation.evidence_sufficient,
            "comparison_satisfied": evaluation.comparison_satisfied,
            "evaluation_disposition": evaluation.disposition.value,
            "verification_disposition": verification_disposition.value,
        }

        return GovernanceInterventionOutcomeVerificationResult(
            verification_result_id=payload["verification_result_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            contract_hash=payload["contract_hash"],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            requirement_id=payload["requirement_id"],
            requirement_hash=payload["requirement_hash"],
            measurement_hash=payload["measurement_hash"],
            observation_hash=payload["observation_hash"],
            execution_receipt_hash=payload[
                "execution_receipt_hash"
            ],
            evaluation_hash=payload["evaluation_hash"],
            metric_id=payload["metric_id"],
            operator=payload["operator"],
            target_value=payload["target_value"],
            observed_value=payload["observed_value"],
            unit=payload["unit"],
            evidence_sufficient=payload["evidence_sufficient"],
            comparison_satisfied=payload[
                "comparison_satisfied"
            ],
            evaluation_disposition=payload[
                "evaluation_disposition"
            ],
            verification_disposition=verification_disposition,
            verification_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _map_disposition(
        *,
        evaluation: GovernanceInterventionRequirementEvaluation,
    ) -> GovernanceInterventionOutcomeVerificationDisposition:
        if (
            evaluation.disposition
            is GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED
        ):
            return (
                GovernanceInterventionOutcomeVerificationDisposition
                .VERIFIED
            )

        if (
            evaluation.disposition
            is GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED
        ):
            return (
                GovernanceInterventionOutcomeVerificationDisposition
                .NOT_VERIFIED
            )

        if (
            evaluation.disposition
            is GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ):
            return (
                GovernanceInterventionOutcomeVerificationDisposition
                .INCONCLUSIVE
            )

        raise GovernanceInterventionOutcomeVerificationResultDispositionError(
            "unsupported deterministic evaluation disposition"
        )

    @staticmethod
    def _validate_semantics(
        *,
        evaluation: GovernanceInterventionRequirementEvaluation,
        verification_disposition: (
            GovernanceInterventionOutcomeVerificationDisposition
        ),
    ) -> None:
        if (
            verification_disposition
            is GovernanceInterventionOutcomeVerificationDisposition.VERIFIED
        ):
            if evaluation.evidence_sufficient is not True:
                raise (
                    GovernanceInterventionOutcomeVerificationResultIntegrityError(
                        "VERIFIED requires sufficient evidence"
                    )
                )

            if evaluation.comparison_satisfied is not True:
                raise (
                    GovernanceInterventionOutcomeVerificationResultIntegrityError(
                        "VERIFIED requires a satisfied comparison"
                    )
                )

            return

        if (
            verification_disposition
            is GovernanceInterventionOutcomeVerificationDisposition
            .NOT_VERIFIED
        ):
            if evaluation.evidence_sufficient is not True:
                raise (
                    GovernanceInterventionOutcomeVerificationResultIntegrityError(
                        "NOT_VERIFIED requires sufficient evidence"
                    )
                )

            if evaluation.comparison_satisfied is not False:
                raise (
                    GovernanceInterventionOutcomeVerificationResultIntegrityError(
                        "NOT_VERIFIED requires an unsatisfied comparison"
                    )
                )

            return

        if (
            verification_disposition
            is GovernanceInterventionOutcomeVerificationDisposition
            .INCONCLUSIVE
        ):
            if evaluation.evidence_sufficient is not False:
                raise (
                    GovernanceInterventionOutcomeVerificationResultIntegrityError(
                        "INCONCLUSIVE requires insufficient evidence"
                    )
                )

            if evaluation.comparison_satisfied is not None:
                raise (
                    GovernanceInterventionOutcomeVerificationResultIntegrityError(
                        "INCONCLUSIVE requires no comparison result"
                    )
                )

            return

        raise GovernanceInterventionOutcomeVerificationResultDispositionError(
            "unsupported governed verification disposition"
        )