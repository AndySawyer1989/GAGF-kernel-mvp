from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import uuid

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_agent_workflow_contract import (
    AgentWorkflowEvent,
    WorkItemState,
    WorkflowState,
    validate_work_item_transition,
)

from backend.app.gagf.governance_agent_work_item_recovery import AgentWorkItemRecoveryMixin

from backend.app.gagf.governance_agent_work_item_contract import (
    AgentWorkItemContractError,
    AgentWorkItemRecord,
)

from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)


WORK_ITEM_STORE_VERSION = "0.1.0"


class AgentWorkItemStoreError(RuntimeError):
    """Base exception for durable work-item store failures."""


class AgentWorkItemNotFoundError(AgentWorkItemStoreError):
    """Raised when a tenant-scoped work item does not exist."""


class AgentWorkItemConflictError(AgentWorkItemStoreError):
    """Raised when an operation conflicts with persisted state."""


class AgentWorkItemIntegrityError(AgentWorkItemStoreError):
    """Raised when persisted work-item or event integrity fails."""


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkItemStoreError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise AgentWorkItemStoreError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AgentWorkItemStoreError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _datetime_text(value: datetime) -> str:
    return _normalize_datetime(value, "timestamp").isoformat()


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AgentWorkItemIntegrityError(
            "Persisted timestamp is invalid"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AgentWorkItemIntegrityError(
            "Persisted timestamp is not timezone-aware"
        )

    return parsed.astimezone(timezone.utc)


def _canonical_json(value: Mapping[str, Any]) -> str:
    if not isinstance(value, Mapping):
        raise AgentWorkItemStoreError(
            "Input payload must be a mapping"
        )

    try:
        encoded = json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AgentWorkItemStoreError(
            "Input payload must contain valid JSON values"
        ) from exc

    return encoded


def _request_hash(payload: Mapping[str, Any]) -> str:
    encoded = _canonical_json(payload)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class AgentWorkItemStore(AgentWorkItemRecoveryMixin):
    """
    Tenant-scoped durable work-item persistence.

    This store persists work-item lifecycle state. It does not execute workers,
    authorize actions, or replace the deterministic GAGF Kernel.

    Use the same file-backed SQLite database path as AgentWorkflowStore.
    """

    def __init__(
        self,
        database_path: str | Path,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise AgentWorkItemStoreError(
                "timeout_seconds must be a finite positive number"
            )

        self.database_path = str(database_path)
        self.timeout_seconds = float(timeout_seconds)

        if self.database_path == ":memory:":
            raise AgentWorkItemStoreError(
                "Use a file-backed SQLite database for the work-item store"
            )

        Path(self.database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}"
        )
        return connection

    def _initialize(self) -> None:
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_work_items (
                    tenant_id TEXT NOT NULL,
                    work_item_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    available_at TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    assigned_worker_id TEXT,
                    lease_expires_at TEXT,
                    fencing_token INTEGER NOT NULL,
                    last_error_code TEXT,
                    last_error_message TEXT,
                    PRIMARY KEY (tenant_id, work_item_id),
                    UNIQUE (tenant_id, workflow_id, work_item_id),
                    FOREIGN KEY (tenant_id, workflow_id)
                        REFERENCES gagf_agent_workflows (
                            tenant_id,
                            workflow_id
                        )
                        ON DELETE RESTRICT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_gagf_agent_work_items_dispatch
                ON gagf_agent_work_items (
                    tenant_id,
                    state,
                    available_at,
                    created_at
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_work_item_events (
                    event_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    work_item_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    causation_id TEXT,
                    idempotency_key TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    event_hash TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    UNIQUE (tenant_id, idempotency_key),
                    FOREIGN KEY (
                        tenant_id,
                        workflow_id,
                        work_item_id
                    )
                    REFERENCES gagf_agent_work_items (
                        tenant_id,
                        workflow_id,
                        work_item_id
                    )
                    ON DELETE RESTRICT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_gagf_agent_work_item_events_history
                ON gagf_agent_work_item_events (
                    tenant_id,
                    work_item_id,
                    occurred_at,
                    event_id
                )
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_work_item_events_no_update
                BEFORE UPDATE ON gagf_agent_work_item_events
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'work-item events are append-only'
                    );
                END
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_work_item_events_no_delete
                BEFORE DELETE ON gagf_agent_work_item_events
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'work-item events are append-only'
                    );
                END
                """
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def _record(
        self,
        row: sqlite3.Row,
    ) -> AgentWorkItemRecord:
        try:
            return AgentWorkItemRecord(
                work_item_id=row["work_item_id"],
                tenant_id=row["tenant_id"],
                workflow_id=row["workflow_id"],
                task_type=row["task_type"],
                state=WorkItemState(row["state"]),
                correlation_id=row["correlation_id"],
                idempotency_key=row["idempotency_key"],
                input_json=row["input_json"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
                available_at=_parse_datetime(row["available_at"]),
                attempt_count=row["attempt_count"],
                max_attempts=row["max_attempts"],
                assigned_worker_id=row["assigned_worker_id"],
                lease_expires_at=(
                    _parse_datetime(row["lease_expires_at"])
                    if row["lease_expires_at"]
                    else None
                ),
                fencing_token=row["fencing_token"],
                last_error_code=row["last_error_code"],
                last_error_message=row["last_error_message"],
            )
        except (
            AgentWorkItemContractError,
            ValueError,
            TypeError,
            KeyError,
        ) as exc:
            raise AgentWorkItemIntegrityError(
                "Persisted work-item record failed validation"
            ) from exc

    def _get_record(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> AgentWorkItemRecord:
        row = connection.execute(
            """
            SELECT *
            FROM gagf_agent_work_items
            WHERE tenant_id = ?
              AND work_item_id = ?
            """,
            (tenant_id, work_item_id),
        ).fetchone()

        if row is None:
            raise AgentWorkItemNotFoundError(
                "Work item was not found for this tenant"
            )

        return self._record(row)

    def _workflow_context(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        workflow_id: str,
    ) -> tuple[WorkflowState, str]:
        row = connection.execute(
            """
            SELECT state, correlation_id
            FROM gagf_agent_workflows
            WHERE tenant_id = ?
              AND workflow_id = ?
            """,
            (tenant_id, workflow_id),
        ).fetchone()

        if row is None:
            raise AgentWorkItemConflictError(
                "Parent workflow does not exist for this tenant"
            )

        try:
            return WorkflowState(row["state"]), row["correlation_id"]
        except ValueError as exc:
            raise AgentWorkItemIntegrityError(
                "Parent workflow has an invalid state"
            ) from exc

    def _existing_request(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        idempotency_key: str,
        request_hash: str,
    ) -> sqlite3.Row | None:
        row = connection.execute(
            """
            SELECT *
            FROM gagf_agent_work_item_events
            WHERE tenant_id = ?
              AND idempotency_key = ?
            """,
            (tenant_id, idempotency_key),
        ).fetchone()

        if row is None:
            return None

        # Never treat an idempotent replay as valid until the persisted event
        # envelope itself has passed its integrity check.
        self._event(row)

        if row["request_hash"] != request_hash:
            raise AgentWorkItemConflictError(
                "Idempotency key was reused with a different request"
            )

        return row

    def _insert_event(
        self,
        connection: sqlite3.Connection,
        *,
        record: AgentWorkItemRecord,
        event_type: str,
        idempotency_key: str,
        request_hash: str,
        payload: Mapping[str, Any],
        occurred_at: datetime,
        causation_id: str | None = None,
    ) -> AgentWorkflowEvent:
        event = AgentWorkflowEvent.create(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            tenant_id=record.tenant_id,
            workflow_id=record.workflow_id,
            work_item_id=record.work_item_id,
            correlation_id=record.correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            occurred_at=occurred_at,
            payload=payload,
        )

        connection.execute(
            """
            INSERT INTO gagf_agent_work_item_events (
                event_id,
                tenant_id,
                workflow_id,
                work_item_id,
                event_type,
                correlation_id,
                causation_id,
                idempotency_key,
                occurred_at,
                payload_json,
                schema_version,
                event_hash,
                request_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.tenant_id,
                event.workflow_id,
                event.work_item_id,
                event.event_type,
                event.correlation_id,
                event.causation_id,
                event.idempotency_key,
                _datetime_text(event.occurred_at),
                event.payload_json,
                event.schema_version,
                event.event_hash,
                request_hash,
            ),
        )

        return event

    def _event(self, row: sqlite3.Row) -> AgentWorkflowEvent:
        try:
            event = AgentWorkflowEvent(
                event_id=row["event_id"],
                tenant_id=row["tenant_id"],
                workflow_id=row["workflow_id"],
                work_item_id=row["work_item_id"],
                event_type=row["event_type"],
                correlation_id=row["correlation_id"],
                causation_id=row["causation_id"],
                idempotency_key=row["idempotency_key"],
                occurred_at=_parse_datetime(row["occurred_at"]),
                payload_json=row["payload_json"],
                schema_version=row["schema_version"],
                event_hash=row["event_hash"],
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise AgentWorkItemIntegrityError(
                "Persisted work-item event could not be reconstructed"
            ) from exc

        if not event.verify_integrity():
            raise AgentWorkItemIntegrityError(
                "Persisted work-item event failed integrity verification"
            )

        return event

    def create_work_item(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        work_item_id: str,
        task_type: str,
        idempotency_key: str,
        input_payload: Mapping[str, Any],
        max_attempts: int = 3,
        available_at: datetime | None = None,
        now: datetime | None = None,
    ) -> AgentWorkItemRecord:
        tenant_id = _require_text(tenant_id, "tenant_id")
        workflow_id = _require_text(workflow_id, "workflow_id")
        work_item_id = _require_text(work_item_id, "work_item_id")
        task_type = _require_text(task_type, "task_type")
        idempotency_key = _require_text(
            idempotency_key,
            "idempotency_key",
        )

        if (
            isinstance(max_attempts, bool)
            or not isinstance(max_attempts, int)
            or max_attempts < 1
        ):
            raise AgentWorkItemStoreError(
                "max_attempts must be an integer greater than zero"
            )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )
        ready_time = _normalize_datetime(
            available_at or current_time,
            "available_at",
        )
        input_json = _canonical_json(input_payload)

        request = {
            "operation": "create_work_item",
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "work_item_id": work_item_id,
            "task_type": task_type,
            "idempotency_key": idempotency_key,
            "input_json": input_json,
            "max_attempts": max_attempts,
            # The default ready time is derived from `now`; it is not an
            # explicit part of the caller's request and must not make an
            # otherwise exact replay conflict merely because time advanced.
            "available_at": (
                _datetime_text(ready_time)
                if available_at is not None
                else None
            ),
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

            workflow_state, correlation_id = self._workflow_context(
                connection,
                tenant_id=tenant_id,
                workflow_id=workflow_id,
            )

            record = AgentWorkItemRecord(
                work_item_id=work_item_id,
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                task_type=task_type,
                state=WorkItemState.PENDING,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                input_json=input_json,
                created_at=current_time,
                updated_at=current_time,
                available_at=ready_time,
                attempt_count=0,
                max_attempts=max_attempts,
                assigned_worker_id=None,
                lease_expires_at=None,
                fencing_token=0,
                last_error_code=None,
                last_error_message=None,
            )

            connection.execute(
                """
                INSERT INTO gagf_agent_work_items (
                    tenant_id,
                    work_item_id,
                    workflow_id,
                    task_type,
                    state,
                    correlation_id,
                    idempotency_key,
                    input_json,
                    created_at,
                    updated_at,
                    available_at,
                    attempt_count,
                    max_attempts,
                    assigned_worker_id,
                    lease_expires_at,
                    fencing_token,
                    last_error_code,
                    last_error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.tenant_id,
                    record.work_item_id,
                    record.workflow_id,
                    record.task_type,
                    record.state.value,
                    record.correlation_id,
                    record.idempotency_key,
                    record.input_json,
                    _datetime_text(record.created_at),
                    _datetime_text(record.updated_at),
                    _datetime_text(record.available_at),
                    record.attempt_count,
                    record.max_attempts,
                    record.assigned_worker_id,
                    None,
                    record.fencing_token,
                    None,
                    None,
                ),
            )

            self._insert_event(
                connection,
                record=record,
                event_type="work_item.created",
                idempotency_key=idempotency_key,
                request_hash=digest,
                payload={
                    "task_type": task_type,
                    "max_attempts": max_attempts,
                    "available_at": _datetime_text(ready_time),
                },
                occurred_at=current_time,
            )

            connection.commit()
            return record

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> AgentWorkItemRecord:
        tenant_id = _require_text(tenant_id, "tenant_id")
        work_item_id = _require_text(work_item_id, "work_item_id")

        connection = self._connect()

        try:
            return self._get_record(
                connection,
                tenant_id=tenant_id,
                work_item_id=work_item_id,
            )
        finally:
            connection.close()

    def list_ready_work_items(
        self,
        *,
        tenant_id: str,
        workflow_id: str | None = None,
        now: datetime | None = None,
        limit: int = 100,
    ) -> list[AgentWorkItemRecord]:
        """Return a bounded, deterministic page of claimable work items.

        This is a read-only candidate query. The registered claim operation
        remains responsible for transactional eligibility and worker checks.
        """
        tenant_id = _require_text(tenant_id, "tenant_id")

        if workflow_id is not None:
            workflow_id = _require_text(workflow_id, "workflow_id")

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
            or limit > 500
        ):
            raise AgentWorkItemStoreError(
                "limit must be an integer between 1 and 500"
            )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )

        connection = self._connect()

        try:
            query = """
                SELECT work_item.*
                FROM gagf_agent_work_items AS work_item
                INNER JOIN gagf_agent_workflows AS workflow
                    ON workflow.tenant_id = work_item.tenant_id
                   AND workflow.workflow_id = work_item.workflow_id
                WHERE work_item.tenant_id = ?
                  AND work_item.state = ?
                  AND work_item.available_at <= ?
                  AND work_item.attempt_count < work_item.max_attempts
                  AND workflow.state = ?
            """

            parameters = [
                tenant_id,
                WorkItemState.PENDING.value,
                _datetime_text(current_time),
                WorkflowState.ACTIVE.value,
            ]

            if workflow_id is not None:
                query += "\n AND work_item.workflow_id = ?"
                parameters.append(workflow_id)

            query += """
                ORDER BY
                    work_item.available_at ASC,
                    work_item.created_at ASC,
                    work_item.work_item_id ASC
                LIMIT ?
            """
            parameters.append(limit)

            rows = connection.execute(
                query,
                tuple(parameters),
            ).fetchall()

            return [self._record(row) for row in rows]

        finally:
            connection.close()

    def list_events(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> list[AgentWorkflowEvent]:
        tenant_id = _require_text(tenant_id, "tenant_id")
        work_item_id = _require_text(work_item_id, "work_item_id")

        connection = self._connect()

        try:
            self._get_record(
                connection,
                tenant_id=tenant_id,
                work_item_id=work_item_id,
            )

            rows = connection.execute(
                """
                SELECT *
                FROM gagf_agent_work_item_events
                WHERE tenant_id = ?
                  AND work_item_id = ?
                ORDER BY rowid ASC
                """,
                (tenant_id, work_item_id),
            ).fetchall()

            return [self._event(row) for row in rows]

        finally:
            connection.close()

    def _registered_worker(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        worker_id: str,
    ):
        from backend.app.gagf.governance_agent_worker_registry_contract import (
            AgentWorkerRegistrationIntegrityError,
            AgentWorkerRegistrationNotFoundError,
        )
        from backend.app.gagf.governance_agent_worker_registry_store import (
            AgentWorkerRegistryStore,
        )

        try:
            row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_worker_registry
                WHERE tenant_id = ?
                  AND worker_id = ?
                """,
                (tenant_id, worker_id),
            ).fetchone()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc).lower():
                raise AgentWorkerRegistrationIntegrityError(
                    "Worker registry table is unavailable"
                ) from exc
            raise

        if row is None:
            raise AgentWorkerRegistrationNotFoundError(
                "Worker registration was not found for this tenant"
            )

        return AgentWorkerRegistryStore._record(row)

    def claim_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        worker_id: str,
        lease_seconds: int,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> AgentWorkItemRecord:
        return self._claim_work_item(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
            idempotency_key=idempotency_key,
            now=now,
            expected_registration_revision=None,
            required_capabilities=None,
        )

    def claim_registered_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        worker_id: str,
        expected_registration_revision: int,
        required_capabilities: tuple[str, ...],
        lease_seconds: int,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> AgentWorkItemRecord:
        if (
            isinstance(expected_registration_revision, bool)
            or not isinstance(expected_registration_revision, int)
            or expected_registration_revision < 1
        ):
            raise AgentWorkItemStoreError(
                "expected_registration_revision must be a positive integer"
            )

        if isinstance(required_capabilities, (str, bytes)):
            raise AgentWorkItemStoreError(
                "required_capabilities must be a collection of strings"
            )

        try:
            normalized_capabilities = tuple(
                sorted(
                    {
                        _require_text(capability, "required_capabilities")
                        for capability in required_capabilities
                    }
                )
            )
        except TypeError as exc:
            raise AgentWorkItemStoreError(
                "required_capabilities must be an iterable of strings"
            ) from exc

        return self._claim_work_item(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
            idempotency_key=idempotency_key,
            now=now,
            expected_registration_revision=expected_registration_revision,
            required_capabilities=normalized_capabilities,
        )

    def _claim_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        worker_id: str,
        lease_seconds: int,
        idempotency_key: str,
        now: datetime | None,
        expected_registration_revision: int | None,
        required_capabilities: tuple[str, ...] | None,
    ) -> AgentWorkItemRecord:
        tenant_id = _require_text(tenant_id, "tenant_id")
        work_item_id = _require_text(work_item_id, "work_item_id")
        worker_id = _require_text(worker_id, "worker_id")
        idempotency_key = _require_text(
            idempotency_key,
            "idempotency_key",
        )

        registered_claim = expected_registration_revision is not None

        if registered_claim != (required_capabilities is not None):
            raise AgentWorkItemStoreError(
                "Registered claim qualification is incomplete"
            )

        if (
            isinstance(lease_seconds, bool)
            or not isinstance(lease_seconds, int)
            or lease_seconds < 1
        ):
            raise AgentWorkItemStoreError(
                "lease_seconds must be a positive integer"
            )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )
        lease_expiry = current_time + timedelta(
            seconds=lease_seconds
        )

        if registered_claim:
            request = {
                "operation": "claim_registered_work_item",
                "tenant_id": tenant_id,
                "work_item_id": work_item_id,
                "worker_id": worker_id,
                "lease_seconds": lease_seconds,
                "expected_registration_revision": expected_registration_revision,
                "required_capabilities": list(required_capabilities),
            }
        else:
            request = {
                "operation": "claim_work_item",
                "tenant_id": tenant_id,
                "work_item_id": work_item_id,
                "worker_id": worker_id,
                "lease_seconds": lease_seconds,
            }

        digest = _request_hash(request)
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            if registered_claim:
                record = self._get_record(
                    connection,
                    tenant_id=tenant_id,
                    work_item_id=work_item_id,
                )

                registration = self._registered_worker(
                    connection,
                    tenant_id=tenant_id,
                    worker_id=worker_id,
                )

                if not registration.enabled:
                    raise AgentWorkItemConflictError(
                        "Worker registration is disabled"
                    )

                if record.task_type not in registration.supported_task_types:
                    raise AgentWorkItemConflictError(
                        "Worker registration does not support this task type"
                    )

                if not set(required_capabilities).issubset(
                    registration.capabilities
                ):
                    raise AgentWorkItemConflictError(
                        "Worker registration lacks required capabilities"
                    )

                if (
                    registration.registration_revision
                    != expected_registration_revision
                ):
                    raise AgentWorkItemConflictError(
                        "Worker registration revision changed after matching"
                    )

                existing = self._existing_request(
                    connection,
                    tenant_id=tenant_id,
                    idempotency_key=idempotency_key,
                    request_hash=digest,
                )

                if existing is not None:
                    connection.commit()
                    return record

            else:
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
                    "Work items can only be claimed while the workflow is ACTIVE"
                )

            if record.state is not WorkItemState.PENDING:
                raise AgentWorkItemConflictError(
                    "Only PENDING work items can be claimed"
                )

            if record.available_at > current_time:
                raise AgentWorkItemConflictError(
                    "Work item is not yet available"
                )

            if record.attempt_count >= record.max_attempts:
                raise AgentWorkItemConflictError(
                    "Work item has exhausted its attempt limit"
                )

            validate_work_item_transition(
                record.state,
                WorkItemState.CLAIMED,
            )

            updated = AgentWorkItemRecord(
                work_item_id=record.work_item_id,
                tenant_id=record.tenant_id,
                workflow_id=record.workflow_id,
                task_type=record.task_type,
                state=WorkItemState.CLAIMED,
                correlation_id=record.correlation_id,
                idempotency_key=record.idempotency_key,
                input_json=record.input_json,
                created_at=record.created_at,
                updated_at=current_time,
                available_at=record.available_at,
                attempt_count=record.attempt_count + 1,
                max_attempts=record.max_attempts,
                assigned_worker_id=worker_id,
                lease_expires_at=lease_expiry,
                fencing_token=record.fencing_token + 1,
                last_error_code=None,
                last_error_message=None,
            )

            update_cursor = connection.execute(
                """
                UPDATE gagf_agent_work_items
                SET state = ?,
                    updated_at = ?,
                    attempt_count = ?,
                    assigned_worker_id = ?,
                    lease_expires_at = ?,
                    fencing_token = ?,
                    last_error_code = NULL,
                    last_error_message = NULL
                WHERE tenant_id = ?
                  AND work_item_id = ?
                  AND state = ?
                """,
                (
                    updated.state.value,
                    _datetime_text(updated.updated_at),
                    updated.attempt_count,
                    updated.assigned_worker_id,
                    _datetime_text(updated.lease_expires_at),
                    updated.fencing_token,
                    tenant_id,
                    work_item_id,
                    WorkItemState.PENDING.value,
                ),
            )

            if update_cursor.rowcount != 1:
                raise AgentWorkItemConflictError(
                    "Work item changed before the claim could be persisted"
                )

            event_payload = {
                "worker_id": worker_id,
                "attempt_count": updated.attempt_count,
                "lease_expires_at": _datetime_text(lease_expiry),
                "fencing_token": updated.fencing_token,
            }

            if registered_claim:
                event_payload["registration_revision"] = (
                    expected_registration_revision
                )
                event_payload["required_capabilities"] = list(
                    required_capabilities
                )

            self._insert_event(
                connection,
                record=updated,
                event_type="work_item.claimed",
                idempotency_key=idempotency_key,
                request_hash=digest,
                payload=event_payload,
                occurred_at=current_time,
            )

            connection.commit()
            return updated

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def start_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        worker_id: str,
        fencing_token: int,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> AgentWorkItemRecord:
        return self._transition_active_work_item(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            worker_id=worker_id,
            fencing_token=fencing_token,
            idempotency_key=idempotency_key,
            expected_state=WorkItemState.CLAIMED,
            target_state=WorkItemState.RUNNING,
            event_type="work_item.started",
            now=now,
            error_code=None,
            error_message=None,
            success=None,
        )

    def complete_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        worker_id: str,
        fencing_token: int,
        idempotency_key: str,
        success: bool,
        error_code: str | None = None,
        error_message: str | None = None,
        now: datetime | None = None,
    ) -> AgentWorkItemRecord:
        if not isinstance(success, bool):
            raise AgentWorkItemStoreError(
                "success must be a boolean"
            )

        if success and (error_code is not None or error_message is not None):
            raise AgentWorkItemStoreError(
                "Successful completion cannot include error details"
            )

        if not success and (
            not isinstance(error_code, str)
            or not error_code.strip()
            or not isinstance(error_message, str)
            or not error_message.strip()
        ):
            raise AgentWorkItemStoreError(
                "Failed completion requires error_code and error_message"
            )

        return self._transition_active_work_item(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            worker_id=worker_id,
            fencing_token=fencing_token,
            idempotency_key=idempotency_key,
            expected_state=WorkItemState.RUNNING,
            target_state=(
                WorkItemState.SUCCEEDED
                if success
                else WorkItemState.FAILED
            ),
            event_type=(
                "work_item.succeeded"
                if success
                else "work_item.failed"
            ),
            now=now,
            error_code=error_code,
            error_message=error_message,
            success=success,
        )

    def _transition_active_work_item(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        worker_id: str,
        fencing_token: int,
        idempotency_key: str,
        expected_state: WorkItemState,
        target_state: WorkItemState,
        event_type: str,
        now: datetime | None,
        error_code: str | None,
        error_message: str | None,
        success: bool | None,
    ) -> AgentWorkItemRecord:
        tenant_id = _require_text(tenant_id, "tenant_id")
        work_item_id = _require_text(work_item_id, "work_item_id")
        worker_id = _require_text(worker_id, "worker_id")
        idempotency_key = _require_text(
            idempotency_key,
            "idempotency_key",
        )

        if (
            isinstance(fencing_token, bool)
            or not isinstance(fencing_token, int)
            or fencing_token < 1
        ):
            raise AgentWorkItemStoreError(
                "fencing_token must be a positive integer"
            )

        current_time = _normalize_datetime(
            now or _utc_now(),
            "now",
        )

        request = {
            "operation": event_type,
            "tenant_id": tenant_id,
            "work_item_id": work_item_id,
            "worker_id": worker_id,
            "fencing_token": fencing_token,
            "success": success,
            "error_code": error_code,
            "error_message": error_message,
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
                    "Work-item execution requires an ACTIVE workflow"
                )

            if record.state is not expected_state:
                raise AgentWorkItemConflictError(
                    f"Expected work-item state {expected_state.value}"
                )

            if record.assigned_worker_id != worker_id:
                raise AgentWorkItemConflictError(
                    "Worker identity does not match the active claim"
                )

            if record.fencing_token != fencing_token:
                raise AgentWorkItemConflictError(
                    "Fencing token is stale or does not match the active claim"
                )

            if (
                record.lease_expires_at is None
                or record.lease_expires_at <= current_time
            ):
                raise AgentWorkItemConflictError(
                    "Work-item lease has expired"
                )

            validate_work_item_transition(
                record.state,
                target_state,
            )

            active = target_state in {
                WorkItemState.CLAIMED,
                WorkItemState.RUNNING,
            }

            updated = AgentWorkItemRecord(
                work_item_id=record.work_item_id,
                tenant_id=record.tenant_id,
                workflow_id=record.workflow_id,
                task_type=record.task_type,
                state=target_state,
                correlation_id=record.correlation_id,
                idempotency_key=record.idempotency_key,
                input_json=record.input_json,
                created_at=record.created_at,
                updated_at=current_time,
                available_at=record.available_at,
                attempt_count=record.attempt_count,
                max_attempts=record.max_attempts,
                assigned_worker_id=worker_id if active else None,
                lease_expires_at=(
                    record.lease_expires_at if active else None
                ),
                fencing_token=record.fencing_token,
                last_error_code=error_code,
                last_error_message=error_message,
            )

            update_cursor = connection.execute(
                """
                UPDATE gagf_agent_work_items
                SET state = ?,
                    updated_at = ?,
                    assigned_worker_id = ?,
                    lease_expires_at = ?,
                    last_error_code = ?,
                    last_error_message = ?
                WHERE tenant_id = ?
                  AND work_item_id = ?
                  AND state = ?
                  AND fencing_token = ?
                """,
                (
                    updated.state.value,
                    _datetime_text(updated.updated_at),
                    updated.assigned_worker_id,
                    (
                        _datetime_text(updated.lease_expires_at)
                        if updated.lease_expires_at
                        else None
                    ),
                    updated.last_error_code,
                    updated.last_error_message,
                    tenant_id,
                    work_item_id,
                    expected_state.value,
                    fencing_token,
                ),
            )
            if update_cursor.rowcount != 1:
                raise AgentWorkItemConflictError(
                    "Work item changed before the lifecycle transition "
                    "could be persisted"
                )

            self._insert_event(
                connection,
                record=updated,
                event_type=event_type,
                idempotency_key=idempotency_key,
                request_hash=digest,
                payload={
                    "worker_id": worker_id,
                    "fencing_token": fencing_token,
                    "success": success,
                    "error_code": error_code,
                    "error_message": error_message,
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