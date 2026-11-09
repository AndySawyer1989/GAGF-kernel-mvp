"""Bounded execution contract for FIP/GAGF agent workers.

Workers receive immutable execution requests and return structured results.
They do not control workflow state, approvals, authorization, or Kernel
governance decisions.
"""

from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Protocol


WORKER_CONTRACT_ID = "gagf-agent-worker-contract"
WORKER_CONTRACT_VERSION = "0.1.0"
WORKER_SCHEMA_VERSION = 1
MAX_WORKER_PAYLOAD_BYTES = 262144


class AgentWorkerContractError(ValueError):
    """Raised when a worker request or result violates the contract."""


class AgentWorkerOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RETRYABLE_FAILURE = "retryable_failure"
    REJECTED = "rejected"


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkerContractError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AgentWorkerContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AgentWorkerContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonical_payload(
    value: Mapping[str, Any],
    field_name: str,
) -> str:
    if not isinstance(value, Mapping):
        raise AgentWorkerContractError(
            f"{field_name} must be a mapping"
        )

    try:
        serialized = json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AgentWorkerContractError(
            f"{field_name} must contain JSON-compatible values"
        ) from exc

    if len(serialized.encode("utf-8")) > MAX_WORKER_PAYLOAD_BYTES:
        raise AgentWorkerContractError(
            f"{field_name} exceeds the maximum payload size"
        )

    return serialized


def _validate_payload_json(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise AgentWorkerContractError(
            f"{field_name} must be a JSON string"
        )

    try:
        decoded = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise AgentWorkerContractError(
            f"{field_name} must contain valid JSON"
        ) from exc

    if not isinstance(decoded, Mapping):
        raise AgentWorkerContractError(
            f"{field_name} must contain a JSON object"
        )

    return _canonical_payload(decoded, field_name)


def _validate_schema_version(value: Any) -> None:
    if type(value) is not int or value != WORKER_SCHEMA_VERSION:
        raise AgentWorkerContractError(
            "Unsupported worker contract schema version"
        )


@dataclass(frozen=True, slots=True)
class AgentWorkerRequest:
    """Immutable, tenant-scoped instructions for one bounded work item."""

    request_id: str
    tenant_id: str
    workflow_id: str
    work_item_id: str
    worker_id: str
    task_type: str
    instruction: str
    correlation_id: str
    idempotency_key: str
    issued_at: datetime
    input_json: str
    schema_version: int = WORKER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "tenant_id",
            "workflow_id",
            "work_item_id",
            "worker_id",
            "task_type",
            "instruction",
            "correlation_id",
            "idempotency_key",
        ):
            _require_text(
                getattr(self, field_name),
                field_name,
            )

        normalized_time = _require_aware_datetime(
            self.issued_at,
            "issued_at",
        )
        normalized_payload = _validate_payload_json(
            self.input_json,
            "input_payload",
        )
        _validate_schema_version(self.schema_version)

        object.__setattr__(self, "issued_at", normalized_time)
        object.__setattr__(self, "input_json", normalized_payload)
    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        tenant_id: str,
        workflow_id: str,
        work_item_id: str,
        worker_id: str,
        task_type: str,
        instruction: str,
        correlation_id: str,
        idempotency_key: str,
        issued_at: datetime,
        input_payload: Mapping[str, Any],
    ) -> AgentWorkerRequest:
        if not isinstance(input_payload, Mapping):
            raise AgentWorkerContractError(
                "input_payload must be a mapping"
            )

        return cls(
            request_id=_require_text(request_id, "request_id"),
            tenant_id=_require_text(tenant_id, "tenant_id"),
            workflow_id=_require_text(workflow_id, "workflow_id"),
            work_item_id=_require_text(work_item_id, "work_item_id"),
            worker_id=_require_text(worker_id, "worker_id"),
            task_type=_require_text(task_type, "task_type"),
            instruction=_require_text(instruction, "instruction"),
            correlation_id=_require_text(
                correlation_id, "correlation_id"
            ),
            idempotency_key=_require_text(
                idempotency_key, "idempotency_key"
            ),
            issued_at=_require_aware_datetime(issued_at, "issued_at"),
            input_json=_canonical_payload(
                input_payload, "input_payload"
            ),
        )

    @property
    def input_payload(self) -> dict[str, Any]:
        return json.loads(self.input_json)


@dataclass(frozen=True, slots=True)
class AgentWorkerResult:
    """Structured worker output. Output is untrusted until validated."""

    request_id: str
    tenant_id: str
    workflow_id: str
    work_item_id: str
    worker_id: str
    correlation_id: str
    idempotency_key: str
    outcome: AgentWorkerOutcome
    executed_at: datetime
    output_json: str
    error_code: str | None
    error_message: str | None
    schema_version: int = WORKER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "tenant_id",
            "workflow_id",
            "work_item_id",
            "worker_id",
            "correlation_id",
            "idempotency_key",
        ):
            _require_text(
                getattr(self, field_name),
                field_name,
            )

        if not isinstance(self.outcome, AgentWorkerOutcome):
            raise AgentWorkerContractError(
                "outcome must be an AgentWorkerOutcome"
            )

        normalized_time = _require_aware_datetime(
            self.executed_at,
            "executed_at",
        )
        normalized_output = _validate_payload_json(
            self.output_json,
            "output",
        )

        normalized_error_code = (
            _require_text(self.error_code, "error_code")
            if self.error_code is not None
            else None
        )
        normalized_error_message = (
            _require_text(self.error_message, "error_message")
            if self.error_message is not None
            else None
        )

        if self.outcome == AgentWorkerOutcome.SUCCESS:
            if (
                normalized_error_code is not None
                or normalized_error_message is not None
            ):
                raise AgentWorkerContractError(
                    "successful results cannot contain error details"
                )
        elif (
            normalized_error_code is None
            or normalized_error_message is None
        ):
            raise AgentWorkerContractError(
                "non-success results require error_code and error_message"
            )

        _validate_schema_version(self.schema_version)

        object.__setattr__(self, "executed_at", normalized_time)
        object.__setattr__(self, "output_json", normalized_output)
        object.__setattr__(self, "error_code", normalized_error_code)
        object.__setattr__(self, "error_message", normalized_error_message)
    @classmethod
    def create(
        cls,
        *,
        request: AgentWorkerRequest,
        outcome: AgentWorkerOutcome,
        executed_at: datetime,
        output: Mapping[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AgentWorkerResult:
        if not isinstance(request, AgentWorkerRequest):
            raise AgentWorkerContractError(
                "request must be an AgentWorkerRequest"
            )

        if not isinstance(outcome, AgentWorkerOutcome):
            raise AgentWorkerContractError(
                "outcome must be an AgentWorkerOutcome"
            )

        normalized_error_code = (
            _require_text(error_code, "error_code")
            if error_code is not None
            else None
        )
        normalized_error_message = (
            _require_text(error_message, "error_message")
            if error_message is not None
            else None
        )

        if outcome == AgentWorkerOutcome.SUCCESS:
            if (
                normalized_error_code is not None
                or normalized_error_message is not None
            ):
                raise AgentWorkerContractError(
                    "successful results cannot contain error details"
                )
        elif (
            normalized_error_code is None
            or normalized_error_message is None
        ):
            raise AgentWorkerContractError(
                "non-success results require error_code and error_message"
            )

        normalized_output = {} if output is None else output

        return cls(
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            workflow_id=request.workflow_id,
            work_item_id=request.work_item_id,
            worker_id=request.worker_id,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            outcome=outcome,
            executed_at=_require_aware_datetime(
                executed_at, "executed_at"
            ),
            output_json=_canonical_payload(
                normalized_output, "output"
            ),
            error_code=normalized_error_code,
            error_message=normalized_error_message,
        )

    @property
    def output(self) -> dict[str, Any]:
        return json.loads(self.output_json)

    def validate_against(
        self,
        request: AgentWorkerRequest,
    ) -> None:
        """Reject results that do not correspond to the issued request."""

        if not isinstance(request, AgentWorkerRequest):
            raise AgentWorkerContractError(
                "request must be an AgentWorkerRequest"
            )

        expected = (
            request.request_id,
            request.tenant_id,
            request.workflow_id,
            request.work_item_id,
            request.worker_id,
            request.correlation_id,
            request.idempotency_key,
        )

        actual = (
            self.request_id,
            self.tenant_id,
            self.workflow_id,
            self.work_item_id,
            self.worker_id,
            self.correlation_id,
            self.idempotency_key,
        )

        if actual != expected:
            raise AgentWorkerContractError(
                "worker result context does not match its request"
            )


class AgentWorker(Protocol):
    """Interface implemented by bounded worker adapters."""

    def execute(
        self,
        request: AgentWorkerRequest,
    ) -> AgentWorkerResult:
        """Execute the assigned task and return a structured result."""
        ...