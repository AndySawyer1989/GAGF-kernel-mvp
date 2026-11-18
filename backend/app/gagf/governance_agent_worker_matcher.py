from __future__ import annotations

from backend.app.gagf.governance_agent_worker_registry_contract import (
    AgentWorkerMatchError,
    AgentWorkerMatchRejection,
    AgentWorkerMatchResult,
    AgentWorkerRegistryError,
)
from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)


class AgentWorkerMatcher:
    """Deterministically selects a registered worker for a task."""

    def __init__(
        self,
        registry_store: AgentWorkerRegistryStore,
    ) -> None:
        if not isinstance(registry_store, AgentWorkerRegistryStore):
            raise AgentWorkerMatchError(
                "registry_store must be an AgentWorkerRegistryStore"
            )

        self.registry_store = registry_store

    def match(
        self,
        *,
        tenant_id: str,
        task_type: str,
        required_capabilities: tuple[str, ...] = (),
    ) -> AgentWorkerMatchResult:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise AgentWorkerMatchError(
                "tenant_id must be a non-empty string"
            )

        if not isinstance(task_type, str) or not task_type.strip():
            raise AgentWorkerMatchError(
                "task_type must be a non-empty string"
            )

        if isinstance(required_capabilities, (str, bytes)):
            raise AgentWorkerMatchError(
                "required_capabilities must be a collection of strings"
            )

        try:
            supplied_capabilities = tuple(required_capabilities)
        except TypeError as exc:
            raise AgentWorkerMatchError(
                "required_capabilities must be an iterable of strings"
            ) from exc

        if any(
            not isinstance(capability, str)
            or not capability.strip()
            for capability in supplied_capabilities
        ):
            raise AgentWorkerMatchError(
                "required_capabilities must contain non-empty strings"
            )

        required = tuple(
            sorted(
                {
                    capability.strip()
                    for capability in supplied_capabilities
                }
            )
        )

        normalized_tenant_id = tenant_id.strip()
        normalized_task_type = task_type.strip()

        try:
            registrations = self.registry_store.list_workers(
                tenant_id=normalized_tenant_id,
                include_disabled=True,
            )
        except AgentWorkerRegistryError:
            raise

        eligible = []
        rejections = []

        for registration in registrations:
            reasons = []

            if not registration.enabled:
                reasons.append("worker_disabled")

            if normalized_task_type not in registration.supported_task_types:
                reasons.append("unsupported_task_type")

            missing_capabilities = sorted(
                set(required) - set(registration.capabilities)
            )

            if missing_capabilities:
                reasons.append(
                    "missing_capabilities:"
                    + ",".join(missing_capabilities)
                )

            if reasons:
                rejections.append(
                    AgentWorkerMatchRejection(
                        worker_id=registration.worker_id,
                        registration_revision=(
                            registration.registration_revision
                        ),
                        reasons=tuple(reasons),
                    )
                )
            else:
                eligible.append(registration)

        selected = None

        if eligible:
            selected = min(
                eligible,
                key=lambda registration: registration.worker_id,
            )

            for registration in eligible:
                if registration.worker_id != selected.worker_id:
                    rejections.append(
                        AgentWorkerMatchRejection(
                            worker_id=registration.worker_id,
                            registration_revision=(
                                registration.registration_revision
                            ),
                            reasons=("deterministic_tie_break",),
                        )
                    )

        rejections.sort(key=lambda item: item.worker_id)

        return AgentWorkerMatchResult(
            tenant_id=normalized_tenant_id,
            task_type=normalized_task_type,
            required_capabilities=required,
            selected_worker=selected,
            rejections=tuple(rejections),
            registered_worker_count=len(registrations),
        )