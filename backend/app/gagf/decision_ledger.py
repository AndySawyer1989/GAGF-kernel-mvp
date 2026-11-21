import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class DecisionLedger:
    def __init__(self, db_path="gagf.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _require_tenant_id(tenant_id):
        normalized = (
            tenant_id.strip()
            if isinstance(tenant_id, str)
            else ""
        )

        if not normalized:
            raise ValueError("tenant_id is required")

        return normalized

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_decision_records (
                    decision_id TEXT PRIMARY KEY,
                    snapshot_id TEXT,
                    tenant_id TEXT,
                    active_strategy TEXT,
                    strategy_proposal TEXT,
                    kernel_decision TEXT NOT NULL,
                    selected_strategy TEXT,
                    reason_json TEXT NOT NULL,
                    decision_meta_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(gagf_decision_records)"
                ).fetchall()
            }

            if "tenant_id" not in columns:
                conn.execute(
                    """
                    ALTER TABLE gagf_decision_records
                    ADD COLUMN tenant_id TEXT
                    """
                )

            snapshot_table_exists = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'gagf_state_snapshots'
                """
            ).fetchone()

            if snapshot_table_exists:
                snapshot_columns = {
                    row[1]
                    for row in conn.execute(
                        "PRAGMA table_info(gagf_state_snapshots)"
                    ).fetchall()
                }

                if {"snapshot_id", "tenant_id"}.issubset(snapshot_columns):
                    conn.execute(
                        """
                        UPDATE gagf_decision_records
                        SET tenant_id = (
                            SELECT snapshots.tenant_id
                            FROM gagf_state_snapshots AS snapshots
                            WHERE snapshots.snapshot_id =
                                  gagf_decision_records.snapshot_id
                        )
                        WHERE tenant_id IS NULL
                          AND snapshot_id IS NOT NULL
                          AND EXISTS (
                              SELECT 1
                              FROM gagf_state_snapshots AS snapshots
                              WHERE snapshots.snapshot_id =
                                    gagf_decision_records.snapshot_id
                                AND snapshots.tenant_id IS NOT NULL
                                AND TRIM(snapshots.tenant_id) != ''
                          )
                        """
                    )

    def save_decision(self, decision, *, tenant_id, evidence=None):
        tenant_id = self._require_tenant_id(tenant_id)
        evidence = evidence or []

        decision_id = str(uuid4())

        with self._connect() as conn:
            snapshot = conn.execute(
                """
                SELECT tenant_id
                FROM gagf_state_snapshots
                WHERE snapshot_id = ?
                """,
                (decision.snapshot_id,),
            ).fetchone()

            if snapshot is None:
                raise ValueError(
                    "decision snapshot does not exist"
                )

            snapshot_tenant_id = snapshot[0]

            if snapshot_tenant_id != tenant_id:
                raise ValueError(
                    "decision tenant_id does not match snapshot owner"
                )

            conn.execute(
                """
                INSERT INTO gagf_decision_records (
                    decision_id,
                    snapshot_id,
                    tenant_id,
                    active_strategy,
                    strategy_proposal,
                    kernel_decision,
                    selected_strategy,
                    reason_json,
                    decision_meta_json,
                    evidence_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    decision.snapshot_id,
                    tenant_id,
                    decision.active_strategy,
                    decision.strategy_proposal,
                    decision.kernel_decision,
                    decision.selected_strategy,
                    json.dumps(decision.reason),
                    json.dumps(decision.decision_meta.model_dump()),
                    json.dumps(evidence),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        return decision_id

    def get_decision(self, decision_id, *, tenant_id):
        tenant_id = self._require_tenant_id(tenant_id)

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT *
                FROM gagf_decision_records
                WHERE decision_id = ?
                  AND tenant_id = ?
                """,
                (decision_id, tenant_id),
            ).fetchone()

        return dict(row) if row else None

    def list_decisions(self, *, tenant_id):
        tenant_id = self._require_tenant_id(tenant_id)

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT *
                FROM gagf_decision_records
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            ).fetchall()

        return [dict(row) for row in rows]
