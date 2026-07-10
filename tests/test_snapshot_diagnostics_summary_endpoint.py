from fastapi.testclient import TestClient

import backend.app.main as main
from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger
from backend.app.gagf.snapshot_diagnostics_summary_service import (
    SnapshotDiagnosticsSummaryService,
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

    def build_test_summary_service():
        return SnapshotDiagnosticsSummaryService(build_test_ledger())

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsLedger",
        build_test_ledger,
    )

    monkeypatch.setattr(
        main,
        "SnapshotDiagnosticsSummaryService",
        build_test_summary_service,
    )


def test_snapshot_diagnostics_summary_endpoint_returns_empty_summary(monkeypatch, tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    install_test_diagnostics_ledger(monkeypatch, ledger_path)

    response = client.get("/snapshot-diagnostics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["record_count"] == 0
    assert data["average_confidence_score"] == 0.0
    assert data["confidence_band_counts"]["high"] == 0
    assert data["diagnostic_band_counts"]["healthy"] == 0
    assert data["conflict_summary"]["total_conflicts"] == 0
    assert data["source_summary"]["supporting_sources"] == []


def test_snapshot_diagnostics_summary_endpoint_summarizes_persisted_snapshot_diagnostics(
    monkeypatch,
    tmp_path,
):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    install_test_diagnostics_ledger(monkeypatch, ledger_path)

    response_one = client.post(
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

    response_two = client.post(
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

    assert response_one.status_code == 200
    assert response_two.status_code == 200

    response = client.get("/snapshot-diagnostics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["record_count"] == 2
    assert data["average_confidence_score"] == 0.8848

    assert data["confidence_band_counts"]["high"] == 1
    assert data["confidence_band_counts"]["medium"] == 1
    assert data["confidence_band_counts"]["low"] == 0

    assert data["diagnostic_band_counts"]["healthy"] == 1
    assert data["diagnostic_band_counts"]["watch"] == 1

    assert data["conflict_summary"]["total_conflicts"] == 1
    assert data["conflict_summary"]["severity_counts"]["warning"] == 1

    assert data["source_summary"]["average_source_count"] == 2.5
    assert data["source_summary"]["supporting_sources"] == [
        "defender",
        "jira",
        "okta",
        "sentinelone",
    ]


def test_snapshot_diagnostics_summary_route_is_not_captured_as_snapshot_id(
    monkeypatch,
    tmp_path,
):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    install_test_diagnostics_ledger(monkeypatch, ledger_path)

    response = client.get("/snapshot-diagnostics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "snapshot_diagnostics_not_found" not in str(data)