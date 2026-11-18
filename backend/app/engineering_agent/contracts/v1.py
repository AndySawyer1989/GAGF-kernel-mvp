from __future__ import annotations

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator, model_validator


class ContractModel(BaseModel):
    """Base model for versioned Engineering Agent contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class HealthResponse(ContractModel):
    """Health endpoint response."""

    status: Literal["healthy"]
    application: Literal["engineering-agent"]
    version: str


class ApplicationStatusResponse(ContractModel):
    """Application initialization and authority status."""

    application: Literal["engineering-agent"]
    version: str
    api_version: Literal["v1"]

    initialized: bool
    execution_enabled: bool
    workspace_manager_initialized: bool
    approval_service_initialized: bool


class ErrorDetail(ContractModel):
    """Structured service error."""

    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1000)


class ErrorResponse(ContractModel):
    """Standardized API error envelope."""

    error: ErrorDetail
    request_id: str | None = None

class RuntimeDispatchRequest(ContractModel):
    """Strict request contract for bounded workflow dispatch."""

    dispatch_cycle_id: StrictStr = Field(min_length=1, max_length=128)
    lease_seconds: StrictInt = Field(default=300, ge=1, le=86400)
    max_candidates: StrictInt = Field(default=100, ge=1, le=500)
    max_claims: StrictInt = Field(default=10, ge=1, le=500)

    @field_validator("dispatch_cycle_id")
    @classmethod
    def validate_dispatch_cycle_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("dispatch_cycle_id must not be blank")
        return value

    @model_validator(mode="after")
    def validate_claim_limit(self) -> "RuntimeDispatchRequest":
        if self.max_claims > self.max_candidates:
            raise ValueError("max_claims cannot exceed max_candidates")
        return self


class RuntimeRoutingDecisionResponse(ContractModel):
    """Public, tenant-redacted workflow routing decision."""

    workflow_id: str
    workflow_type: str
    current_state: Literal[
        "created",
        "active",
        "awaiting_approval",
        "completed",
        "failed",
        "cancelled",
    ]
    action: Literal[
        "prepare_activation",
        "coordinate_work",
        "wait_for_human_approval",
        "terminal_completed",
        "terminal_failed",
        "terminal_cancelled",
    ]
    allowed_transitions: tuple[
        Literal[
            "created",
            "active",
            "awaiting_approval",
            "completed",
            "failed",
            "cancelled",
        ],
        ...,
    ]
    requires_human_approval: bool
    terminal: bool
    reason: str


class RuntimeDispatchOutcomeResponse(ContractModel):
    """Sanitized outcome for one work item; never includes its record payload."""

    work_item_id: str
    status: Literal["claimed", "unmatched", "rejected"]
    reason_codes: tuple[
        Literal[
            "no_eligible_worker",
            "missing_capability_policy",
            "claim_conflict",
            "rejected",
        ],
        ...,
    ] = ()


class RuntimeBoundedDispatchResponse(ContractModel):
    """Summary of bounded claims; this does not represent worker execution."""

    dispatch_cycle_id: str
    dispatched_at: datetime
    candidate_limit: StrictInt
    claim_limit: StrictInt
    candidate_count: StrictInt
    scanned_count: StrictInt
    claimed_count: StrictInt
    outcomes: tuple[RuntimeDispatchOutcomeResponse, ...]


class RuntimeDispatchResponse(ContractModel):
    """Versioned response separating routing from bounded dispatch."""

    routing_decision: RuntimeRoutingDecisionResponse
    dispatch_performed: bool
    dispatch_result: RuntimeBoundedDispatchResponse | None = None

    @model_validator(mode="after")
    def validate_dispatch_consistency(self) -> "RuntimeDispatchResponse":
        if self.dispatch_performed != (self.dispatch_result is not None):
            raise ValueError(
                "dispatch_performed must match dispatch_result presence"
            )
        return self
