from backend.app.gagf.governance_debt_indicator_service import (
    GovernanceDebtIndicatorService,
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


def test_governance_debt_indicator_service_returns_empty_result():
    result = GovernanceDebtIndicatorService().assess_events([])

    assert result == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "friction_signal_count": 0,
        "debt_indicator_count": 0,
        "dominant_debt_type": "none",
        "governance_debt_score": 0.0,
        "governance_debt_band": "none",
        "debt_posture": "none",
        "intervention_urgency": "none",
        "amplifier_pressure": 0.0,
        "debt_type_counts": {
            "evidence_debt": 0,
            "security_governance_debt": 0,
            "identity_governance_debt": 0,
            "process_governance_debt": 0,
            "delivery_governance_debt": 0,
            "operational_governance_debt": 0,
        },
        "debt_indicators": [],
    }


def test_governance_debt_indicator_service_detects_security_governance_debt():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        )
    ]

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["signal_count"] == 1
    assert result["friction_signal_count"] == 1
    assert result["debt_indicator_count"] == 1
    assert result["dominant_debt_type"] == "security_governance_debt"
    assert result["governance_debt_score"] == 0.8635
    assert result["governance_debt_band"] == "critical"
    assert result["debt_posture"] == "critical_debt"
    assert result["intervention_urgency"] == "immediate"
    assert result["amplifier_pressure"] == 0.0
    assert result["debt_type_counts"]["security_governance_debt"] == 1

    indicator = result["debt_indicators"][0]

    assert indicator["event_id"] == "evt-1"
    assert indicator["source_system"] == "defender"
    assert indicator["source_friction_type"] == "security_pressure"
    assert indicator["debt_type"] == "security_governance_debt"
    assert indicator["debt_score"] == 0.8635
    assert indicator["debt_band"] == "critical"
    assert "Security pressure is accumulating governance debt" in indicator[
        "governance_interpretation"
    ]


def test_governance_debt_indicator_service_detects_identity_governance_debt():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        )
    ]

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert result["dominant_debt_type"] == "identity_governance_debt"
    assert result["governance_debt_score"] == 0.8034
    assert result["governance_debt_band"] == "high"
    assert result["debt_posture"] == "high_debt"
    assert result["intervention_urgency"] == "near_term"

    indicator = result["debt_indicators"][0]

    assert indicator["source_friction_type"] == "access_friction"
    assert indicator["debt_type"] == "identity_governance_debt"
    assert indicator["debt_score"] == 0.8034
    assert indicator["debt_band"] == "high"


def test_governance_debt_indicator_service_detects_process_delivery_debt_with_amplifier():
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

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert result["event_count"] == 2
    assert result["signal_count"] == 2
    assert result["friction_signal_count"] == 2
    assert result["debt_indicator_count"] == 2
    assert result["dominant_debt_type"] == "process_governance_debt"
    assert result["governance_debt_score"] == 0.727
    assert result["governance_debt_band"] == "high"
    assert result["debt_posture"] == "high_debt"
    assert result["intervention_urgency"] == "near_term"
    assert result["amplifier_pressure"] == 0.73

    assert result["debt_type_counts"] == {
        "evidence_debt": 0,
        "security_governance_debt": 0,
        "identity_governance_debt": 0,
        "process_governance_debt": 1,
        "delivery_governance_debt": 1,
        "operational_governance_debt": 0,
    }

    assert [
        indicator["debt_type"]
        for indicator in result["debt_indicators"]
    ] == [
        "process_governance_debt",
        "delivery_governance_debt",
    ]


def test_governance_debt_indicator_service_detects_evidence_debt():
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

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert result["dominant_debt_type"] == "evidence_debt"
    assert result["governance_debt_score"] == 0.8595
    assert result["governance_debt_band"] == "critical"
    assert result["debt_posture"] == "critical_debt"
    assert result["intervention_urgency"] == "immediate"

    indicator = result["debt_indicators"][0]

    assert indicator["source_friction_type"] == "evidence_friction"
    assert indicator["debt_type"] == "evidence_debt"
    assert indicator["debt_score"] == 0.8595
    assert indicator["debt_band"] == "critical"
    assert "Evidence disagreement is accumulating governance debt" in indicator[
        "governance_interpretation"
    ]


def test_governance_debt_indicator_service_ignores_unknown_signals():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
        )
    ]

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert result["event_count"] == 1
    assert result["signal_count"] == 1
    assert result["friction_signal_count"] == 0
    assert result["debt_indicator_count"] == 0
    assert result["dominant_debt_type"] == "none"
    assert result["governance_debt_score"] == 0.0
    assert result["governance_debt_band"] == "none"
    assert result["debt_posture"] == "none"
    assert result["intervention_urgency"] == "none"
    assert result["debt_indicators"] == []


def test_governance_debt_indicator_service_uses_amplifier_for_critical_debt_posture():
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

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert result["amplifier_pressure"] == 0.91
    assert result["governance_debt_score"] == 0.8488
    assert result["governance_debt_band"] == "high"
    assert result["debt_posture"] == "critical_debt"
    assert result["intervention_urgency"] == "immediate"


def test_governance_debt_indicator_service_sorts_debt_indicators_by_score():
    events = [
        make_event(
            event_id="evt-1",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
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
    ]

    result = GovernanceDebtIndicatorService().assess_events(events)

    assert [
        indicator["debt_type"]
        for indicator in result["debt_indicators"]
    ] == [
        "security_governance_debt",
        "process_governance_debt",
        "delivery_governance_debt",
    ]


def test_governance_debt_indicator_service_calculates_scores_safely():
    service = GovernanceDebtIndicatorService()

    assert service.calculate_debt_indicator_score(
        base_debt_weight=0.85,
        friction_intensity=0.88,
    ) == 0.8635

    assert service.calculate_debt_indicator_score(
        base_debt_weight=0.85,
        friction_intensity="unknown",
    ) == 0.4675

    assert service.calculate_governance_debt_score(
        debt_indicators=[
            {
                "debt_score": 0.80,
            },
            {
                "debt_score": 0.60,
            },
        ],
        amplifier_pressure=0.90,
    ) == 0.74
