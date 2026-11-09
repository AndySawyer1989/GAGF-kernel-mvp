import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalRequest,
    ApprovalActionClass,
    ApprovalActorType,
    ApprovalRequesterType,
)
from backend.app.gagf.governance_agent_approval_store import (
    AgentApprovalNotFoundError,
    AgentApprovalStore,
)
from backend.app.gagf.governance_agent_approval_service import (
    GovernanceAgentApprovalService,
)
from backend.app.gagf.governance_agent_workflow_approval_integration import (
    APPROVAL_REQUESTED_EVENT,
    GovernanceAgentWorkflowApprovalIntegration,
    WorkflowApprovalConflictError,
    WorkflowApprovalIntegrationError,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowStore,
)


class UnusedIdentityProvider:
    """Approval-link tests do not authenticate or submit decisions."""

    def resolve_actor(self, *, tenant_id, authentication_context):
        raise AssertionError(
            "Identity provider must not be called by approval-link operations"
        )


def make_integration(tmp_path):
    workflow_store = AgentWorkflowStore(
        tmp_path / "agent_workflows.db"
    )
    approval_store = AgentApprovalStore(
        tmp_path / "agent_approvals.db"
    )
    approval_service = GovernanceAgentApprovalService(
        store=approval_store,
        identity_provider=UnusedIdentityProvider(),
    )

    integration = GovernanceAgentWorkflowApprovalIntegration(
        workflow_store=workflow_store,
        approval_service=approval_service,
    )

    return integration, workflow_store, approval_service


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
            "body": "test",
        },
    }

    values.update(overrides)
    return AgentApprovalRequest.create(**values)


def test_request_approval_persists_request_and_workflow_link(tmp_path):
    integration, workflow_store, approval_service = make_integration(
        tmp_path
    )
    create_active_workflow(workflow_store)
    request = make_request()

    result = integration.request_approval(
        request=request,
        workflow_transition_idempotency_key="approval-transition-001",
    )

    assert result.approval_request.request_hash == request.request_hash
    assert result.workflow.state is WorkflowState.AWAITING_APPROVAL

    persisted = approval_service.get_request(
        tenant_id="tenant-a",
        request_id=request.request_id,
    )
    assert persisted.request_hash == request.request_hash

    events = workflow_store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    approval_events = [
        event for event in events
        if event.event_type == APPROVAL_REQUESTED_EVENT
    ]

    assert len(approval_events) == 1

    event = approval_events[0]
    assert event.verify_integrity() is True
    assert event.payload["previous_state"] == WorkflowState.ACTIVE.value
    assert (
        event.payload["target_state"]
        == WorkflowState.AWAITING_APPROVAL.value
    )

    assert event.payload["data"] == {
        "approval_request_id": request.request_id,
        "approval_request_hash": request.request_hash,
        "action_hash": request.action_hash,
        "work_item_id": request.work_item_id,
        "action_class": request.action_class.value,
        "approval_idempotency_key": request.idempotency_key,
    }


def test_request_approval_replay_does_not_duplicate_link_event(tmp_path):
    integration, workflow_store, _ = make_integration(tmp_path)
    create_active_workflow(workflow_store)
    request = make_request()

    first = integration.request_approval(
        request=request,
        workflow_transition_idempotency_key="approval-transition-001",
    )
    second = integration.request_approval(
        request=request,
        workflow_transition_idempotency_key="approval-transition-001",
    )

    assert first.approval_request.request_hash == (
        second.approval_request.request_hash
    )
    assert second.workflow.state is WorkflowState.AWAITING_APPROVAL

    events = workflow_store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert sum(
        event.event_type == APPROVAL_REQUESTED_EVENT
        for event in events
    ) == 1


def test_get_linked_approval_returns_verified_link(tmp_path):
    integration, workflow_store, _ = make_integration(tmp_path)
    create_active_workflow(workflow_store)
    request = make_request()

    integration.request_approval(
        request=request,
        workflow_transition_idempotency_key="approval-transition-001",
    )

    result = integration.get_linked_approval(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        request_id=request.request_id,
    )

    assert result.workflow.state is WorkflowState.AWAITING_APPROVAL
    assert result.approval_request.request_hash == request.request_hash


def test_request_approval_rejects_workflow_not_active(tmp_path):
    integration, workflow_store, approval_service = make_integration(
        tmp_path
    )

    workflow_store.create_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        workflow_type="engineering",
        idempotency_key="create-workflow-001",
        correlation_id="correlation-001",
    )

    request = make_request()

    with pytest.raises(WorkflowApprovalConflictError):
        integration.request_approval(
            request=request,
            workflow_transition_idempotency_key="approval-transition-001",
        )

    with pytest.raises(AgentApprovalNotFoundError):
        approval_service.get_request(
            tenant_id="tenant-a",
            request_id=request.request_id,
        )

    workflow = workflow_store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert workflow.state is WorkflowState.CREATED


def test_request_approval_rejects_context_mismatch_before_persistence(
    tmp_path,
):
    integration, workflow_store, approval_service = make_integration(
        tmp_path
    )
    create_active_workflow(workflow_store)

    request = make_request(correlation_id="wrong-correlation")

    with pytest.raises(WorkflowApprovalConflictError):
        integration.request_approval(
            request=request,
            workflow_transition_idempotency_key="approval-transition-001",
        )

    with pytest.raises(AgentApprovalNotFoundError):
        approval_service.get_request(
            tenant_id="tenant-a",
            request_id=request.request_id,
        )


def test_request_approval_rejects_expired_request(tmp_path):
    integration, workflow_store, approval_service = make_integration(
        tmp_path
    )
    create_active_workflow(workflow_store)

    now = datetime.now(timezone.utc)
    request = make_request(
        requested_at=now - timedelta(minutes=20),
        expires_at=now - timedelta(minutes=10),
    )

    with pytest.raises(WorkflowApprovalConflictError):
        integration.request_approval(
            request=request,
            workflow_transition_idempotency_key="approval-transition-001",
        )

    with pytest.raises(AgentApprovalNotFoundError):
        approval_service.get_request(
            tenant_id="tenant-a",
            request_id=request.request_id,
        )

def test_request_approval_recovers_after_workflow_transition_failure(
    tmp_path,
):
    integration, workflow_store, approval_service = make_integration(
        tmp_path
    )
    create_active_workflow(workflow_store)
    request = make_request()

    database_path = workflow_store.database_path

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TRIGGER fail_approval_event_insert
            BEFORE INSERT ON gagf_agent_workflow_events
            WHEN NEW.event_type = 'approval.requested'
            BEGIN
                SELECT RAISE(ABORT, 'forced approval event failure');
            END
            """
        )

    with pytest.raises(
        WorkflowApprovalIntegrationError,
        match="workflow linkage did not commit",
    ):
        integration.request_approval(
            request=request,
            workflow_transition_idempotency_key="approval-transition-001",
        )

    # The approval request was committed independently.
    persisted = approval_service.get_request(
        tenant_id="tenant-a",
        request_id=request.request_id,
    )
    assert persisted.request_hash == request.request_hash

    # The failed workflow transaction must leave the workflow ACTIVE.
    workflow = workflow_store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert workflow.state is WorkflowState.ACTIVE

    # No approval linkage event may be reported as committed.
    events = workflow_store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    assert not any(
        event.event_type == APPROVAL_REQUESTED_EVENT
        for event in events
    )

    # Remove the injected failure and retry with the same immutable request
    # and workflow transition idempotency key.
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "DROP TRIGGER fail_approval_event_insert"
        )

    result = integration.request_approval(
        request=request,
        workflow_transition_idempotency_key="approval-transition-001",
    )

    assert result.workflow.state is WorkflowState.AWAITING_APPROVAL
    assert result.approval_request.request_hash == request.request_hash

    events = workflow_store.list_events(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )
    approval_events = [
        event for event in events
        if event.event_type == APPROVAL_REQUESTED_EVENT
    ]

    assert len(approval_events) == 1
    assert approval_events[0].verify_integrity() is True