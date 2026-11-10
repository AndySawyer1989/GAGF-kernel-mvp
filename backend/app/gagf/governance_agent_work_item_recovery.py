from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_agent_workflow_contract import (
    WorkItemState,
    WorkflowState,
    validate_work_item_transition,
)


class AgentWorkItemRecoveryMixin:
    """
    Deterministic lease recovery and retry promotion.

    This mixin persists lifecycle transitions only. It does not execute
    workers, select workers, apply probabilistic retry decisions, or
    replace the deterministic GAGF Kernel.
    """

    def list_expired_work_items(
        self,
        *,
        tenant_id: str,
        now: datetime | None = None,
        limit: int = 100,
    ):
        from backend.app.gagf.governance_agent_work_item_store import (
            AgentWorkItemStoreError,
            _datetime_text,
            _normalize_datetime,
            _require_text,
            _utc_now,
        )

        tenant_id = _require_text(tenant_id, "tenant_id")

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise AgentWorkItemStoreError(
                "limit must be a positive integer"
            )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )

        connection = self._connect()

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM gagf_agent_work_items
                WHERE tenant_id = ?
                  AND state IN (?, ?)
                  AND lease_expires_at IS NOT NULL
                  AND lease_expires_at <= ?
                ORDER BY lease_expires_at ASC, created_at ASC,
                         work_item_id ASC
                LIMIT ?
                """,
                (
                    tenant_id,
                    WorkItemState.CLAIMED.value,
                    WorkItemState.RUNNING.value,
                    _datetime_text(current_time),
                    limit,
                ),
            ).fetchall()

            return [self._record(row) for row in rows]

        finally:
            connection.close()

    def recover_expired_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        idempotency_key: str,
        now: datetime | None = None,
    ):
        from backend.app.gagf.governance_agent_work_item_store import (
            AgentWorkItemConflictError,
            AgentWorkItemStoreError,
            _datetime_text,
            _normalize_datetime,
            _request_hash,
            _require_text,
            _utc_now,
        )

        tenant_id = _require_text(tenant_id, "tenant_id")
        work_item_id = _require_text(work_item_id, "work_item_id")
        idempotency_key = _require_text(
            idempotency_key,
            "idempotency_key",
        )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )

        # The operation identity deliberately excludes the wall-clock
        # timestamp. A replay remains the same request as time advances.
        request = {
            "operation": "recover_expired_work_item",
            "tenant_id": tenant_id,
            "work_item_id": work_item_id,
        }
        digest = _request_hash(request)

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = self._existing_request(
                connection,
                tenant_id=tenant_id,
                idempotency_key=idempotency_key,
                request_hash=digest,
            )

            if existing is not None:
                record = self._get_record(
                    connection,
                    tenant_id=tenant_id,
                    work_item_id=work_item_id,
                )
                connection.commit()
                return record

            record = self._get_record(
                connection,
                tenant_id=tenant_id,
                work_item_id=work_item_id,
            )

            workflow_state, _ = self._workflow_context(
                connection,
                tenant_id=tenant_id,
                workflow_id=record.workflow_id,
            )

            if workflow_state is not WorkflowState.ACTIVE:
                raise AgentWorkItemConflictError(
                    "Expired work items can only be recovered while "
                    "the parent workflow is ACTIVE"
                )

            if record.state not in {
                WorkItemState.CLAIMED,
                WorkItemState.RUNNING,
            }:
                raise AgentWorkItemConflictError(
                    "Only CLAIMED or RUNNING work items can be recovered"
                )

            if (
                record.lease_expires_at is None
                or record.lease_expires_at > current_time
            ):
                raise AgentWorkItemConflictError(
                    "Work-item lease has not expired"
                )

            exhausted = record.attempt_count >= record.max_attempts

            if exhausted:
                target_state = WorkItemState.FAILED
                error_code = "LEASE_EXPIRED_MAX_ATTEMPTS"
                error_message = (
                    "The work-item lease expired after the maximum "
                    "number of attempts was reached."
                )
            elif record.state is WorkItemState.CLAIMED:
                target_state = WorkItemState.PENDING
                error_code = None
                error_message = None
            else:
                target_state = WorkItemState.RETRY_WAIT
                error_code = "LEASE_EXPIRED"
                error_message = (
                    "The running worker lease expired; the work item "
                    "is waiting for explicit retry promotion."
                )

            validate_work_item_transition(
                record.state,
                target_state,
            )

            updated = replace(
                record,
                state=target_state,
                updated_at=current_time,
                available_at=(
                    current_time
                    if target_state is WorkItemState.RETRY_WAIT
                    else record.available_at
                ),
                assigned_worker_id=None,
                lease_expires_at=None,
                # Fencing tokens are preserved. The next claim increments
                # this value, invalidating the previous worker's token.
                fencing_token=record.fencing_token,
                last_error_code=error_code,
                last_error_message=error_message,
            )

            update_cursor = connection.execute(
                """
                UPDATE gagf_agent_work_items
                SET state = ?,
                    updated_at = ?,
                    available_at = ?,
                    assigned_worker_id = NULL,
                    lease_expires_at = NULL,
                    last_error_code = ?,
                    last_error_message = ?
                WHERE tenant_id = ?
                  AND work_item_id = ?
                  AND state = ?
                  AND fencing_token = ?
                  AND lease_expires_at IS NOT NULL
                  AND lease_expires_at <= ?
                """,
                (
                    updated.state.value,
                    _datetime_text(updated.updated_at),
                    _datetime_text(updated.available_at),
                    updated.last_error_code,
                    updated.last_error_message,
                    tenant_id,
                    work_item_id,
                    record.state.value,
                    record.fencing_token,
                    _datetime_text(current_time),
                ),
            )

            if update_cursor.rowcount != 1:
                raise AgentWorkItemConflictError(
                    "Work item changed before recovery could be persisted"
                )

            self._insert_event(
                connection,
                record=updated,
                event_type="work_item.lease_recovered",
                idempotency_key=idempotency_key,
                request_hash=digest,
                payload={
                    "previous_state": record.state.value,
                    "resulting_state": target_state.value,
                    "attempt_count": record.attempt_count,
                    "max_attempts": record.max_attempts,
                    "worker_id": record.assigned_worker_id,
                    "expired_lease_at": _datetime_text(
                        record.lease_expires_at
                    ),
                    "fencing_token": record.fencing_token,
                    "attempts_exhausted": exhausted,
                    "error_code": error_code,
                },
                occurred_at=current_time,
            )

            connection.commit()
            return updated

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def promote_due_retry_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        idempotency_key: str,
        now: datetime | None = None,
    ):
        from backend.app.gagf.governance_agent_work_item_store import (
            AgentWorkItemConflictError,
            _datetime_text,
            _normalize_datetime,
            _request_hash,
            _require_text,
            _utc_now,
        )

        tenant_id = _require_text(tenant_id, "tenant_id")
        work_item_id = _require_text(work_item_id, "work_item_id")
        idempotency_key = _require_text(
            idempotency_key,
            "idempotency_key",
        )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )

        request = {
            "operation": "promote_due_retry_work_item",
            "tenant_id": tenant_id,
            "work_item_id": work_item_id,
        }
        digest = _request_hash(request)

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = self._existing_request(
                connection,
                tenant_id=tenant_id,
                idempotency_key=idempotency_key,
                request_hash=digest,
            )

            if existing is not None:
                record = self._get_record(
                    connection,
                    tenant_id=tenant_id,
                    work_item_id=work_item_id,
                )
                connection.commit()
                return record

            record = self._get_record(
                connection,
                tenant_id=tenant_id,
                work_item_id=work_item_id,
            )

            workflow_state, _ = self._workflow_context(
                connection,
                tenant_id=tenant_id,
                workflow_id=record.workflow_id,
            )

            if workflow_state is not WorkflowState.ACTIVE:
                raise AgentWorkItemConflictError(
                    "Retry promotion requires an ACTIVE parent workflow"
                )

            if record.state is not WorkItemState.RETRY_WAIT:
                raise AgentWorkItemConflictError(
                    "Only RETRY_WAIT work items can be promoted"
                )

            if record.available_at > current_time:
                raise AgentWorkItemConflictError(
                    "Retry is not yet due"
                )

            if record.attempt_count >= record.max_attempts:
                raise AgentWorkItemConflictError(
                    "Work item has exhausted its attempt limit"
                )

            validate_work_item_transition(
                WorkItemState.RETRY_WAIT,
                WorkItemState.PENDING,
            )

            updated = replace(
                record,
                state=WorkItemState.PENDING,
                updated_at=current_time,
                assigned_worker_id=None,
                lease_expires_at=None,
                # Preserve the prior attempt's error for audit. A successful
                # subsequent claim clears the error using existing behavior.
                fencing_token=record.fencing_token,
            )

            update_cursor = connection.execute(
                """
                UPDATE gagf_agent_work_items
                SET state = ?,
                    updated_at = ?,
                    assigned_worker_id = NULL,
                    lease_expires_at = NULL
                WHERE tenant_id = ?
                  AND work_item_id = ?
                  AND state = ?
                  AND available_at <= ?
                  AND fencing_token = ?
                """,
                (
                    updated.state.value,
                    _datetime_text(updated.updated_at),
                    tenant_id,
                    work_item_id,
                    WorkItemState.RETRY_WAIT.value,
                    _datetime_text(current_time),
                    record.fencing_token,
                ),
            )

            if update_cursor.rowcount != 1:
                raise AgentWorkItemConflictError(
                    "Retry changed before promotion could be persisted"
                )

            self._insert_event(
                connection,
                record=updated,
                event_type="work_item.retry_promoted",
                idempotency_key=idempotency_key,
                request_hash=digest,
                payload={
                    "attempt_count": record.attempt_count,
                    "max_attempts": record.max_attempts,
                    "available_at": _datetime_text(record.available_at),
                    "fencing_token": record.fencing_token,
                },
                occurred_at=current_time,
            )

            connection.commit()
            return updated

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()