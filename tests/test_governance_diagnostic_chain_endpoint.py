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


def test_governance_diagnostic_chain_endpoint_returns_empty_chain():
    response = client.post(
        "/governance/diagnostics/chain",
        json=[],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 0
    assert data["chain_stage_count"] == 5
    assert data["chain_posture"] == "none"
    assert data["recommended_next_action"] == "none"

    assert data["chain_summary"] == {
        "dominant_signal": "none",
        "governance_posture": "none",
        "correlation_posture": "none",
        "dominant_friction_type": "none",
        "friction_posture": "none",
        "dominant_debt_type": "none",
        "governance_debt_score": 0.0,
        "governance_debt_band": "none",
        "debt_posture": "none",
        "intervention_urgency": "none",
        "dominant_intervention_type": "none",
        "intervention_posture": "none",
        "signal_count": 0,
        "correlation_count": 0,
        "friction_signal_count": 0,
        "debt_indicator_count": 0,
        "intervention_candidate_count": 0,
    }


def test_governance_diagnostic_chain_endpoint_diagnoses_security_chain():
    response = client.post(
        "/governance/diagnostics/chain",
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
    assert data["chain_stage_count"] == 5
    assert data["chain_posture"] == "critical_governance_diagnosis"
    assert data["recommended_next_action"].startswith("Review security policy")

    summary = data["chain_summary"]

    assert summary["dominant_signal"] == "security_risk"
    assert summary["governance_posture"] == "urgent_attention"
    assert summary["correlation_posture"] == "none"
    assert summary["dominant_friction_type"] == "security_pressure"
    assert summary["friction_posture"] == "severe_friction"
    assert summary["dominant_debt_type"] == "security_governance_debt"
    assert summary["governance_debt_score"] == 0.8635
    assert summary["governance_debt_band"] == "critical"
    assert summary["debt_posture"] == "critical_debt"
    assert summary["intervention_urgency"] == "immediate"
    assert summary["dominant_intervention_type"] == "security_policy_review"
    assert summary["intervention_posture"] == "immediate_intervention"
    assert summary["signal_count"] == 1
    assert summary["correlation_count"] == 0
    assert summary["friction_signal_count"] == 1
    assert summary["debt_indicator_count"] == 1
    assert summary["intervention_candidate_count"] == 1


def test_governance_diagnostic_chain_endpoint_diagnoses_process_delivery_chain():
    response = client.post(
        "/governance/diagnostics/chain",
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

    assert data["chain_posture"] == "high_governance_diagnosis"
    assert data["recommended_next_action"].startswith("Refactor approval")

    summary = data["chain_summary"]

    assert summary["dominant_signal"] == "workflow_friction"
    assert summary["correlation_posture"] == "moderate_correlation"
    assert summary["dominant_friction_type"] == "process_friction"
    assert summary["friction_posture"] == "high_friction"
    assert summary["dominant_debt_type"] == "process_governance_debt"
    assert summary["governance_debt_score"] == 0.727
    assert summary["governance_debt_band"] == "high"
    assert summary["debt_posture"] == "high_debt"
    assert summary["intervention_urgency"] == "near_term"
    assert summary["dominant_intervention_type"] == "process_refactor"
    assert summary["intervention_posture"] == "prioritize_intervention"
    assert summary["signal_count"] == 2
    assert summary["correlation_count"] == 1
    assert summary["friction_signal_count"] == 2
    assert summary["debt_indicator_count"] == 2
    assert summary["intervention_candidate_count"] == 2


def test_governance_diagnostic_chain_endpoint_diagnoses_evidence_conflict_chain():
    response = client.post(
        "/governance/diagnostics/chain",
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

    assert data["chain_posture"] == "critical_governance_diagnosis"
    assert data["recommended_next_action"].startswith(
        "Reconcile conflicting evidence claims"
    )

    summary = data["chain_summary"]

    assert summary["dominant_signal"] == "evidence_conflict"
    assert summary["governance_posture"] == "reconcile_evidence"
    assert summary["dominant_friction_type"] == "evidence_friction"
    assert summary["dominant_debt_type"] == "evidence_debt"
    assert summary["dominant_intervention_type"] == "evidence_reconciliation"


def test_governance_diagnostic_chain_endpoint_exposes_full_stage_payloads():
    response = client.post(
        "/governance/diagnostics/chain",
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

    assert "signal_summary" in data
    assert "correlation_result" in data
    assert "friction_result" in data
    assert "debt_result" in data
    assert "intervention_result" in data

    assert data["signal_summary"]["dominant_signal"] == "security_risk"
    assert data["friction_result"]["dominant_friction_type"] == (
        "security_pressure"
    )
    assert data["debt_result"]["dominant_debt_type"] == (
        "security_governance_debt"
    )
    assert data["intervention_result"]["dominant_intervention_type"] == (
        "security_policy_review"
    )


def test_governance_diagnostic_chain_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/diagnostics/chain" in actual_routes

