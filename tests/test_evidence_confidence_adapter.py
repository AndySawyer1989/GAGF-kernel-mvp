from backend.app.gagf.evidence_confidence_adapter import EvidenceConfidenceAdapter
from backend.app.gagf.schemas import EvidenceConfidence, RawSecurityEvent, TimestampQuality


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


def test_evidence_confidence_adapter_builds_confidence_for_strong_multi_source_evidence():
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

    result = EvidenceConfidenceAdapter().build_confidence(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 3
    assert result["confidence_score"] == 0.9622
    assert result["confidence_band"] == "high"
    assert isinstance(result["evidence_confidence"], EvidenceConfidence)

    confidence = result["evidence_confidence"]

    assert confidence.score == 0.9622
    assert confidence.factors["evidence_quality"] == 0.995
    assert confidence.factors["cross_source_agreement"] == 0.88
    assert confidence.factors["conflict_health"] == 1.0
    assert confidence.factors["source_coverage"] == 1.0
    assert confidence.factors["diagnostic_score"] == 0.9622


def test_evidence_confidence_adapter_builds_confidence_for_single_source_evidence():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        )
    ]

    result = EvidenceConfidenceAdapter().build_confidence(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["confidence_score"] == 0.874
    assert result["confidence_band"] == "high"

    confidence = result["evidence_confidence"]

    assert confidence.score == 0.874
    assert confidence.factors["evidence_quality"] == 1.0
    assert confidence.factors["cross_source_agreement"] == 0.58
    assert confidence.factors["conflict_health"] == 1.0
    assert confidence.factors["source_coverage"] == 1.0


def test_evidence_confidence_adapter_lowers_confidence_for_conflicting_evidence():
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

    result = EvidenceConfidenceAdapter().build_confidence(events)

    confidence = result["evidence_confidence"]

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["confidence_score"] == 0.8074
    assert result["confidence_band"] == "medium"
    assert confidence.score == 0.8074
    assert confidence.factors["conflict_health"] == 0.65
    assert result["diagnostics"]["conflicts"]["conflict_count"] == 1


def test_evidence_confidence_adapter_lowers_confidence_for_unknown_source():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unauthorized_api_call",
        )
    ]

    result = EvidenceConfidenceAdapter().build_confidence(events)

    confidence = result["evidence_confidence"]

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["confidence_score"] == 0.586
    assert result["confidence_band"] == "low"
    assert confidence.score == 0.586
    assert confidence.factors["evidence_quality"] == 0.4
    assert confidence.factors["cross_source_agreement"] == 0.32


def test_evidence_confidence_adapter_handles_empty_event_batch():
    result = EvidenceConfidenceAdapter().build_confidence([])

    confidence = result["evidence_confidence"]

    assert result["status"] == "ok"
    assert result["event_count"] == 0
    assert result["confidence_score"] == 0.35
    assert result["confidence_band"] == "low"
    assert confidence.score == 0.35
    assert confidence.factors["evidence_quality"] == 0.0
    assert confidence.factors["cross_source_agreement"] == 0.0
    assert confidence.factors["conflict_health"] == 1.0
    assert confidence.factors["source_coverage"] == 1.0


def test_evidence_confidence_adapter_scores_conflict_health():
    adapter = EvidenceConfidenceAdapter()

    assert adapter.score_conflict_health(
        {
            "conflict_count": 0,
            "severity_counts": {
                "critical": 0,
                "warning": 0,
                "info": 0,
            },
        }
    ) == 1.0

    assert adapter.score_conflict_health(
        {
            "conflict_count": 1,
            "severity_counts": {
                "critical": 0,
                "warning": 1,
                "info": 0,
            },
        }
    ) == 0.65

    assert adapter.score_conflict_health(
        {
            "conflict_count": 2,
            "severity_counts": {
                "critical": 0,
                "warning": 2,
                "info": 0,
            },
        }
    ) == 0.35

    assert adapter.score_conflict_health(
        {
            "conflict_count": 1,
            "severity_counts": {
                "critical": 1,
                "warning": 0,
                "info": 0,
            },
        }
    ) == 0.0


def test_evidence_confidence_adapter_scores_source_coverage():
    adapter = EvidenceConfidenceAdapter()

    assert adapter.score_source_coverage(
        {
            "total_sources": 7,
            "enabled_sources": 7,
            "coverage_gaps": [],
        }
    ) == 1.0

    assert adapter.score_source_coverage(
        {
            "total_sources": 4,
            "enabled_sources": 2,
            "coverage_gaps": [],
        }
    ) == 0.5

    assert adapter.score_source_coverage(
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

    assert adapter.score_source_coverage(
        {
            "total_sources": 0,
            "enabled_sources": 0,
            "coverage_gaps": [],
        }
    ) == 0.0


def test_evidence_confidence_adapter_assigns_confidence_bands():
    adapter = EvidenceConfidenceAdapter()

    assert adapter.get_confidence_band(0.90) == "high"
    assert adapter.get_confidence_band(0.70) == "medium"
    assert adapter.get_confidence_band(0.40) == "low"
    assert adapter.get_confidence_band(0.0) == "invalid"





