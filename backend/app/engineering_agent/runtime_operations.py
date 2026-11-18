from __future__ import annotations

import logging
from datetime import datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from backend.app.gagf.governance_agent_runtime_coordinator import (
    GovernanceAgentRuntimeCoordinationResult,
    GovernanceAgentRuntimeCoordinator,
)

from .tracing import child_trace_context


class RuntimeOperationsService:
    """Observable application service for bounded runtime coordination."""

    def __init__(
        self,
        *,
        runtime_coordinator: GovernanceAgentRuntimeCoordinator,
        logger: logging.Logger | None = None,
    ) -> None:
        if not isinstance(
            runtime_coordinator,
            GovernanceAgentRuntimeCoordinator,
        ):
            raise TypeError(
                "runtime_coordinator must be a "
                "GovernanceAgentRuntimeCoordinator"
            )

        self._runtime_coordinator = runtime_coordinator
        self._logger = logger or logging.getLogger("engineering_agent")

    def dispatch_workflow(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        dispatch_cycle_id: str,
        lease_seconds: int = 300,
        max_candidates: int = 100,
        max_claims: int = 10,
        now: datetime | None = None,
    ) -> GovernanceAgentRuntimeCoordinationResult:
        operation_id = uuid4().hex
        started_at = perf_counter()

        with child_trace_context():
            base_metadata = {
                "operation_id": operation_id,
                "workflow_id": workflow_id,
                "dispatch_cycle_id": dispatch_cycle_id,
            }

            self._logger.info(
                "Runtime operation started",
                extra={
                    "event": "runtime_operation_started",
                    **base_metadata,
                },
            )

            try:
                result = self._runtime_coordinator.dispatch_workflow(
                    tenant_id=tenant_id,
                    workflow_id=workflow_id,
                    dispatch_cycle_id=dispatch_cycle_id,
                    lease_seconds=lease_seconds,
                    max_candidates=max_candidates,
                    max_claims=max_claims,
                    now=now,
                )

                if not isinstance(
                    result,
                    GovernanceAgentRuntimeCoordinationResult,
                ):
                    raise TypeError(
                        "Runtime coordinator returned an invalid result"
                    )

                duration_ms = round(
                    (perf_counter() - started_at) * 1000,
                    3,
                )
                dispatch_result = result.dispatch_result

                metadata: dict[str, Any] = {
                    **base_metadata,
                    "dispatch_performed": dispatch_result is not None,
                    "duration_ms": duration_ms,
                }

                if dispatch_result is not None:
                    metadata.update(
                        {
                            "candidate_count": dispatch_result.candidate_count,
                            "scanned_count": dispatch_result.scanned_count,
                            "claimed_count": dispatch_result.claimed_count,
                            "candidate_limit": dispatch_result.candidate_limit,
                            "claim_limit": dispatch_result.claim_limit,
                        }
                    )

                self._logger.info(
                    "Runtime operation completed",
                    extra={
                        "event": "runtime_operation_completed",
                        **metadata,
                    },
                )

                return result

            except Exception:
                duration_ms = round(
                    (perf_counter() - started_at) * 1000,
                    3,
                )

                self._logger.exception(
                    "Runtime operation failed",
                    extra={
                        "event": "runtime_operation_failed",
                        **base_metadata,
                        "duration_ms": duration_ms,
                    },
                )
                raise