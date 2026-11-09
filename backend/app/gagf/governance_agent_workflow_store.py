from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import uuid

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_agent_workflow_contract import (
    AgentWorkflowContractError,
    AgentWorkflowEvent,
    WorkflowState,
    validate_workflow_transition,
)


STORE_VERSION = "0.1.0"


class AgentWorkflowStoreError(Exception):
    """Base exception for workflow-store failures."""


class AgentWorkflowNotFoundError(AgentWorkflowStoreError):
    """Raised when a tenant-scoped workflow does not exist."""


class AgentWorkflowConflictError(AgentWorkflowStoreError):
    """Raised when an identifier or idempotency key conflicts."""


class AgentWorkflowIntegrityError(AgentWorkflowStoreError):
    """Raised when persisted event integrity verification fails."""


@dataclass(frozen=True, slots=True)
class AgentWorkflowRecord:
    workflow_id: str
    tenant_id: str
    workflow_type: str
    state: WorkflowState
    correlation_id: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "workflow_type": self.workflow_type,
            "state": self.state.value,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkflowStoreError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise AgentWorkflowStoreError(
            "Value cannot be represented as canonical JSON"
        ) from exc


def _request_hash(value: Mapping[str, Any]) -> str:
    canonical = _canonical_json(dict(value))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_payload(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if payload is None:
        return {}

    if not isinstance(payload, Mapping):
        raise AgentWorkflowStoreError("payload must be a mapping")

    normalized = dict(payload)

    if any(not isinstance(key, str) for key in normalized):
        raise AgentWorkflowStoreError(
            "payload keys must all be strings"
        )

    _canonical_json(normalized)
    return normalized


class AgentWorkflowStore:
    """Tenant-scoped SQLite persistence for agent workflow state and events."""

    def __init__(
        self,
        database_path: str | Path,
        timeout_seconds: float = 10.0,
    ) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise AgentWorkflowStoreError(
                "timeout_seconds must be a finite number greater than zero"
            )

        try:
            valid_timeout = (
                math.isfinite(float(timeout_seconds))
                and timeout_seconds > 0
            )
        except (OverflowError, ValueError):
            valid_timeout = False

        if not valid_timeout:
            raise AgentWorkflowStoreError(
                "timeout_seconds must be a finite number greater than zero"
            )

        self.database_path = Path(database_path)
        self.timeout_seconds = float(timeout_seconds)

        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=self.timeout_seconds,
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
                CREATE TABLE IF NOT EXISTS gagf_agent_workflows (
                    tenant_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    workflow_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, workflow_id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_workflow_events (
                    event_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    work_item_id TEXT,
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
                    FOREIGN KEY (tenant_id, workflow_id)
                        REFERENCES gagf_agent_workflows (
                            tenant_id,
                            workflow_id
                        )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_gagf_agent_workflow_events_history
                ON gagf_agent_workflow_events (
                    tenant_id,
                    workflow_id,
                    occurred_at,
                    event_id
                )
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_workflow_events_no_update
                BEFORE UPDATE ON gagf_agent_workflow_events
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'workflow events are append-only'
                    );
                END
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_workflow_events_no_delete
                BEFORE DELETE ON gagf_agent_workflow_events
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'workflow events are append-only'
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

    @staticmethod
    def _record(row: sqlite3.Row) -> AgentWorkflowRecord:
        try:
            return AgentWorkflowRecord(
                workflow_id=row["workflow_id"],
                tenant_id=row["tenant_id"],
                workflow_type=row["workflow_type"],
                state=WorkflowState(row["state"]),
                correlation_id=row["correlation_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AgentWorkflowIntegrityError(
                "Stored workflow record is invalid"
            ) from exc

    @staticmethod
    def _event(row: sqlite3.Row) -> AgentWorkflowEvent:
        try:
            event = AgentWorkflowEvent(
                event_id=row["event_id"],
                event_type=row["event_type"],
                tenant_id=row["tenant_id"],
                workflow_id=row["workflow_id"],
                work_item_id=row["work_item_id"],
                correlation_id=row["correlation_id"],
                causation_id=row["causation_id"],
                idempotency_key=row["idempotency_key"],
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
                payload_json=row["payload_json"],
                schema_version=row["schema_version"],
                event_hash=row["event_hash"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AgentWorkflowIntegrityError(
                "Stored workflow event is invalid"
            ) from exc

        if not event.verify_integrity():
            raise AgentWorkflowIntegrityError(
                f"Workflow event integrity check failed: {event.event_id}"
            )

        return event

    @staticmethod
    def _existing_request(
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        idempotency_key: str,
        request_hash: str,
    ) -> sqlite3.Row | None:
        row = connection.execute(
            """
            SELECT *
            FROM gagf_agent_workflow_events
            WHERE tenant_id = ?
              AND idempotency_key = ?
            """,
            (tenant_id, idempotency_key),
        ).fetchone()

        if row is None:
            return None

        # Verify the stored event before accepting an idempotent replay.
        AgentWorkflowStore._event(row)

        if row["request_hash"] != request_hash:
            raise AgentWorkflowConflictError(
                "Idempotency key was already used for a different request"
            )

        return row

    @staticmethod
    def _insert_event(
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        workflow_id: str,
        event_type: str,
        correlation_id: str,
        idempotency_key: str,
        request_hash: str,
        payload: Mapping[str, Any],
        causation_id: str | None = None,
        work_item_id: str | None = None,
    ) -> AgentWorkflowEvent:
        event = AgentWorkflowEvent.create(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            work_item_id=work_item_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            occurred_at=datetime.now(timezone.utc),
            payload=payload,
        )

        connection.execute(
            """
            INSERT INTO gagf_agent_workflow_events (
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
                event.occurred_at.isoformat(),
                event.payload_json,
                event.schema_version,
                event.event_hash,
                request_hash,
            ),
        )

        return event

    def create_workflow(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        workflow_type: str,
        idempotency_key: str,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> AgentWorkflowRecord:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(workflow_id, "workflow_id")
        kind = _require_text(workflow_type, "workflow_type")
        key = _require_text(idempotency_key, "idempotency_key")
        correlation = (
            _require_text(correlation_id, "correlation_id")
            if correlation_id is not None
            else identifier
        )
        event_payload = _normalize_payload(payload)

        request_digest = _request_hash(
            {
                "operation": "create_workflow",
                "tenant_id": tenant,
                "workflow_id": identifier,
                "workflow_type": kind,
                "correlation_id": correlation,
                "payload": event_payload,
            }
        )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = self._existing_request(
                connection,
                tenant_id=tenant,
                idempotency_key=key,
                request_hash=request_digest,
            )

            if existing is not None:
                row = connection.execute(
                    """
                    SELECT *
                    FROM gagf_agent_workflows
                    WHERE tenant_id = ?
                      AND workflow_id = ?
                    """,
                    (tenant, identifier),
                ).fetchone()

                if row is None:
                    raise AgentWorkflowIntegrityError(
                        "Idempotent creation event has no workflow record"
                    )

                record = self._record(row)
                connection.commit()
                return record

            existing_workflow = connection.execute(
                """
                SELECT 1
                FROM gagf_agent_workflows
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if existing_workflow is not None:
                raise AgentWorkflowConflictError(
                    "Workflow already exists for this tenant"
                )

            now = datetime.now(timezone.utc).isoformat()

            connection.execute(
                """
                INSERT INTO gagf_agent_workflows (
                    tenant_id,
                    workflow_id,
                    workflow_type,
                    state,
                    correlation_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant,
                    identifier,
                    kind,
                    WorkflowState.CREATED.value,
                    correlation,
                    now,
                    now,
                ),
            )

            self._insert_event(
                connection,
                tenant_id=tenant,
                workflow_id=identifier,
                event_type="workflow.created",
                correlation_id=correlation,
                idempotency_key=key,
                request_hash=request_digest,
                payload={
                    "workflow_type": kind,
                    "data": event_payload,
                },
            )

            row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_workflows
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if row is None:
                raise AgentWorkflowIntegrityError(
                    "Created workflow could not be read back"
                )

            record = self._record(row)
            connection.commit()
            return record

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_workflow(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
    ) -> AgentWorkflowRecord:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(workflow_id, "workflow_id")

        connection = self._connect()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_workflows
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if row is None:
                raise AgentWorkflowNotFoundError(
                    "Workflow not found for this tenant"
                )

            return self._record(row)
        finally:
            connection.close()

    def transition_workflow(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        target_state: WorkflowState,
        idempotency_key: str,
        event_type: str,
        causation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> AgentWorkflowRecord:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(workflow_id, "workflow_id")
        key = _require_text(idempotency_key, "idempotency_key")
        kind = _require_text(event_type, "event_type")

        if not isinstance(target_state, WorkflowState):
            raise AgentWorkflowStoreError(
                "target_state must be a WorkflowState"
            )

        normalized_causation = (
            _require_text(causation_id, "causation_id")
            if causation_id is not None
            else None
        )
        event_payload = _normalize_payload(payload)

        request_digest = _request_hash(
            {
                "operation": "transition_workflow",
                "tenant_id": tenant,
                "workflow_id": identifier,
                "target_state": target_state.value,
                "event_type": kind,
                "causation_id": normalized_causation,
                "payload": event_payload,
            }
        )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = self._existing_request(
                connection,
                tenant_id=tenant,
                idempotency_key=key,
                request_hash=request_digest,
            )

            if existing is not None:
                row = connection.execute(
                    """
                    SELECT *
                    FROM gagf_agent_workflows
                    WHERE tenant_id = ?
                      AND workflow_id = ?
                    """,
                    (tenant, identifier),
                ).fetchone()

                if row is None:
                    raise AgentWorkflowIntegrityError(
                        "Idempotent transition event has no workflow record"
                    )

                record = self._record(row)
                connection.commit()
                return record

            row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_workflows
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if row is None:
                raise AgentWorkflowNotFoundError(
                    "Workflow not found for this tenant"
                )

            current = self._record(row)
            validate_workflow_transition(
                current.state,
                target_state,
            )

            now = datetime.now(timezone.utc).isoformat()

            connection.execute(
                """
                UPDATE gagf_agent_workflows
                SET state = ?,
                    updated_at = ?
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (
                    target_state.value,
                    now,
                    tenant,
                    identifier,
                ),
            )

            self._insert_event(
                connection,
                tenant_id=tenant,
                workflow_id=identifier,
                event_type=kind,
                correlation_id=current.correlation_id,
                causation_id=normalized_causation,
                idempotency_key=key,
                request_hash=request_digest,
                payload={
                    "previous_state": current.state.value,
                    "target_state": target_state.value,
                    "data": event_payload,
                },
            )

            updated_row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_workflows
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if updated_row is None:
                raise AgentWorkflowIntegrityError(
                    "Transitioned workflow could not be read back"
                )

            record = self._record(updated_row)
            connection.commit()
            return record

        except AgentWorkflowContractError as exc:
            connection.rollback()
            raise AgentWorkflowStoreError(str(exc)) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def append_workflow_event(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
        idempotency_key: str,
        event_type: str,
        expected_state: WorkflowState,
        causation_id: str | None = None,
        work_item_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> AgentWorkflowEvent:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(workflow_id, "workflow_id")
        key = _require_text(idempotency_key, "idempotency_key")
        kind = _require_text(event_type, "event_type")

        if not isinstance(expected_state, WorkflowState):
            raise AgentWorkflowStoreError(
                "expected_state must be a WorkflowState"
            )

        normalized_causation = (
            _require_text(causation_id, "causation_id")
            if causation_id is not None
            else None
        )
        normalized_work_item = (
            _require_text(work_item_id, "work_item_id")
            if work_item_id is not None
            else None
        )
        event_payload = _normalize_payload(payload)

        request_digest = _request_hash(
            {
                "operation": "append_workflow_event",
                "tenant_id": tenant,
                "workflow_id": identifier,
                "idempotency_key": key,
                "event_type": kind,
                "expected_state": expected_state.value,
                "causation_id": normalized_causation,
                "work_item_id": normalized_work_item,
                "payload": event_payload,
            }
        )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = self._existing_request(
                connection,
                tenant_id=tenant,
                idempotency_key=key,
                request_hash=request_digest,
            )

            if existing is not None:
                event = self._event(existing)
                connection.commit()
                return event

            workflow_row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_workflows
                WHERE tenant_id = ?
                  AND workflow_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if workflow_row is None:
                raise AgentWorkflowNotFoundError(
                    "Workflow not found for this tenant"
                )

            current_state = WorkflowState(workflow_row["state"])

            if current_state is not expected_state:
                raise AgentWorkflowConflictError(
                    "Workflow state does not match expected_state"
                )

            envelope = {
                "previous_state": current_state.value,
                "target_state": current_state.value,
                "data": event_payload,
            }

            event = self._insert_event(
                connection,
                tenant_id=tenant,
                workflow_id=identifier,
                event_type=kind,
                correlation_id=workflow_row["correlation_id"],
                idempotency_key=key,
                request_hash=request_digest,
                payload=envelope,
                causation_id=normalized_causation,
                work_item_id=normalized_work_item,
            )

            connection.commit()
            return event

        except AgentWorkflowContractError as exc:
            connection.rollback()
            raise AgentWorkflowStoreError(str(exc)) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
    def list_events(
        self,
        *,
        tenant_id: str,
        workflow_id: str,
    ) -> list[AgentWorkflowEvent]:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(workflow_id, "workflow_id")

        connection = self._connect()

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM gagf_agent_workflow_events
                WHERE tenant_id = ?
                  AND workflow_id = ?
                ORDER BY rowid ASC
                """,
                (tenant, identifier),
            ).fetchall()

            return [self._event(row) for row in rows]
        finally:
            connection.close()