from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_agent_event_bus import (
    AgentEventBusError,
    GovernanceAgentEventBus,
)
from backend.app.gagf.governance_agent_workflow_contract import (
    AgentWorkflowEvent,
)


def make_event(
    *,
    event_type: str = "workflow.created",
) -> AgentWorkflowEvent:
    return AgentWorkflowEvent.create(
        event_id="event-001",
        event_type=event_type,
        tenant_id="tenant-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        idempotency_key="idempotency-001",
        occurred_at=datetime.now(timezone.utc),
        payload={"state": "created"},
    )


def test_publish_delivers_to_all_subscribers():
    bus = GovernanceAgentEventBus()
    received = []

    bus.subscribe(handler=received.append)
    bus.subscribe(handler=received.append)

    event = make_event()
    result = bus.publish(event=event)

    assert result.event_id == event.event_id
    assert result.event_type == event.event_type
    assert result.matched_handler_count == 2
    assert result.delivered_handler_count == 2
    assert result.failed_handler_count == 0
    assert result.successful is True
    assert received == [event, event]


def test_publish_filters_by_event_type():
    bus = GovernanceAgentEventBus()
    received = []

    bus.subscribe(handler=received.append)
    bus.subscribe(
        handler=received.append,
        event_type="workflow.completed",
    )

    event = make_event(event_type="workflow.created")
    result = bus.publish(event=event)

    assert result.matched_handler_count == 1
    assert result.delivered_handler_count == 1
    assert received == [event]


def test_unsubscribe_removes_subscription():
    bus = GovernanceAgentEventBus()
    received = []

    subscription_id = bus.subscribe(
        handler=received.append,
    )

    assert bus.unsubscribe(
        subscription_id=subscription_id,
    ) is True

    assert bus.unsubscribe(
        subscription_id=subscription_id,
    ) is False

    result = bus.publish(event=make_event())

    assert result.matched_handler_count == 0
    assert result.delivered_handler_count == 0
    assert received == []


def test_handler_failure_does_not_block_other_handlers():
    bus = GovernanceAgentEventBus()
    received = []

    def failing_handler(event):
        raise RuntimeError("simulated handler failure")

    bus.subscribe(handler=failing_handler)
    bus.subscribe(handler=received.append)

    event = make_event()
    result = bus.publish(event=event)

    assert result.matched_handler_count == 2
    assert result.delivered_handler_count == 1
    assert result.failed_handler_count == 1
    assert result.successful is False
    assert result.failures[0].event_id == event.event_id
    assert result.failures[0].exception_type == "RuntimeError"
    assert received == [event]


def test_invalid_event_type_is_rejected():
    bus = GovernanceAgentEventBus()

    with pytest.raises(
        AgentEventBusError,
        match="AgentWorkflowEvent",
    ):
        bus.publish(event={"event_type": "workflow.created"})


def test_event_with_invalid_integrity_is_rejected():
    bus = GovernanceAgentEventBus()

    event = make_event()
    corrupted_event = replace(
        event,
        event_hash="invalid-hash",
    )

    with pytest.raises(
        AgentEventBusError,
        match="integrity",
    ):
        bus.publish(event=corrupted_event)


def test_subscription_requires_callable_handler():
    bus = GovernanceAgentEventBus()

    with pytest.raises(
        AgentEventBusError,
        match="callable",
    ):
        bus.subscribe(handler=None)


def test_subscription_rejects_blank_event_type():
    bus = GovernanceAgentEventBus()

    with pytest.raises(
        AgentEventBusError,
        match="event_type",
    ):
        bus.subscribe(
            handler=lambda event: None,
            event_type="   ",
        )


def test_dispatch_uses_subscription_snapshot():
    bus = GovernanceAgentEventBus()
    received = []
    subscription_ids = {}

    def first_handler(event):
        received.append("first")
        bus.unsubscribe(
            subscription_id=subscription_ids["second"],
        )

    bus.subscribe(handler=first_handler)

    subscription_ids["second"] = bus.subscribe(
        handler=lambda event: received.append("second"),
    )

    first_result = bus.publish(event=make_event())

    assert first_result.matched_handler_count == 2
    assert first_result.delivered_handler_count == 2
    assert received == ["first", "second"]

    received.clear()

    second_result = bus.publish(event=make_event())

    assert second_result.matched_handler_count == 1
    assert second_result.delivered_handler_count == 1
    assert received == ["first"]


def test_subscription_added_during_dispatch_applies_next_time():
    bus = GovernanceAgentEventBus()
    received = []
    subscription_ids = []

    def first_handler(event):
        received.append("first")

        if not subscription_ids:
            subscription_ids.append(
                bus.subscribe(
                    handler=lambda next_event: received.append(
                        "late"
                    )
                )
            )

    bus.subscribe(handler=first_handler)

    first_result = bus.publish(event=make_event())

    assert first_result.matched_handler_count == 1
    assert received == ["first"]

    received.clear()

    second_result = bus.publish(event=make_event())

    assert second_result.matched_handler_count == 2
    assert received == ["first", "late"]