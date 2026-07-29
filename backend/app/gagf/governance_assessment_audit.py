from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from backend.app.gagf.governance_assessment_audit_integrity import (
    ASSESSMENT_AUDIT_GENESIS_HASH,
    ASSESSMENT_AUDIT_HASH_VERSION,
    AssessmentAuditChainVerification,
    compute_assessment_audit_hash,
    verify_assessment_audit_chain,
)


ASSESSMENT_AUDIT_VERSION = "2.0.0"


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
    previous_hash: str = ASSESSMENT_AUDIT_GENESIS_HASH
    event_hash: str = ""
    hash_version: str = ASSESSMENT_AUDIT_HASH_VERSION

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
                    occurred_at TEXT NOT NULL,
                    previous_hash TEXT,
                    event_hash TEXT,
                    hash_version TEXT
                )
                """
            )
            self._ensure_integrity_columns(connection)
            self._backfill_integrity_chain(connection)
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

    @staticmethod
    def _ensure_integrity_columns(
        connection: sqlite3.Connection,
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(assessment_audit_events)"
            ).fetchall()
        }

        required_columns = {
            "previous_hash": "TEXT",
            "event_hash": "TEXT",
            "hash_version": "TEXT",
        }

        for name, column_type in required_columns.items():
            if name not in columns:
                connection.execute(
                    "ALTER TABLE assessment_audit_events "
                    f"ADD COLUMN {name} {column_type}"
                )

    @staticmethod
    def _backfill_integrity_chain(
        connection: sqlite3.Connection,
    ) -> None:
        rows = connection.execute(
            """
            SELECT rowid, *
            FROM assessment_audit_events
            ORDER BY tenant_id, rowid
            """
        ).fetchall()

        previous_hashes: dict[str | None, str] = {}

        for row in rows:
            tenant_id = row["tenant_id"]
            previous_hash = previous_hashes.get(
                tenant_id,
                ASSESSMENT_AUDIT_GENESIS_HASH,
            )
            hash_version = ASSESSMENT_AUDIT_HASH_VERSION
            event_hash = compute_assessment_audit_hash(
                event_id=row["event_id"],
                request_id=row["request_id"],
                tenant_id=tenant_id,
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
                previous_hash=previous_hash,
                hash_version=hash_version,
            )

            if (
                row["previous_hash"] != previous_hash
                or row["event_hash"] != event_hash
                or row["hash_version"] != hash_version
            ):
                connection.execute(
                    """
                    UPDATE assessment_audit_events
                    SET previous_hash = ?,
                        event_hash = ?,
                        hash_version = ?
                    WHERE rowid = ?
                    """,
                    (
                        previous_hash,
                        event_hash,
                        hash_version,
                        row["rowid"],
                    ),
                )

            previous_hashes[tenant_id] = event_hash

    def append(
        self,
        event: AssessmentAuditEvent,
    ) -> AssessmentAuditEvent:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            latest = connection.execute(
                """
                SELECT event_hash
                FROM assessment_audit_events
                WHERE tenant_id IS ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (event.tenant_id,),
            ).fetchone()

            previous_hash = (
                latest["event_hash"]
                if latest is not None
                else ASSESSMENT_AUDIT_GENESIS_HASH
            )

            event_hash = compute_assessment_audit_hash(
                event_id=event.event_id,
                request_id=event.request_id,
                tenant_id=event.tenant_id,
                actor_id=event.actor_id,
                actor_roles=event.actor_roles,
                method=event.method,
                route=event.route,
                outcome=event.outcome,
                status_code=event.status_code,
                reason_code=event.reason_code,
                occurred_at=event.occurred_at,
                previous_hash=previous_hash,
                hash_version=ASSESSMENT_AUDIT_HASH_VERSION,
            )

            chained_event = replace(
                event,
                previous_hash=previous_hash,
                event_hash=event_hash,
                hash_version=ASSESSMENT_AUDIT_HASH_VERSION,
            )

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
                    occurred_at,
                    previous_hash,
                    event_hash,
                    hash_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chained_event.event_id,
                    chained_event.request_id,
                    chained_event.tenant_id,
                    chained_event.actor_id,
                    json.dumps(list(chained_event.actor_roles)),
                    chained_event.method,
                    chained_event.route,
                    chained_event.outcome,
                    chained_event.status_code,
                    chained_event.reason_code,
                    chained_event.occurred_at,
                    chained_event.previous_hash,
                    chained_event.event_hash,
                    chained_event.hash_version,
                ),
            )
            connection.commit()

        return chained_event

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
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (tenant_id, safe_limit),
            ).fetchall()

        return [self._row_to_event(row) for row in rows]

    def list_events_chronological(
        self,
        *,
        tenant_id: str,
    ) -> list[AssessmentAuditEvent]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM assessment_audit_events
                WHERE tenant_id = ?
                ORDER BY rowid
                """,
                (tenant_id,),
            ).fetchall()

        return [self._row_to_event(row) for row in rows]

    def verify_tenant_chain(
        self,
        *,
        tenant_id: str,
    ) -> AssessmentAuditChainVerification:
        events = self.list_events_chronological(
            tenant_id=tenant_id
        )

        return verify_assessment_audit_chain(
            [event.to_dict() for event in events]
        )

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
            previous_hash=row["previous_hash"],
            event_hash=row["event_hash"],
            hash_version=row["hash_version"],
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
    event_id = str(uuid4())
    occurred_at = datetime.now(timezone.utc).isoformat()

    event_hash = compute_assessment_audit_hash(
        event_id=event_id,
        request_id=request_id or event_id,
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        method=method,
        route=route,
        outcome=outcome,
        status_code=status_code,
        reason_code=reason_code,
        occurred_at=occurred_at,
        previous_hash=ASSESSMENT_AUDIT_GENESIS_HASH,
        hash_version=ASSESSMENT_AUDIT_HASH_VERSION,
    )

    return AssessmentAuditEvent(
        event_id=event_id,
        request_id=request_id or event_id,
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        method=method.upper(),
        route=route,
        outcome=outcome,
        status_code=status_code,
        reason_code=reason_code,
        occurred_at=occurred_at,
        previous_hash=ASSESSMENT_AUDIT_GENESIS_HASH,
        event_hash=event_hash,
        hash_version=ASSESSMENT_AUDIT_HASH_VERSION,
    )
