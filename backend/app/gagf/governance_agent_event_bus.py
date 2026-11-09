from __future__ import annotations

import threading
import uuid

from dataclasses import dataclass
from typing import Callable

from backend.app.gagf.governance_agent_workflow_contract import (
    AgentWorkflowEvent,
)


AGENT_EVENT_BUS_ID = "governance-agent-event-bus"
AGENT_EVENT_BUS_VERSION = "0.1.0"


class AgentEventBusError(ValueError):
    """Raised when event-bus configuration or publication is invalid."""


@dataclass(frozen=True, slots=True)
class AgentEventHandlerFailure:
    subscription_id: str
    event_id: str
    event_type: str
    exception_type: str


@dataclass(frozen=True, slots=True)
class AgentEventDispatchResult:
    event_id: str
    event_type: str
    matched_handler_count: int
    delivered_handler_count: int
    failures: tuple[AgentEventHandlerFailure, ...]

    @property
    def failed_handler_count(self) -> int:
        return len(self.failures)

    @property
    def successful(self) -> bool:
        return not self.failures


@dataclass(frozen=True, slots=True)
class _AgentEventSubscription:
    subscription_id: str
    handler: Callable[[AgentWorkflowEvent], None]
    event_type: str | None


class GovernanceAgentEventBus:
    """
    Synchronous in-process notification for persisted workflow events.

    The workflow store remains the durable source of truth. This bus does
    not persist, replay, authorize, or execute workflow operations.

    Handler failures are reported in the dispatch result. They do not
    change or reverse any database transaction that occurred before
    publication.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscriptions: dict[
            str,
            _AgentEventSubscription,
        ] = {}

    def subscribe(
        self,
        *,
        handler: Callable[[AgentWorkflowEvent], None],
        event_type: str | None = None,
    ) -> str:
        if not callable(handler):
            raise AgentEventBusError(
                "handler must be callable"
            )

        normalized_event_type = (
            self._require_text(event_type, "event_type")
            if event_type is not None
            else None
        )

        subscription_id = str(uuid.uuid4())

        subscription = _AgentEventSubscription(
            subscription_id=subscription_id,
            handler=handler,
            event_type=normalized_event_type,
        )

        with self._lock:
            self._subscriptions[subscription_id] = subscription

        return subscription_id

    def unsubscribe(
        self,
        *,
        subscription_id: str,
    ) -> bool:
        normalized_id = self._require_text(
            subscription_id,
            "subscription_id",
        )

        with self._lock:
            return (
                self._subscriptions.pop(
                    normalized_id,
                    None,
                )
                is not None
            )

    def publish(
        self,
        *,
        event: AgentWorkflowEvent,
    ) -> AgentEventDispatchResult:
        if not isinstance(event, AgentWorkflowEvent):
            raise AgentEventBusError(
                "event must be an AgentWorkflowEvent"
            )

        if not event.verify_integrity():
            raise AgentEventBusError(
                "event integrity verification failed"
            )

        with self._lock:
            subscriptions = tuple(
                subscription
                for subscription in self._subscriptions.values()
                if (
                    subscription.event_type is None
                    or subscription.event_type == event.event_type
                )
            )

        failures: list[AgentEventHandlerFailure] = []
        delivered_count = 0

        for subscription in subscriptions:
            try:
                subscription.handler(event)
            except Exception as exc:
                failures.append(
                    AgentEventHandlerFailure(
                        subscription_id=(
                            subscription.subscription_id
                        ),
                        event_id=event.event_id,
                        event_type=event.event_type,
                        exception_type=type(exc).__name__,
                    )
                )
            else:
                delivered_count += 1

        return AgentEventDispatchResult(
            event_id=event.event_id,
            event_type=event.event_type,
            matched_handler_count=len(subscriptions),
            delivered_handler_count=delivered_count,
            failures=tuple(failures),
        )

    @staticmethod
    def _require_text(
        value: str,
        field_name: str,
    ) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise AgentEventBusError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()


SERVICE_TYPE = GovernanceAgentEventBus