from backend.app.gagf.governance_signal_summary_service import (
    GovernanceSignalSummaryService,
)
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


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


def test_governance_signal_summary_service_returns_empty_summary():
    result = GovernanceSignalSummaryService().summarize_events([])

    assert result == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "dominant_signal": "none",
        "governance_posture": "none",
        "average_signal_strength": 0.0,
        "signal_counts": {
            "evidence_conflict": 0,
            "security_risk": 0,
            "identity_friction": 0,
            "workflow_friction": 0,
            "delivery_friction": 0,
            "operational_incident": 0,
            "governance_unknown": 0,
        },
        "source_distribution": {},
        "high_strength_signal_count": 0,
        "high_strength_signals": [],
    }


def test_governance_signal_summary_service_summarizes_mixed_signals():
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
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
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

    result = GovernanceSignalSummaryService().summarize_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 4
    assert result["signal_count"] == 4
    assert result["dominant_signal"] == "security_risk"
    assert result["governance_posture"] == "urgent_attention"
    assert result["average_signal_strength"] == 0.8125

    assert result["signal_counts"] == {
        "evidence_conflict": 0,
        "security_risk": 1,
        "identity_friction": 1,
        "workflow_friction": 1,
        "delivery_friction": 1,
        "operational_incident": 0,
        "governance_unknown": 0,
    }

    assert result["source_distribution"] == {
        "defender": 1,
        "github": 1,
        "jira": 1,
        "okta": 1,
    }

    assert result["high_strength_signal_count"] == 3
    assert result["high_strength_signals"] == [
        {
            "event_id": "evt-1",
            "source_system": "defender",
            "signal_type": "security_risk",
            "signal_strength": 1.0,
        },
        {
            "event_id": "evt-2",
            "source_system": "okta",
            "signal_type": "identity_friction",
            "signal_strength": 1.0,
        },
        {
            "event_id": "evt-3",
            "source_system": "jira",
            "signal_type": "workflow_friction",
            "signal_strength": 0.75,
        },
    ]


def test_governance_signal_summary_service_recommends_reconcile_evidence_for_conflict():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="security_resolution_mismatch",
            metadata={
                "status": "conflict",
                "severity": "high",
            },
        )
    ]

    result = GovernanceSignalSummaryService().summarize_events(events)

    assert result["dominant_signal"] == "evidence_conflict"
    assert result["governance_posture"] == "reconcile_evidence"
    assert result["signal_counts"]["evidence_conflict"] == 1
    assert result["average_signal_strength"] == 0.75


def test_governance_signal_summary_service_recommends_classification_gap_for_unknown():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
            metadata={
                "note": "no known governance mapping",
            },
        )
    ]

    result = GovernanceSignalSummaryService().summarize_events(events)

    assert result["dominant_signal"] == "governance_unknown"
    assert result["governance_posture"] == "classification_gap"
    assert result["average_signal_strength"] == 0.0
    assert result["high_strength_signal_count"] == 0


def test_governance_signal_summary_service_recommends_watch_for_single_high_signal():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        )
    ]

    result = GovernanceSignalSummaryService().summarize_events(events)

    assert result["dominant_signal"] == "workflow_friction"
    assert result["governance_posture"] == "watch"
    assert result["average_signal_strength"] == 0.75
    assert result["high_strength_signal_count"] == 1


def test_governance_signal_summary_service_recommends_stable_for_low_strength_known_signal():
    events = [
        make_event(
            event_id="evt-1",
            source_system="servicenow",
            event_type="incident",
            metadata={
                "impact": "routine",
            },
        )
    ]

    result = GovernanceSignalSummaryService().summarize_events(events)

    assert result["dominant_signal"] == "operational_incident"
    assert result["governance_posture"] == "stable"
    assert result["average_signal_strength"] == 0.5
    assert result["high_strength_signal_count"] == 0


def test_governance_signal_summary_service_average_ignores_non_numeric_strengths():
    service = GovernanceSignalSummaryService()

    result = service.average_signal_strength(
        [
            {
                "signal_strength": 1.0,
            },
            {
                "signal_strength": "unknown",
            },
            {
                "signal_strength": 0.5,
            },
        ]
    )

    assert result == 0.75



