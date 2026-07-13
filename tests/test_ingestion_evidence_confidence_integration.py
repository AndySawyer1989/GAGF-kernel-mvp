from types import SimpleNamespace

import backend.app.main as main
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


def make_event(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
    metadata=None,
):
    if metadata is None:
        metadata = {
            "raw_payload": {
                "id": event_id,
            },
        }

    return RawSecurityEvent(
        event_id=event_id,
        event_type=event_type,
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=timestamp_quality,
        kernel_eligible=True,
        source_system=source_system,
        metadata=metadata,
    )


class FakeConnector:
    def __init__(self, events):
        self.events = events

    def normalize_events(self, raw_events):
        return self.events


class FakeSnapshotLedger:
    saved_snapshot = None
    normalization_applied = None

    def save_snapshot(self, snapshot, normalization_applied=None):
        FakeSnapshotLedger.saved_snapshot = snapshot
        FakeSnapshotLedger.normalization_applied = normalization_applied


class FakeDecisionLedger:
    saved_decision = None
    saved_snapshot_id = None

    def save_decision(self, decision, snapshot_id):
        FakeDecisionLedger.saved_decision = decision
        FakeDecisionLedger.saved_snapshot_id = snapshot_id
        return "decision-test-id"


class FakeArbiter:
    def arbitrate(self, snapshot, active_strategy, proposal):
        return SimpleNamespace(
            selected_strategy="Normal",
            kernel_decision="ALLOW",
            reason="test decision",
        )


def reset_fakes():
    FakeSnapshotLedger.saved_snapshot = None
    FakeSnapshotLedger.normalization_applied = None
    FakeDecisionLedger.saved_decision = None
    FakeDecisionLedger.saved_snapshot_id = None


def install_fakes(monkeypatch):
    reset_fakes()

    monkeypatch.setattr(main, "SnapshotLedger", lambda: FakeSnapshotLedger())
    monkeypatch.setattr(main, "DecisionLedger", lambda: FakeDecisionLedger())
    monkeypatch.setattr(main, "get_arbiter", lambda: FakeArbiter())


def test_ingest_source_saves_snapshot_with_upgraded_single_source_confidence(monkeypatch):
    install_fakes(monkeypatch)

    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        )
    ]

    result = main.ingest_source(
        payload={"events": [{"id": "raw-1"}]},
        validation_errors=[],
        connector=FakeConnector(events),
        source_system="defender",
        snapshot_prefix="defender",
        work_item_id="defender-ingestion",
    )

    snapshot = FakeSnapshotLedger.saved_snapshot

    assert result["status"] == "ingested"
    assert result["events_normalized"] == 1
    assert snapshot is not None
    assert snapshot.evidence_confidence.score == 0.874
    assert snapshot.evidence_confidence.factors["evidence_quality"] == 1.0
    assert snapshot.evidence_confidence.factors["cross_source_agreement"] == 0.58
    assert snapshot.evidence_confidence.factors["conflict_health"] == 1.0
    assert snapshot.evidence_confidence.factors["source_coverage"] == 1.0


def test_ingest_source_saves_snapshot_with_conflict_adjusted_confidence(monkeypatch):
    install_fakes(monkeypatch)

    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="sentinelone",
            event_type="verification_passed",
            metadata={
                "mitigation_status": "mitigated",
            },
        ),
    ]

    result = main.ingest_source(
        payload={"events": [{"id": "raw-1"}, {"id": "raw-2"}]},
        validation_errors=[],
        connector=FakeConnector(events),
        source_system="defender",
        snapshot_prefix="defender",
        work_item_id="defender-ingestion",
    )

    snapshot = FakeSnapshotLedger.saved_snapshot

    assert result["status"] == "ingested"
    assert result["events_normalized"] == 2
    assert snapshot is not None
    assert snapshot.evidence_confidence.score == 0.8074
    assert snapshot.evidence_confidence.factors["conflict_health"] == 0.65


def test_ingest_source_does_not_save_snapshot_when_validation_fails(monkeypatch):
    install_fakes(monkeypatch)

    result = main.ingest_source(
        payload={"events": []},
        validation_errors=["events_list_is_empty"],
        connector=FakeConnector([]),
        source_system="defender",
        snapshot_prefix="defender",
        work_item_id="defender-ingestion",
    )

    assert result == {
        "status": "failed",
        "source_system": "defender",
        "events_normalized": 0,
        "errors": ["events_list_is_empty"],
    }

    assert FakeSnapshotLedger.saved_snapshot is None
    assert FakeDecisionLedger.saved_decision is None




