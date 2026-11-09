from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_agent_event_bus import (
    GovernanceAgentEventBus,
)
from backend.app.gagf.governance_agent_orchestrator import (
    AgentOrchestratorEventError,
    GovernanceAgentOrchestrator,
)
from backend.app.gagf.governance_agent_state_router import (
    GovernanceAgentStateRouter,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    AgentWorkflowEvent,
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowNotFoundError,
    AgentWorkflowStore,
)


def make_event(
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-001",
    event_type="workflow.created",
):
    return AgentWorkflowEvent.create(
        event_id="event-001",
        event_type=event_type,
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        correlation_id="correlation-001",
        idempotency_key="event-idempotency-001",
        occurred_at=datetime.now(timezone.utc),
        payload={"source": "orchestrator-test"},
    )


def make_components(tmp_path):
    store = AgentWorkflowStore(
        tmp_path / "agent_workflows.db"
    )

    store.create_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        workflow_type="engineering",
        idempotency_key="create-001",
        payload={"source": "orchestrator-test"},
    )

    event_bus = GovernanceAgentEventBus()
    router = GovernanceAgentStateRouter(store)

    orchestrator = GovernanceAgentOrchestrator(
        event_bus=event_bus,
        state_router=router,
    )

    return store, event_bus, orchestrator


def test_handle_event_returns_authoritative_routing_decision(tmp_path):
    store, _, orchestrator = make_components(tmp_path)

    result = orchestrator.handle_event(make_event())

    persisted = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert result.event_id == "event-001"
    assert result.event_type == "workflow.created"
    assert result.tenant_id == "tenant-a"
    assert result.workflow_id == "workflow-001"
    assert result.correlation_id == "correlation-001"
    assert result.routing_decision.current_state is WorkflowState.CREATED
    assert result.routing_decision.workflow_id == persisted.workflow_id


def test_handle_event_rejects_invalid_event_integrity(tmp_path):
    _, _, orchestrator = make_components(tmp_path)

    corrupted_event = replace(
        make_event(),
        event_hash="invalid-hash",
    )

    with pytest.raises(
        AgentOrchestratorEventError,
        match="integrity",
    ):
        orchestrator.handle_event(corrupted_event)


def test_handle_event_rejects_non_event_input(tmp_path):
    _, _, orchestrator = make_components(tmp_path)

    with pytest.raises(
        AgentOrchestratorEventError,
        match="AgentWorkflowEvent",
    ):
        orchestrator.handle_event({"workflow_id": "workflow-001"})


def test_handle_event_enforces_tenant_scoped_workflow_lookup(tmp_path):
    _, _, orchestrator = make_components(tmp_path)

    cross_tenant_event = make_event(
        tenant_id="tenant-b",
    )

    with pytest.raises(AgentWorkflowNotFoundError):
        orchestrator.handle_event(cross_tenant_event)


def test_start_subscribes_once_and_delivers_result(tmp_path):
    _, event_bus, orchestrator = make_components(tmp_path)
    received = []

    first_subscription = orchestrator.start(
        result_handler=received.append,
    )

    second_subscription = orchestrator.start(
        result_handler=received.append,
    )

    assert first_subscription == second_subscription
    assert orchestrator.is_running

    dispatch = event_bus.publish(event=make_event())

    assert dispatch.matched_handler_count == 1
    assert dispatch.delivered_handler_count == 1
    assert dispatch.failed_handler_count == 0
    assert len(received) == 1
    assert received[0].workflow_id == "workflow-001"


def test_start_rejects_non_callable_result_handler(tmp_path):
    _, _, orchestrator = make_components(tmp_path)

    with pytest.raises(TypeError, match="callable"):
        orchestrator.start(result_handler=None)

    assert not orchestrator.is_running


def test_callback_failure_is_reported_by_event_bus(tmp_path):
    _, event_bus, orchestrator = make_components(tmp_path)

    def failing_callback(result):
        raise RuntimeError("simulated result callback failure")

    orchestrator.start(result_handler=failing_callback)

    dispatch = event_bus.publish(event=make_event())

    assert dispatch.matched_handler_count == 1
    assert dispatch.delivered_handler_count == 0
    assert dispatch.failed_handler_count == 1
    assert dispatch.failures[0].exception_type == "RuntimeError"


def test_stop_unsubscribes_and_is_idempotent(tmp_path):
    _, event_bus, orchestrator = make_components(tmp_path)
    received = []

    orchestrator.start(result_handler=received.append)

    assert orchestrator.stop() is True
    assert orchestrator.is_running is False

    assert orchestrator.stop() is False

    dispatch = event_bus.publish(event=make_event())

    assert dispatch.matched_handler_count == 0
    assert received == []


def test_event_handling_does_not_mutate_workflow_state(tmp_path):
    store, _, orchestrator = make_components(tmp_path)

    before = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    orchestrator.handle_event(make_event())

    after = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert after == before
    assert after.state is WorkflowState.CREATED


def test_orchestrator_does_not_advance_workflow_after_notification(tmp_path):
    store, event_bus, orchestrator = make_components(tmp_path)
    received = []

    orchestrator.start(result_handler=received.append)
    event_bus.publish(event=make_event())

    persisted = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert len(received) == 1
    assert persisted.state is WorkflowState.CREATED