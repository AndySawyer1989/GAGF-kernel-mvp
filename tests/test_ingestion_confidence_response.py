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

    def save_snapshot(self, snapshot, normalization_applied=None):
        FakeSnapshotLedger.saved_snapshot = snapshot


class FakeDecisionLedger:
    def save_decision(self, decision, snapshot_id):
        return "decision-test-id"


class FakeArbiter:
    def arbitrate(self, snapshot, active_strategy, proposal):
        return SimpleNamespace(
            selected_strategy="Normal",
            kernel_decision="ALLOW",
            reason="test decision",
        )


def install_fakes(monkeypatch):
    FakeSnapshotLedger.saved_snapshot = None

    monkeypatch.setattr(main, "SnapshotLedger", lambda: FakeSnapshotLedger())
    monkeypatch.setattr(main, "DecisionLedger", lambda: FakeDecisionLedger())
    monkeypatch.setattr(main, "get_arbiter", lambda: FakeArbiter())


def test_ingest_source_response_includes_evidence_confidence_score_band_and_factors(monkeypatch):
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

    assert result["status"] == "ingested"
    assert result["events_normalized"] == 1

    assert result["evidence_confidence_score"] == 0.874
    assert result["evidence_confidence_band"] == "high"
    assert result["evidence_confidence_factors"]["evidence_quality"] == 1.0
    assert result["evidence_confidence_factors"]["cross_source_agreement"] == 0.58
    assert result["evidence_confidence_factors"]["conflict_health"] == 1.0
    assert result["evidence_confidence_factors"]["source_coverage"] == 1.0

    snapshot = FakeSnapshotLedger.saved_snapshot

    assert snapshot is not None
    assert snapshot.evidence_confidence.score == result["evidence_confidence_score"]
    assert (
        snapshot.evidence_confidence.factors
        == result["evidence_confidence_factors"]
    )


def test_ingest_source_response_includes_conflict_adjusted_confidence(monkeypatch):
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

    assert result["status"] == "ingested"
    assert result["events_normalized"] == 2

    assert result["evidence_confidence_score"] == 0.8074
    assert result["evidence_confidence_band"] == "medium"
    assert result["evidence_confidence_factors"]["conflict_health"] == 0.65


def test_ingest_source_failed_validation_does_not_return_confidence_fields(monkeypatch):
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

    assert "evidence_confidence_score" not in result
    assert "evidence_confidence_band" not in result
    assert "evidence_confidence_factors" not in result




