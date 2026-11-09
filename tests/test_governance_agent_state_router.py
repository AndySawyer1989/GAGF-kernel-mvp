from dataclasses import replace

import pytest

from backend.app.gagf.governance_agent_state_router import (
    AgentWorkflowStateRouterError,
    GovernanceAgentStateRouter,
    WorkflowRoutingAction,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WORKFLOW_TRANSITIONS,
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowNotFoundError,
    AgentWorkflowRecord,
    AgentWorkflowStore,
)


def make_store(tmp_path):
    return AgentWorkflowStore(
        tmp_path / "agent_workflows.db",
    )


def create_record(store):
    return store.create_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        workflow_type="engineering",
        idempotency_key="create-001",
        payload={"source": "state-router-test"},
    )


def transition(store, target_state, idempotency_key):
    return store.transition_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
        target_state=target_state,
        idempotency_key=idempotency_key,
        event_type=f"workflow.{target_state.value}",
    )


def make_record_for_state(store, target_state):
    record = create_record(store)

    if target_state is WorkflowState.CREATED:
        return record

    record = transition(
        store,
        WorkflowState.ACTIVE,
        "activate-001",
    )

    if target_state is WorkflowState.ACTIVE:
        return record

    return transition(
        store,
        target_state,
        f"transition-{target_state.value}",
    )


EXPECTED_ACTIONS = {
    WorkflowState.CREATED: WorkflowRoutingAction.PREPARE_ACTIVATION,
    WorkflowState.ACTIVE: WorkflowRoutingAction.COORDINATE_WORK,
    WorkflowState.AWAITING_APPROVAL: (
        WorkflowRoutingAction.WAIT_FOR_HUMAN_APPROVAL
    ),
    WorkflowState.COMPLETED: WorkflowRoutingAction.TERMINAL_COMPLETED,
    WorkflowState.FAILED: WorkflowRoutingAction.TERMINAL_FAILED,
    WorkflowState.CANCELLED: WorkflowRoutingAction.TERMINAL_CANCELLED,
}


@pytest.mark.parametrize(
    "state",
    list(WorkflowState),
)
def test_route_returns_expected_action_for_each_state(tmp_path, state):
    store = make_store(tmp_path)
    make_record_for_state(store, state)

    router = GovernanceAgentStateRouter(store)

    decision = router.route(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert decision.current_state is state
    assert decision.action is EXPECTED_ACTIONS[state]


@pytest.mark.parametrize(
    "state",
    list(WorkflowState),
)
def test_allowed_transitions_come_from_workflow_contract(tmp_path, state):
    store = make_store(tmp_path)
    make_record_for_state(store, state)

    decision = GovernanceAgentStateRouter(store).route(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert decision.allowed_transitions == tuple(
        sorted(
            WORKFLOW_TRANSITIONS[state],
            key=lambda item: item.value,
        )
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (WorkflowState.CREATED, False),
        (WorkflowState.ACTIVE, False),
        (WorkflowState.AWAITING_APPROVAL, True),
        (WorkflowState.COMPLETED, False),
        (WorkflowState.FAILED, False),
        (WorkflowState.CANCELLED, False),
    ],
)
def test_human_approval_flag_is_only_set_for_approval_state(
    tmp_path,
    state,
    expected,
):
    store = make_store(tmp_path)
    make_record_for_state(store, state)

    decision = GovernanceAgentStateRouter(store).route(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert decision.requires_human_approval is expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (WorkflowState.CREATED, False),
        (WorkflowState.ACTIVE, False),
        (WorkflowState.AWAITING_APPROVAL, False),
        (WorkflowState.COMPLETED, True),
        (WorkflowState.FAILED, True),
        (WorkflowState.CANCELLED, True),
    ],
)
def test_terminal_flag_matches_workflow_state(
    tmp_path,
    state,
    expected,
):
    store = make_store(tmp_path)
    make_record_for_state(store, state)

    decision = GovernanceAgentStateRouter(store).route(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert decision.terminal is expected


def test_route_does_not_modify_persisted_workflow(tmp_path):
    store = make_store(tmp_path)
    original = make_record_for_state(store, WorkflowState.ACTIVE)

    router = GovernanceAgentStateRouter(store)

    router.route(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    persisted = store.get_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-001",
    )

    assert persisted == original


def test_route_preserves_tenant_scoping(tmp_path):
    store = make_store(tmp_path)
    create_record(store)

    router = GovernanceAgentStateRouter(store)

    with pytest.raises(AgentWorkflowNotFoundError):
        router.route(
            tenant_id="tenant-b",
            workflow_id="workflow-001",
        )


def test_route_rejects_record_with_wrong_tenant():
    record = AgentWorkflowRecord(
        workflow_id="workflow-001",
        tenant_id="tenant-b",
        workflow_type="engineering",
        state=WorkflowState.CREATED,
        correlation_id="correlation-001",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )

    class StaticStore:
        def get_workflow(self, *, tenant_id, workflow_id):
            return record

    router = GovernanceAgentStateRouter(StaticStore())

    with pytest.raises(
        AgentWorkflowStateRouterError,
        match="tenant",
    ):
        router.route(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )


def test_route_rejects_record_with_wrong_workflow_id():
    record = AgentWorkflowRecord(
        workflow_id="workflow-other",
        tenant_id="tenant-a",
        workflow_type="engineering",
        state=WorkflowState.CREATED,
        correlation_id="correlation-001",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )

    class StaticStore:
        def get_workflow(self, *, tenant_id, workflow_id):
            return record

    router = GovernanceAgentStateRouter(StaticStore())

    with pytest.raises(
        AgentWorkflowStateRouterError,
        match="workflow",
    ):
        router.route(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )


@pytest.mark.parametrize(
    "bad_state",
    ["active", None, 123],
)
def test_route_rejects_malformed_state(bad_state):
    record = AgentWorkflowRecord(
        workflow_id="workflow-001",
        tenant_id="tenant-a",
        workflow_type="engineering",
        state=WorkflowState.CREATED,
        correlation_id="correlation-001",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    malformed_record = replace(record, state=bad_state)

    class StaticStore:
        def get_workflow(self, *, tenant_id, workflow_id):
            return malformed_record

    router = GovernanceAgentStateRouter(StaticStore())

    with pytest.raises(
        AgentWorkflowStateRouterError,
        match="state",
    ):
        router.route(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )


def test_route_rejects_invalid_record_type():
    class StaticStore:
        def get_workflow(self, *, tenant_id, workflow_id):
            return {"state": "created"}

    router = GovernanceAgentStateRouter(StaticStore())

    with pytest.raises(
        AgentWorkflowStateRouterError,
        match="record type",
    ):
        router.route(
            tenant_id="tenant-a",
            workflow_id="workflow-001",
        )


def test_route_rejects_empty_identifiers(tmp_path):
    router = GovernanceAgentStateRouter(make_store(tmp_path))

    with pytest.raises(AgentWorkflowStateRouterError):
        router.route(
            tenant_id=" ",
            workflow_id="workflow-001",
        )

    with pytest.raises(AgentWorkflowStateRouterError):
        router.route(
            tenant_id="tenant-a",
            workflow_id=" ",
        )


def test_route_propagates_store_not_found_error(tmp_path):
    router = GovernanceAgentStateRouter(make_store(tmp_path))

    with pytest.raises(AgentWorkflowNotFoundError):
        router.route(
            tenant_id="tenant-a",
            workflow_id="missing-workflow",
        )