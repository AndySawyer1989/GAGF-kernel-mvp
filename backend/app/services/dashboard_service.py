import json

from backend.app.gagf.decision_ledger import DecisionLedger
from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.services.evidence_source_registry import EvidenceSourceRegistry


class DashboardService:
    def get_dashboard_summary(self):
        snapshots = SnapshotLedger().list_snapshots()
        decisions = DecisionLedger().list_decisions()

        latest_snapshot = snapshots[0] if snapshots else None
        latest_decision = decisions[0] if decisions else None

        return {
            "kernel_status": "ONLINE",
            "snapshot_count": len(snapshots),
            "decision_count": len(decisions),
            "latest_snapshot": self._format_snapshot(latest_snapshot),
            "latest_decision": self._format_decision(latest_decision),
            "latest_evidence_source": self._detect_latest_evidence_source(latest_snapshot),
        }

    def _format_snapshot(self, snapshot):
        if snapshot is None:
            return None

        return {
            "snapshot_id": snapshot["snapshot_id"],
            "status": snapshot["status"],
            "adaptive_state": json.loads(snapshot["adaptive_state_json"]),
            "evidence_confidence": json.loads(snapshot["evidence_confidence_json"]),
            "created_at": snapshot["created_at"],
        }

    def _format_decision(self, decision):
        if decision is None:
            return None

        return {
            "decision_id": decision["decision_id"],
            "snapshot_id": decision["snapshot_id"],
            "selected_strategy": decision["selected_strategy"],
            "kernel_decision": decision["kernel_decision"],
            "reason": json.loads(decision["reason_json"]),
            "decision_meta": json.loads(decision["decision_meta_json"]),
            "created_at": decision["created_at"],
        }

    def _detect_latest_evidence_source(self, snapshot):
        return EvidenceSourceRegistry.detect_from_snapshot(snapshot)