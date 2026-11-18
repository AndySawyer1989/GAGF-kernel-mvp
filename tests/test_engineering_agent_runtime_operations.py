import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.app.engineering_agent.runtime_operations import (
    RuntimeOperationsService,
)
from backend.app.engineering_agent.tracing import (
    TraceContext,
    get_trace_context,
    set_trace_context,
    reset_trace_context,
)
from backend.app.gagf.governance_agent_runtime_coordinator import (
    GovernanceAgentRuntimeCoordinationResult,
    GovernanceAgentRuntimeCoordinator,
)


def make_service():
    coordinator = Mock(spec=GovernanceAgentRuntimeCoordinator)
    logger = Mock(spec=logging.Logger)

    service = RuntimeOperationsService(
        runtime_coordinator=coordinator,
        logger=logger,
    )
    return service, coordinator, logger


def test_runtime_operation_returns_original_result_and_logs_metadata():
    service, coordinator, logger = make_service()

    dispatch_result = SimpleNamespace(
        candidate_count=8,
        scanned_count=6,
        claimed_count=2,
        candidate_limit=20,
        claim_limit=5,
    )
    expected = GovernanceAgentRuntimeCoordinationResult(
        routing_decision=Mock(),
        dispatch_result=dispatch_result,
    )
    coordinator.dispatch_workflow.return_value = expected

    result = service.dispatch_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id="cycle-a",
        lease_seconds=120,
        max_candidates=20,
        max_claims=5,
    )

    assert result is expected

    coordinator.dispatch_workflow.assert_called_once_with(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id="cycle-a",
        lease_seconds=120,
        max_candidates=20,
        max_claims=5,
        now=None,
    )

    events = [
        call.kwargs["extra"]
        for call in logger.info.call_args_list
    ]

    assert [event["event"] for event in events] == [
        "runtime_operation_started",
        "runtime_operation_completed",
    ]

    completed = events[1]
    assert completed["workflow_id"] == "workflow-a"
    assert completed["dispatch_cycle_id"] == "cycle-a"
    assert completed["dispatch_performed"] is True
    assert completed["candidate_count"] == 8
    assert completed["scanned_count"] == 6
    assert completed["claimed_count"] == 2
    assert completed["candidate_limit"] == 20
    assert completed["claim_limit"] == 5
    assert completed["duration_ms"] >= 0
    assert events[0]["operation_id"] == completed["operation_id"]


def test_runtime_operation_logs_no_dispatch_when_dispatch_is_absent():
    service, coordinator, logger = make_service()

    expected = GovernanceAgentRuntimeCoordinationResult(
        routing_decision=Mock(),
        dispatch_result=None,
    )
    coordinator.dispatch_workflow.return_value = expected

    result = service.dispatch_workflow(
        tenant_id="tenant-a",
        workflow_id="workflow-a",
        dispatch_cycle_id="cycle-a",
    )

    assert result is expected

    completed = logger.info.call_args_list[1].kwargs["extra"]
    assert completed["event"] == "runtime_operation_completed"
    assert completed["dispatch_performed"] is False
    assert "claimed_count" not in completed


def test_runtime_operation_logs_failure_and_propagates_exception():
    service, coordinator, logger = make_service()
    coordinator.dispatch_workflow.side_effect = RuntimeError("dispatch failed")

    with pytest.raises(RuntimeError, match="dispatch failed"):
        service.dispatch_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-a",
            dispatch_cycle_id="cycle-a",
        )

    assert logger.info.call_count == 1
    logger.exception.assert_called_once()

    failure = logger.exception.call_args.kwargs["extra"]
    assert failure["event"] == "runtime_operation_failed"
    assert failure["workflow_id"] == "workflow-a"
    assert failure["duration_ms"] >= 0


def test_runtime_operation_creates_child_span_and_restores_parent():
    service, coordinator, logger = make_service()

    parent = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        trace_flags="01",
    )
    token = set_trace_context(parent)

    expected = GovernanceAgentRuntimeCoordinationResult(
        routing_decision=Mock(),
        dispatch_result=None,
    )
    observed = {}

    def dispatch(**kwargs):
        observed["context"] = get_trace_context()
        return expected

    coordinator.dispatch_workflow.side_effect = dispatch

    try:
        result = service.dispatch_workflow(
            tenant_id="tenant-a",
            workflow_id="workflow-a",
            dispatch_cycle_id="cycle-a",
            now=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        assert result is expected
        child = observed["context"]
        assert child.trace_id == parent.trace_id
        assert child.span_id != parent.span_id
        assert child.parent_span_id == parent.span_id
        assert get_trace_context() == parent
    finally:
        reset_trace_context(token)