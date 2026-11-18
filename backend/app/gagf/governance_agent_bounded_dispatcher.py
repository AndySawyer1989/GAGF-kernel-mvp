from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_agent_task_capability_policy import (
    AgentTaskCapabilityPolicy,
    AgentTaskCapabilityPolicyError,
)
from backend.app.gagf.governance_agent_work_item_contract import (
    AgentWorkItemRecord,
)
from backend.app.gagf.governance_agent_work_item_store import (
    AgentWorkItemConflictError,
    AgentWorkItemStore,
    AgentWorkItemStoreError,
    _normalize_datetime,
    _require_text,
    _utc_now,
)
from backend.app.gagf.governance_agent_worker_matcher import (
    AgentWorkerMatcher,
)


@dataclass(frozen=True)
class AgentWorkItemDispatchOutcome:
    work_item_id: str
    status: str
    reason_codes: tuple[str, ...] = ()
    worker_id: str | None = None
    registration_revision: int | None = None
    record: AgentWorkItemRecord | None = None


@dataclass(frozen=True)
class BoundedDispatchResult:
    tenant_id: str
    workflow_id: str
    dispatch_cycle_id: str
    dispatched_at: datetime
    candidate_limit: int
    claim_limit: int
    candidate_count: int
    scanned_count: int
    claimed_count: int
    outcomes: tuple[AgentWorkItemDispatchOutcome, ...]


class AgentBoundedDispatcher:
    """Bounded coordinator that matches and claims work without executing it."""

    def __init__(
        self,
        *,
        work_item_store: AgentWorkItemStore,
        worker_matcher: AgentWorkerMatcher,
    ) -> None:
        if not isinstance(work_item_store, AgentWorkItemStore):
            raise AgentWorkItemStoreError(
                "work_item_store must be an AgentWorkItemStore"
            )

        if not isinstance(worker_matcher, AgentWorkerMatcher):
            raise AgentWorkItemStoreError(
                "worker_matcher must be an AgentWorkerMatcher"
            )

        self.work_item_store = work_item_store
        self.worker_matcher = worker_matcher

    @staticmethod
    def _claim_idempotency_key(
        *,
        tenant_id: str,
        workflow_id: str,
        dispatch_cycle_id: str,
        work_item_id: str,
        worker_id: str,
        registration_revision: int,
    ) -> str:
        payload = {
            "operation": "bounded_dispatch_claim",
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "dispatch_cycle_id": dispatch_cycle_id,
            "work_item_id": work_item_id,
            "worker_id": worker_id,
            "registration_revision": registration_revision,
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return f"dispatch:{digest}"

    def dispatch(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        dispatch_cycle_id: str,
        task_capability_policy: AgentTaskCapabilityPolicy,
        lease_seconds: int = 300,
        max_candidates: int = 100,
        max_claims: int = 10,
        now: datetime | None = None,
    ) -> BoundedDispatchResult:
        tenant_id = _require_text(tenant_id, "tenant_id")
        workflow_id = _require_text(workflow_id, "workflow_id")
        dispatch_cycle_id = _require_text(
            dispatch_cycle_id,
            "dispatch_cycle_id",
        )

        for name, value, maximum in (
            ("max_candidates", max_candidates, 500),
            ("max_claims", max_claims, 500),
            ("lease_seconds", lease_seconds, None),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
                or (maximum is not None and value > maximum)
            ):
                if maximum is None:
                    message = f"{name} must be a positive integer"
                else:
                    message = (
                        f"{name} must be an integer between 1 and {maximum}"
                    )
                raise AgentWorkItemStoreError(message)

        if max_claims > max_candidates:
            raise AgentWorkItemStoreError(
                "max_claims cannot exceed max_candidates"
            )

        if not isinstance(task_capability_policy, AgentTaskCapabilityPolicy):
            raise AgentWorkItemStoreError(
                "task_capability_policy must be an AgentTaskCapabilityPolicy"
            )

        try:
            task_capability_policy.validate()
        except AgentTaskCapabilityPolicyError as exc:
            raise AgentWorkItemStoreError(
                f"Invalid task capability policy: {exc}"
            ) from exc

        dispatch_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )

        candidates = self.work_item_store.list_ready_work_items(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            now=dispatch_time,
            limit=max_candidates,
        )

        for candidate in candidates:
            if (
                candidate.tenant_id != tenant_id
                or candidate.workflow_id != workflow_id
            ):
                raise AgentWorkItemStoreError(
                    "Ready-item query returned a candidate outside "
                    "the requested tenant/workflow scope"
                )

        outcomes: list[AgentWorkItemDispatchOutcome] = []
        claimed_count = 0
        scanned_count = 0

        for candidate in candidates:
            if claimed_count >= max_claims:
                break

            scanned_count += 1

            try:
                required_capabilities = (
                    task_capability_policy.get_required_capabilities(
                        candidate.task_type
                    )
                )
            except AgentTaskCapabilityPolicyError as exc:
                raise AgentWorkItemStoreError(
                    f"Candidate has an unrecognized task type: {exc}"
                ) from exc

            if required_capabilities is None:
                outcomes.append(
                    AgentWorkItemDispatchOutcome(
                        work_item_id=candidate.work_item_id,
                        status="rejected",
                        reason_codes=("missing_capability_policy",),
                    )
                )
                continue

            match = self.worker_matcher.match(
                tenant_id=tenant_id,
                task_type=candidate.task_type,
                required_capabilities=required_capabilities,
            )

            worker = match.selected_worker

            if worker is None:
                reason_codes = ["no_eligible_worker"]

                for rejection in match.rejections:
                    for reason in rejection.reasons:
                        reason_codes.append(
                            f"{rejection.worker_id}:{reason}"
                        )

                outcomes.append(
                    AgentWorkItemDispatchOutcome(
                        work_item_id=candidate.work_item_id,
                        status="unmatched",
                        reason_codes=tuple(sorted(set(reason_codes))),
                    )
                )
                continue

            idempotency_key = self._claim_idempotency_key(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                dispatch_cycle_id=dispatch_cycle_id,
                work_item_id=candidate.work_item_id,
                worker_id=worker.worker_id,
                registration_revision=worker.registration_revision,
            )

            try:
                claimed = self.work_item_store.claim_registered_work_item(
                    tenant_id=tenant_id,
                    work_item_id=candidate.work_item_id,
                    worker_id=worker.worker_id,
                    expected_registration_revision=(
                        worker.registration_revision
                    ),
                    required_capabilities=match.required_capabilities,
                    lease_seconds=lease_seconds,
                    idempotency_key=idempotency_key,
                    now=dispatch_time,
                )

            except AgentWorkItemConflictError as exc:
                outcomes.append(
                    AgentWorkItemDispatchOutcome(
                        work_item_id=candidate.work_item_id,
                        status="rejected",
                        reason_codes=(f"claim_conflict:{str(exc)}",),
                        worker_id=worker.worker_id,
                        registration_revision=(
                            worker.registration_revision
                        ),
                    )
                )
                continue

            claimed_count += 1

            outcomes.append(
                AgentWorkItemDispatchOutcome(
                    work_item_id=candidate.work_item_id,
                    status="claimed",
                    worker_id=worker.worker_id,
                    registration_revision=(
                        worker.registration_revision
                    ),
                    record=claimed,
                )
            )

        return BoundedDispatchResult(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            dispatch_cycle_id=dispatch_cycle_id,
            dispatched_at=dispatch_time,
            candidate_limit=max_candidates,
            claim_limit=max_claims,
            candidate_count=len(candidates),
            scanned_count=scanned_count,
            claimed_count=claimed_count,
            outcomes=tuple(outcomes),
        )