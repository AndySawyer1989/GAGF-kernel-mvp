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


def test_governance_signal_summary_endpoint_returns_empty_summary():
    response = client.post(
        "/governance/signals/summary",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
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


def test_governance_signal_summary_endpoint_summarizes_mixed_signals():
    response = client.post(
        "/governance/signals/summary",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="okta",
                event_type="login_failed",
                metadata={
                    "outcome": "failed",
                },
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="jira",
                event_type="approval_delayed",
                metadata={
                    "status": "waiting",
                },
            ),
            make_event_payload(
                event_id="evt-4",
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

    assert data["status"] == "ok"
    assert data["event_count"] == 4
    assert data["signal_count"] == 4
    assert data["dominant_signal"] == "security_risk"
    assert data["governance_posture"] == "urgent_attention"
    assert data["average_signal_strength"] == 0.8125

    assert data["signal_counts"] == {
        "evidence_conflict": 0,
        "security_risk": 1,
        "identity_friction": 1,
        "workflow_friction": 1,
        "delivery_friction": 1,
        "operational_incident": 0,
        "governance_unknown": 0,
    }

    assert data["source_distribution"] == {
        "defender": 1,
        "github": 1,
        "jira": 1,
        "okta": 1,
    }

    assert data["high_strength_signal_count"] == 3
    assert data["high_strength_signals"] == [
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


def test_governance_signal_summary_endpoint_recommends_reconcile_evidence_for_conflict():
    response = client.post(
        "/governance/signals/summary",
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

    assert data["dominant_signal"] == "evidence_conflict"
    assert data["governance_posture"] == "reconcile_evidence"
    assert data["signal_counts"]["evidence_conflict"] == 1
    assert data["average_signal_strength"] == 0.75


def test_governance_signal_summary_endpoint_recommends_classification_gap_for_unknown():
    response = client.post(
        "/governance/signals/summary",
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

    assert data["dominant_signal"] == "governance_unknown"
    assert data["governance_posture"] == "classification_gap"
    assert data["average_signal_strength"] == 0.0
    assert data["high_strength_signal_count"] == 0


def test_governance_signal_summary_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/signals/summary" in actual_routes




