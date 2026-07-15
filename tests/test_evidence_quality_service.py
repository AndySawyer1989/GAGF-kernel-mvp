from backend.app.gagf.evidence_quality_service import EvidenceQualityService
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


def make_event(
    event_id="evt-1",
    source_system="defender",
    timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
    metadata=None,
):
    if metadata is None:
        metadata = {
            "raw_payload": {
                "id": event_id,
            },
            "severity": "high",
        }

    return RawSecurityEvent(
        event_id=event_id,
        event_type="unauthorized_api_call",
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=timestamp_quality,
        kernel_eligible=True,
        source_system=source_system,
        metadata=metadata,
    )


def test_evidence_quality_service_scores_security_source_as_high_quality():
    event = make_event(source_system="defender")

    result = EvidenceQualityService().score_event(event)

    assert result["status"] == "ok"
    assert result["event_id"] == "evt-1"
    assert result["source_system"] == "defender"
    assert result["quality_score"] == 1.0
    assert result["quality_band"] == "high"
    assert result["factors"]["timestamp_quality"] == 1.0
    assert result["factors"]["source_registered"] == 1.0
    assert result["factors"]["source_enabled"] == 1.0
    assert result["factors"]["metadata_completeness"] == 1.0
    assert result["factors"]["kernel_role_present"] == 1.0
    assert result["factors"]["trust_tier_weight"] == 1.0


def test_evidence_quality_service_scores_operational_source_with_operational_trust_weight():
    event = make_event(source_system="github")

    result = EvidenceQualityService().score_event(event)

    assert result["status"] == "ok"
    assert result["source_system"] == "github"
    assert result["quality_score"] == 0.985
    assert result["quality_band"] == "high"
    assert result["factors"]["trust_tier_weight"] == 0.85


def test_evidence_quality_service_lowers_score_for_backfilled_timestamp():
    event = make_event(
        source_system="defender",
        timestamp_quality=TimestampQuality.BACKFILLED_FROM_CREATED_AT,
    )

    result = EvidenceQualityService().score_event(event)

    assert result["status"] == "ok"
    assert result["quality_score"] == 0.925
    assert result["quality_band"] == "high"
    assert result["factors"]["timestamp_quality"] == 0.7


def test_evidence_quality_service_lowers_score_for_missing_timestamp():
    event = make_event(
        source_system="defender",
        timestamp_quality=TimestampQuality.MISSING_TIMESTAMP,
    )

    result = EvidenceQualityService().score_event(event)

    assert result["status"] == "ok"
    assert result["quality_score"] == 0.75
    assert result["quality_band"] == "medium"
    assert result["factors"]["timestamp_quality"] == 0.0


def test_evidence_quality_service_lowers_score_for_missing_metadata():
    event = make_event(
        source_system="defender",
        metadata={},
    )

    result = EvidenceQualityService().score_event(event)

    assert result["status"] == "ok"
    assert result["quality_score"] == 0.85
    assert result["quality_band"] == "high"
    assert result["factors"]["metadata_completeness"] == 0.0


def test_evidence_quality_service_scores_unknown_source_as_low_quality():
    event = make_event(source_system="unknown-source")

    result = EvidenceQualityService().score_event(event)

    assert result["status"] == "ok"
    assert result["source_system"] == "unknown-source"
    assert result["quality_score"] == 0.4
    assert result["quality_band"] == "low"
    assert result["factors"]["source_registered"] == 0.0
    assert result["factors"]["source_enabled"] == 0.0
    assert result["factors"]["kernel_role_present"] == 0.0
    assert result["factors"]["trust_tier_weight"] == 0.0


def test_evidence_quality_service_scores_batch_events():
    events = [
        make_event(event_id="evt-1", source_system="defender"),
        make_event(event_id="evt-2", source_system="sentinelone"),
        make_event(event_id="evt-3", source_system="github"),
    ]

    result = EvidenceQualityService().score_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 3
    assert result["average_quality_score"] == 0.995
    assert result["average_quality_band"] == "high"
    assert len(result["events"]) == 3


def test_evidence_quality_service_scores_empty_batch_as_invalid():
    result = EvidenceQualityService().score_events([])

    assert result["status"] == "ok"
    assert result["event_count"] == 0
    assert result["average_quality_score"] == 0.0
    assert result["average_quality_band"] == "invalid"
    assert result["events"] == []





