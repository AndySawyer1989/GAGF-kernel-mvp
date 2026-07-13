from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.schemas import RawSecurityEvent, AdaptiveStateSnapshot
from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService


def build_snapshot(events, snapshot_id):
    adapter_result = MetricAdapter().build_snapshot(events)

    return AdaptiveStateSnapshot(
        snapshot_id=snapshot_id,
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


def test_sustained_attack_lifecycle_normal_probe_contain():
    gpl = GPLLoader("backend/app/gagf/policies/gpl_v0_1.yaml")
    arbiter = ArbitrationService(gpl)

    events = []

    snapshot = build_snapshot(events, "state-t0")
    decision = arbiter.arbitrate(snapshot, "Normal", "continue")
    assert decision.selected_strategy == "Normal"

    events.append(
        RawSecurityEvent(
            event_id="evt-1",
            event_type="honeyfile_interaction",
            timestamp_quality="SOURCE_OCCURRED_AT",
        )
    )

    snapshot = build_snapshot(events, "state-t1")
    decision = arbiter.arbitrate(snapshot, "Normal", "continue")
    assert decision.selected_strategy == "Normal"

    events.append(
        RawSecurityEvent(
            event_id="evt-2",
            event_type="honeyfile_interaction",
            timestamp_quality="SOURCE_OCCURRED_AT",
        )
    )

    snapshot = build_snapshot(events, "state-t2")
    decision = arbiter.arbitrate(snapshot, "Normal", "continue")
    assert decision.selected_strategy == "Probe"

    events.extend(
        [
            RawSecurityEvent(
                event_id="evt-3",
                event_type="unauthorized_api_call",
                timestamp_quality="SOURCE_OCCURRED_AT",
            ),
            RawSecurityEvent(
                event_id="evt-4",
                event_type="lateral_movement_pattern",
                timestamp_quality="SOURCE_OCCURRED_AT",
            ),
        ]
    )

    snapshot = build_snapshot(events, "state-t3")
    decision = arbiter.arbitrate(snapshot, "Probe", "continue")
    assert decision.selected_strategy == "Contain"
    assert decision.decision_meta.is_override_triggered is True



