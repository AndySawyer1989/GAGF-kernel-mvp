from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.schemas import RawSecurityEvent, AdaptiveStateSnapshot
from backend.app.gagf.snapshot_ledger import SnapshotLedger


events = [
    RawSecurityEvent(
        event_id="evt-1",
        event_type="honeyfile_interaction",
        timestamp_quality="SOURCE_OCCURRED_AT",
    )
]

adapter_result = MetricAdapter().build_snapshot(events)

snapshot = AdaptiveStateSnapshot(
    snapshot_id="snapshot-001",
    tenant_id="tenant-a",
    work_item_id="deception-test",
    status="VALID",
    adaptive_state=adapter_result.adaptive_state,
    evidence_confidence=adapter_result.evidence_confidence,
    evidence=adapter_result.evidence,
    timestamp_quality_distribution={
        "SOURCE_OCCURRED_AT": 1,
        "BACKFILLED_FROM_CREATED_AT": 0,
        "MISSING_TIMESTAMP": 0,
    },
)

ledger = SnapshotLedger()

ledger.save_snapshot(
    snapshot,
    normalization_applied=adapter_result.normalization_applied,
)

loaded = ledger.get_snapshot("snapshot-001")

print("Loaded Snapshot")
print("----------------")
print(loaded)