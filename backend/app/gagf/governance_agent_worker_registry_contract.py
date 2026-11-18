from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


WORKER_REGISTRY_CONTRACT_ID = "gagf-agent-worker-registry-contract"
WORKER_REGISTRY_CONTRACT_VERSION = "0.1.0"
WORKER_REGISTRY_SCHEMA_VERSION = 1


class AgentWorkerRegistryError(Exception):
    """Base exception for worker registry failures."""


class AgentWorkerRegistrationNotFoundError(AgentWorkerRegistryError):
    """Raised when a worker registration is not found for a tenant."""


class AgentWorkerRegistrationConflictError(AgentWorkerRegistryError):
    """Raised when a worker registration conflicts with existing data."""


class AgentWorkerRegistrationIntegrityError(AgentWorkerRegistryError):
    """Raised when persisted worker registration data fails validation."""


class AgentWorkerMatchError(AgentWorkerRegistryError):
    """Raised when worker matching input is invalid."""


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkerRegistryError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _normalize_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AgentWorkerRegistryError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AgentWorkerRegistryError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _normalize_string_collection(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise AgentWorkerRegistryError(
            f"{field_name} must be a collection of strings"
        )

    try:
        normalized = tuple(
            sorted(
                {
                    _require_text(value, field_name)
                    for value in values
                }
            )
        )
    except TypeError as exc:
        raise AgentWorkerRegistryError(
            f"{field_name} must be an iterable of strings"
        ) from exc

    return normalized


@dataclass(frozen=True, slots=True)
class AgentWorkerRegistration:
    """Current tenant-scoped registration for one worker."""

    tenant_id: str
    worker_id: str
    worker_type: str
    version: str
    supported_task_types: tuple[str, ...]
    capabilities: tuple[str, ...]
    enabled: bool
    registration_revision: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "worker_id",
            "worker_type",
            "version",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        object.__setattr__(
            self,
            "supported_task_types",
            _normalize_string_collection(
                self.supported_task_types,
                "supported_task_types",
            ),
        )

        object.__setattr__(
            self,
            "capabilities",
            _normalize_string_collection(
                self.capabilities,
                "capabilities",
            ),
        )

        if not self.supported_task_types:
            raise AgentWorkerRegistryError(
                "supported_task_types must not be empty"
            )

        if not isinstance(self.enabled, bool):
            raise AgentWorkerRegistryError(
                "enabled must be a boolean"
            )

        if (
            isinstance(self.registration_revision, bool)
            or not isinstance(self.registration_revision, int)
            or self.registration_revision < 1
        ):
            raise AgentWorkerRegistryError(
                "registration_revision must be a positive integer"
            )

        object.__setattr__(
            self,
            "created_at",
            _normalize_datetime(self.created_at, "created_at"),
        )

        object.__setattr__(
            self,
            "updated_at",
            _normalize_datetime(self.updated_at, "updated_at"),
        )

        if self.updated_at < self.created_at:
            raise AgentWorkerRegistryError(
                "updated_at must not precede created_at"
            )


@dataclass(frozen=True, slots=True)
class AgentWorkerMatchRejection:
    """Explainable reason a registered worker was not selected."""

    worker_id: str
    registration_revision: int
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "worker_id",
            _require_text(self.worker_id, "worker_id"),
        )

        if (
            isinstance(self.registration_revision, bool)
            or not isinstance(self.registration_revision, int)
            or self.registration_revision < 1
        ):
            raise AgentWorkerMatchError(
                "registration_revision must be a positive integer"
            )

        normalized_reasons = _normalize_string_collection(
            self.reasons,
            "reasons",
        )

        if not normalized_reasons:
            raise AgentWorkerMatchError(
                "reasons must not be empty"
            )

        object.__setattr__(
            self,
            "reasons",
            normalized_reasons,
        )


@dataclass(frozen=True, slots=True)
class AgentWorkerMatchResult:
    """Deterministic worker selection and its explainable outcome."""

    tenant_id: str
    task_type: str
    required_capabilities: tuple[str, ...]
    selected_worker: AgentWorkerRegistration | None
    rejections: tuple[AgentWorkerMatchRejection, ...]
    registered_worker_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _require_text(self.tenant_id, "tenant_id"),
        )

        object.__setattr__(
            self,
            "task_type",
            _require_text(self.task_type, "task_type"),
        )

        object.__setattr__(
            self,
            "required_capabilities",
            _normalize_string_collection(
                self.required_capabilities,
                "required_capabilities",
            ),
        )

        if self.selected_worker is not None:
            if not isinstance(
                self.selected_worker,
                AgentWorkerRegistration,
            ):
                raise AgentWorkerMatchError(
                    "selected_worker must be an AgentWorkerRegistration"
                )

            if self.selected_worker.tenant_id != self.tenant_id:
                raise AgentWorkerMatchError(
                    "selected worker tenant does not match match result"
                )

        normalized_rejections = tuple(self.rejections)

        if any(
            not isinstance(item, AgentWorkerMatchRejection)
            for item in normalized_rejections
        ):
            raise AgentWorkerMatchError(
                "rejections must contain AgentWorkerMatchRejection records"
            )

        if (
            isinstance(self.registered_worker_count, bool)
            or not isinstance(self.registered_worker_count, int)
            or self.registered_worker_count < 0
        ):
            raise AgentWorkerMatchError(
                "registered_worker_count must be a non-negative integer"
            )

        if self.selected_worker is not None:
            if self.selected_worker.worker_id in {
                item.worker_id for item in normalized_rejections
            }:
                raise AgentWorkerMatchError(
                    "selected worker cannot also be rejected"
                )

        object.__setattr__(
            self,
            "rejections",
            normalized_rejections,
        )

    @property
    def matched(self) -> bool:
        return self.selected_worker is not None

    @property
    def selected_worker_id(self) -> str | None:
        if self.selected_worker is None:
            return None

        return self.selected_worker.worker_id

    @property
    def selected_registration_revision(self) -> int | None:
        if self.selected_worker is None:
            return None

        return self.selected_worker.registration_revision