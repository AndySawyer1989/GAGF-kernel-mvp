from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.schemas import RawSecurityEvent, AdaptiveStateSnapshot
from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService
from backend.app.gagf.decision_ledger import DecisionLedger


def test_full_pipeline_selects_contain():
    events = [
        RawSecurityEvent(event_id="evt-1", event_type="honeyfile_interaction", timestamp_quality="SOURCE_OCCURRED_AT"),
        RawSecurityEvent(event_id="evt-2", event_type="honeyfile_interaction", timestamp_quality="SOURCE_OCCURRED_AT"),
        RawSecurityEvent(event_id="evt-3", event_type="unauthorized_api_call", timestamp_quality="SOURCE_OCCURRED_AT"),
        RawSecurityEvent(event_id="evt-4", event_type="lateral_movement_pattern", timestamp_quality="SOURCE_OCCURRED_AT"),
    ]

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id="pytest-snapshot-001",
        tenant_id="tenant-a",
        work_item_id="deception-test",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=adapter_result.evidence,
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(snapshot, adapter_result.normalization_applied)

    gpl = GPLLoader("backend/app/gagf/policies/gpl_v0_1.yaml")
    decision = ArbitrationService(gpl).arbitrate(snapshot, "Probe", "continue")

    decision_id = DecisionLedger().save_decision(decision, evidence=snapshot.evidence)

    assert snapshot.adaptive_state.risk_index == 0.9
    assert decision.selected_strategy == "Contain"
    assert decision.kernel_decision == "transition_to_contain"
    assert decision.decision_meta.is_override_triggered is True
    assert decision_id is not None


