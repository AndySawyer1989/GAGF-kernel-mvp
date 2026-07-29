from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


ASSESSMENT_AUDIT_VERSION = "1.0.0"


@dataclass(frozen=True)
class AssessmentAuditEvent:
    event_id: str
    request_id: str
    tenant_id: str | None
    actor_id: str | None
    actor_roles: tuple[str, ...]
    method: str
    route: str
    outcome: str
    status_code: int
    reason_code: str | None
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["actor_roles"] = list(self.actor_roles)
        return payload


class AssessmentAuditLedger:
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
                CREATE TABLE IF NOT EXISTS assessment_audit_events (
                    event_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    tenant_id TEXT,
                    actor_id TEXT,
                    actor_roles_json TEXT NOT NULL,
                    method TEXT NOT NULL,
                    route TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    reason_code TEXT,
                    occurred_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_assessment_audit_tenant_time
                ON assessment_audit_events(
                    tenant_id,
                    occurred_at
                )
                """
            )
            connection.commit()

    def append(self, event: AssessmentAuditEvent) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessment_audit_events (
                    event_id,
                    request_id,
                    tenant_id,
                    actor_id,
                    actor_roles_json,
                    method,
                    route,
                    outcome,
                    status_code,
                    reason_code,
                    occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.request_id,
                    event.tenant_id,
                    event.actor_id,
                    json.dumps(list(event.actor_roles)),
                    event.method,
                    event.route,
                    event.outcome,
                    event.status_code,
                    event.reason_code,
                    event.occurred_at,
                ),
            )
            connection.commit()

    def list_events(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
    ) -> list[AssessmentAuditEvent]:
        safe_limit = max(1, min(limit, 500))

        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM assessment_audit_events
                WHERE tenant_id = ?
                ORDER BY occurred_at DESC, event_id DESC
                LIMIT ?
                """,
                (tenant_id, safe_limit),
            ).fetchall()

        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(
        row: sqlite3.Row,
    ) -> AssessmentAuditEvent:
        return AssessmentAuditEvent(
            event_id=row["event_id"],
            request_id=row["request_id"],
            tenant_id=row["tenant_id"],
            actor_id=row["actor_id"],
            actor_roles=tuple(
                json.loads(row["actor_roles_json"])
            ),
            method=row["method"],
            route=row["route"],
            outcome=row["outcome"],
            status_code=row["status_code"],
            reason_code=row["reason_code"],
            occurred_at=row["occurred_at"],
        )


def build_assessment_audit_event(
    *,
    request_id: str | None,
    tenant_id: str | None,
    actor_id: str | None,
    actor_roles: tuple[str, ...] = (),
    method: str,
    route: str,
    outcome: str,
    status_code: int,
    reason_code: str | None = None,
) -> AssessmentAuditEvent:
    return AssessmentAuditEvent(
        event_id=str(uuid4()),
        request_id=request_id or str(uuid4()),
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        method=method.upper(),
        route=route,
        outcome=outcome,
        status_code=status_code,
        reason_code=reason_code,
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )
