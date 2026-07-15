from fastapi.testclient import TestClient

import backend.app.main as main
from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger


client = TestClient(main.app)


def make_event_payload(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    timestamp_quality="SOURCE_OCCURRED_AT",
    metadata=None,
):
    if metadata is None:
        metadata = {
            "raw_payload": {
                "id": event_id,
            },
        }

    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_occurred_at": "2026-07-09T10:00:00Z",
        "timestamp_quality": timestamp_quality,
        "kernel_eligible": True,
        "source_system": source_system,
        "metadata": metadata,
    }


def test_snapshot_endpoint_persists_diagnostics_for_snapshot(monkeypatch, tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsLedger",
        lambda: SnapshotDiagnosticsLedger(str(ledger_path)),
    )

    response = client.post(
        "/snapshot",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="okta",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="defender",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="jira",
                event_type="unauthorized_api_call",
            ),
        ],
    )

    assert response.status_code == 200

    snapshot = response.json()
    snapshot_id = snapshot["snapshot_id"]

    diagnostics_response = client.get(f"/snapshot-diagnostics/{snapshot_id}")

    assert diagnostics_response.status_code == 200

    data = diagnostics_response.json()

    assert data["status"] == "ok"
    assert data["snapshot_id"] == snapshot_id

    record = data["diagnostics"]

    assert record["snapshot_id"] == snapshot_id
    assert record["diagnostics"]["confidence_score"] == 0.9622
    assert record["diagnostics"]["confidence_band"] == "high"
    assert record["diagnostics"]["evidence_confidence_factors"]["evidence_quality"] == 0.995
    assert record["diagnostics"]["evidence_confidence_factors"]["cross_source_agreement"] == 0.88
    assert record["diagnostics"]["diagnostics"]["agreement"]["source_count"] == 3
    assert record["diagnostics"]["diagnostics"]["conflicts"]["conflict_count"] == 0


def test_snapshot_diagnostics_list_endpoint_returns_persisted_records(monkeypatch, tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsLedger",
        lambda: SnapshotDiagnosticsLedger(str(ledger_path)),
    )

    response = client.post(
        "/snapshot",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
            )
        ],
    )

    assert response.status_code == 200

    diagnostics_response = client.get("/snapshot-diagnostics")

    assert diagnostics_response.status_code == 200

    data = diagnostics_response.json()

    assert data["status"] == "ok"
    assert len(data["diagnostics"]) == 1
    assert data["diagnostics"][0]["diagnostics"]["confidence_score"] == 0.874
    assert data["diagnostics"][0]["diagnostics"]["confidence_band"] == "high"


def test_snapshot_diagnostics_endpoint_returns_failed_for_missing_snapshot(monkeypatch, tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsLedger",
        lambda: SnapshotDiagnosticsLedger(str(ledger_path)),
    )

    response = client.get("/snapshot-diagnostics/missing-snapshot")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "status": "failed",
        "error": "snapshot_diagnostics_not_found",
        "snapshot_id": "missing-snapshot",
    }





