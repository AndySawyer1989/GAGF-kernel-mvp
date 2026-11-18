from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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