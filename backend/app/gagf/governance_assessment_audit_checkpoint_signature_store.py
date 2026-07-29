from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature import (
    SignedAssessmentAuditCheckpoint,
)


class SignedAssessmentAuditCheckpointStore:
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
                signed_assessment_audit_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    checkpoint_json TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    signature_algorithm TEXT NOT NULL,
                    signature_version TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_signed_checkpoint_tenant_time
                ON signed_assessment_audit_checkpoints(
                    tenant_id,
                    created_at
                )
                """
            )
            connection.commit()

    def append(
        self,
        signed_checkpoint: SignedAssessmentAuditCheckpoint,
    ) -> None:
        checkpoint = signed_checkpoint.checkpoint

        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO signed_assessment_audit_checkpoints (
                    checkpoint_id,
                    tenant_id,
                    checkpoint_json,
                    key_id,
                    signature,
                    signature_algorithm,
                    signature_version,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.tenant_id,
                    json.dumps(
                        checkpoint.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    signed_checkpoint.key_id,
                    signed_checkpoint.signature,
                    signed_checkpoint.signature_algorithm,
                    signed_checkpoint.signature_version,
                    checkpoint.created_at,
                ),
            )
            connection.commit()

    def list_signed_checkpoints(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
    ) -> list[SignedAssessmentAuditCheckpoint]:
        safe_limit = max(1, min(limit, 500))

        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM signed_assessment_audit_checkpoints
                WHERE tenant_id = ?
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (tenant_id, safe_limit),
            ).fetchall()

        return [
            self._row_to_signed_checkpoint(row)
            for row in rows
        ]

    @staticmethod
    def _row_to_signed_checkpoint(
        row: sqlite3.Row,
    ) -> SignedAssessmentAuditCheckpoint:
        payload = json.loads(row["checkpoint_json"])

        checkpoint = AssessmentAuditCheckpoint(
            checkpoint_id=payload["checkpoint_id"],
            tenant_id=payload["tenant_id"],
            chain_head_hash=payload["chain_head_hash"],
            checked_count=payload["checked_count"],
            valid=payload["valid"],
            reason_code=payload["reason_code"],
            created_at=payload["created_at"],
            checkpoint_version=payload["checkpoint_version"],
        )

        return SignedAssessmentAuditCheckpoint(
            checkpoint=checkpoint,
            key_id=row["key_id"],
            signature=row["signature"],
            signature_algorithm=row["signature_algorithm"],
            signature_version=row["signature_version"],
        )
