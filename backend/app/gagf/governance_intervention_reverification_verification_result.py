from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_reverification_requirement_evaluation import (
    GovernanceInterventionReverificationRequirementEvaluation,
    GovernanceInterventionReverificationRequirementEvaluationDisposition,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_ID = (
    "governance-intervention-reverification-verification-result"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationVerificationDisposition(
    str,
    Enum,
):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class GovernanceInterventionReverificationVerificationResultError(
    ValueError
):
    """Base error for governed reverification verification."""


class GovernanceInterventionReverificationVerificationResultIntegrityError(
    GovernanceInterventionReverificationVerificationResultError
):
    """Raised when the deterministic reverification evaluation is invalid."""


class GovernanceInterventionReverificationVerificationResultDispositionError(
    GovernanceInterventionReverificationVerificationResultError
):
    """Raised when an unsupported evaluation disposition reaches verification."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationVerificationResult:
    """
    Immutable governed verification result for one deterministic
    reverification requirement evaluation.

    VERIFIED means only that sufficient governed reverification evidence
    deterministically satisfied the structured verification requirement.

    NOT_VERIFIED means only that sufficient governed reverification evidence
    deterministically did not satisfy the structured verification requirement.

    INCONCLUSIVE means the governed reverification evidence was insufficient
    to resolve the requirement.

    This artifact does not:
    - claim intervention success or failure;
    - establish causation;
    - complete a reverification attempt;
    - supersede any verification record;
    - mutate verification lifecycle state;
    - authorize future intervention activity;
    - order continuation, rollback, or remediation;
    - alter the requirement, measurement, or evaluation.
    """

    verification_result_id: str
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
    evaluation_hash: str

    actuation_contract_hash: str
    intervention_type: str

    requirement_id: str
    requirement_hash: str
    metric_id: str

    operator: str
    target_value: float
    observed_value: float
    unit: str

    evidence_sufficient: bool
    comparison_satisfied: bool | None
    evaluation_disposition: str
    verification_disposition: (
        GovernanceInterventionReverificationVerificationDisposition
    )

    verification_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "verification_result_id": (
                self.verification_result_id
            ),
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
            "evaluation_hash": (
                self.evaluation_hash
            ),
            "actuation_contract_hash": (
                self.actuation_contract_hash
            ),
            "intervention_type": (
                self.intervention_type
            ),
            "requirement_id": (
                self.requirement_id
            ),
            "requirement_hash": (
                self.requirement_hash
            ),
            "metric_id": self.metric_id,
            "operator": self.operator,
            "target_value": self.target_value,
            "observed_value": self.observed_value,
            "unit": self.unit,
            "evidence_sufficient": (
                self.evidence_sufficient
            ),
            "comparison_satisfied": (
                self.comparison_satisfied
            ),
            "evaluation_disposition": (
                self.evaluation_disposition
            ),
            "verification_disposition": (
                self.verification_disposition.value
            ),
        }

    def verify(self) -> bool:
        return (
            self.verification_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_hash": (
                self.verification_hash
            ),
        }


class GovernanceInterventionReverificationVerificationResultBuilder:
    """
    Converts one verified deterministic I-Q evaluation into one bounded
    governed reverification verification disposition.

    This builder performs no measurement, comparison, causal attribution,
    execution, lifecycle mutation, supersession, authorization, rollback,
    continuation, remediation, or policy selection.
    """

    @classmethod
    def build(
        cls,
        *,
        evaluation: (
            GovernanceInterventionReverificationRequirementEvaluation
        ),
    ) -> GovernanceInterventionReverificationVerificationResult:
        if not evaluation.verify():
            raise (
                GovernanceInterventionReverificationVerificationResultIntegrityError(
                    "reverification requirement evaluation "
                    "failed deterministic verification"
                )
            )

        verification_disposition = (
            cls._map_disposition(
                evaluation=evaluation
            )
        )

        cls._validate_semantics(
            evaluation=evaluation,
            verification_disposition=(
                verification_disposition
            ),
        )

        payload: dict[str, Any] = {
            "verification_result_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_SCHEMA_VERSION
            ),
            "tenant_id": evaluation.tenant_id,
            "intervention_id": (
                evaluation.intervention_id
            ),
            "verification_record_hash": (
                evaluation.verification_record_hash
            ),
            "request_hash": (
                evaluation.request_hash
            ),
            "work_order_hash": (
                evaluation.work_order_hash
            ),
            "attempt_id": evaluation.attempt_id,
            "attempt_execution_id": (
                evaluation.attempt_execution_id
            ),
            "reverification_scope": (
                evaluation.reverification_scope
            ),
            "evidence_hash": (
                evaluation.evidence_hash
            ),
            "measurement_hash": (
                evaluation.measurement_hash
            ),
            "evaluation_hash": (
                evaluation.evaluation_hash
            ),
            "actuation_contract_hash": (
                evaluation.actuation_contract_hash
            ),
            "intervention_type": (
                evaluation.intervention_type
            ),
            "requirement_id": (
                evaluation.requirement_id
            ),
            "requirement_hash": (
                evaluation.requirement_hash
            ),
            "metric_id": evaluation.metric_id,
            "operator": evaluation.operator.value,
            "target_value": (
                evaluation.target_value
            ),
            "observed_value": (
                evaluation.observed_value
            ),
            "unit": evaluation.unit,
            "evidence_sufficient": (
                evaluation.evidence_sufficient
            ),
            "comparison_satisfied": (
                evaluation.comparison_satisfied
            ),
            "evaluation_disposition": (
                evaluation.disposition.value
            ),
            "verification_disposition": (
                verification_disposition.value
            ),
        }

        return (
            GovernanceInterventionReverificationVerificationResult(
                verification_result_id=payload[
                    "verification_result_id"
                ],
                version=payload["version"],
                schema_version=payload[
                    "schema_version"
                ],
                tenant_id=payload[
                    "tenant_id"
                ],
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
                evaluation_hash=payload[
                    "evaluation_hash"
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
                operator=payload["operator"],
                target_value=payload[
                    "target_value"
                ],
                observed_value=payload[
                    "observed_value"
                ],
                unit=payload["unit"],
                evidence_sufficient=payload[
                    "evidence_sufficient"
                ],
                comparison_satisfied=payload[
                    "comparison_satisfied"
                ],
                evaluation_disposition=payload[
                    "evaluation_disposition"
                ],
                verification_disposition=(
                    verification_disposition
                ),
                verification_hash=sha256_hex(
                    canonical_json(payload)
                ),
            )
        )

    @staticmethod
    def _map_disposition(
        *,
        evaluation: (
            GovernanceInterventionReverificationRequirementEvaluation
        ),
    ) -> (
        GovernanceInterventionReverificationVerificationDisposition
    ):
        if (
            evaluation.disposition
            is GovernanceInterventionReverificationRequirementEvaluationDisposition
            .SATISFIED
        ):
            return (
                GovernanceInterventionReverificationVerificationDisposition
                .VERIFIED
            )

        if (
            evaluation.disposition
            is GovernanceInterventionReverificationRequirementEvaluationDisposition
            .NOT_SATISFIED
        ):
            return (
                GovernanceInterventionReverificationVerificationDisposition
                .NOT_VERIFIED
            )

        if (
            evaluation.disposition
            is GovernanceInterventionReverificationRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ):
            return (
                GovernanceInterventionReverificationVerificationDisposition
                .INCONCLUSIVE
            )

        raise (
            GovernanceInterventionReverificationVerificationResultDispositionError(
                "unsupported deterministic reverification "
                "evaluation disposition"
            )
        )

    @staticmethod
    def _validate_semantics(
        *,
        evaluation: (
            GovernanceInterventionReverificationRequirementEvaluation
        ),
        verification_disposition: (
            GovernanceInterventionReverificationVerificationDisposition
        ),
    ) -> None:
        if (
            verification_disposition
            is GovernanceInterventionReverificationVerificationDisposition
            .VERIFIED
        ):
            if (
                evaluation.evidence_sufficient
                is not True
            ):
                raise (
                    GovernanceInterventionReverificationVerificationResultIntegrityError(
                        "VERIFIED requires sufficient evidence"
                    )
                )

            if (
                evaluation.comparison_satisfied
                is not True
            ):
                raise (
                    GovernanceInterventionReverificationVerificationResultIntegrityError(
                        "VERIFIED requires a satisfied comparison"
                    )
                )

            return

        if (
            verification_disposition
            is GovernanceInterventionReverificationVerificationDisposition
            .NOT_VERIFIED
        ):
            if (
                evaluation.evidence_sufficient
                is not True
            ):
                raise (
                    GovernanceInterventionReverificationVerificationResultIntegrityError(
                        "NOT_VERIFIED requires sufficient evidence"
                    )
                )

            if (
                evaluation.comparison_satisfied
                is not False
            ):
                raise (
                    GovernanceInterventionReverificationVerificationResultIntegrityError(
                        "NOT_VERIFIED requires an unsatisfied comparison"
                    )
                )

            return

        if (
            verification_disposition
            is GovernanceInterventionReverificationVerificationDisposition
            .INCONCLUSIVE
        ):
            if (
                evaluation.evidence_sufficient
                is not False
            ):
                raise (
                    GovernanceInterventionReverificationVerificationResultIntegrityError(
                        "INCONCLUSIVE requires insufficient evidence"
                    )
                )

            if (
                evaluation.comparison_satisfied
                is not None
            ):
                raise (
                    GovernanceInterventionReverificationVerificationResultIntegrityError(
                        "INCONCLUSIVE requires no comparison result"
                    )
                )

            return

        raise (
            GovernanceInterventionReverificationVerificationResultDispositionError(
                "unsupported governed reverification "
                "verification disposition"
            )
        )