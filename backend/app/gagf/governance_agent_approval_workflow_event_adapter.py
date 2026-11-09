"""Persist verified approval decisions as workflow history events.

This adapter records decision evidence only. It does not resume workflows,
execute actions, or grant GAGF Kernel authorization.
"""

from __future__ import annotations

from typing import Any

from .governance_agent_approval_contract import (
    AgentApprovalContractError,
    ApprovalDecision,
)
from .governance_agent_approval_service import (
    GovernanceAgentApprovalService,
)
from .governance_agent_workflow_approval_integration import (
    GovernanceAgentWorkflowApprovalIntegration,
    WorkflowApprovalIntegrationError,
)
from .governance_agent_workflow_contract import (
    AgentWorkflowEvent,
    WorkflowState,
)
from .governance_agent_workflow_store import (
    AgentWorkflowStore,
)


APPROVAL_APPROVED_EVENT = "approval.approved"
APPROVAL_REJECTED_EVENT = "approval.rejected"


class ApprovalWorkflowEventAdapterError(Exception):
    """Base exception for approval-to-workflow event adapter failures."""


class ApprovalWorkflowEventIntegrityError(
    ApprovalWorkflowEventAdapterError
):
    """Raised when persisted approval evidence does not verify."""


class GovernanceAgentApprovalWorkflowEventAdapter:
    """Append verified approval decisions to immutable workflow history."""

    def __init__(
        self,
        *,
        workflow_store: AgentWorkflowStore,
        approval_service: GovernanceAgentApprovalService,
        workflow_approval_integration: (
            GovernanceAgentWorkflowApprovalIntegration
        ),
    ) -> None:
        if not isinstance(workflow_store, AgentWorkflowStore):
            raise ApprovalWorkflowEventAdapterError(
                "workflow_store must be an AgentWorkflowStore"
            )

        if not isinstance(
            approval_service,
            GovernanceAgentApprovalService,
        ):
            raise ApprovalWorkflowEventAdapterError(
                "approval_service must be a GovernanceAgentApprovalService"
            )

        if not isinstance(
            workflow_approval_integration,
            GovernanceAgentWorkflowApprovalIntegration,
        ):
            raise ApprovalWorkflowEventAdapterError(
                "workflow_approval_integration must be a "
                "GovernanceAgentWorkflowApprovalIntegration"
            )

        self._workflow_store = workflow_store
        self._approval_service = approval_service
        self._workflow_approval_integration = (
            workflow_approval_integration
        )

    def record_decision_event(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        request_id: str,
    ) -> AgentWorkflowEvent:
        """Persist a workflow event for an existing verified decision.

        The decision is retrieved from the approval ledger. No caller-
        supplied decision record is accepted.
        """

        try:
            link = self._workflow_approval_integration.get_linked_approval(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                request_id=request_id,
            )
        except WorkflowApprovalIntegrationError:
            raise
        except Exception as exc:
            raise ApprovalWorkflowEventAdapterError(
                "Could not verify the persisted workflow approval link"
            ) from exc

        request = self._approval_service.get_request(
            tenant_id=tenant_id,
            request_id=request_id,
        )

        if (
            link.approval_request.request_hash != request.request_hash
            or link.approval_request.request_id != request.request_id
            or link.workflow.tenant_id != tenant_id
            or link.workflow.workflow_id != workflow_id
        ):
            raise ApprovalWorkflowEventIntegrityError(
                "Persisted workflow approval link does not match request"
            )

        decision = self._approval_service.get_decision(
            tenant_id=tenant_id,
            request_id=request_id,
        )

        try:
            decision.validate_against(request)
        except AgentApprovalContractError as exc:
            raise ApprovalWorkflowEventIntegrityError(
                "Persisted approval decision failed request validation"
            ) from exc

        if (
            decision.tenant_id != tenant_id
            or decision.workflow_id != workflow_id
            or decision.request_id != request_id
        ):
            raise ApprovalWorkflowEventIntegrityError(
                "Persisted decision does not match requested workflow context"
            )

        event_type_by_decision = {
            ApprovalDecision.APPROVE: APPROVAL_APPROVED_EVENT,
            ApprovalDecision.REJECT: APPROVAL_REJECTED_EVENT,
        }

        try:
            event_type = event_type_by_decision[decision.decision]
        except KeyError as exc:
            raise ApprovalWorkflowEventIntegrityError(
                "Unsupported persisted approval decision"
            ) from exc

        payload: dict[str, Any] = {
            "approval_decision_id": decision.decision_id,
            "approval_request_id": request.request_id,
            "approval_request_hash": request.request_hash,
            "action_hash": request.action_hash,
            "decision": decision.decision.value,
            "approver_id": decision.approver_id,
            "approver_type": decision.approver_type.value,
            "decided_at": decision.decided_at.isoformat(),
            "decision_idempotency_key": decision.idempotency_key,
            "decision_hash": decision.decision_hash,
            "work_item_id": request.work_item_id,
            "action_class": request.action_class.value,
            "correlation_id": request.correlation_id,
        }

        return self._workflow_store.append_workflow_event(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            idempotency_key=(
                f"approval-decision:{decision.decision_id}"
            ),
            event_type=event_type,
            expected_state=WorkflowState.AWAITING_APPROVAL,
            causation_id=decision.decision_id,
            work_item_id=request.work_item_id,
            payload=payload,
        )