from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def build_drift_result(
    drift_status="high_architecture_drift",
    severity="high",
    adi_delta=-0.2443,
    crr_delta=-0.2238,
    mononal_delta=0.2443,
    posture_regressed=True,
    recommended_action="review_architecture_regression_sources",
):
    return {
        "status": "ok",
        "drift_type": "architecture_drift",
        "baseline_component_count": 4,
        "current_component_count": 11,
        "component_count_delta": 7,
        "baseline_scores": {
            "architectural_diversity_index": 0.8125,
            "complexity_resilience_ratio": 0.8875,
            "mononal_risk_score": 0.1875,
        },
        "current_scores": {
            "architectural_diversity_index": 0.5682,
            "complexity_resilience_ratio": 0.6637,
            "mononal_risk_score": 0.4318,
        },
        "score_drift": {
            "architectural_diversity_index_delta": adi_delta,
            "complexity_resilience_ratio_delta": crr_delta,
            "mononal_risk_score_delta": mononal_delta,
            "diversity_regressed": adi_delta < 0,
            "resilience_regressed": crr_delta < 0,
            "mononal_risk_increased": mononal_delta > 0,
            "severity": severity,
        },
        "posture_drift": {
            "architecture_posture_changed": True,
            "concentration_risk_changed": True,
            "platform_architecture_status_changed": True,
            "baseline_architecture_posture": (
                "adaptive_diverse_architecture"
            ),
            "current_architecture_posture": (
                "mixed_resilience_architecture"
            ),
            "baseline_concentration_risk": "low",
            "current_concentration_risk": "moderate",
            "baseline_platform_architecture_status": (
                "platform_architecture_resilient"
            ),
            "current_platform_architecture_status": (
                "platform_architecture_balanced"
            ),
            "posture_regressed": posture_regressed,
        },
        "drift_status": drift_status,
        "recommended_action": recommended_action,
    }


def test_architecture_drift_dashboard_endpoint_exists():
    response = client.post(
        "/governance/architecture/drift/dashboard",
        json={
            "drift_result": build_drift_result(),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_architecture_drift_dashboard_endpoint_returns_summary_header():
    response = client.post(
        "/governance/architecture/drift/dashboard",
        json={
            "drift_result": build_drift_result(),
        },
    )

    payload = response.json()

    assert payload["summary_type"] == "architecture_drift_dashboard"
    assert payload["drift_status"] == "high_architecture_drift"
    assert payload["drift_severity"] == "high"
    assert payload["operator_message"] == (
        "Architecture drift is high and requires regression review."
    )
    assert payload["recommended_action"] == (
        "review_architecture_regression_sources"
    )


def test_architecture_drift_dashboard_endpoint_returns_scorecards():
    response = client.post(
        "/governance/architecture/drift/dashboard",
        json={
            "drift_result": build_drift_result(),
        },
    )

    payload = response.json()

    assert payload["scorecards"] == [
        {
            "label": "ADI Drift",
            "metric": "architectural_diversity_index_delta",
            "value": -0.2443,
            "interpretation": "regressed",
        },
        {
            "label": "CRR Drift",
            "metric": "complexity_resilience_ratio_delta",
            "value": -0.2238,
            "interpretation": "regressed",
        },
        {
            "label": "Mononal Risk Drift",
            "metric": "mononal_risk_score_delta",
            "value": 0.2443,
            "interpretation": "risk_increased",
        },
    ]


def test_architecture_drift_dashboard_endpoint_returns_component_and_posture_summary():
    response = client.post(
        "/governance/architecture/drift/dashboard",
        json={
            "drift_result": build_drift_result(),
        },
    )

    payload = response.json()

    assert payload["component_summary"] == {
        "baseline_component_count": 4,
        "current_component_count": 11,
        "component_count_delta": 7,
    }

    assert payload["posture_summary"]["posture_regressed"] is True
    assert payload["posture_summary"]["baseline_architecture_posture"] == (
        "adaptive_diverse_architecture"
    )
    assert payload["posture_summary"]["current_architecture_posture"] == (
        "mixed_resilience_architecture"
    )


def test_architecture_drift_dashboard_endpoint_returns_risk_summary():
    response = client.post(
        "/governance/architecture/drift/dashboard",
        json={
            "drift_result": build_drift_result(),
        },
    )

    payload = response.json()

    assert payload["risk_summary"] == {
        "drift_status": "high_architecture_drift",
        "drift_severity": "high",
        "diversity_regressed": True,
        "resilience_regressed": True,
        "mononal_risk_increased": True,
        "posture_regressed": True,
        "highest_attention_area": "mononal_risk_increase",
    }


def test_architecture_drift_dashboard_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.0.0",
        "release": "product-packaging-checkpoint",
        "sprint": "3.9",
        "status": "complete",
    }



