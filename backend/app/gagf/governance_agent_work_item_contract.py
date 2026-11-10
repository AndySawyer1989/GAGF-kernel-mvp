from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
)


WORK_ITEM_CONTRACT_VERSION = "0.1.0"
WORK_ITEM_SCHEMA_VERSION = 1
MAX_WORK_ITEM_PAYLOAD_BYTES = 262144


class AgentWorkItemContractError(Exception):
    """Raised when a work-item record violates its contract."""


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkItemContractError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _require_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AgentWorkItemContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AgentWorkItemContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_integer(
    value: int,
    field_name: str,
    *,
    minimum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AgentWorkItemContractError(
            f"{field_name} must be an integer"
        )

    if value < minimum:
        raise AgentWorkItemContractError(
            f"{field_name} must be at least {minimum}"
        )

    return value


def _normalize_input_json(value: str) -> str:
    if not isinstance(value, str):
        raise AgentWorkItemContractError(
            "input_json must be a JSON string"
        )

    try:
        payload = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise AgentWorkItemContractError(
            "input_json must contain valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise AgentWorkItemContractError(
            "work-item input must be a JSON object"
        )

    if any(not isinstance(key, str) for key in payload):
        raise AgentWorkItemContractError(
            "work-item input keys must be strings"
        )

    try:
        normalized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise AgentWorkItemContractError(
            "work-item input cannot be represented as canonical JSON"
        ) from exc

    if len(normalized.encode("utf-8")) > MAX_WORK_ITEM_PAYLOAD_BYTES:
        raise AgentWorkItemContractError(
            "work-item input exceeds the maximum payload size"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class AgentWorkItemRecord:
    """Immutable persisted representation of a tenant-scoped work item."""

    work_item_id: str
    tenant_id: str
    workflow_id: str
    task_type: str
    state: WorkItemState
    correlation_id: str
    idempotency_key: str
    input_json: str
    created_at: datetime
    updated_at: datetime
    available_at: datetime
    attempt_count: int
    max_attempts: int
    assigned_worker_id: str | None
    lease_expires_at: datetime | None
    fencing_token: int
    last_error_code: str | None = None
    last_error_message: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "work_item_id",
            "tenant_id",
            "workflow_id",
            "task_type",
            "correlation_id",
            "idempotency_key",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(self.state, WorkItemState):
            raise AgentWorkItemContractError(
                "state must be a WorkItemState"
            )

        for field_name in (
            "created_at",
            "updated_at",
            "available_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_datetime(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if self.lease_expires_at is not None:
            object.__setattr__(
                self,
                "lease_expires_at",
                _require_datetime(
                    self.lease_expires_at,
                    "lease_expires_at",
                ),
            )

        object.__setattr__(
            self,
            "attempt_count",
            _require_integer(
                self.attempt_count,
                "attempt_count",
                minimum=0,
            ),
        )
        object.__setattr__(
            self,
            "max_attempts",
            _require_integer(
                self.max_attempts,
                "max_attempts",
                minimum=1,
            ),
        )
        object.__setattr__(
            self,
            "fencing_token",
            _require_integer(
                self.fencing_token,
                "fencing_token",
                minimum=0,
            ),
        )

        if self.attempt_count > self.max_attempts:
            raise AgentWorkItemContractError(
                "attempt_count cannot exceed max_attempts"
            )

        normalized_input = _normalize_input_json(self.input_json)
        object.__setattr__(self, "input_json", normalized_input)

        if self.assigned_worker_id is not None:
            object.__setattr__(
                self,
                "assigned_worker_id",
                _require_text(
                    self.assigned_worker_id,
                    "assigned_worker_id",
                ),
            )

        if self.state in (
            WorkItemState.CLAIMED,
            WorkItemState.RUNNING,
        ):
            if self.assigned_worker_id is None:
                raise AgentWorkItemContractError(
                    "claimed and running items require an assigned worker"
                )

            if self.lease_expires_at is None:
                raise AgentWorkItemContractError(
                    "claimed and running items require a lease expiry"
                )

            if self.fencing_token < 1:
                raise AgentWorkItemContractError(
                    "claimed and running items require a positive fencing token"
                )
        elif (
            self.assigned_worker_id is not None
            or self.lease_expires_at is not None
        ):
            raise AgentWorkItemContractError(
                "only claimed and running items may hold a worker lease"
            )

        if self.last_error_code is not None:
            object.__setattr__(
                self,
                "last_error_code",
                _require_text(
                    self.last_error_code,
                    "last_error_code",
                ),
            )

        if self.last_error_message is not None:
            object.__setattr__(
                self,
                "last_error_message",
                _require_text(
                    self.last_error_message,
                    "last_error_message",
                ),
            )

        if (
            (self.last_error_code is None)
            != (self.last_error_message is None)
        ):
            raise AgentWorkItemContractError(
                "last_error_code and last_error_message must be provided together"
            )

    @property
    def input_payload(self) -> dict[str, Any]:
        return json.loads(self.input_json)

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_item_id": self.work_item_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "task_type": self.task_type,
            "state": self.state.value,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "input_payload": self.input_payload,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "available_at": self.available_at.isoformat(),
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "assigned_worker_id": self.assigned_worker_id,
            "lease_expires_at": (
                self.lease_expires_at.isoformat()
                if self.lease_expires_at is not None
                else None
            ),
            "fencing_token": self.fencing_token,
            "last_error_code": self.last_error_code,
            "last_error_message": self.last_error_message,
        }