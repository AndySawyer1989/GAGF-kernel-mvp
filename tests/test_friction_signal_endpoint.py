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


def test_friction_signal_endpoint_returns_empty_result():
    response = client.post(
        "/governance/friction/signals",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "friction_signal_count": 0,
        "dominant_friction_type": "none",
        "friction_posture": "none",
        "average_friction_intensity": 0.0,
        "friction_type_counts": {
            "evidence_friction": 0,
            "security_pressure": 0,
            "access_friction": 0,
            "process_friction": 0,
            "delivery_friction": 0,
            "operational_friction": 0,
        },
        "correlation_amplifier_count": 0,
        "correlation_amplifiers": [],
        "friction_signals": [],
    }


def test_friction_signal_endpoint_detects_security_pressure():
    response = client.post(
        "/governance/friction/signals",
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
    assert data["dominant_friction_type"] == "security_pressure"
    assert data["friction_posture"] == "severe_friction"
    assert data["average_friction_intensity"] == 0.88
    assert data["friction_type_counts"]["security_pressure"] == 1

    signal = data["friction_signals"][0]

    assert signal["event_id"] == "evt-1"
    assert signal["source_system"] == "defender"
    assert signal["source_signal_type"] == "security_risk"
    assert signal["friction_type"] == "security_pressure"
    assert signal["friction_intensity"] == 0.88
    assert signal["friction_band"] == "severe"
    assert "Security risk is creating governance pressure" in signal[
        "governance_interpretation"
    ]


def test_friction_signal_endpoint_detects_process_delivery_with_amplifier():
    response = client.post(
        "/governance/friction/signals",
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
    assert data["dominant_friction_type"] == "process_friction"
    assert data["friction_posture"] == "high_friction"
    assert data["average_friction_intensity"] == 0.685

    assert data["friction_type_counts"] == {
        "evidence_friction": 0,
        "security_pressure": 0,
        "access_friction": 0,
        "process_friction": 1,
        "delivery_friction": 1,
        "operational_friction": 0,
    }

    assert data["correlation_amplifier_count"] == 1
    assert data["correlation_amplifiers"][0]["relationship_type"] == (
        "process_delivery_coupling"
    )
    assert data["correlation_amplifiers"][0]["amplifier_strength"] == 0.73
    assert data["correlation_amplifiers"][0]["amplifier_band"] == "moderate"


def test_friction_signal_endpoint_detects_strong_correlation_amplifier():
    response = client.post(
        "/governance/friction/signals",
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

    assert data["friction_posture"] == "severe_friction"
    assert data["correlation_amplifier_count"] == 1

    amplifier = data["correlation_amplifiers"][0]

    assert amplifier["relationship_type"] == "access_security_coupling"
    assert amplifier["left_event_id"] == "evt-1"
    assert amplifier["right_event_id"] == "evt-2"
    assert amplifier["amplifier_strength"] == 0.91
    assert amplifier["amplifier_band"] == "strong"
    assert "amplify friction" in amplifier["governance_interpretation"]


def test_friction_signal_endpoint_ignores_unknown_signals():
    response = client.post(
        "/governance/friction/signals",
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
    assert data["dominant_friction_type"] == "none"
    assert data["friction_posture"] == "none"
    assert data["average_friction_intensity"] == 0.0
    assert data["friction_signals"] == []


def test_friction_signal_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/friction/signals" in actual_routes




