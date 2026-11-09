from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_agent_workflow_contract import (
    WORKFLOW_TRANSITIONS,
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowRecord,
    AgentWorkflowStore,
)


ROUTER_ID = "governance-agent-state-router"
ROUTER_VERSION = "0.1.0"


class AgentWorkflowStateRouterError(ValueError):
    """Raised when persisted workflow state cannot be routed safely."""


class WorkflowRoutingAction(str, Enum):
    PREPARE_ACTIVATION = "prepare_activation"
    COORDINATE_WORK = "coordinate_work"
    WAIT_FOR_HUMAN_APPROVAL = "wait_for_human_approval"
    TERMINAL_COMPLETED = "terminal_completed"
    TERMINAL_FAILED = "terminal_failed"
    TERMINAL_CANCELLED = "terminal_cancelled"


@dataclass(frozen=True, slots=True)
class AgentWorkflowRoutingDecision:
    tenant_id: str
    workflow_id: str
    workflow_type: str
    current_state: WorkflowState
    action: WorkflowRoutingAction
    allowed_transitions: tuple[WorkflowState, ...]
    requires_human_approval: bool
    terminal: bool
    reason: str


_STATE_ACTIONS = {
    WorkflowState.CREATED: (
        WorkflowRoutingAction.PREPARE_ACTIVATION,
        False,
        False,
        "Workflow is created and may be prepared for activation.",
    ),
    WorkflowState.ACTIVE: (
        WorkflowRoutingAction.COORDINATE_WORK,
        False,
        False,
        "Workflow is active and may coordinate bounded work.",
    ),
    WorkflowState.AWAITING_APPROVAL: (
        WorkflowRoutingAction.WAIT_FOR_HUMAN_APPROVAL,
        True,
        False,
        "Workflow is waiting for an explicit human approval decision.",
    ),
    WorkflowState.COMPLETED: (
        WorkflowRoutingAction.TERMINAL_COMPLETED,
        False,
        True,
        "Workflow completed; no further workflow transition is permitted.",
    ),
    WorkflowState.FAILED: (
        WorkflowRoutingAction.TERMINAL_FAILED,
        False,
        True,
        "Workflow failed; no further workflow transition is permitted.",
    ),
    WorkflowState.CANCELLED: (
        WorkflowRoutingAction.TERMINAL_CANCELLED,
        False,
        True,
        "Workflow was cancelled; no further workflow transition is permitted.",
    ),
}


class GovernanceAgentStateRouter:
    """
    Read-only router for persisted agent workflow state.

    The workflow store remains authoritative for persistence.
    The workflow contract remains authoritative for transitions.
    This router does not execute agents or authorize actions.
    """

    SERVICE_TYPE = "governance_agent_state_router"

    def __init__(self, store: AgentWorkflowStore) -> None:
        if not callable(getattr(store, "get_workflow", None)):
            raise TypeError("store must provide a callable get_workflow method")

        self._store = store

    def route(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
    ) -> AgentWorkflowRoutingDecision:
        tenant = self._require_identifier(tenant_id, "tenant_id")
        identifier = self._require_identifier(workflow_id, "workflow_id")

        record = self._store.get_workflow(
            tenant_id=tenant,
            workflow_id=identifier,
        )

        return self._decision_for_record(
            record,
            tenant_id=tenant,
            workflow_id=identifier,
        )

    @staticmethod
    def _require_identifier(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AgentWorkflowStateRouterError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _decision_for_record(
        record: AgentWorkflowRecord,
        *,
        tenant_id: str,
        workflow_id: str,
    ) -> AgentWorkflowRoutingDecision:
        if not isinstance(record, AgentWorkflowRecord):
            raise AgentWorkflowStateRouterError(
                "Workflow store returned an invalid record type"
            )

        if record.tenant_id != tenant_id:
            raise AgentWorkflowStateRouterError(
                "Workflow record tenant does not match requested tenant"
            )

        if record.workflow_id != workflow_id:
            raise AgentWorkflowStateRouterError(
                "Workflow record ID does not match requested workflow"
            )

        if not isinstance(record.workflow_type, str) or not record.workflow_type.strip():
            raise AgentWorkflowStateRouterError(
                "Workflow record has an invalid workflow_type"
            )

        if not isinstance(record.state, WorkflowState):
            raise AgentWorkflowStateRouterError(
                "Workflow record has an invalid workflow state"
            )

        transition_set = WORKFLOW_TRANSITIONS.get(record.state)

        if transition_set is None:
            raise AgentWorkflowStateRouterError(
                "Workflow state has no registered transition definition"
            )

        action, requires_approval, terminal, reason = _STATE_ACTIONS[
            record.state
        ]

        return AgentWorkflowRoutingDecision(
            tenant_id=record.tenant_id,
            workflow_id=record.workflow_id,
            workflow_type=record.workflow_type,
            current_state=record.state,
            action=action,
            allowed_transitions=tuple(
                sorted(transition_set, key=lambda state: state.value)
            ),
            requires_human_approval=requires_approval,
            terminal=terminal,
            reason=reason,
        )