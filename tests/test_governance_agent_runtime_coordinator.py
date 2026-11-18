from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_bounded_dispatcher import (
    AgentBoundedDispatcher,
)
from backend.app.gagf.governance_agent_runtime_coordinator import (
    GovernanceAgentRuntimeCoordinator,
    GovernanceAgentRuntimeCoordinatorInputError,
)
from backend.app.gagf.governance_agent_state_router import (
    GovernanceAgentStateRouter,
    WorkflowRoutingAction,
)
from backend.app.gagf.governance_agent_task_capability_policy import (
    default_engineering_task_capability_policy,
)
from backend.app.gagf.governance_agent_work_item_store import (
    AgentWorkItemStore,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowNotFoundError,
    AgentWorkflowStore,
)
from backend.app.gagf.governance_agent_worker_matcher import (
    AgentWorkerMatcher,
)
from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)


TEST_NOW = datetime(2026, 11, 12, 18, 0, tzinfo=timezone.utc)


def make_coordinator(tmp_path):
    database_path = tmp_path / "runtime_coordinator.db"

    workflow_store = AgentWorkflowStore(database_path)
    work_item_store = AgentWorkItemStore(database_path)
    registry_store = AgentWorkerRegistryStore(database_path)

    state_router = GovernanceAgentStateRouter(workflow_store)
    worker_matcher = AgentWorkerMatcher(registry_store)

    bounded_dispatcher = AgentBoundedDispatcher(
        work_item_store=work_item_store,
        worker_matcher=worker_matcher,
    )

    coordinator = GovernanceAgentRuntimeCoordinator(
        state_router=state_router,
        bounded_dispatcher=bounded_dispatcher,
        task_capability_policy=(
            default_engineering_task_capability_policy()
        ),
    )

    return (
        workflow_store,
        work_item_store,
        registry_store,
        coordinator,
    )


def create_workflow(
    workflow_store,
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-a",
    activate=False,
):
    workflow_store.create_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        workflow_type="engineering",
        idempotency_key=f"create-{tenant_id}-{workflow_id}",
        payload={"source": "runtime-coordinator-test"},
    )

    if activate:
        workflow_store.transition_workflow(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            target_state=WorkflowState.ACTIVE,
            idempotency_key=f"activate-{tenant_id}-{workflow_id}",
            event_type="workflow.activated",
        )


def create_pending_item(work_item_store):
    return work_item_store.create_work_item(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        work_item_id="item-a",
        task_type="code.review",
        idempotency_key="create-item-a",
        input_payload={"task": "review"},
        available_at=TEST_NOW,
        now=TEST_NOW + timedelta(seconds=2),
    )


def register_worker(registry_store):
    return registry_store.register_worker(
        tenant_id="tenant-a",
        worker_id="worker-a",
        worker_type="engineering",
        version="1.0.0",
        supported_task_types=("code.review",),
        capabilities=("runtime.python", "tool.pytest"),
        enabled=True,
        now=TEST_NOW,
    )


def test_active_workflow_dispatches_only_its_own_work(tmp_path):
    (
        workflow_store,
        work_item_store,
        registry_store,
        coordinator,
    ) = make_coordinator(tmp_path)

    create_workflow(workflow_store, activate=True)
    create_pending_item(work_item_store)
    register_worker(registry_store)

    result = coordinator.dispatch_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id="cycle-001",
        now=TEST_NOW + timedelta(seconds=3),
    )

    assert result.dispatch_performed is True
    assert result.routing_decision.current_state is WorkflowState.ACTIVE
    assert (
        result.routing_decision.action
        is WorkflowRoutingAction.COORDINATE_WORK
    )

    assert result.dispatch_result is not None
    assert result.dispatch_result.tenant_id == "tenant-a"
    assert result.dispatch_result.workflow_id == "workflow-a"
    assert result.dispatch_result.claimed_count == 1

    item = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )

    # Coordination claims work; it does not execute or complete it.
    assert item.state is WorkItemState.CLAIMED


def test_created_workflow_does_not_dispatch_pending_work(tmp_path):
    (
        workflow_store,
        work_item_store,
        _registry_store,
        coordinator,
    ) = make_coordinator(tmp_path)

    create_workflow(workflow_store, activate=False)
    create_pending_item(work_item_store)

    result = coordinator.dispatch_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id="cycle-002",
        now=TEST_NOW + timedelta(seconds=3),
    )

    assert result.dispatch_performed is False
    assert result.dispatch_result is None
    assert result.routing_decision.current_state is WorkflowState.CREATED
    assert (
        result.routing_decision.action
        is WorkflowRoutingAction.PREPARE_ACTIVATION
    )

    item = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )

    assert item.state is WorkItemState.PENDING


@pytest.mark.parametrize(
    "field,value",
    [
        ("tenant_id", ""),
        ("workflow_id", " "),
        ("dispatch_cycle_id", ""),
    ],
)
def test_dispatch_workflow_rejects_empty_identifiers(
    tmp_path,
    field,
    value,
):
    (
        workflow_store,
        _work_item_store,
        _registry_store,
        coordinator,
    ) = make_coordinator(tmp_path)

    create_workflow(workflow_store)

    arguments = {
        "tenant_id": "tenant-a",
        "workflow_id": "workflow-a",
        "dispatch_cycle_id": "cycle-003",
    }
    arguments[field] = value

    with pytest.raises(GovernanceAgentRuntimeCoordinatorInputError):
        coordinator.dispatch_workflow(**arguments)

def test_awaiting_approval_workflow_does_not_dispatch_pending_work(tmp_path):
    (
        workflow_store,
        work_item_store,
        registry_store,
        coordinator,
    ) = make_coordinator(tmp_path)

    create_workflow(workflow_store, activate=True)
    create_pending_item(work_item_store)
    register_worker(registry_store)

    workflow_store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        target_state=WorkflowState.AWAITING_APPROVAL,
        idempotency_key="await-approval-tenant-a-workflow-a",
        event_type="workflow.approval_requested",
    )

    result = coordinator.dispatch_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id="cycle-awaiting-approval",
        now=TEST_NOW + timedelta(seconds=3),
    )

    assert result.dispatch_performed is False
    assert result.dispatch_result is None
    assert (
        result.routing_decision.current_state
        is WorkflowState.AWAITING_APPROVAL
    )
    assert (
        result.routing_decision.action
        is WorkflowRoutingAction.WAIT_FOR_HUMAN_APPROVAL
    )
    assert result.routing_decision.requires_human_approval is True
    assert result.routing_decision.terminal is False

    item = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )
    assert item.state is WorkItemState.PENDING


@pytest.mark.parametrize(
    "target_state",
    [
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
    ],
)
def test_terminal_workflow_does_not_dispatch_pending_work(
    tmp_path,
    target_state,
):
    (
        workflow_store,
        work_item_store,
        registry_store,
        coordinator,
    ) = make_coordinator(tmp_path)

    create_workflow(workflow_store, activate=True)
    create_pending_item(work_item_store)
    register_worker(registry_store)

    workflow_store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        target_state=target_state,
        idempotency_key=f"terminal-{target_state.value}-workflow-a",
        event_type=f"workflow.{target_state.value}",
    )

    result = coordinator.dispatch_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id=f"cycle-terminal-{target_state.value}",
        now=TEST_NOW + timedelta(seconds=3),
    )

    assert result.dispatch_performed is False
    assert result.dispatch_result is None
    assert result.routing_decision.current_state is target_state
    assert result.routing_decision.terminal is True
    assert result.routing_decision.requires_human_approval is False

    item = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )
    assert item.state is WorkItemState.PENDING


def test_coordinator_cannot_dispatch_another_tenants_workflow(tmp_path):
    (
        workflow_store,
        work_item_store,
        registry_store,
        coordinator,
    ) = make_coordinator(tmp_path)

    create_workflow(
        workflow_store,
        tenant_id="tenant-b",
        workflow_id="workflow-a",
        activate=True,
    )

    work_item_store.create_work_item(
        tenant_id="tenant-b",
        workflow_id="workflow-a",
        work_item_id="item-b",
        task_type="code.review",
        idempotency_key="create-item-b",
        input_payload={"task": "review"},
        available_at=TEST_NOW,
        now=TEST_NOW + timedelta(seconds=2),
    )

    # Even an eligible worker in tenant B cannot make a tenant A
    # request resolve or dispatch tenant B's workflow.
    register_worker(registry_store)

    with pytest.raises(AgentWorkflowNotFoundError):
        coordinator.dispatch_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-a",
            dispatch_cycle_id="cycle-cross-tenant",
            now=TEST_NOW + timedelta(seconds=3),
        )

    item = work_item_store.get_work_item(
        tenant_id="tenant-b",
        work_item_id="item-b",
    )
    assert item.state is WorkItemState.PENDING