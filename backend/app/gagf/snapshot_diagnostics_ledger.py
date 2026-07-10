import json
from datetime import datetime, timezone
from pathlib import Path


class SnapshotDiagnosticsLedger:
    def __init__(self, ledger_path: str = "data/snapshot_diagnostics.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def save_diagnostics(self, snapshot_id: str, diagnostics: dict) -> dict:
        record = {
            "snapshot_id": snapshot_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "diagnostics": diagnostics,
        }

        with open(self.ledger_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, default=str) + "\n")

        return record

    def list_diagnostics(self) -> list[dict]:
        if not self.ledger_path.exists():
            return []

        records = []

        with open(self.ledger_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                records.append(json.loads(line))

        return records

    def get_diagnostics(self, snapshot_id: str) -> dict | None:
        records = self.list_diagnostics()

        for record in reversed(records):
            if record.get("snapshot_id") == snapshot_id:
                return record

        return None