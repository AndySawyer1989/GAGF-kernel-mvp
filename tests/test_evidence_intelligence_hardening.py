from backend.app.gagf.evidence_confidence_adapter import EvidenceConfidenceAdapter
from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger
from backend.app.gagf.snapshot_diagnostics_risk_service import (
    SnapshotDiagnosticsRiskService,
)
from backend.app.gagf.snapshot_diagnostics_summary_service import (
    SnapshotDiagnosticsSummaryService,
)


def test_snapshot_diagnostics_ledger_ignores_blank_lines(tmp_path):
    ledger_path = tmp_path / "snapshot_diagnostics.jsonl"

    ledger_path.write_text(
        "\n"
        '{"snapshot_id": "snapshot-1", "diagnostics": {"confidence_score": 0.9}}\n'
        "\n",
        encoding="utf-8",
    )

    ledger = SnapshotDiagnosticsLedger(str(ledger_path))

    records = ledger.list_diagnostics()

    assert len(records) == 1
    assert records[0]["snapshot_id"] == "snapshot-1"
    assert records[0]["diagnostics"]["confidence_score"] == 0.9


def test_snapshot_diagnostics_ledger_returns_latest_duplicate_snapshot_record(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": 0.4,
            "confidence_band": "low",
        },
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": 0.9,
            "confidence_band": "high",
        },
    )

    result = ledger.get_diagnostics("snapshot-1")

    assert result["snapshot_id"] == "snapshot-1"
    assert result["diagnostics"]["confidence_score"] == 0.9
    assert result["diagnostics"]["confidence_band"] == "high"


def test_snapshot_diagnostics_summary_service_ignores_non_numeric_confidence_scores(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": "unknown",
            "confidence_band": "unknown",
            "diagnostics": {
                "diagnostic_band": "unknown",
                "agreement": {
                    "source_count": "unknown",
                    "supporting_sources": [],
                    "missing_roles": [],
                },
                "conflicts": {
                    "conflict_count": 0,
                    "severity_counts": {},
                },
            },
        },
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary["record_count"] == 1
    assert summary["average_confidence_score"] == 0.0
    assert summary["confidence_band_counts"]["unknown"] == 1
    assert summary["diagnostic_band_counts"]["unknown"] == 1


def test_snapshot_diagnostics_summary_service_merges_unknown_conflict_severities(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics={
            "confidence_score": 0.7,
            "confidence_band": "medium",
            "diagnostics": {
                "diagnostic_band": "watch",
                "agreement": {
                    "source_count": 2,
                    "supporting_sources": ["defender"],
                    "missing_roles": [],
                },
                "conflicts": {
                    "conflict_count": 1,
                    "severity_counts": {
                        "critical": 0,
                        "warning": 0,
                        "info": 0,
                        "experimental": 1,
                    },
                },
            },
        },
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary["conflict_summary"]["total_conflicts"] == 1
    assert summary["conflict_summary"]["severity_counts"]["experimental"] == 1


def test_snapshot_diagnostics_risk_service_threshold_bands_are_locked():
    service = SnapshotDiagnosticsRiskService()

    assert service.get_risk_band(0.75) == "critical"
    assert service.get_risk_band(0.50) == "high"
    assert service.get_risk_band(0.01) == "watch"
    assert service.get_risk_band(0.0) == "none"


def test_snapshot_diagnostics_risk_service_factor_scoring_is_locked():
    service = SnapshotDiagnosticsRiskService()

    assert service.score_low_confidence(0.90) == 0.0
    assert service.score_low_confidence(0.70) == 0.35
    assert service.score_low_confidence(0.40) == 0.75
    assert service.score_low_confidence(0.0) == 1.0
    assert service.score_low_confidence("unknown") == 0.5

    assert service.score_diagnostic_degradation("healthy") == 0.0
    assert service.score_diagnostic_degradation("watch") == 0.35
    assert service.score_diagnostic_degradation("degraded") == 0.75
    assert service.score_diagnostic_degradation("invalid") == 1.0
    assert service.score_diagnostic_degradation("unknown") == 0.5

    assert service.score_low_source_support(3) == 0.0
    assert service.score_low_source_support(2) == 0.35
    assert service.score_low_source_support(1) == 0.75
    assert service.score_low_source_support(0) == 1.0
    assert service.score_low_source_support("unknown") == 0.5


def test_evidence_confidence_adapter_band_thresholds_are_locked():
    adapter = EvidenceConfidenceAdapter()

    assert adapter.get_confidence_band(0.85) == "high"
    assert adapter.get_confidence_band(0.65) == "medium"
    assert adapter.get_confidence_band(0.01) == "low"
    assert adapter.get_confidence_band(0.0) == "invalid"


def test_evidence_confidence_adapter_source_coverage_handles_zero_sources():
    adapter = EvidenceConfidenceAdapter()

    assert adapter.score_source_coverage(
        {
            "total_sources": 0,
            "enabled_sources": 0,
            "coverage_gaps": [],
        }
    ) == 0.0


def test_evidence_confidence_adapter_conflict_health_prioritizes_critical():
    adapter = EvidenceConfidenceAdapter()

    result = adapter.score_conflict_health(
        {
            "conflict_count": 1,
            "severity_counts": {
                "critical": 1,
                "warning": 0,
                "info": 0,
            },
        }
    )

    assert result == 0.0





