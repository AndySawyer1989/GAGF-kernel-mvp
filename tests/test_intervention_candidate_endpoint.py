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


def test_intervention_candidate_endpoint_returns_empty_result():
    response = client.post(
        "/governance/interventions/candidates",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "friction_signal_count": 0,
        "debt_indicator_count": 0,
        "intervention_candidate_count": 0,
        "dominant_intervention_type": "none",
        "intervention_posture": "none",
        "recommended_next_action": "none",
        "governance_debt_score": 0.0,
        "governance_debt_band": "none",
        "debt_posture": "none",
        "intervention_urgency": "none",
        "amplifier_pressure": 0.0,
        "intervention_type_counts": {
            "evidence_reconciliation": 0,
            "security_policy_review": 0,
            "access_policy_tuning": 0,
            "process_refactor": 0,
            "delivery_pipeline_review": 0,
            "operations_stabilization": 0,
        },
        "intervention_candidates": [],
    }


def test_intervention_candidate_endpoint_recommends_security_policy_review():
    response = client.post(
        "/governance/interventions/candidates",
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
    assert data["intervention_candidate_count"] == 1
    assert data["dominant_intervention_type"] == "security_policy_review"
    assert data["intervention_posture"] == "immediate_intervention"
    assert data["governance_debt_score"] == 0.8635
    assert data["governance_debt_band"] == "critical"
    assert data["debt_posture"] == "critical_debt"
    assert data["intervention_urgency"] == "immediate"

    candidate = data["intervention_candidates"][0]

    assert candidate["event_id"] == "evt-1"
    assert candidate["source_system"] == "defender"
    assert candidate["source_debt_type"] == "security_governance_debt"
    assert candidate["intervention_type"] == "security_policy_review"
    assert candidate["priority_score"] == 0.8279
    assert candidate["priority_band"] == "high"
    assert "Review security policy" in candidate["recommended_action"]


def test_intervention_candidate_endpoint_recommends_process_and_delivery_interventions():
    response = client.post(
        "/governance/interventions/candidates",
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

    assert data["intervention_candidate_count"] == 2
    assert data["dominant_intervention_type"] == "process_refactor"
    assert data["intervention_posture"] == "prioritize_intervention"
    assert data["governance_debt_score"] == 0.727
    assert data["governance_debt_band"] == "high"
    assert data["amplifier_pressure"] == 0.73

    assert data["intervention_type_counts"] == {
        "evidence_reconciliation": 0,
        "security_policy_review": 0,
        "access_policy_tuning": 0,
        "process_refactor": 1,
        "delivery_pipeline_review": 1,
        "operations_stabilization": 0,
    }

    assert [
        candidate["intervention_type"]
        for candidate in data["intervention_candidates"]
    ] == [
        "process_refactor",
        "delivery_pipeline_review",
    ]

    assert data["intervention_candidates"][0]["priority_score"] == 0.7825
    assert data["intervention_candidates"][1]["priority_score"] == 0.7055


def test_intervention_candidate_endpoint_recommends_evidence_reconciliation():
    response = client.post(
        "/governance/interventions/candidates",
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

    assert data["dominant_intervention_type"] == "evidence_reconciliation"
    assert data["intervention_posture"] == "immediate_intervention"
    assert data["recommended_next_action"].startswith(
        "Reconcile conflicting evidence claims"
    )

    candidate = data["intervention_candidates"][0]

    assert candidate["source_debt_type"] == "evidence_debt"
    assert candidate["intervention_type"] == "evidence_reconciliation"
    assert candidate["priority_score"] == 0.8488
    assert candidate["priority_band"] == "high"


def test_intervention_candidate_endpoint_ignores_unknown_signals():
    response = client.post(
        "/governance/interventions/candidates",
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
    assert data["intervention_candidate_count"] == 0
    assert data["dominant_intervention_type"] == "none"
    assert data["intervention_posture"] == "none"
    assert data["recommended_next_action"] == "none"
    assert data["intervention_candidates"] == []


def test_intervention_candidate_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/interventions/candidates" in actual_routes



