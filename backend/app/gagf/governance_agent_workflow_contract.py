from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


CONTRACT_TYPE = "gagf-agent-workflow-contract"
CONTRACT_VERSION = "1.0.0"
EVENT_SCHEMA_VERSION = 1


class AgentWorkflowContractError(ValueError):
    pass


class WorkflowState(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkItemState(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    RETRY_WAIT = "retry_wait"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


WORKFLOW_TRANSITIONS = {
    WorkflowState.CREATED: frozenset({
        WorkflowState.ACTIVE,
        WorkflowState.CANCELLED,
    }),
    WorkflowState.ACTIVE: frozenset({
        WorkflowState.AWAITING_APPROVAL,
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
    }),
    WorkflowState.AWAITING_APPROVAL: frozenset({
        WorkflowState.ACTIVE,
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
    }),
    WorkflowState.COMPLETED: frozenset(),
    WorkflowState.FAILED: frozenset(),
    WorkflowState.CANCELLED: frozenset(),
}


WORK_ITEM_TRANSITIONS = {
    WorkItemState.PENDING: frozenset({
        WorkItemState.CLAIMED,
        WorkItemState.CANCELLED,
    }),
    WorkItemState.CLAIMED: frozenset({
        WorkItemState.RUNNING,
        WorkItemState.PENDING,
        WorkItemState.FAILED,
        WorkItemState.CANCELLED,
    }),
    WorkItemState.RUNNING: frozenset({
        WorkItemState.SUCCEEDED,
        WorkItemState.RETRY_WAIT,
        WorkItemState.FAILED,
        WorkItemState.CANCELLED,
    }),
    WorkItemState.RETRY_WAIT: frozenset({
        WorkItemState.PENDING,
        WorkItemState.DEAD_LETTER,
        WorkItemState.CANCELLED,
    }),
    WorkItemState.SUCCEEDED: frozenset(),
    WorkItemState.FAILED: frozenset({
        WorkItemState.DEAD_LETTER,
    }),
    WorkItemState.DEAD_LETTER: frozenset(),
    WorkItemState.CANCELLED: frozenset(),
}


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkflowContractError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AgentWorkflowContractError(
            "Payload must contain valid JSON-compatible values"
        ) from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_workflow_transition(
    current: WorkflowState,
    target: WorkflowState,
) -> None:
    if not isinstance(current, WorkflowState):
        raise AgentWorkflowContractError(
            "current must be a WorkflowState"
        )

    if not isinstance(target, WorkflowState):
        raise AgentWorkflowContractError(
            "target must be a WorkflowState"
        )

    if target not in WORKFLOW_TRANSITIONS[current]:
        raise AgentWorkflowContractError(
            f"Illegal workflow transition: "
            f"{current.value} -> {target.value}"
        )


def validate_work_item_transition(
    current: WorkItemState,
    target: WorkItemState,
) -> None:
    if not isinstance(current, WorkItemState):
        raise AgentWorkflowContractError(
            "current must be a WorkItemState"
        )

    if not isinstance(target, WorkItemState):
        raise AgentWorkflowContractError(
            "target must be a WorkItemState"
        )

    if target not in WORK_ITEM_TRANSITIONS[current]:
        raise AgentWorkflowContractError(
            f"Illegal work-item transition: "
            f"{current.value} -> {target.value}"
        )


@dataclass(frozen=True, slots=True)
class AgentWorkflowEvent:
    event_id: str
    event_type: str
    tenant_id: str
    workflow_id: str
    work_item_id: str | None
    correlation_id: str
    causation_id: str | None
    idempotency_key: str
    occurred_at: datetime
    payload_json: str
    schema_version: int
    event_hash: str

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        event_type: str,
        tenant_id: str,
        workflow_id: str,
        correlation_id: str,
        idempotency_key: str,
        work_item_id: str | None = None,
        occurred_at: datetime,
        payload: Mapping[str, Any],
        causation_id: str | None = None,
    ) -> AgentWorkflowEvent:
        if not isinstance(payload, Mapping):
            raise AgentWorkflowContractError(
                "payload must be a mapping"
            )

        if not isinstance(occurred_at, datetime):
            raise AgentWorkflowContractError(
                "occurred_at must be a datetime"
            )

        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise AgentWorkflowContractError(
                "occurred_at must be timezone-aware"
            )

        normalized_causation = (
            _require_text(causation_id, "causation_id")
            if causation_id is not None
            else None
        )

        payload_json = _canonical_json(dict(payload))

        fields = {
            "event_id": _require_text(event_id, "event_id"),
            "event_type": _require_text(event_type, "event_type"),
            "tenant_id": _require_text(tenant_id, "tenant_id"),
            "workflow_id": _require_text(workflow_id, "workflow_id"),
            "work_item_id": (
                _require_text(work_item_id, "work_item_id")
                if work_item_id is not None
                else None
            ),
            "correlation_id": _require_text(
                correlation_id, "correlation_id"
            ),
            "causation_id": normalized_causation,
            "idempotency_key": _require_text(
                idempotency_key, "idempotency_key"
            ),
            "occurred_at": occurred_at.astimezone(timezone.utc),
            "payload_json": payload_json,
            "schema_version": EVENT_SCHEMA_VERSION,
        }

        event_hash = _sha256_text(_canonical_json({
            **{
                key: (
                    value.isoformat()
                    if isinstance(value, datetime)
                    else value
                )
                for key, value in fields.items()
            }
        }))

        return cls(**fields, event_hash=event_hash)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)

    def verify_integrity(self) -> bool:
        expected = _sha256_text(_canonical_json({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "work_item_id": self.work_item_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "idempotency_key": self.idempotency_key,
            "occurred_at": self.occurred_at.isoformat(),
            "payload_json": self.payload_json,
            "schema_version": self.schema_version,
        }))
        return expected == self.event_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "work_item_id": self.work_item_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "idempotency_key": self.idempotency_key,
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload,
            "schema_version": self.schema_version,
            "event_hash": self.event_hash,
        }
