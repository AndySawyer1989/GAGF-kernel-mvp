from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger
from backend.app.gagf.snapshot_diagnostics_risk_service import (
    SnapshotDiagnosticsRiskService,
)


def make_diagnostics_record(
    confidence_score=0.9622,
    confidence_band="high",
    diagnostic_band="healthy",
    source_count=3,
    missing_roles=None,
    conflict_count=0,
    severity_counts=None,
):
    if missing_roles is None:
        missing_roles = []

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
                "supporting_sources": ["defender", "jira", "okta"],
                "missing_roles": missing_roles,
            },
            "conflicts": {
                "conflict_count": conflict_count,
                "severity_counts": severity_counts,
            },
        },
    }


def test_snapshot_diagnostics_risk_service_returns_empty_summary(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    result = SnapshotDiagnosticsRiskService(ledger).get_risk_summary()

    assert result == {
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


def test_snapshot_diagnostics_risk_service_scores_healthy_snapshot_as_no_risk(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-healthy",
        diagnostics=make_diagnostics_record(),
    )

    result = SnapshotDiagnosticsRiskService(ledger).get_risk_summary()
    risk = result["top_risks"][0]

    assert result["record_count"] == 1
    assert result["risk_record_count"] == 0
    assert result["risk_band_counts"]["none"] == 1
    assert risk["snapshot_id"] == "snapshot-healthy"
    assert risk["risk_score"] == 0.0
    assert risk["risk_band"] == "none"


def test_snapshot_diagnostics_risk_service_scores_watch_snapshot(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-watch",
        diagnostics=make_diagnostics_record(
            confidence_score=0.8074,
            confidence_band="medium",
            diagnostic_band="watch",
            source_count=2,
            missing_roles=["identity_evidence"],
            conflict_count=1,
            severity_counts={
                "critical": 0,
                "warning": 1,
                "info": 0,
            },
        ),
    )

    result = SnapshotDiagnosticsRiskService(ledger).get_risk_summary()
    risk = result["top_risks"][0]

    assert result["risk_record_count"] == 1
    assert result["risk_band_counts"]["watch"] == 1
    assert risk["snapshot_id"] == "snapshot-watch"
    assert risk["risk_score"] == 0.38
    assert risk["risk_band"] == "watch"
    assert risk["factors"]["conflict_pressure"] == 0.5


def test_snapshot_diagnostics_risk_service_scores_high_risk_snapshot(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-high-risk",
        diagnostics=make_diagnostics_record(
            confidence_score=0.586,
            confidence_band="low",
            diagnostic_band="degraded",
            source_count=1,
            missing_roles=[
                "identity_evidence",
                "workflow_evidence",
                "incident_evidence",
            ],
            conflict_count=2,
            severity_counts={
                "critical": 0,
                "warning": 2,
                "info": 0,
            },
        ),
    )

    result = SnapshotDiagnosticsRiskService(ledger).get_risk_summary()
    risk = result["top_risks"][0]

    assert result["risk_record_count"] == 1
    assert result["risk_band_counts"]["high"] == 1
    assert risk["snapshot_id"] == "snapshot-high-risk"
    assert risk["risk_score"] == 0.735
    assert risk["risk_band"] == "high"


def test_snapshot_diagnostics_risk_service_scores_critical_snapshot(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-critical",
        diagnostics=make_diagnostics_record(
            confidence_score=0.0,
            confidence_band="invalid",
            diagnostic_band="invalid",
            source_count=0,
            missing_roles=[
                "identity_evidence",
                "threat_evidence",
                "delivery_evidence",
                "workflow_evidence",
                "incident_evidence",
            ],
            conflict_count=1,
            severity_counts={
                "critical": 1,
                "warning": 0,
                "info": 0,
            },
        ),
    )

    result = SnapshotDiagnosticsRiskService(ledger).get_risk_summary()
    risk = result["top_risks"][0]

    assert result["risk_record_count"] == 1
    assert result["risk_band_counts"]["critical"] == 1
    assert risk["snapshot_id"] == "snapshot-critical"
    assert risk["risk_score"] == 1.0
    assert risk["risk_band"] == "critical"


def test_snapshot_diagnostics_risk_service_sorts_highest_risk_first(tmp_path):
    ledger = SnapshotDiagnosticsLedger(
        str(tmp_path / "snapshot_diagnostics.jsonl")
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-watch",
        diagnostics=make_diagnostics_record(
            confidence_score=0.8074,
            confidence_band="medium",
            diagnostic_band="watch",
            source_count=2,
            missing_roles=["identity_evidence"],
            conflict_count=1,
            severity_counts={
                "critical": 0,
                "warning": 1,
                "info": 0,
            },
        ),
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-critical",
        diagnostics=make_diagnostics_record(
            confidence_score=0.0,
            confidence_band="invalid",
            diagnostic_band="invalid",
            source_count=0,
            missing_roles=[
                "identity_evidence",
                "threat_evidence",
                "delivery_evidence",
                "workflow_evidence",
                "incident_evidence",
            ],
            conflict_count=1,
            severity_counts={
                "critical": 1,
                "warning": 0,
                "info": 0,
            },
        ),
    )

    ledger.save_diagnostics(
        snapshot_id="snapshot-healthy",
        diagnostics=make_diagnostics_record(),
    )

    result = SnapshotDiagnosticsRiskService(ledger).get_risk_summary()

    assert [record["snapshot_id"] for record in result["top_risks"]] == [
        "snapshot-critical",
        "snapshot-watch",
        "snapshot-healthy",
    ]


def test_snapshot_diagnostics_risk_service_handles_missing_or_malformed_values():
    service = SnapshotDiagnosticsRiskService()

    record = {
        "snapshot_id": "snapshot-malformed",
        "diagnostics": {
            "confidence_score": "unknown",
            "confidence_band": "unknown",
            "diagnostics": {
                "diagnostic_band": "unknown",
                "agreement": {
                    "source_count": "unknown",
                    "missing_roles": ["identity_evidence"],
                },
                "conflicts": {
                    "conflict_count": 0,
                    "severity_counts": {},
                },
            },
        },
    }

    risk = service.score_record(record)

    assert risk["snapshot_id"] == "snapshot-malformed"
    assert risk["risk_score"] == 0.3775
    assert risk["risk_band"] == "watch"
    assert risk["factors"]["low_confidence"] == 0.5
    assert risk["factors"]["diagnostic_degradation"] == 0.5
    assert risk["factors"]["low_source_support"] == 0.5


