from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService
from backend.app.gagf.schemas import AdaptiveState, AdaptiveStateSnapshot, EvidenceConfidence


def test_invalid_snapshot_blocks_arbitration():
    snapshot = AdaptiveStateSnapshot(
        snapshot_id="invalid-snapshot-001",
        tenant_id="tenant-a",
        work_item_id="deception-test",
        status="INVALID",
        adaptive_state=AdaptiveState(),
        evidence_confidence=EvidenceConfidence(
            score=0.0,
            factors={
                "timestamp_quality": 0.0,
                "sensor_reliability": 0.0,
                "cross_source_agreement": 0.0,
                "telemetry_completeness": 0.0,
            },
        ),
        evidence=[],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": 0,
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 1,
        },
    )

    gpl = GPLLoader("backend/app/gagf/policies/gpl_v0_1.yaml")
    decision = ArbitrationService(gpl).arbitrate(snapshot, "Normal", "continue")

    assert decision.kernel_decision == "blocked_decision"
    assert decision.selected_strategy is None
    assert "snapshot_invalid" in decision.reason

