from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def build_architecture_result(
    component_count=11,
    architectural_diversity_index=0.5682,
    complexity_resilience_ratio=0.6637,
    mononal_risk_score=0.4318,
    architecture_posture="mixed_resilience_architecture",
    concentration_risk="moderate",
    platform_architecture_status="platform_architecture_balanced",
):
    return {
        "status": "ok",
        "component_count": component_count,
        "architectural_diversity_index": architectural_diversity_index,
        "complexity_resilience_ratio": complexity_resilience_ratio,
        "mononal_risk_score": mononal_risk_score,
        "architecture_posture": architecture_posture,
        "concentration_risk": concentration_risk,
        "platform_architecture_status": platform_architecture_status,
    }


def test_architecture_drift_detection_endpoint_exists():
    response = client.post(
        "/governance/architecture/drift",
        json={
            "baseline_result": build_architecture_result(),
            "current_result": build_architecture_result(),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_architecture_drift_detection_endpoint_detects_no_drift():
    response = client.post(
        "/governance/architecture/drift",
        json={
            "baseline_result": build_architecture_result(),
            "current_result": build_architecture_result(),
        },
    )

    payload = response.json()

    assert payload["drift_type"] == "architecture_drift"
    assert payload["baseline_component_count"] == 11
    assert payload["current_component_count"] == 11
    assert payload["component_count_delta"] == 0
    assert payload["drift_status"] == "no_architecture_drift"
    assert payload["recommended_action"] == "continue_monitoring"


def test_architecture_drift_detection_endpoint_detects_high_drift():
    response = client.post(
        "/governance/architecture/drift",
        json={
            "baseline_result": build_architecture_result(
                architectural_diversity_index=0.8125,
                complexity_resilience_ratio=0.8875,
                mononal_risk_score=0.1875,
                architecture_posture="adaptive_diverse_architecture",
                concentration_risk="low",
                platform_architecture_status=(
                    "platform_architecture_resilient"
                ),
            ),
            "current_result": build_architecture_result(
                architectural_diversity_index=0.5682,
                complexity_resilience_ratio=0.6637,
                mononal_risk_score=0.4318,
                architecture_posture="mixed_resilience_architecture",
                concentration_risk="moderate",
                platform_architecture_status=(
                    "platform_architecture_balanced"
                ),
            ),
        },
    )

    payload = response.json()

    assert payload["score_drift"] == {
        "architectural_diversity_index_delta": -0.2443,
        "complexity_resilience_ratio_delta": -0.2238,
        "mononal_risk_score_delta": 0.2443,
        "diversity_regressed": True,
        "resilience_regressed": True,
        "mononal_risk_increased": True,
        "severity": "high",
    }
    assert payload["posture_drift"]["posture_regressed"] is True
    assert payload["drift_status"] == "high_architecture_drift"


def test_architecture_drift_detection_endpoint_detects_critical_drift():
    response = client.post(
        "/governance/architecture/drift",
        json={
            "baseline_result": build_architecture_result(
                architectural_diversity_index=0.8125,
                complexity_resilience_ratio=0.8875,
                mononal_risk_score=0.1875,
                architecture_posture="adaptive_diverse_architecture",
                concentration_risk="low",
                platform_architecture_status=(
                    "platform_architecture_resilient"
                ),
            ),
            "current_result": build_architecture_result(
                architectural_diversity_index=0.25,
                complexity_resilience_ratio=0.2625,
                mononal_risk_score=0.75,
                architecture_posture="mononal_architecture_risk",
                concentration_risk="critical",
                platform_architecture_status=(
                    "platform_architecture_mononal_risk"
                ),
            ),
        },
    )

    payload = response.json()

    assert payload["score_drift"]["severity"] == "critical"
    assert payload["posture_drift"]["current_platform_architecture_status"] == (
        "platform_architecture_mononal_risk"
    )
    assert payload["drift_status"] == "critical_architecture_drift"
    assert payload["recommended_action"] == (
        "stabilize_architecture_and_reduce_mononal_risk"
    )


def test_architecture_drift_detection_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/drift" in actual_routes


def test_architecture_drift_detection_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "0.7.0",
        "release": "architectural-diversity-diagnostics",
        "sprint": "3.6",
        "status": "complete",
    }