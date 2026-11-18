from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_task_capability_policy import (
    AgentTaskCapabilityPolicy,
    default_engineering_task_capability_policy,
)
from backend.app.gagf.governance_agent_bounded_dispatcher import (
    AgentBoundedDispatcher,
)
from backend.app.gagf.governance_agent_work_item_store import (
    AgentWorkItemStoreError,
    AgentWorkItemStore,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
    WorkflowState,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowStore,
)
from backend.app.gagf.governance_agent_worker_matcher import (
    AgentWorkerMatcher,
)
from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)


TEST_NOW = datetime(2026, 11, 12, 18, 0, tzinfo=timezone.utc)


def make_dispatcher(tmp_path):
    database_path = tmp_path / "bounded_dispatch.db"

    workflow_store = AgentWorkflowStore(database_path)
    work_item_store = AgentWorkItemStore(database_path)
    registry_store = AgentWorkerRegistryStore(database_path)

    matcher = AgentWorkerMatcher(registry_store)
    dispatcher = AgentBoundedDispatcher(
        work_item_store=work_item_store,
        worker_matcher=matcher,
    )

    return workflow_store, work_item_store, registry_store, dispatcher


def create_active_workflow(
    workflow_store,
    *,
    tenant_id="tenant-a",
    workflow_id="workflow-a",
):
    workflow_store.create_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        workflow_type="engineering",
        idempotency_key=f"create-{tenant_id}-{workflow_id}",
        payload={"source": "bounded-dispatch-test"},
    )

    workflow_store.transition_workflow(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        target_state=WorkflowState.ACTIVE,
        idempotency_key=f"activate-{tenant_id}-{workflow_id}",
        event_type="workflow.activated",
    )


def create_item(
    work_item_store,
    *,
    work_item_id,
    tenant_id="tenant-a",
    workflow_id="workflow-a",
    task_type="code.review",
):
    return work_item_store.create_work_item(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        work_item_id=work_item_id,
        task_type=task_type,
        idempotency_key=f"create-{tenant_id}-{work_item_id}",
        input_payload={"task": work_item_id},
        available_at=TEST_NOW,
        now=TEST_NOW + timedelta(seconds=2),
    )


def register_worker(
    registry_store,
    *,
    worker_id="worker-a",
    tenant_id="tenant-a",
    task_types=("code.review",),
    capabilities=("runtime.python", "tool.pytest"),
    enabled=True,
):
    return registry_store.register_worker(
        tenant_id=tenant_id,
        worker_id=worker_id,
        worker_type="engineering",
        version="1.0.0",
        supported_task_types=task_types,
        capabilities=capabilities,
        enabled=enabled,
        now=TEST_NOW,
    )


def run_dispatch(dispatcher, **overrides):
    arguments = {
        "tenant_id": "tenant-a",
        "workflow_id": "workflow-a",
        "dispatch_cycle_id": "cycle-001",
        "task_capability_policy": (
            default_engineering_task_capability_policy()
        ),
        "lease_seconds": 60,
        "max_candidates": 20,
        "max_claims": 10,
        "now": TEST_NOW + timedelta(seconds=3),
    }
    arguments.update(overrides)
    return dispatcher.dispatch(**arguments)


def test_dispatch_claims_qualified_work_without_executing_it(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)
    create_item(work_item_store, work_item_id="item-a")
    register_worker(registry_store)

    result = run_dispatch(dispatcher)

    assert result.candidate_count == 1
    assert result.scanned_count == 1
    assert result.claimed_count == 1
    assert len(result.outcomes) == 1

    outcome = result.outcomes[0]
    assert outcome.status == "claimed"
    assert outcome.worker_id == "worker-a"
    assert outcome.record is not None
    assert outcome.record.state is WorkItemState.CLAIMED
    assert outcome.record.attempt_count == 1
    assert outcome.record.fencing_token == 1


def test_dispatch_respects_max_claims(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)

    for item_id in ("item-a", "item-b", "item-c"):
        create_item(work_item_store, work_item_id=item_id)

    register_worker(registry_store)

    result = run_dispatch(
        dispatcher,
        max_candidates=3,
        max_claims=1,
    )

    assert result.candidate_count == 3
    assert result.scanned_count == 1
    assert result.claimed_count == 1
    assert result.outcomes[0].work_item_id == "item-a"
    assert result.outcomes[0].status == "claimed"

    remaining = work_item_store.list_ready_work_items(
        tenant_id="tenant-a",
        now=TEST_NOW + timedelta(seconds=3),
        limit=10,
    )
    assert len(remaining) == 2


def test_dispatch_respects_candidate_scan_bound(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)

    for item_id in ("item-a", "item-b", "item-c"):
        create_item(work_item_store, work_item_id=item_id)

    # No worker is registered: each inspected item is unmatched.
    result = run_dispatch(
        dispatcher,
        max_candidates=2,
        max_claims=2,
    )

    assert result.candidate_count == 2
    assert result.scanned_count == 2
    assert result.claimed_count == 0
    assert all(
        outcome.status == "unmatched"
        for outcome in result.outcomes
    )

    remaining = work_item_store.list_ready_work_items(
        tenant_id="tenant-a",
        now=TEST_NOW + timedelta(seconds=3),
        limit=10,
    )
    assert len(remaining) == 3


def test_dispatch_leaves_unmatched_item_pending(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)
    original = create_item(
        work_item_store,
        work_item_id="item-a",
    )

    result = run_dispatch(dispatcher)

    assert result.claimed_count == 0
    assert result.outcomes[0].status == "unmatched"

    persisted = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )
    assert persisted == original
    assert persisted.state is WorkItemState.PENDING
    assert persisted.attempt_count == 0
    assert persisted.fencing_token == 0


def test_dispatch_uses_deterministic_worker_selection(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)
    create_item(work_item_store, work_item_id="item-a")

    register_worker(registry_store, worker_id="worker-z")
    register_worker(registry_store, worker_id="worker-a")

    result = run_dispatch(dispatcher)

    assert result.claimed_count == 1
    assert result.outcomes[0].worker_id == "worker-a"


def test_dispatch_uses_per_task_capability_requirements(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)
    create_item(
        work_item_store,
        work_item_id="item-a",
        task_type="security.review",
    )

    register_worker(
        registry_store,
        task_types=("security.review",),
        capabilities=("expertise.security_review",),
    )

    result = run_dispatch(dispatcher)

    assert result.claimed_count == 1
    assert result.outcomes[0].status == "claimed"


def test_dispatch_rejects_stale_registration_revision(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)
    create_item(work_item_store, work_item_id="item-a")
    register_worker(registry_store)

    original_matcher = dispatcher.worker_matcher

    class RegistrationChangingMatcher:
        def match(self, **kwargs):
            result = original_matcher.match(**kwargs)

            registry_store.register_worker(
                tenant_id="tenant-a",
                worker_id="worker-a",
                worker_type="engineering",
                version="2.0.0",
                supported_task_types=("code.review",),
                capabilities=("runtime.python", "tool.pytest"),
                enabled=True,
                now=TEST_NOW + timedelta(seconds=4),
            )

            return result

    dispatcher.worker_matcher = RegistrationChangingMatcher()

    result = run_dispatch(dispatcher)

    assert result.claimed_count == 0
    assert result.outcomes[0].status == "rejected"
    assert "revision changed" in result.outcomes[0].reason_codes[0]

    persisted = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )
    assert persisted.state is WorkItemState.PENDING
    assert persisted.attempt_count == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"max_candidates": 0},
        {"max_candidates": 501},
        {"max_candidates": True},
        {"max_claims": 0},
        {"max_claims": 11, "max_candidates": 10},
        {"lease_seconds": False},
        {"lease_seconds": 0},
    ],
)
def test_dispatch_rejects_invalid_bounds(tmp_path, overrides):
    _, _, _, dispatcher = make_dispatcher(tmp_path)

    with pytest.raises(AgentWorkItemStoreError):
        run_dispatch(dispatcher, **overrides)


def test_dispatch_rejects_naive_timestamp(tmp_path):
    _, _, _, dispatcher = make_dispatcher(tmp_path)

    with pytest.raises(AgentWorkItemStoreError):
        run_dispatch(
            dispatcher,
            now=datetime(2026, 11, 12, 18, 0),
        )

def test_dispatch_rejects_task_without_capability_policy(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(workflow_store)
    create_item(work_item_store, work_item_id="item-a")
    register_worker(registry_store)

    class MatcherMustNotRun:
        def match(self, **kwargs):
            raise AssertionError(
                "Matcher must not run without a capability policy."
            )

    dispatcher.worker_matcher = MatcherMustNotRun()

    result = run_dispatch(
        dispatcher,
        task_capability_policy=AgentTaskCapabilityPolicy(
            requirements_by_task_type={}
        ),
    )

    assert result.candidate_count == 1
    assert result.scanned_count == 1
    assert result.claimed_count == 0
    assert len(result.outcomes) == 1
    assert result.outcomes[0].work_item_id == "item-a"
    assert result.outcomes[0].status == "rejected"
    assert result.outcomes[0].reason_codes == (
        "missing_capability_policy",
    )

    persisted = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )

    assert persisted.state is WorkItemState.PENDING
    assert persisted.assigned_worker_id is None
    assert persisted.attempt_count == 0
    assert persisted.fencing_token == 0
    assert persisted.lease_expires_at is None

def test_dispatch_only_claims_work_from_requested_workflow(tmp_path):
    workflow_store, work_item_store, registry_store, dispatcher = (
        make_dispatcher(tmp_path)
    )

    create_active_workflow(
        workflow_store,
        workflow_id="workflow-a",
    )
    create_active_workflow(
        workflow_store,
        workflow_id="workflow-b",
    )

    create_item(
        work_item_store,
        work_item_id="item-a",
        workflow_id="workflow-a",
    )
    create_item(
        work_item_store,
        work_item_id="item-b",
        workflow_id="workflow-b",
    )

    register_worker(registry_store)

    result = run_dispatch(
        dispatcher,
        workflow_id="workflow-a",
    )

    assert result.workflow_id == "workflow-a"
    assert result.candidate_count == 1
    assert result.claimed_count == 1
    assert [outcome.work_item_id for outcome in result.outcomes] == [
        "item-a"
    ]

    item_a = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )
    item_b = work_item_store.get_work_item(
        tenant_id="tenant-a",
        work_item_id="item-b",
    )

    assert item_a.state is WorkItemState.CLAIMED
    assert item_b.state is WorkItemState.PENDING
