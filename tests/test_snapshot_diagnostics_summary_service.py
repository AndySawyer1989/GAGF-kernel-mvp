from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger
from backend.app.gagf.snapshot_diagnostics_summary_service import (
    SnapshotDiagnosticsSummaryService,
)


def make_diagnostics_record(
    confidence_score=0.9622,
    confidence_band="high",
    diagnostic_band="healthy",
    source_count=3,
    supporting_sources=None,
    missing_roles=None,
    conflict_count=0,
    severity_counts=None,
):
    if supporting_sources is None:
        supporting_sources = ["defender", "jira", "okta"]

    if missing_roles is None:
        missing_roles = ["delivery_evidence"]

    if severity_counts is None:
        severity_counts = {
            "critical": 0,
            "warning": 0,
            "info": 0,
        }

    return {
        "confidence_score": confidence_score,
        "confidence_band": confidence_band,
        "evidence_confidence_factors": {
            "evidence_quality": 0.995,
            "cross_source_agreement": 0.88,
            "conflict_health": 1.0,
            "source_coverage": 1.0,
            "diagnostic_score": confidence_score,
        },
        "diagnostics": {
            "diagnostic_score": confidence_score,
            "diagnostic_band": diagnostic_band,
            "agreement": {
                "source_count": source_count,
                "supporting_sources": supporting_sources,
                "missing_roles": missing_roles,
            },
            "conflicts": {
                "conflict_count": conflict_count,
                "severity_counts": severity_counts,
            },
        },
    }


def test_snapshot_diagnostics_summary_service_returns_empty_summary(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary == {
        "status": "ok",
        "record_count": 0,
        "average_confidence_score": 0.0,
        "confidence_band_counts": {
            "high": 0,
            "medium": 0,
            "low": 0,
            "invalid": 0,
            "unknown": 0,
        },
        "diagnostic_band_counts": {
            "healthy": 0,
            "watch": 0,
            "degraded": 0,
            "invalid": 0,
            "unknown": 0,
        },
        "conflict_summary": {
            "total_conflicts": 0,
            "severity_counts": {
                "critical": 0,
                "warning": 0,
                "info": 0,
            },
        },
        "source_summary": {
            "average_source_count": 0.0,
            "supporting_sources": [],
            "missing_kernel_roles": [],
        },
    }


def test_snapshot_diagnostics_summary_service_summarizes_confidence_scores_and_bands(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics=make_diagnostics_record(
            confidence_score=0.9622,
            confidence_band="high",
            diagnostic_band="healthy",
        ),
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-2",
        diagnostics=make_diagnostics_record(
            confidence_score=0.8074,
            confidence_band="medium",
            diagnostic_band="watch",
        ),
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-3",
        diagnostics=make_diagnostics_record(
            confidence_score=0.586,
            confidence_band="low",
            diagnostic_band="degraded",
        ),
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary["status"] == "ok"
    assert summary["record_count"] == 3
    assert summary["average_confidence_score"] == 0.7852

    assert summary["confidence_band_counts"] == {
        "high": 1,
        "medium": 1,
        "low": 1,
        "invalid": 0,
        "unknown": 0,
    }

    assert summary["diagnostic_band_counts"] == {
        "healthy": 1,
        "watch": 1,
        "degraded": 1,
        "invalid": 0,
        "unknown": 0,
    }


def test_snapshot_diagnostics_summary_service_summarizes_conflicts(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics=make_diagnostics_record(
            conflict_count=1,
            severity_counts={
                "critical": 0,
                "warning": 1,
                "info": 0,
            },
        ),
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-2",
        diagnostics=make_diagnostics_record(
            conflict_count=2,
            severity_counts={
                "critical": 1,
                "warning": 1,
                "info": 0,
            },
        ),
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary["conflict_summary"] == {
        "total_conflicts": 3,
        "severity_counts": {
            "critical": 1,
            "warning": 2,
            "info": 0,
        },
    }


def test_snapshot_diagnostics_summary_service_summarizes_sources_and_missing_roles(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics=make_diagnostics_record(
            source_count=3,
            supporting_sources=["defender", "jira", "okta"],
            missing_roles=["delivery_evidence", "incident_evidence"],
        ),
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-2",
        diagnostics=make_diagnostics_record(
            source_count=2,
            supporting_sources=["defender", "sentinelone"],
            missing_roles=["identity_evidence"],
        ),
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary["source_summary"] == {
        "average_source_count": 2.5,
        "supporting_sources": [
            "defender",
            "jira",
            "okta",
            "sentinelone",
        ],
        "missing_kernel_roles": [
            "delivery_evidence",
            "identity_evidence",
            "incident_evidence",
        ],
    }


def test_snapshot_diagnostics_summary_service_handles_unknown_bands(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-1",
        diagnostics=make_diagnostics_record(
            confidence_band="experimental",
            diagnostic_band="experimental",
        ),
    )

    summary = SnapshotDiagnosticsSummaryService(ledger).get_summary()

    assert summary["confidence_band_counts"]["unknown"] == 1
    assert summary["diagnostic_band_counts"]["unknown"] == 1


def test_snapshot_diagnostics_summary_service_average_handles_empty_values():
    service = SnapshotDiagnosticsSummaryService()

    assert service.average([]) == 0.0
