from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalRequest,
    ApprovalActionClass,
    ApprovalActorType,
    ApprovalDecision,
    ApprovalRequesterType,
)
from backend.app.gagf.governance_agent_approval_service import (
    AuthenticatedApprovalActor,
    GovernanceAgentApprovalService,
)
from backend.app.gagf.governance_agent_approval_store import (
    AgentApprovalNotFoundError,
    AgentApprovalStore,
)
from backend.app.gagf.governance_agent_approval_workflow_event_adapter import (
    APPROVAL_APPROVED_EVENT,
    APPROVAL_REJECTED_EVENT,
    ApprovalWorkflowEventAdapterError,
    GovernanceAgentApprovalWorkflowEventAdapter,
)
from backend.app.gagf.governance_agent_workflow_approval_integration import (
    GovernanceAgentWorkflowApprovalIntegration,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowStore,
)


class FakeIdentityProvider:
    """Controlled identity provider for adapter tests."""

    def resolve_actor(
        self,
        *,
        tenant_id,
        authentication_context,
    ):
        if authentication_context != "valid-test-auth-context":
            raise ValueError("Invalid test authentication context")

        return AuthenticatedApprovalActor(
            tenant_id=tenant_id,
            actor_id="human-operator-001",
            actor_type=ApprovalActorType.HUMAN,
        )


def make_adapter(tmp_path):
    workflow_store = AgentWorkflowStore(
        tmp_path / "agent_workflows.db"
    )
    approval_store = AgentApprovalStore(
        tmp_path / "agent_approvals.db"
    )
    approval_service = GovernanceAgentApprovalService(
        store=approval_store,
        identity_provider=FakeIdentityProvider(),
    )
    integration = GovernanceAgentWorkflowApprovalIntegration(
        workflow_store=workflow_store,
        approval_service=approval_service,
    )
    adapter = GovernanceAgentApprovalWorkflowEventAdapter(
        workflow_store=workflow_store,
        approval_service=approval_service,
        workflow_approval_integration=integration,
    )

    return adapter, workflow_store, approval_service, integration


def create_active_workflow(workflow_store):
    workflow_store.create_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        workflow_type="engineering",
        idempotency_key="create-workflow-001",
        correlation_id="correlation-001",
    )

    workflow_store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=WorkflowState.ACTIVE,
        idempotency_key="activate-workflow-001",
        event_type="workflow.active",
    )


def make_request(**overrides):
    now = datetime.now(timezone.utc)

    values = {
        "request_id": "approval-request-001",
        "tenant_id": "tenant-a",
        "workflow_id": "workflow-001",
        "work_item_id": "work-item-001",
        "action_class": ApprovalActionClass.EXTERNAL_COMMUNICATION,
        "requester_id": "engineering-worker",
        "requester_type": ApprovalRequesterType.WORKER,
        "requested_at": now,
        "expires_at": now + timedelta(minutes=15),
        "correlation_id": "correlation-001",
        "idempotency_key": "approval-request-key-001",
        "action": {
            "operation": "send_message",
            "destination": "customer-001",
            "body": "sensitive action body must not be copied",
        },
    }

    values.update(overrides)
    return AgentApprovalRequest.create(**values)


def prepare_pending_approval(tmp_path, *, decision=None):
    adapter, workflow_store, approval_service, integration = (
        make_adapter(tmp_path)
    )

    create_active_workflow(workflow_store)
    request = make_request()

    integration.request_approval(
        request=request,
        workflow_transition_idempotency_key="approval-transition-001",
    )

    if decision is not None:
        approval_service.submit_decision(
            tenant_id="tenant-a",
            request_id=request.request_id,
            decision=decision,
            authentication_context="valid-test-auth-context",
            idempotency_key="decision-key-001",
            reason="Reviewed by human operator.",
        )

    return adapter, workflow_store, approval_service, request


def list_decision_events(workflow_store):
    return [
        event
        for event in workflow_store.list_events(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )
        if event.event_type in {
            APPROVAL_APPROVED_EVENT,
            APPROVAL_REJECTED_EVENT,
        }
    ]


def test_approved_decision_is_persisted_as_verified_workflow_event(
    tmp_path,
):
    adapter, workflow_store, approval_service, request = (
        prepare_pending_approval(
            tmp_path,
            decision=ApprovalDecision.APPROVE,
        )
    )

    decision = approval_service.get_decision(
        tenant_id="tenant-a",
        request_id=request.request_id,
    )

    event = adapter.record_decision_event(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        request_id=request.request_id,
    )

    assert event.event_type == APPROVAL_APPROVED_EVENT
    assert event.tenant_id == "tenant-a"
    assert event.workflow_id == "workflow-001"
    assert event.work_item_id == request.work_item_id
    assert event.causation_id == decision.decision_id
    assert event.idempotency_key == (
        f"approval-decision:{decision.decision_id}"
    )
    assert event.verify_integrity() is True

    data = event.payload["data"]

    assert data["approval_decision_id"] == decision.decision_id
    assert data["approval_request_id"] == request.request_id
    assert data["approval_request_hash"] == request.request_hash
    assert data["action_hash"] == request.action_hash
    assert data["decision"] == ApprovalDecision.APPROVE.value
    assert data["approver_id"] == "human-operator-001"
    assert data["approver_type"] == ApprovalActorType.HUMAN.value
    assert data["decision_hash"] == decision.decision_hash
    assert data["work_item_id"] == request.work_item_id
    assert data["action_class"] == request.action_class.value
    assert data["correlation_id"] == request.correlation_id

    assert (
        "sensitive action body must not be copied"
        not in event.payload_json
    )

    workflow = workflow_store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert workflow.state is WorkflowState.AWAITING_APPROVAL
    assert len(list_decision_events(workflow_store)) == 1


def test_rejected_decision_is_persisted_without_resuming_workflow(
    tmp_path,
):
    adapter, workflow_store, _, request = prepare_pending_approval(
        tmp_path,
        decision=ApprovalDecision.REJECT,
    )

    event = adapter.record_decision_event(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        request_id=request.request_id,
    )

    assert event.event_type == APPROVAL_REJECTED_EVENT
    assert event.payload["data"]["decision"] == (
        ApprovalDecision.REJECT.value
    )
    assert event.verify_integrity() is True

    workflow = workflow_store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert workflow.state is WorkflowState.AWAITING_APPROVAL
    assert len(list_decision_events(workflow_store)) == 1


def test_decision_event_replay_returns_original_event_without_duplication(
    tmp_path,
):
    adapter, workflow_store, _, request = prepare_pending_approval(
        tmp_path,
        decision=ApprovalDecision.APPROVE,
    )

    first = adapter.record_decision_event(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        request_id=request.request_id,
    )
    second = adapter.record_decision_event(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        request_id=request.request_id,
    )

    assert second == first
    assert second.event_id == first.event_id
    assert second.event_hash == first.event_hash
    assert len(list_decision_events(workflow_store)) == 1


def test_missing_decision_does_not_append_workflow_event(tmp_path):
    adapter, workflow_store, _, request = prepare_pending_approval(
        tmp_path
    )

    with pytest.raises(AgentApprovalNotFoundError):
        adapter.record_decision_event(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
            request_id=request.request_id,
        )

    assert list_decision_events(workflow_store) == []

    workflow = workflow_store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert workflow.state is WorkflowState.AWAITING_APPROVAL


def test_cross_tenant_workflow_lookup_fails_closed(tmp_path):
    adapter, workflow_store, _, request = prepare_pending_approval(
        tmp_path,
        decision=ApprovalDecision.APPROVE,
    )

    with pytest.raises(ApprovalWorkflowEventAdapterError):
        adapter.record_decision_event(
            tenant_id="tenant-b",
            workflow_id="workflow-001",
            request_id=request.request_id,
        )

    assert list_decision_events(workflow_store) == []

    workflow = workflow_store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert workflow.state is WorkflowState.AWAITING_APPROVAL