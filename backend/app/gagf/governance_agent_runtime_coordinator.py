"""Workflow-scoped coordination for the GAGF Engineering Agent runtime.

This component connects read-only workflow-state routing to bounded work
dispatch. It does not execute workers, mutate workflow state, authorize
human approvals, or perform repository operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.app.gagf.governance_agent_bounded_dispatcher import (
    AgentBoundedDispatcher,
    BoundedDispatchResult,
)
from backend.app.gagf.governance_agent_state_router import (
    AgentWorkflowRoutingDecision,
    GovernanceAgentStateRouter,
    WorkflowRoutingAction,
)
from backend.app.gagf.governance_agent_task_capability_policy import (
    AgentTaskCapabilityPolicy,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
)


GOVERNANCE_AGENT_RUNTIME_COORDINATOR_ID = (
    "gagf-governance-agent-runtime-coordinator"
)
GOVERNANCE_AGENT_RUNTIME_COORDINATOR_VERSION = "1.0.0"


class GovernanceAgentRuntimeCoordinatorError(RuntimeError):
    """Base error for runtime coordination failures."""


class GovernanceAgentRuntimeCoordinatorDependencyError(
    GovernanceAgentRuntimeCoordinatorError
):
    """Raised when a required runtime dependency is invalid."""


class GovernanceAgentRuntimeCoordinatorInputError(
    GovernanceAgentRuntimeCoordinatorError
):
    """Raised when coordination input is invalid."""


@dataclass(frozen=True)
class GovernanceAgentRuntimeCoordinationResult:
    """Immutable record of a workflow coordination decision."""

    routing_decision: AgentWorkflowRoutingDecision
    dispatch_result: BoundedDispatchResult | None

    @property
    def dispatch_performed(self) -> bool:
        return self.dispatch_result is not None


class GovernanceAgentRuntimeCoordinator:
    """Coordinate eligible workflow work without executing workers."""

    def __init__(
        self,
        *,
        state_router: GovernanceAgentStateRouter,
        bounded_dispatcher: AgentBoundedDispatcher,
        task_capability_policy: AgentTaskCapabilityPolicy,
    ) -> None:
        if not isinstance(state_router, GovernanceAgentStateRouter):
            raise GovernanceAgentRuntimeCoordinatorDependencyError(
                "state_router must be a GovernanceAgentStateRouter"
            )

        if not isinstance(bounded_dispatcher, AgentBoundedDispatcher):
            raise GovernanceAgentRuntimeCoordinatorDependencyError(
                "bounded_dispatcher must be an AgentBoundedDispatcher"
            )

        if not isinstance(task_capability_policy, AgentTaskCapabilityPolicy):
            raise GovernanceAgentRuntimeCoordinatorDependencyError(
                "task_capability_policy must be an AgentTaskCapabilityPolicy"
            )

        self.state_router = state_router
        self.bounded_dispatcher = bounded_dispatcher
        self.task_capability_policy = task_capability_policy

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise GovernanceAgentRuntimeCoordinatorInputError(
                f"{field_name} must be non-empty text"
            )

        return value.strip()

    def dispatch_workflow(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        dispatch_cycle_id: str,
        lease_seconds: int = 300,
        max_candidates: int = 100,
        max_claims: int = 10,
        now: datetime | None = None,
    ) -> GovernanceAgentRuntimeCoordinationResult:
        """Route a workflow and dispatch only when it is actively eligible.

        The state router remains read-only. The dispatcher independently
        rechecks workflow state during each claim transaction.
        """

        tenant_id = self._require_text(tenant_id, "tenant_id")
        workflow_id = self._require_text(workflow_id, "workflow_id")
        dispatch_cycle_id = self._require_text(
            dispatch_cycle_id,
            "dispatch_cycle_id",
        )

        routing_decision = self.state_router.route(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
        )

        if not isinstance(
            routing_decision,
            AgentWorkflowRoutingDecision,
        ):
            raise GovernanceAgentRuntimeCoordinatorError(
                "State router returned an invalid routing decision"
            )

        is_dispatch_eligible = (
            routing_decision.current_state is WorkflowState.ACTIVE
            and routing_decision.action
            is WorkflowRoutingAction.COORDINATE_WORK
            and routing_decision.terminal is False
            and routing_decision.requires_human_approval is False
        )

        if not is_dispatch_eligible:
            return GovernanceAgentRuntimeCoordinationResult(
                routing_decision=routing_decision,
                dispatch_result=None,
            )

        dispatch_result = self.bounded_dispatcher.dispatch(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            dispatch_cycle_id=dispatch_cycle_id,
            task_capability_policy=self.task_capability_policy,
            lease_seconds=lease_seconds,
            max_candidates=max_candidates,
            max_claims=max_claims,
            now=now,
        )

        if not isinstance(dispatch_result, BoundedDispatchResult):
            raise GovernanceAgentRuntimeCoordinatorError(
                "Bounded dispatcher returned an invalid dispatch result"
            )

        if (
            dispatch_result.tenant_id != tenant_id
            or dispatch_result.workflow_id != workflow_id
        ):
            raise GovernanceAgentRuntimeCoordinatorError(
                "Bounded dispatcher returned a result outside "
                "the requested tenant/workflow scope"
            )

        return GovernanceAgentRuntimeCoordinationResult(
            routing_decision=routing_decision,
            dispatch_result=dispatch_result,
        )