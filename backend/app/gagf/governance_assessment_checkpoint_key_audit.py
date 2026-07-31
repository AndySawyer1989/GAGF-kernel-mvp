from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


ASSESSMENT_CHECKPOINT_KEY_AUDIT_VERSION = "1.0.0"

CHECKPOINT_KEY_ACTIVATED = (
    "ASSESSMENT_CHECKPOINT_SIGNING_KEY_ACTIVATED"
)


@dataclass(frozen=True)
class AssessmentCheckpointKeyAuditEvent:
    event_id: str
    tenant_id: str
    actor_id: str
    operation: str
    previous_key_id: str | None
    active_key_id: str
    occurred_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "operation": self.operation,
            "previous_key_id": self.previous_key_id,
            "active_key_id": self.active_key_id,
            "occurred_at": self.occurred_at,
            "metadata": dict(self.metadata),
        }


def create_checkpoint_key_activation_audit_event(
    *,
    tenant_id: str,
    actor_id: str,
    previous_key_id: str | None,
    active_key_id: str,
    metadata: dict[str, Any] | None = None,
) -> AssessmentCheckpointKeyAuditEvent:
    return AssessmentCheckpointKeyAuditEvent(
        event_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        actor_id=actor_id,
        operation=CHECKPOINT_KEY_ACTIVATED,
        previous_key_id=previous_key_id,
        active_key_id=active_key_id,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        metadata=dict(metadata or {}),
    )


class AssessmentCheckpointKeyAuditStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                assessment_checkpoint_key_audit_events (
                    event_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    previous_key_id TEXT,
                    active_key_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_checkpoint_key_audit_tenant_time
                ON assessment_checkpoint_key_audit_events(
                    tenant_id,
                    occurred_at DESC
                )
                """
            )
            connection.commit()

    def append(
        self,
        event: AssessmentCheckpointKeyAuditEvent,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessment_checkpoint_key_audit_events (
                    event_id,
                    tenant_id,
                    actor_id,
                    operation,
                    previous_key_id,
                    active_key_id,
                    occurred_at,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.tenant_id,
                    event.actor_id,
                    event.operation,
                    event.previous_key_id,
                    event.active_key_id,
                    event.occurred_at,
                    json.dumps(
                        event.metadata,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
            connection.commit()

    def list_events(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
    ) -> list[AssessmentCheckpointKeyAuditEvent]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM assessment_checkpoint_key_audit_events
                WHERE tenant_id = ?
                ORDER BY occurred_at DESC, event_id DESC
                LIMIT ?
                """,
                (tenant_id, limit),
            ).fetchall()

        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(
        row: sqlite3.Row,
    ) -> AssessmentCheckpointKeyAuditEvent:
        return AssessmentCheckpointKeyAuditEvent(
            event_id=row["event_id"],
            tenant_id=row["tenant_id"],
            actor_id=row["actor_id"],
            operation=row["operation"],
            previous_key_id=row["previous_key_id"],
            active_key_id=row["active_key_id"],
            occurred_at=row["occurred_at"],
            metadata=json.loads(row["metadata_json"]),
        )
