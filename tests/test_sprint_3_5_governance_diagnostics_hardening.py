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


def make_process_delivery_payload():
    return [
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
    ]


def test_sprint_3_5_governance_diagnostics_routes_exist():
    actual_routes = {route.path for route in app.routes}

    required_routes = {
        "/governance/signals",
        "/governance/signals/summary",
        "/governance/signals/correlations",
        "/governance/friction/signals",
        "/governance/debt/indicators",
        "/governance/interventions/candidates",
        "/governance/diagnostics/chain",
    }

    assert required_routes.issubset(actual_routes)


def test_sprint_3_5_empty_payloads_remain_deterministic():
    endpoint_expectations = {
        "/governance/signals": {
            "status": "ok",
            "event_count": 0,
            "signal_count": 0,
            "dominant_signal": "none",
        },
        "/governance/signals/summary": {
            "status": "ok",
            "event_count": 0,
            "signal_count": 0,
            "dominant_signal": "none",
            "governance_posture": "none",
        },
        "/governance/signals/correlations": {
            "status": "ok",
            "event_count": 0,
            "signal_count": 0,
            "correlation_count": 0,
            "correlation_posture": "none",
        },
        "/governance/friction/signals": {
            "status": "ok",
            "event_count": 0,
            "signal_count": 0,
            "friction_signal_count": 0,
            "friction_posture": "none",
        },
        "/governance/debt/indicators": {
            "status": "ok",
            "event_count": 0,
            "signal_count": 0,
            "friction_signal_count": 0,
            "debt_indicator_count": 0,
            "debt_posture": "none",
        },
        "/governance/interventions/candidates": {
            "status": "ok",
            "event_count": 0,
            "signal_count": 0,
            "friction_signal_count": 0,
            "debt_indicator_count": 0,
            "intervention_candidate_count": 0,
            "intervention_posture": "none",
        },
        "/governance/diagnostics/chain": {
            "status": "ok",
            "event_count": 0,
            "chain_stage_count": 5,
            "chain_posture": "none",
            "recommended_next_action": "none",
        },
    }

    for endpoint, expected_values in endpoint_expectations.items():
        response = client.post(endpoint, json=[])

        assert response.status_code == 200

        data = response.json()

        for key, expected_value in expected_values.items():
            assert data[key] == expected_value


def test_sprint_3_5_process_delivery_chain_matches_individual_endpoints():
    payload = make_process_delivery_payload()

    signal_summary = client.post(
        "/governance/signals/summary",
        json=payload,
    ).json()
    correlation_result = client.post(
        "/governance/signals/correlations",
        json=payload,
    ).json()
    friction_result = client.post(
        "/governance/friction/signals",
        json=payload,
    ).json()
    debt_result = client.post(
        "/governance/debt/indicators",
        json=payload,
    ).json()
    intervention_result = client.post(
        "/governance/interventions/candidates",
        json=payload,
    ).json()
    chain_result = client.post(
        "/governance/diagnostics/chain",
        json=payload,
    ).json()

    summary = chain_result["chain_summary"]

    assert summary["dominant_signal"] == signal_summary["dominant_signal"]
    assert summary["governance_posture"] == signal_summary["governance_posture"]
    assert summary["signal_count"] == signal_summary["signal_count"]

    assert summary["correlation_posture"] == correlation_result[
        "correlation_posture"
    ]
    assert summary["correlation_count"] == correlation_result[
        "correlation_count"
    ]

    assert summary["dominant_friction_type"] == friction_result[
        "dominant_friction_type"
    ]
    assert summary["friction_posture"] == friction_result["friction_posture"]
    assert summary["friction_signal_count"] == friction_result[
        "friction_signal_count"
    ]

    assert summary["dominant_debt_type"] == debt_result["dominant_debt_type"]
    assert summary["governance_debt_score"] == debt_result[
        "governance_debt_score"
    ]
    assert summary["governance_debt_band"] == debt_result[
        "governance_debt_band"
    ]
    assert summary["debt_posture"] == debt_result["debt_posture"]
    assert summary["intervention_urgency"] == debt_result[
        "intervention_urgency"
    ]
    assert summary["debt_indicator_count"] == debt_result[
        "debt_indicator_count"
    ]

    assert summary["dominant_intervention_type"] == intervention_result[
        "dominant_intervention_type"
    ]
    assert summary["intervention_posture"] == intervention_result[
        "intervention_posture"
    ]
    assert summary["intervention_candidate_count"] == intervention_result[
        "intervention_candidate_count"
    ]

    assert chain_result["recommended_next_action"] == intervention_result[
        "recommended_next_action"
    ]


def test_sprint_3_5_security_chain_preserves_expected_diagnosis():
    payload = [
        make_event_payload(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        )
    ]

    response = client.post(
        "/governance/diagnostics/chain",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()
    summary = data["chain_summary"]

    assert data["chain_posture"] == "critical_governance_diagnosis"
    assert data["recommended_next_action"].startswith("Review security policy")

    assert summary["dominant_signal"] == "security_risk"
    assert summary["dominant_friction_type"] == "security_pressure"
    assert summary["dominant_debt_type"] == "security_governance_debt"
    assert summary["dominant_intervention_type"] == "security_policy_review"
    assert summary["governance_debt_score"] == 0.8635


def test_sprint_3_5_evidence_conflict_chain_preserves_reconciliation_path():
    payload = [
        make_event_payload(
            event_id="evt-1",
            source_system="defender",
            event_type="security_resolution_mismatch",
            metadata={
                "status": "conflict",
                "severity": "high",
            },
        )
    ]

    response = client.post(
        "/governance/diagnostics/chain",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()
    summary = data["chain_summary"]

    assert data["chain_posture"] == "critical_governance_diagnosis"
    assert data["recommended_next_action"].startswith(
        "Reconcile conflicting evidence claims"
    )

    assert summary["dominant_signal"] == "evidence_conflict"
    assert summary["governance_posture"] == "reconcile_evidence"
    assert summary["dominant_friction_type"] == "evidence_friction"
    assert summary["dominant_debt_type"] == "evidence_debt"
    assert summary["dominant_intervention_type"] == "evidence_reconciliation"


def test_sprint_3_5_unknown_signal_chain_preserves_classification_gap():
    payload = [
        make_event_payload(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
            metadata={
                "note": "no known governance mapping",
            },
        )
    ]

    response = client.post(
        "/governance/diagnostics/chain",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()
    summary = data["chain_summary"]

    assert data["chain_posture"] == "low_governance_diagnosis"
    assert data["recommended_next_action"] == "none"

    assert summary["dominant_signal"] == "governance_unknown"
    assert summary["governance_posture"] == "classification_gap"
    assert summary["dominant_friction_type"] == "none"
    assert summary["dominant_debt_type"] == "none"
    assert summary["dominant_intervention_type"] == "none"