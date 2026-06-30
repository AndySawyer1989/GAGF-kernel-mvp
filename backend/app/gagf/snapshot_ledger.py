import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SnapshotLedger:
    def __init__(self, db_path="gagf.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_state_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    work_item_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    adaptive_state_json TEXT NOT NULL,
                    evidence_confidence_json TEXT NOT NULL,
                    timestamp_quality_distribution_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    normalization_applied_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_snapshot(self, snapshot, normalization_applied=None):
        normalization_applied = normalization_applied or []

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO gagf_state_snapshots (
                    snapshot_id,
                    tenant_id,
                    work_item_id,
                    status,
                    adaptive_state_json,
                    evidence_confidence_json,
                    timestamp_quality_distribution_json,
                    evidence_json,
                    normalization_applied_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.tenant_id,
                    snapshot.work_item_id,
                    snapshot.status,
                    json.dumps(snapshot.adaptive_state.model_dump()),
                    json.dumps(snapshot.evidence_confidence.model_dump()),
                    json.dumps(snapshot.timestamp_quality_distribution),
                    json.dumps(snapshot.evidence),
                    json.dumps([item.model_dump() for item in normalization_applied]),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        return snapshot.snapshot_id

    def get_snapshot(self, snapshot_id):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT *
                FROM gagf_state_snapshots
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            ).fetchone()

        return dict(row) if row else None

    def list_snapshots(self):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT *
                FROM gagf_state_snapshots
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]