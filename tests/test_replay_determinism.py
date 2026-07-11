from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService
from backend.app.gagf.schemas import AdaptiveState, AdaptiveStateSnapshot, EvidenceConfidence


def test_replay_determinism():
    snapshot = AdaptiveStateSnapshot(
        snapshot_id="replay-snapshot-001",
        tenant_id="tenant-a",
        work_item_id="deception-test",
        status="VALID",
        adaptive_state=AdaptiveState(
            risk_index=0.90,
            uncertainty=0.40,
            coherence_psi=0.85,
            revision_pressure=0.10,
            governance_momentum=0.50,
        ),
        evidence_confidence=EvidenceConfidence(
            score=1.0,
            factors={
                "timestamp_quality": 1.0,
                "sensor_reliability": 1.0,
                "cross_source_agreement": 1.0,
                "telemetry_completeness": 1.0,
            },
        ),
        evidence=["evt-1", "evt-2"],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": 2,
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    gpl = GPLLoader("backend/app/gagf/policies/gpl_v0_1.yaml")
    arbiter = ArbitrationService(gpl)

    decision1 = arbiter.arbitrate(snapshot, "Probe", "continue")
    decision2 = arbiter.arbitrate(snapshot, "Probe", "continue")

    assert decision1 == decision2
    assert decision1.selected_strategy == "Contain"
