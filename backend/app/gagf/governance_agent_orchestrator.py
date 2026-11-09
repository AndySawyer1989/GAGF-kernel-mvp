"""Central orchestration coordinator for governance agent workflows.

The orchestrator coordinates event observation and deterministic routing.
It does not execute agents, mutate workflow state, or exercise GAGF Kernel
governance authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable

from .governance_agent_event_bus import (
    GovernanceAgentEventBus,
)
from .governance_agent_state_router import (
    AgentWorkflowRoutingDecision,
    GovernanceAgentStateRouter,
)
from .governance_agent_workflow_contract import (
    AgentWorkflowEvent,
)


ORCHESTRATOR_ID = "governance-agent-orchestrator"
ORCHESTRATOR_VERSION = "0.1.0"


class AgentOrchestratorError(Exception):
    """Base exception for orchestration coordination failures."""


class AgentOrchestratorEventError(AgentOrchestratorError):
    """Raised when an event cannot be safely processed."""


class AgentOrchestratorLifecycleError(AgentOrchestratorError):
    """Raised when subscription lifecycle operations fail."""


@dataclass(frozen=True, slots=True)
class AgentOrchestrationResult:
    """Read-only result of processing a workflow event."""

    event_id: str
    event_type: str
    tenant_id: str
    workflow_id: str
    correlation_id: str
    routing_decision: AgentWorkflowRoutingDecision


AgentOrchestrationResultHandler = Callable[
    [AgentOrchestrationResult],
    None,
]


class GovernanceAgentOrchestrator:
    """Coordinate workflow-event observation and deterministic routing.

    The workflow store remains authoritative. The event bus is a
    synchronous, in-process notification mechanism.

    This component does not:
    - execute agents or work items;
    - advance workflow state;
    - grant approvals;
    - authorize tenant actions;
    - override GAGF Kernel decisions;
    - claim durable event delivery or replay.
    """

    def __init__(
        self,
        *,
        event_bus: GovernanceAgentEventBus,
        state_router: GovernanceAgentStateRouter,
    ) -> None:
        if not callable(getattr(event_bus, "subscribe", None)):
            raise TypeError(
                "event_bus must provide a callable subscribe method"
            )

        if not callable(getattr(event_bus, "unsubscribe", None)):
            raise TypeError(
                "event_bus must provide a callable unsubscribe method"
            )

        if not callable(getattr(state_router, "route", None)):
            raise TypeError(
                "state_router must provide a callable route method"
            )

        self._event_bus = event_bus
        self._state_router = state_router
        self._lock = RLock()
        self._subscription_id: str | None = None
        self._result_handler: (
            AgentOrchestrationResultHandler | None
        ) = None

    @property
    def is_running(self) -> bool:
        """Whether this orchestrator currently holds a bus subscription."""

        with self._lock:
            return self._subscription_id is not None

    def start(
        self,
        *,
        result_handler: AgentOrchestrationResultHandler,
    ) -> str:
        """Subscribe to events and deliver results to an explicit callback.

        Repeated calls while running return the existing subscription ID.
        A callback is required so event-processing results are not silently
        discarded by the bus's notification-only handler interface.
        """

        if not callable(result_handler):
            raise TypeError("result_handler must be callable")

        with self._lock:
            if self._subscription_id is not None:
                return self._subscription_id

            self._result_handler = result_handler

            try:
                subscription_id = self._event_bus.subscribe(
                    handler=self._handle_event_notification,
                )
            except Exception as exc:
                self._result_handler = None
                raise AgentOrchestratorLifecycleError(
                    "orchestrator subscription failed"
                ) from exc

            if (
                not isinstance(subscription_id, str)
                or not subscription_id.strip()
            ):
                self._result_handler = None
                raise AgentOrchestratorLifecycleError(
                    "event bus returned an invalid subscription ID"
                )

            self._subscription_id = subscription_id
            return subscription_id

    def stop(self) -> bool:
        """Unsubscribe. Returns False when already stopped."""

        with self._lock:
            subscription_id = self._subscription_id

            if subscription_id is None:
                return False

            try:
                removed = self._event_bus.unsubscribe(
                    subscription_id=subscription_id,
                )
            except Exception as exc:
                raise AgentOrchestratorLifecycleError(
                    "orchestrator unsubscription failed"
                ) from exc

            if removed:
                self._subscription_id = None
                self._result_handler = None

            return removed

    def handle_event(
        self,
        event: AgentWorkflowEvent,
    ) -> AgentOrchestrationResult:
        """Validate an event and return the current authoritative route."""

        if not isinstance(event, AgentWorkflowEvent):
            raise AgentOrchestratorEventError(
                "event must be an AgentWorkflowEvent"
            )

        try:
            integrity_valid = event.verify_integrity()
        except Exception as exc:
            raise AgentOrchestratorEventError(
                "event integrity verification could not be completed"
            ) from exc

        if not integrity_valid:
            raise AgentOrchestratorEventError(
                "event integrity verification failed"
            )

        self._require_identifier(event.event_id, "event_id")
        self._require_identifier(event.event_type, "event_type")
        self._require_identifier(event.tenant_id, "tenant_id")
        self._require_identifier(event.workflow_id, "workflow_id")
        self._require_identifier(
            event.correlation_id,
            "correlation_id",
        )

        # The event identifies the workflow to inspect. Its payload does
        # not replace the workflow store as the authoritative state source.
        decision = self._state_router.route(
            tenant_id=event.tenant_id,
            workflow_id=event.workflow_id,
        )

        if not isinstance(decision, AgentWorkflowRoutingDecision):
            raise AgentOrchestratorError(
                "state router returned an invalid routing decision"
            )

        if (
            decision.tenant_id != event.tenant_id
            or decision.workflow_id != event.workflow_id
        ):
            raise AgentOrchestratorError(
                "routing decision does not match the event tenant/workflow"
            )

        return AgentOrchestrationResult(
            event_id=event.event_id,
            event_type=event.event_type,
            tenant_id=event.tenant_id,
            workflow_id=event.workflow_id,
            correlation_id=event.correlation_id,
            routing_decision=decision,
        )

    def _handle_event_notification(
        self,
        event: AgentWorkflowEvent,
    ) -> None:
        """Bus callback. Handler failures are reported by the event bus."""

        with self._lock:
            result_handler = self._result_handler

        if result_handler is None:
            raise AgentOrchestratorLifecycleError(
                "orchestrator has no active result handler"
            )

        result = self.handle_event(event)
        result_handler(result)

    @staticmethod
    def _require_identifier(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AgentOrchestratorEventError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()


SERVICE_TYPE = GovernanceAgentOrchestrator