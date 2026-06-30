import json

from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.gagf.decision_ledger import DecisionLedger


class DashboardService:
    def __init__(self):
        self.snapshot_ledger = SnapshotLedger()
        self.decision_ledger = DecisionLedger()

    def get_dashboard_summary(self):
        snapshots = self.snapshot_ledger.list_snapshots()
        decisions = self.decision_ledger.list_decisions()

        latest_snapshot = snapshots[0] if snapshots else None
        latest_decision = decisions[0] if decisions else None

        dashboard = {
            "kernel_status": "ONLINE",
            "snapshot_count": len(snapshots),
            "decision_count": len(decisions),
            "latest_snapshot": self._format_snapshot(latest_snapshot),
            "latest_decision": self._format_decision(latest_decision),
        }

        return dashboard

    def _format_snapshot(self, snapshot):
        if snapshot is None:
            return None

        adaptive_state = json.loads(snapshot["adaptive_state_json"])
        evidence_confidence = json.loads(snapshot["evidence_confidence_json"])

        return {
            "snapshot_id": snapshot["snapshot_id"],
            "status": snapshot["status"],
            "adaptive_state": adaptive_state,
            "evidence_confidence": evidence_confidence,
            "created_at": snapshot["created_at"],
        }

    def _format_decision(self, decision):
        if decision is None:
            return None

        return {
            "decision_id": decision["decision_id"],
            "snapshot_id": decision["snapshot_id"],
            "kernel_decision": decision["kernel_decision"],
            "selected_strategy": decision["selected_strategy"],
            "reason": json.loads(decision["reason_json"]),
            "decision_meta": json.loads(decision["decision_meta_json"]),
            "created_at": decision["created_at"],
        }