from uuid import uuid4

from backend.app.connectors.csv_connector import CSVConnector
from backend.app.normalization.validator import EventValidator
from backend.app.normalization.normalizer import EventNormalizer

from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.gagf.decision_ledger import DecisionLedger
from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService
from backend.app.gagf.schemas import AdaptiveStateSnapshot


class IngestionService:
    def __init__(self):
        self.csv_connector = CSVConnector()
        self.validator = EventValidator()
        self.normalizer = EventNormalizer()
        self.metric_adapter = MetricAdapter()
        self.snapshot_ledger = SnapshotLedger()
        self.decision_ledger = DecisionLedger()
        self.gpl = GPLLoader("backend/app/gagf/policies/gpl_v0_1.yaml")
        self.arbiter = ArbitrationService(self.gpl)

    def ingest_csv(self, file_path: str):
        rows = self.csv_connector.read_events(file_path)

        validation = self.validator.validate_rows(rows)
        if not validation.is_valid:
            return {
                "status": "validation_failed",
                "errors": validation.errors,
            }

        events = self.normalizer.normalize_rows(rows)
        adapter_result = self.metric_adapter.build_snapshot(events)

        timestamp_quality_distribution = {
            "SOURCE_OCCURRED_AT": sum(
                1 for event in events if event.timestamp_quality == "SOURCE_OCCURRED_AT"
            ),
            "BACKFILLED_FROM_CREATED_AT": sum(
                1 for event in events if event.timestamp_quality == "BACKFILLED_FROM_CREATED_AT"
            ),
            "MISSING_TIMESTAMP": sum(
                1 for event in events if event.timestamp_quality == "MISSING_TIMESTAMP"
            ),
        }

        snapshot_status = (
            "INVALID"
            if timestamp_quality_distribution["MISSING_TIMESTAMP"] > 0
            else "VALID"
        )

        snapshot = AdaptiveStateSnapshot(
            snapshot_id=str(uuid4()),
            tenant_id="demo",
            work_item_id="csv-import",
            status=snapshot_status,
            adaptive_state=adapter_result.adaptive_state,
            evidence_confidence=adapter_result.evidence_confidence,
            evidence=adapter_result.evidence,
            timestamp_quality_distribution=timestamp_quality_distribution,
        )

        self.snapshot_ledger.save_snapshot(
            snapshot,
            normalization_applied=adapter_result.normalization_applied,
        )

        decision = self.arbiter.arbitrate(
            snapshot,
            active_strategy="Normal",
            proposal="continue",
        )

        decision_id = self.decision_ledger.save_decision(
            decision,
            evidence=snapshot.evidence,
        )

        return {
            "status": "ingested",
            "rows_received": len(rows),
            "events_normalized": len(events),
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_status": snapshot.status,
            "decision_id": decision_id,
            "selected_strategy": decision.selected_strategy,
            "kernel_decision": decision.kernel_decision,
            "reason": decision.reason,
        }