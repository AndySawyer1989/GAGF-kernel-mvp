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


def test_governance_signal_endpoint_classifies_security_risk():
    response = client.post(
        "/governance/signals",
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
    assert data["dominant_signal"] == "security_risk"
    assert data["signal_counts"]["security_risk"] == 1

    signal = data["signals"][0]

    assert signal["event_id"] == "evt-1"
    assert signal["source_system"] == "defender"
    assert signal["event_type"] == "unauthorized_api_call"
    assert signal["signal_type"] == "security_risk"
    assert signal["signal_strength"] == 1.0
    assert "Security telemetry" in signal["governance_interpretation"]


def test_governance_signal_endpoint_classifies_mixed_signal_batch():
    response = client.post(
        "/governance/signals",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="okta",
                event_type="login_failed",
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="jira",
                event_type="approval_delayed",
            ),
            make_event_payload(
                event_id="evt-4",
                source_system="github",
                event_type="pull_request_review_required",
            ),
            make_event_payload(
                event_id="evt-5",
                source_system="servicenow",
                event_type="incident",
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 5
    assert data["signal_count"] == 5
    assert data["dominant_signal"] == "security_risk"

    assert data["signal_counts"] == {
        "evidence_conflict": 0,
        "security_risk": 1,
        "identity_friction": 1,
        "workflow_friction": 1,
        "delivery_friction": 1,
        "operational_incident": 1,
        "governance_unknown": 0,
    }


def test_governance_signal_endpoint_prioritizes_evidence_conflict():
    response = client.post(
        "/governance/signals",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="security_resolution_mismatch",
                metadata={
                    "status": "conflict",
                    "severity": "high",
                },
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    signal = data["signals"][0]

    assert data["dominant_signal"] == "evidence_conflict"
    assert data["signal_counts"]["evidence_conflict"] == 1
    assert signal["signal_type"] == "evidence_conflict"
    assert signal["signal_strength"] == 0.75
    assert "inconsistent claims" in signal["governance_interpretation"]


def test_governance_signal_endpoint_handles_unknown_event():
    response = client.post(
        "/governance/signals",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="unknown-source",
                event_type="unmapped_event",
                metadata={
                    "note": "no known governance mapping",
                },
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    signal = data["signals"][0]

    assert data["dominant_signal"] == "governance_unknown"
    assert data["signal_counts"]["governance_unknown"] == 1
    assert signal["signal_type"] == "governance_unknown"
    assert signal["signal_strength"] == 0.0


def test_governance_signal_endpoint_handles_empty_batch():
    response = client.post(
        "/governance/signals",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
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