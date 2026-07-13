from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger


def test_snapshot_diagnostics_ledger_saves_and_reads_diagnostics(tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"
    ledger = SnapshotDiagnosticsLedger(str(ledger_path))

    record = ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": 0.9622,
            "confidence_band": "high",
            "diagnostics": {
                "event_count": 3,
            },
        },
    )

    assert record["snapshot_id"] == "snapshot-1"
    assert record["diagnostics"]["confidence_score"] == 0.9622
    assert record["diagnostics"]["confidence_band"] == "high"
    assert "saved_at" in record

    records = ledger.list_diagnostics()

    assert len(records) == 1
    assert records[0]["snapshot_id"] == "snapshot-1"


def test_snapshot_diagnostics_ledger_gets_latest_record_for_snapshot_id(tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"
    ledger = SnapshotDiagnosticsLedger(str(ledger_path))

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": 0.80,
        },
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": 0.90,
        },
    )

    result = ledger.get_diagnostics("snapshot-1")

    assert result["snapshot_id"] == "snapshot-1"
    assert result["diagnostics"]["confidence_score"] == 0.90


def test_snapshot_diagnostics_ledger_returns_none_for_missing_snapshot_id(tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"
    ledger = SnapshotDiagnosticsLedger(str(ledger_path))

    assert ledger.get_diagnostics("missing-snapshot") is None


def test_snapshot_diagnostics_ledger_returns_empty_list_when_no_file_exists(tmp_path):
    ledger_path = tmp_path / "missing_snapshot_diagnostics.jsonl"
    ledger = SnapshotDiagnosticsLedger(str(ledger_path))

    assert ledger.list_diagnostics() == []



