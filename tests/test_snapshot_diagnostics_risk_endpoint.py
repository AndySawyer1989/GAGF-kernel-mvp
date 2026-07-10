from fastapi.testclient import TestClient

import backend.app.main as main
from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger
from backend.app.gagf.snapshot_diagnostics_risk_service import (
    SnapshotDiagnosticsRiskService,
)


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


def install_test_diagnostics_ledger(monkeypatch, ledger_path):
    def build_test_ledger():
        return SnapshotDiagnosticsLedger(str(ledger_path))

    def build_test_risk_service():
        return SnapshotDiagnosticsRiskService(build_test_ledger())

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsLedger",
        build_test_ledger,
    )

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsRiskService",
        build_test_risk_service,
    )


def test_snapshot_diagnostics_risk_endpoint_returns_empty_risk_summary(
    monkeypatch,
    tmp_path,
):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    install_test_diagnostics_ledger(monkeypatch, ledger_path)

    response = client.get("/snapshot-diagnostics/risk")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "status": "ok",
        "record_count": 0,
        "risk_record_count": 0,
        "risk_band_counts": {
            "critical": 0,
            "high": 0,
            "watch": 0,
            "none": 0,
        },
        "top_risks": [],
    }


def test_snapshot_diagnostics_risk_endpoint_returns_risk_ranked_snapshots(
    monkeypatch,
    tmp_path,
):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    install_test_diagnostics_ledger(monkeypatch, ledger_path)

    healthy_response = client.post(
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

    conflicted_response = client.post(
        "/snapshot",
        json=[
            make_event_payload(
                event_id="evt-4",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            ),
            make_event_payload(
                event_id="evt-5",
                source_system="sentinelone",
                event_type="verification_passed",
                metadata={
                    "mitigation_status": "mitigated",
                },
            ),
        ],
    )

    assert healthy_response.status_code == 200
    assert conflicted_response.status_code == 200

    healthy_snapshot_id = healthy_response.json()["snapshot_id"]
    conflicted_snapshot_id = conflicted_response.json()["snapshot_id"]

    response = client.get("/snapshot-diagnostics/risk")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["record_count"] == 2
    assert data["risk_record_count"] == 2
    assert data["risk_band_counts"]["watch"] == 2

    top_risks = data["top_risks"]

    assert len(top_risks) == 2
    assert top_risks[0]["snapshot_id"] == conflicted_snapshot_id
    assert top_risks[0]["risk_score"] == 0.425
    assert top_risks[0]["risk_band"] == "watch"
    assert top_risks[0]["conflict_count"] == 1

    assert top_risks[1]["snapshot_id"] == healthy_snapshot_id
    assert top_risks[1]["risk_score"] == 0.0525
    assert top_risks[1]["risk_band"] == "watch"


def test_snapshot_diagnostics_risk_route_is_not_captured_as_snapshot_id(
    monkeypatch,
    tmp_path,
):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    install_test_diagnostics_ledger(monkeypatch, ledger_path)

    response = client.get("/snapshot-diagnostics/risk")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "snapshot_diagnostics_not_found" not in str(data)