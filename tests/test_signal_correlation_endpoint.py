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


def test_signal_correlation_endpoint_returns_empty_result_for_empty_batch():
    response = client.post(
        "/governance/signals/correlations",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "correlation_count": 0,
        "dominant_signal": "none",
        "correlation_posture": "none",
        "correlation_counts": {},
        "correlations": [],
    }


def test_signal_correlation_endpoint_detects_identity_security_coupling():
    response = client.post(
        "/governance/signals/correlations",
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

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["signal_count"] == 2
    assert data["correlation_count"] == 1
    assert data["dominant_signal"] == "security_risk"
    assert data["correlation_posture"] == "strong_correlation"
    assert data["correlation_counts"] == {
        "access_security_coupling": 1,
    }

    correlation = data["correlations"][0]

    assert correlation["left_event_id"] == "evt-1"
    assert correlation["right_event_id"] == "evt-2"
    assert correlation["left_signal_type"] == "identity_friction"
    assert correlation["right_signal_type"] == "security_risk"
    assert correlation["relationship_type"] == "access_security_coupling"
    assert correlation["correlation_strength"] == 0.91
    assert "Identity friction and security risk" in correlation[
        "governance_interpretation"
    ]


def test_signal_correlation_endpoint_detects_workflow_delivery_coupling():
    response = client.post(
        "/governance/signals/correlations",
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

    assert data["correlation_count"] == 1
    assert data["correlation_posture"] == "moderate_correlation"

    correlation = data["correlations"][0]

    assert correlation["relationship_type"] == "process_delivery_coupling"
    assert correlation["correlation_strength"] == 0.73
    assert "process delay" in correlation["governance_interpretation"]


def test_signal_correlation_endpoint_detects_same_signal_cluster():
    response = client.post(
        "/governance/signals/correlations",
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
                source_system="jira",
                event_type="work_blocked",
                metadata={
                    "status": "blocked",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["correlation_count"] == 1
    assert data["correlation_posture"] == "moderate_correlation"

    correlation = data["correlations"][0]

    assert correlation["relationship_type"] == "same_signal_cluster"
    assert correlation["left_signal_type"] == "workflow_friction"
    assert correlation["right_signal_type"] == "workflow_friction"
    assert correlation["correlation_strength"] == 0.74
    assert "clustered governance pattern" in correlation[
        "governance_interpretation"
    ]


def test_signal_correlation_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/signals/correlations" in actual_routes






