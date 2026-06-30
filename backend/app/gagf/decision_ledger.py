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

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_decision_records (
                    decision_id TEXT PRIMARY KEY,
                    snapshot_id TEXT,
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

    def save_decision(self, decision, evidence=None):
        decision_id = str(uuid4())
        evidence = evidence or []

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO gagf_decision_records (
                    decision_id,
                    snapshot_id,
                    active_strategy,
                    strategy_proposal,
                    kernel_decision,
                    selected_strategy,
                    reason_json,
                    decision_meta_json,
                    evidence_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    decision.snapshot_id,
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

    def get_decision(self, decision_id):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT *
                FROM gagf_decision_records
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()

        return dict(row) if row else None
    def list_decisions(self):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT *
                FROM gagf_decision_records
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]