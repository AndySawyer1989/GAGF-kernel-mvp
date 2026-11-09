from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalRequest,
)
from backend.app.gagf.governance_agent_approval_service import (
    GovernanceAgentApprovalService,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowRecord,
    AgentWorkflowStore,
)


APPROVAL_REQUESTED_EVENT = "approval.requested"


class WorkflowApprovalIntegrationError(Exception):
    """Base exception for workflow-approval integration failures."""


class WorkflowApprovalConflictError(WorkflowApprovalIntegrationError):
    """Raised when an approval request conflicts with workflow history."""


class WorkflowApprovalIntegrityError(WorkflowApprovalIntegrationError):
    """Raised when persisted approval linkage cannot be verified."""


@dataclass(frozen=True, slots=True)
class WorkflowApprovalLink:
    """Verified relationship between a workflow and its approval request."""

    workflow: AgentWorkflowRecord
    approval_request: AgentApprovalRequest


class GovernanceAgentWorkflowApprovalIntegration:
    """Coordinate approval persistence and workflow-state linkage.

    This component does not execute actions, resume workflows, authenticate
    requesters, or make Kernel authorization decisions.

    Approval requests and workflow transitions are stored independently.
    The request is persisted first; the workflow event is the durable
    relationship between the two records.
    """

    def __init__(
        self,
        *,
        workflow_store: AgentWorkflowStore,
        approval_service: GovernanceAgentApprovalService,
    ) -> None:
        if not isinstance(workflow_store, AgentWorkflowStore):
            raise WorkflowApprovalIntegrationError(
                "workflow_store must be an AgentWorkflowStore"
            )

        if not isinstance(
            approval_service,
            GovernanceAgentApprovalService,
        ):
            raise WorkflowApprovalIntegrationError(
                "approval_service must be a GovernanceAgentApprovalService"
            )

        self._workflow_store = workflow_store
        self._approval_service = approval_service

    def request_approval(
        self,
        *,
        request: AgentApprovalRequest,
        workflow_transition_idempotency_key: str,
        causation_id: str | None = None,
    ) -> WorkflowApprovalLink:
        """Persist an approval request and link it to an active workflow.

        The caller must reuse the same immutable request and transition
        idempotency key when retrying this operation.
        """

        if not isinstance(request, AgentApprovalRequest):
            raise WorkflowApprovalIntegrationError(
                "request must be an AgentApprovalRequest"
            )

        if (
            not isinstance(workflow_transition_idempotency_key, str)
            or not workflow_transition_idempotency_key.strip()
        ):
            raise WorkflowApprovalIntegrationError(
                "workflow_transition_idempotency_key must be non-empty"
            )

        if causation_id is not None and (
            not isinstance(causation_id, str) or not causation_id.strip()
        ):
            raise WorkflowApprovalIntegrationError(
                "causation_id must be a non-empty string when supplied"
            )

        workflow = self._workflow_store.get_workflow(
            tenant_id=request.tenant_id,
            workflow_id=request.workflow_id,
        )

        self._validate_request_context(request=request, workflow=workflow)

        # Recover an existing durable link before requiring ACTIVE.
        # This permits safe retries after the workflow transition committed.
        existing = self._find_link_event(
            tenant_id=request.tenant_id,
            workflow_id=request.workflow_id,
            request_id=request.request_id,
        )

        if existing is not None:
            self._validate_event_link(existing, request)
            persisted_request = self._approval_service.get_request(
                tenant_id=request.tenant_id,
                request_id=request.request_id,
            )
            self._validate_request_match(
                expected=request,
                actual=persisted_request,
            )
            return WorkflowApprovalLink(
                workflow=workflow,
                approval_request=persisted_request,
            )

        if workflow.state is not WorkflowState.ACTIVE:
            raise WorkflowApprovalConflictError(
                "A new approval request requires an ACTIVE workflow "
                "with no existing approval link"
            )

        if datetime.now(timezone.utc) >= request.expires_at:
            raise WorkflowApprovalConflictError(
                "Cannot link an approval request that has already expired"
            )

        # First durable operation: persist the immutable approval request.
        persisted_request = self._approval_service.create_request(request)

        self._validate_request_match(
            expected=request,
            actual=persisted_request,
        )

        event_payload = {
            "approval_request_id": request.request_id,
            "approval_request_hash": request.request_hash,
            "action_hash": request.action_hash,
            "work_item_id": request.work_item_id,
            "action_class": request.action_class.value,
            "approval_idempotency_key": request.idempotency_key,
        }

        try:
            updated_workflow = self._workflow_store.transition_workflow(
                tenant_id=request.tenant_id,
                workflow_id=request.workflow_id,
                target_state=WorkflowState.AWAITING_APPROVAL,
                idempotency_key=workflow_transition_idempotency_key.strip(),
                event_type=APPROVAL_REQUESTED_EVENT,
                causation_id=(
                    causation_id.strip()
                    if causation_id is not None
                    else None
                ),
                payload=event_payload,
            )
        except Exception as exc:
            # The approval request may already be durable. Recover only if
            # the exact expected linkage event actually committed.
            try:
                recovered_event = self._find_link_event(
                    tenant_id=request.tenant_id,
                    workflow_id=request.workflow_id,
                    request_id=request.request_id,
                )
            except Exception as recovery_exc:
                raise WorkflowApprovalIntegrityError(
                    "Workflow transition failed and linkage recovery "
                    "could not verify workflow history"
                ) from recovery_exc

            if recovered_event is None:
                raise WorkflowApprovalIntegrationError(
                    "Approval request persisted, but workflow linkage "
                    "did not commit. The action must remain blocked. "
                    "Retry with the same request and idempotency key."
                ) from exc

            self._validate_event_link(recovered_event, request)

            updated_workflow = self._workflow_store.get_workflow(
                tenant_id=request.tenant_id,
                workflow_id=request.workflow_id,
            )

        # The transition API can return the current record on idempotent
        # replay. The event, not the returned state alone, proves linkage.
        linked_event = self._find_link_event(
            tenant_id=request.tenant_id,
            workflow_id=request.workflow_id,
            request_id=request.request_id,
        )

        if linked_event is None:
            raise WorkflowApprovalIntegrityError(
                "Workflow transition returned without a durable "
                "approval-requested event"
            )

        self._validate_event_link(linked_event, request)

        return WorkflowApprovalLink(
            workflow=updated_workflow,
            approval_request=persisted_request,
        )

    def get_linked_approval(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        request_id: str,
    ) -> WorkflowApprovalLink:
        """Retrieve and verify an approval request linked by workflow history."""

        workflow = self._workflow_store.get_workflow(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
        )

        event = self._find_link_event(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            request_id=request_id,
        )

        if event is None:
            raise WorkflowApprovalConflictError(
                "No approval linkage exists for this workflow and request"
            )

        data = self._event_data(event)

        persisted_request = self._approval_service.get_request(
            tenant_id=tenant_id,
            request_id=request_id,
        )

        self._validate_event_request_fields(
            data=data,
            request=persisted_request,
        )

        self._validate_request_context(
            request=persisted_request,
            workflow=workflow,
        )

        return WorkflowApprovalLink(
            workflow=workflow,
            approval_request=persisted_request,
        )

    def _find_link_event(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        request_id: str,
    ):
        events = self._workflow_store.list_events(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
        )

        matches = []

        for event in events:
            if event.event_type != APPROVAL_REQUESTED_EVENT:
                continue

            data = self._event_data(event)

            if data.get("approval_request_id") == request_id:
                matches.append((event, data))

        if not matches:
            return None

        first_event, first_data = matches[0]

        for event, data in matches[1:]:
            if (
                data != first_data
                or event.event_hash != first_event.event_hash
            ):
                raise WorkflowApprovalIntegrityError(
                    "Conflicting workflow events reference the same "
                    "approval request"
                )

        return first_event

    @staticmethod
    def _event_data(event) -> dict:
        if not event.verify_integrity():
            raise WorkflowApprovalIntegrityError(
                "Workflow approval event failed integrity verification"
            )

        payload = event.payload

        if not isinstance(payload, dict):
            raise WorkflowApprovalIntegrityError(
                "Workflow event payload must be an object"
            )

        data = payload.get("data")

        if not isinstance(data, dict):
            raise WorkflowApprovalIntegrityError(
                "Workflow event data must be an object"
            )

        if (
            payload.get("previous_state") != WorkflowState.ACTIVE.value
            or payload.get("target_state")
            != WorkflowState.AWAITING_APPROVAL.value
        ):
            raise WorkflowApprovalIntegrityError(
                "Approval event has unexpected transition states"
            )

        return data

    def _validate_event_link(
        self,
        event,
        request: AgentApprovalRequest,
    ) -> None:
        data = self._event_data(event)

        self._validate_event_request_fields(
            data=data,
            request=request,
        )

        if (
            event.tenant_id != request.tenant_id
            or event.workflow_id != request.workflow_id
            or event.correlation_id != request.correlation_id
        ):
            raise WorkflowApprovalIntegrityError(
                "Workflow event context does not match approval request"
            )

    @staticmethod
    def _validate_event_request_fields(
        *,
        data: dict,
        request: AgentApprovalRequest,
    ) -> None:
        expected = {
            "approval_request_id": request.request_id,
            "approval_request_hash": request.request_hash,
            "action_hash": request.action_hash,
            "work_item_id": request.work_item_id,
            "action_class": request.action_class.value,
            "approval_idempotency_key": request.idempotency_key,
        }

        if data != expected:
            raise WorkflowApprovalIntegrityError(
                "Persisted workflow event does not match approval request"
            )

    @staticmethod
    def _validate_request_context(
        *,
        request: AgentApprovalRequest,
        workflow: AgentWorkflowRecord,
    ) -> None:
        if (
            request.tenant_id != workflow.tenant_id
            or request.workflow_id != workflow.workflow_id
            or request.correlation_id != workflow.correlation_id
        ):
            raise WorkflowApprovalConflictError(
                "Approval request tenant, workflow, or correlation "
                "context does not match the persisted workflow"
            )

    @staticmethod
    def _validate_request_match(
        *,
        expected: AgentApprovalRequest,
        actual: AgentApprovalRequest,
    ) -> None:
        if (
            actual.request_id != expected.request_id
            or actual.request_hash != expected.request_hash
            or actual.action_hash != expected.action_hash
            or actual.tenant_id != expected.tenant_id
            or actual.workflow_id != expected.workflow_id
            or actual.work_item_id != expected.work_item_id
            or actual.correlation_id != expected.correlation_id
            or actual.idempotency_key != expected.idempotency_key
            or actual.action_class is not expected.action_class
        ):
            raise WorkflowApprovalIntegrityError(
                "Persisted approval request does not match submitted request"
            )