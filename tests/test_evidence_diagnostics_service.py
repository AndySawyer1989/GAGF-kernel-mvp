from backend.app.gagf.evidence_diagnostics_service import EvidenceDiagnosticsService
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


def test_evidence_diagnostics_service_returns_invalid_for_empty_batch():
    result = EvidenceDiagnosticsService().diagnose_events([])

    assert result["status"] == "ok"
    assert result["event_count"] == 0
    assert result["diagnostic_score"] == 0.35
    assert result["diagnostic_band"] == "degraded"

    assert result["quality"]["event_count"] == 0
    assert result["quality"]["average_quality_score"] == 0.0
    assert result["quality"]["average_quality_band"] == "invalid"

    assert result["agreement"]["event_count"] == 0
    assert result["agreement"]["agreement_score"] == 0.0
    assert result["agreement"]["agreement_band"] == "none"

    assert result["conflicts"]["conflict_count"] == 0
    assert result["source_coverage"]["total_sources"] == 7


def test_evidence_diagnostics_service_scores_strong_multi_source_evidence_as_healthy():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="unauthorized_api_call",
        ),
    ]

    result = EvidenceDiagnosticsService().diagnose_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 3
    assert result["diagnostic_score"] == 0.9622
    assert result["diagnostic_band"] == "healthy"

    assert result["quality"]["average_quality_score"] == 0.995
    assert result["quality"]["average_quality_band"] == "high"

    assert result["agreement"]["agreement_score"] == 0.88
    assert result["agreement"]["agreement_band"] == "strong"

    assert result["conflicts"]["conflict_count"] == 0
    assert result["source_coverage"]["coverage_gap_count"] == 0


def test_evidence_diagnostics_service_scores_single_source_evidence_as_watch():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        )
    ]

    result = EvidenceDiagnosticsService().diagnose_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["diagnostic_score"] == 0.874
    assert result["diagnostic_band"] == "healthy"

    assert result["agreement"]["agreement_score"] == 0.58
    assert result["agreement"]["agreement_band"] == "weak"

    recommendation_types = {
        recommendation["recommendation_type"]
        for recommendation in result["recommendations"]
    }

    assert "increase_cross_source_agreement" in recommendation_types
    assert "missing_kernel_roles" in recommendation_types


def test_evidence_diagnostics_service_detects_conflict_recommendation():
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

    result = EvidenceDiagnosticsService().diagnose_events(events)

    recommendation_types = {
        recommendation["recommendation_type"]
        for recommendation in result["recommendations"]
    }

    assert result["status"] == "ok"
    assert result["conflicts"]["conflict_count"] == 1
    assert result["conflicts"]["severity_counts"]["warning"] == 1
    assert "resolve_evidence_conflicts" in recommendation_types


def test_evidence_diagnostics_service_recommends_improving_low_quality_evidence():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unauthorized_api_call",
        )
    ]

    result = EvidenceDiagnosticsService().diagnose_events(events)

    recommendation_types = {
        recommendation["recommendation_type"]
        for recommendation in result["recommendations"]
    }

    assert result["status"] == "ok"
    assert result["quality"]["average_quality_score"] == 0.4
    assert result["quality"]["average_quality_band"] == "low"
    assert "improve_evidence_quality" in recommendation_types
    assert "increase_cross_source_agreement" in recommendation_types


def test_evidence_diagnostics_service_scores_conflict_health():
    service = EvidenceDiagnosticsService()

    assert service.score_conflict_health(
        {
            "conflict_count": 0,
            "severity_counts": {
                "critical": 0,
                "warning": 0,
                "info": 0,
            },
        }
    ) == 1.0

    assert service.score_conflict_health(
        {
            "conflict_count": 1,
            "severity_counts": {
                "critical": 0,
                "warning": 1,
                "info": 0,
            },
        }
    ) == 0.65

    assert service.score_conflict_health(
        {
            "conflict_count": 2,
            "severity_counts": {
                "critical": 0,
                "warning": 2,
                "info": 0,
            },
        }
    ) == 0.35

    assert service.score_conflict_health(
        {
            "conflict_count": 1,
            "severity_counts": {
                "critical": 1,
                "warning": 0,
                "info": 0,
            },
        }
    ) == 0.0


def test_evidence_diagnostics_service_scores_source_coverage():
    service = EvidenceDiagnosticsService()

    assert service.score_source_coverage(
        {
            "total_sources": 7,
            "enabled_sources": 7,
            "coverage_gaps": [],
        }
    ) == 1.0

    assert service.score_source_coverage(
        {
            "total_sources": 4,
            "enabled_sources": 2,
            "coverage_gaps": [],
        }
    ) == 0.5

    assert service.score_source_coverage(
        {
            "total_sources": 4,
            "enabled_sources": 2,
            "coverage_gaps": [
                {
                    "gap_type": "unhealthy_sources_present",
                }
            ],
        }
    ) == 0.375

    assert service.score_source_coverage(
        {
            "total_sources": 0,
            "enabled_sources": 0,
            "coverage_gaps": [],
        }
    ) == 0.0


def test_evidence_diagnostics_service_assigns_diagnostic_bands():
    service = EvidenceDiagnosticsService()

    assert service.get_diagnostic_band(0.90) == "healthy"
    assert service.get_diagnostic_band(0.70) == "watch"
    assert service.get_diagnostic_band(0.40) == "degraded"
    assert service.get_diagnostic_band(0.0) == "invalid"





