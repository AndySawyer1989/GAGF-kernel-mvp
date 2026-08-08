from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_assessment_roadmap import (
    RoadmapItemStatus,
)
from backend.app.gagf.governance_intervention_execution_binding import (
    GovernanceInterventionExecutionBinding,
)
from backend.app.gagf.scientific_authorization import (
    ScientificAuthorityAction,
    ScientificAuthorityAuthorizationPolicy,
    ScientificAuthorizationDecision,
    ScientificAuthorizationReceipt,
    ScientificAuthorizationRequest,
    ScientificTrustSignals,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)


GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_ID = (
    "governance-intervention-execution-authorization"
)

GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_VERSION = (
    "0.1.0"
)


class GovernanceInterventionExecutionAuthorizationError(
    RuntimeError
):
    """Base error for governed intervention execution authorization."""


class InvalidGovernanceInterventionExecutionBindingError(
    GovernanceInterventionExecutionAuthorizationError
):
    """Raised when execution lineage does not verify."""


class GovernanceInterventionExecutionDeniedError(
    GovernanceInterventionExecutionAuthorizationError
):
    def __init__(
        self,
        *,
        decision: ScientificAuthorizationDecision,
        receipt: ScientificAuthorizationReceipt,
    ) -> None:
        super().__init__(
            "Governed intervention execution authorization was denied."
        )

        self.decision = decision
        self.receipt = receipt


@dataclass(frozen=True, slots=True)
class GovernanceInterventionExecutionAuthorization:
    authorization_id: str
    authorization_version: str
    binding_hash: str
    execution_context_hash: str
    decision: ScientificAuthorizationDecision
    authorization_receipt: ScientificAuthorizationReceipt

    @property
    def allowed(self) -> bool:
        return self.decision.allowed

    def to_dict(self) -> dict:
        return {
            "authorization_id": self.authorization_id,
            "authorization_version": self.authorization_version,
            "binding_hash": self.binding_hash,
            "execution_context_hash": (
                self.execution_context_hash
            ),
            "decision": self.decision.to_dict(),
            "authorization_receipt": (
                self.authorization_receipt.to_dict()
            ),
        }


class GovernanceInterventionExecutionAuthorizationGate:
    def __init__(
        self,
        policy: ScientificAuthorityAuthorizationPolicy
        | None = None,
    ) -> None:
        self.policy = (
            policy
            if policy is not None
            else ScientificAuthorityAuthorizationPolicy()
        )

    def authorize(
        self,
        *,
        binding: GovernanceInterventionExecutionBinding,
        context: ScientificExecutionContext,
        trust_signals: ScientificTrustSignals,
        constitutional_approval_submitted: bool,
    ) -> GovernanceInterventionExecutionAuthorization:
        self._validate_lineage(
            binding=binding,
            context=context,
        )

        request = ScientificAuthorizationRequest(
            context=context,
            action=(
                ScientificAuthorityAction
                .AUTHORIZE_INTERVENTION_EXECUTION
            ),
            target_tenant_id=binding.tenant_id,
            requested_authority=None,
            constitutional_approval_submitted=(
                constitutional_approval_submitted
            ),
            trust_signals=trust_signals,
        )

        decision, receipt = (
            self.policy.evaluate_with_receipt(request)
        )

        if not decision.allowed:
            raise GovernanceInterventionExecutionDeniedError(
                decision=decision,
                receipt=receipt,
            )

        return GovernanceInterventionExecutionAuthorization(
            authorization_id=(
                GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_ID
            ),
            authorization_version=(
                GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_VERSION
            ),
            binding_hash=binding.binding_hash,
            execution_context_hash=context.context_hash,
            decision=decision,
            authorization_receipt=receipt,
        )

    def _validate_lineage(
        self,
        *,
        binding: GovernanceInterventionExecutionBinding,
        context: ScientificExecutionContext,
    ) -> None:
        if not binding.verify():
            raise InvalidGovernanceInterventionExecutionBindingError(
                "Governed intervention execution binding failed "
                "hash verification."
            )

        if binding.roadmap_status != (
            RoadmapItemStatus.APPROVED.value
        ):
            raise InvalidGovernanceInterventionExecutionBindingError(
                "Governed intervention execution binding is not "
                "approved for execution authorization."
            )

        if binding.tenant_id != context.tenant_id:
            raise InvalidGovernanceInterventionExecutionBindingError(
                "Execution context tenant does not match "
                "the governed execution binding."
            )

        if (
            binding.execution_context_hash
            != context.context_hash
        ):
            raise InvalidGovernanceInterventionExecutionBindingError(
                "Execution context hash does not match "
                "the governed execution binding."
            )

        if binding.request_id != context.request_id:
            raise InvalidGovernanceInterventionExecutionBindingError(
                "Execution request ID does not match "
                "the governed execution binding."
            )

        if binding.correlation_id != context.correlation_id:
            raise InvalidGovernanceInterventionExecutionBindingError(
                "Execution correlation ID does not match "
                "the governed execution binding."
            )
