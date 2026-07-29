from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_integrity import (
    ASSESSMENT_AUDIT_GENESIS_HASH,
)


ASSESSMENT_AUDIT_CHECKPOINT_VERSION = "1.0.0"


@dataclass(frozen=True)
class AssessmentAuditCheckpoint:
    checkpoint_id: str
    tenant_id: str
    chain_head_hash: str
    checked_count: int
    valid: bool
    reason_code: str | None
    created_at: str
    checkpoint_version: str = (
        ASSESSMENT_AUDIT_CHECKPOINT_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AssessmentAuditCheckpointStore:
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
                assessment_audit_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    chain_head_hash TEXT NOT NULL,
                    checked_count INTEGER NOT NULL,
                    valid INTEGER NOT NULL,
                    reason_code TEXT,
                    created_at TEXT NOT NULL,
                    checkpoint_version TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_assessment_checkpoint_tenant_time
                ON assessment_audit_checkpoints(
                    tenant_id,
                    created_at
                )
                """
            )
            connection.commit()

    def append(
        self,
        checkpoint: AssessmentAuditCheckpoint,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessment_audit_checkpoints (
                    checkpoint_id,
                    tenant_id,
                    chain_head_hash,
                    checked_count,
                    valid,
                    reason_code,
                    created_at,
                    checkpoint_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.tenant_id,
                    checkpoint.chain_head_hash,
                    checkpoint.checked_count,
                    int(checkpoint.valid),
                    checkpoint.reason_code,
                    checkpoint.created_at,
                    checkpoint.checkpoint_version,
                ),
            )
            connection.commit()

    def list_checkpoints(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
    ) -> list[AssessmentAuditCheckpoint]:
        safe_limit = max(1, min(limit, 500))

        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM assessment_audit_checkpoints
                WHERE tenant_id = ?
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (tenant_id, safe_limit),
            ).fetchall()

        return [self._row_to_checkpoint(row) for row in rows]

    @staticmethod
    def _row_to_checkpoint(
        row: sqlite3.Row,
    ) -> AssessmentAuditCheckpoint:
        return AssessmentAuditCheckpoint(
            checkpoint_id=row["checkpoint_id"],
            tenant_id=row["tenant_id"],
            chain_head_hash=row["chain_head_hash"],
            checked_count=row["checked_count"],
            valid=bool(row["valid"]),
            reason_code=row["reason_code"],
            created_at=row["created_at"],
            checkpoint_version=row["checkpoint_version"],
        )


def create_assessment_audit_checkpoint(
    *,
    tenant_id: str,
    ledger: AssessmentAuditLedger,
) -> AssessmentAuditCheckpoint:
    verification = ledger.verify_tenant_chain(
        tenant_id=tenant_id
    )
    events = ledger.list_events_chronological(
        tenant_id=tenant_id
    )

    chain_head_hash = (
        events[-1].event_hash
        if events
        else ASSESSMENT_AUDIT_GENESIS_HASH
    )

    return AssessmentAuditCheckpoint(
        checkpoint_id=str(uuid4()),
        tenant_id=tenant_id,
        chain_head_hash=chain_head_hash,
        checked_count=verification.checked_count,
        valid=verification.valid,
        reason_code=verification.reason_code,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
