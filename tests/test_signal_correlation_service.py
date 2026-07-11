from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality
from backend.app.gagf.signal_correlation_service import SignalCorrelationService


def make_event(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    metadata=None,
):
    if metadata is None:
        metadata = {}

    return RawSecurityEvent(
        event_id=event_id,
        event_type=event_type,
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
        kernel_eligible=True,
        source_system=source_system,
        metadata=metadata,
    )


def test_signal_correlation_service_returns_empty_result_for_empty_batch():
    result = SignalCorrelationService().correlate_events([])

    assert result == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "correlation_count": 0,
        "dominant_signal": "none",
        "correlation_posture": "none",
        "correlation_counts": {},
        "correlations": [],
    }


def test_signal_correlation_service_detects_identity_security_coupling():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["signal_count"] == 2
    assert result["correlation_count"] == 1
    assert result["dominant_signal"] == "security_risk"
    assert result["correlation_posture"] == "strong_correlation"

    correlation = result["correlations"][0]

    assert correlation["left_event_id"] == "evt-1"
    assert correlation["right_event_id"] == "evt-2"
    assert correlation["left_signal_type"] == "identity_friction"
    assert correlation["right_signal_type"] == "security_risk"
    assert correlation["relationship_type"] == "access_security_coupling"
    assert correlation["correlation_strength"] == 0.91
    assert "Identity friction and security risk" in correlation[
        "governance_interpretation"
    ]


def test_signal_correlation_service_detects_workflow_delivery_coupling():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
            },
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert result["correlation_count"] == 1
    assert result["correlation_posture"] == "moderate_correlation"

    correlation = result["correlations"][0]

    assert correlation["relationship_type"] == "process_delivery_coupling"
    assert correlation["correlation_strength"] == 0.73
    assert "process delay" in correlation["governance_interpretation"]


def test_signal_correlation_service_detects_evidence_conflict_security_disagreement():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="security_resolution_mismatch",
            metadata={
                "status": "conflict",
                "severity": "high",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="sentinelone",
            event_type="malware_detected",
            metadata={
                "severity": "critical",
                "status": "active",
            },
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert result["correlation_count"] == 1
    assert result["correlation_posture"] == "strong_correlation"

    correlation = result["correlations"][0]

    assert correlation["left_signal_type"] == "evidence_conflict"
    assert correlation["right_signal_type"] == "security_risk"
    assert correlation["relationship_type"] == "security_evidence_disagreement"
    assert correlation["correlation_strength"] == 0.89
    assert "security telemetry should be reconciled" in correlation[
        "governance_interpretation"
    ]


def test_signal_correlation_service_detects_same_signal_cluster():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="jira",
            event_type="work_blocked",
            metadata={
                "status": "blocked",
            },
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert result["correlation_count"] == 1
    assert result["correlation_posture"] == "moderate_correlation"

    correlation = result["correlations"][0]

    assert correlation["relationship_type"] == "same_signal_cluster"
    assert correlation["left_signal_type"] == "workflow_friction"
    assert correlation["right_signal_type"] == "workflow_friction"
    assert correlation["correlation_strength"] == 0.74
    assert "clustered governance pattern" in correlation[
        "governance_interpretation"
    ]


def test_signal_correlation_service_ignores_unknown_signals():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
        ),
        make_event(
            event_id="evt-2",
            source_system="another-unknown-source",
            event_type="another_unmapped_event",
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert result["event_count"] == 2
    assert result["signal_count"] == 2
    assert result["correlation_count"] == 0
    assert result["correlation_posture"] == "none"
    assert result["correlations"] == []


def test_signal_correlation_service_counts_relationship_types():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
        make_event(
            event_id="evt-4",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
            },
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert result["correlation_count"] == 2
    assert result["correlation_counts"] == {
        "access_security_coupling": 1,
        "process_delivery_coupling": 1,
    }


def test_signal_correlation_service_sorts_highest_strength_first():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
            },
        ),
        make_event(
            event_id="evt-3",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        ),
        make_event(
            event_id="evt-4",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
    ]

    result = SignalCorrelationService().correlate_events(events)

    assert [
        correlation["relationship_type"]
        for correlation in result["correlations"]
    ] == [
        "access_security_coupling",
        "process_delivery_coupling",
    ]


def test_signal_correlation_service_calculates_pair_strength_safely():
    service = SignalCorrelationService()

    assert service.calculate_pair_strength(
        base_strength=0.80,
        left_strength=1.0,
        right_strength=0.5,
    ) == 0.78

    assert service.calculate_pair_strength(
        base_strength=0.80,
        left_strength="unknown",
        right_strength=0.5,
    ) == 0.58
