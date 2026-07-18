from backend.app.gagf.governance_signal_service import GovernanceSignalService
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


def test_governance_signal_service_classifies_security_sources_as_security_risk():
    event = make_event(
        event_id="evt-1",
        source_system="defender",
        event_type="unauthorized_api_call",
        metadata={
            "severity": "high",
            "status": "active",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["event_id"] == "evt-1"
    assert result["source_system"] == "defender"
    assert result["signal_type"] == "security_risk"
    assert result["signal_strength"] == 1.0
    assert "Security telemetry" in result["governance_interpretation"]


def test_governance_signal_service_classifies_identity_sources_as_identity_friction():
    event = make_event(
        event_id="evt-1",
        source_system="okta",
        event_type="user.authentication.failed",
        metadata={
            "outcome": "login_failed",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["signal_type"] == "identity_friction"
    assert result["signal_strength"] == 1.0
    assert "Identity or access telemetry" in result["governance_interpretation"]


def test_governance_signal_service_classifies_jira_as_workflow_friction():
    event = make_event(
        event_id="evt-1",
        source_system="jira",
        event_type="approval_delayed",
        metadata={
            "status": "waiting",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["signal_type"] == "workflow_friction"
    assert result["signal_strength"] == 0.75
    assert "Work management telemetry" in result["governance_interpretation"]


def test_governance_signal_service_classifies_github_as_delivery_friction():
    event = make_event(
        event_id="evt-1",
        source_system="github",
        event_type="pull_request_review_required",
        metadata={
            "check_suite": "ci_failed",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["signal_type"] == "delivery_friction"
    assert result["signal_strength"] == 1.0
    assert "Delivery telemetry" in result["governance_interpretation"]


def test_governance_signal_service_classifies_servicenow_as_operational_incident():
    event = make_event(
        event_id="evt-1",
        source_system="servicenow",
        event_type="incident",
        metadata={
            "impact": "service_degradation",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["signal_type"] == "operational_incident"
    assert result["signal_strength"] == 0.5
    assert "Operational telemetry" in result["governance_interpretation"]


def test_governance_signal_service_classifies_conflict_terms_first():
    event = make_event(
        event_id="evt-1",
        source_system="defender",
        event_type="security_resolution_mismatch",
        metadata={
            "status": "conflict",
            "severity": "high",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["signal_type"] == "evidence_conflict"
    assert result["signal_strength"] == 0.75
    assert "inconsistent claims" in result["governance_interpretation"]


def test_governance_signal_service_classifies_unknown_events():
    event = make_event(
        event_id="evt-1",
        source_system="unknown-source",
        event_type="unmapped_event",
        metadata={
            "note": "no known governance mapping",
        },
    )

    result = GovernanceSignalService().classify_event(event)

    assert result["signal_type"] == "governance_unknown"
    assert result["signal_strength"] == 0.0
    assert "does not yet map" in result["governance_interpretation"]


def test_governance_signal_service_classifies_batch_and_counts_signals():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-2",
            source_system="okta",
            event_type="login_failed",
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="approval_delayed",
        ),
        make_event(
            event_id="evt-4",
            source_system="github",
            event_type="pull_request_review_required",
        ),
        make_event(
            event_id="evt-5",
            source_system="servicenow",
            event_type="incident",
        ),
    ]

    result = GovernanceSignalService().classify_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 5
    assert result["signal_count"] == 5

    assert result["signal_counts"] == {
        "evidence_conflict": 0,
        "security_risk": 1,
        "identity_friction": 1,
        "workflow_friction": 1,
        "delivery_friction": 1,
        "operational_incident": 1,
        "governance_unknown": 0,
    }

    assert result["dominant_signal"] == "security_risk"


def test_governance_signal_service_dominant_signal_uses_priority_on_ties():
    counts = {
        "evidence_conflict": 0,
        "security_risk": 1,
        "identity_friction": 1,
        "workflow_friction": 1,
        "delivery_friction": 0,
        "operational_incident": 0,
        "governance_unknown": 0,
    }

    result = GovernanceSignalService().get_dominant_signal(counts)

    assert result == "security_risk"


def test_governance_signal_service_returns_none_for_empty_batch():
    result = GovernanceSignalService().classify_events([])

    assert result == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "dominant_signal": "none",
        "signal_counts": {
            "evidence_conflict": 0,
            "security_risk": 0,
            "identity_friction": 0,
            "workflow_friction": 0,
            "delivery_friction": 0,
            "operational_incident": 0,
            "governance_unknown": 0,
        },
        "signals": [],
    }






