from fastapi.testclient import TestClient

from backend.app.gagf.architectural_diversity_platform_service import (
    ArchitecturalDiversityPlatformService,
)
from backend.app.main import app


client = TestClient(app)


def baseline_result(
    component_count=4,
    architectural_diversity_index=0.8125,
    complexity_resilience_ratio=0.8875,
    mononal_risk_score=0.1875,
    architecture_posture="adaptive_diverse_architecture",
    concentration_risk="low",
    platform_architecture_status="platform_architecture_resilient",
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


def fake_current_platform_result(
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
        "component_origin": "platform_telemetry",
        "source_count": 7,
        "kernel_component_count": 4,
        "source_component_count": 7,
        "component_count": component_count,
        "architectural_diversity_index": architectural_diversity_index,
        "complexity_resilience_ratio": complexity_resilience_ratio,
        "mononal_risk_score": mononal_risk_score,
        "architecture_posture": architecture_posture,
        "concentration_risk": concentration_risk,
        "platform_architecture_status": platform_architecture_status,
        "dominant_component_type": "connector",
        "component_type_counts": {},
        "subsystem_counts": {},
        "authority_zone_counts": {},
        "redundancy_group_counts": {},
        "diversity_breakdown": {},
        "component_diagnostics": [],
        "components": [],
    }


def patch_platform_result(monkeypatch, result):
    monkeypatch.setattr(
        ArchitecturalDiversityPlatformService,
        "diagnose_platform",
        lambda self: result,
    )


def test_platform_architecture_drift_endpoint_exists(monkeypatch):
    patch_platform_result(
        monkeypatch,
        fake_current_platform_result(),
    )

    response = client.post(
        "/governance/architecture/platform/drift",
        json={
            "baseline_result": baseline_result(),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_platform_architecture_drift_endpoint_uses_live_platform_current_result(
    monkeypatch,
):
    patch_platform_result(
        monkeypatch,
        fake_current_platform_result(
            component_count=11,
            architectural_diversity_index=0.5682,
            complexity_resilience_ratio=0.6637,
            mononal_risk_score=0.4318,
        ),
    )

    response = client.post(
        "/governance/architecture/platform/drift",
        json={
            "baseline_result": baseline_result(
                component_count=4,
                architectural_diversity_index=0.8125,
                complexity_resilience_ratio=0.8875,
                mononal_risk_score=0.1875,
            ),
        },
    )

    payload = response.json()

    assert payload["baseline_component_count"] == 4
    assert payload["current_component_count"] == 11
    assert payload["component_count_delta"] == 7
    assert payload["current_scores"] == {
        "architectural_diversity_index": 0.5682,
        "complexity_resilience_ratio": 0.6637,
        "mononal_risk_score": 0.4318,
    }


def test_platform_architecture_drift_endpoint_detects_high_platform_drift(
    monkeypatch,
):
    patch_platform_result(
        monkeypatch,
        fake_current_platform_result(
            architecture_posture="mixed_resilience_architecture",
            concentration_risk="moderate",
            platform_architecture_status="platform_architecture_balanced",
        ),
    )

    response = client.post(
        "/governance/architecture/platform/drift",
        json={
            "baseline_result": baseline_result(
                architecture_posture="adaptive_diverse_architecture",
                concentration_risk="low",
                platform_architecture_status=(
                    "platform_architecture_resilient"
                ),
            ),
        },
    )

    payload = response.json()

    assert payload["drift_type"] == "architecture_drift"
    assert payload["score_drift"]["severity"] == "high"
    assert payload["posture_drift"]["posture_regressed"] is True
    assert payload["drift_status"] == "high_architecture_drift"
    assert payload["recommended_action"] == (
        "review_architecture_regression_sources"
    )


def test_platform_architecture_drift_endpoint_detects_critical_platform_drift(
    monkeypatch,
):
    patch_platform_result(
        monkeypatch,
        fake_current_platform_result(
            component_count=4,
            architectural_diversity_index=0.25,
            complexity_resilience_ratio=0.2625,
            mononal_risk_score=0.75,
            architecture_posture="mononal_architecture_risk",
            concentration_risk="critical",
            platform_architecture_status=(
                "platform_architecture_mononal_risk"
            ),
        ),
    )

    response = client.post(
        "/governance/architecture/platform/drift",
        json={
            "baseline_result": baseline_result(),
        },
    )

    payload = response.json()

    assert payload["score_drift"]["severity"] == "critical"
    assert payload["drift_status"] == "critical_architecture_drift"
    assert payload["recommended_action"] == (
        "stabilize_architecture_and_reduce_mononal_risk"
    )


def test_platform_architecture_drift_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/platform/drift" in actual_routes


def test_platform_architecture_drift_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.6.0",
        "release": "assessment-factory-lite-demo-styling-export",
        "sprint": "4.5",
        "status": "complete",
    }










