from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def make_event_payload(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    metadata=None,
):
    if metadata is None:
        metadata = {}

    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_occurred_at": "2026-07-09T10:00:00Z",
        "timestamp_quality": "SOURCE_OCCURRED_AT",
        "kernel_eligible": True,
        "source_system": source_system,
        "metadata": metadata,
    }


def test_governance_debt_indicator_endpoint_returns_empty_result():
    response = client.post(
        "/governance/debt/indicators",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
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


def test_governance_debt_indicator_endpoint_detects_security_governance_debt():
    response = client.post(
        "/governance/debt/indicators",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert data["signal_count"] == 1
    assert data["friction_signal_count"] == 1
    assert data["debt_indicator_count"] == 1
    assert data["dominant_debt_type"] == "security_governance_debt"
    assert data["governance_debt_score"] == 0.8635
    assert data["governance_debt_band"] == "critical"
    assert data["debt_posture"] == "critical_debt"
    assert data["intervention_urgency"] == "immediate"
    assert data["amplifier_pressure"] == 0.0
    assert data["debt_type_counts"]["security_governance_debt"] == 1

    indicator = data["debt_indicators"][0]

    assert indicator["event_id"] == "evt-1"
    assert indicator["source_system"] == "defender"
    assert indicator["source_friction_type"] == "security_pressure"
    assert indicator["debt_type"] == "security_governance_debt"
    assert indicator["debt_score"] == 0.8635
    assert indicator["debt_band"] == "critical"
    assert "Security pressure is accumulating governance debt" in indicator[
        "governance_interpretation"
    ]


def test_governance_debt_indicator_endpoint_detects_process_delivery_debt_with_amplifier():
    response = client.post(
        "/governance/debt/indicators",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="jira",
                event_type="approval_delayed",
                metadata={
                    "status": "waiting",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="github",
                event_type="pull_request_review_required",
                metadata={
                    "state": "review_required",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_count"] == 2
    assert data["signal_count"] == 2
    assert data["friction_signal_count"] == 2
    assert data["debt_indicator_count"] == 2
    assert data["dominant_debt_type"] == "process_governance_debt"
    assert data["governance_debt_score"] == 0.727
    assert data["governance_debt_band"] == "high"
    assert data["debt_posture"] == "high_debt"
    assert data["intervention_urgency"] == "near_term"
    assert data["amplifier_pressure"] == 0.73

    assert data["debt_type_counts"] == {
        "evidence_debt": 0,
        "security_governance_debt": 0,
        "identity_governance_debt": 0,
        "process_governance_debt": 1,
        "delivery_governance_debt": 1,
        "operational_governance_debt": 0,
    }


def test_governance_debt_indicator_endpoint_detects_amplifier_driven_critical_posture():
    response = client.post(
        "/governance/debt/indicators",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="okta",
                event_type="login_failed",
                metadata={
                    "outcome": "failed",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amplifier_pressure"] == 0.91
    assert data["governance_debt_score"] == 0.8488
    assert data["governance_debt_band"] == "high"
    assert data["debt_posture"] == "critical_debt"
    assert data["intervention_urgency"] == "immediate"


def test_governance_debt_indicator_endpoint_ignores_unknown_signals():
    response = client.post(
        "/governance/debt/indicators",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="unknown-source",
                event_type="unmapped_event",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_count"] == 1
    assert data["signal_count"] == 1
    assert data["friction_signal_count"] == 0
    assert data["debt_indicator_count"] == 0
    assert data["dominant_debt_type"] == "none"
    assert data["governance_debt_score"] == 0.0
    assert data["governance_debt_band"] == "none"
    assert data["debt_posture"] == "none"
    assert data["intervention_urgency"] == "none"
    assert data["debt_indicators"] == []


def test_governance_debt_indicator_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/debt/indicators" in actual_routes

