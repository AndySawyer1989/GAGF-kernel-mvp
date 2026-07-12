from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_architectural_diversity_platform_endpoint_returns_ok():
    response = client.get("/governance/architecture/platform")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["component_origin"] == "platform_telemetry"
    assert data["component_count"] >= 4
    assert data["kernel_component_count"] == 4
    assert data["source_component_count"] >= 0


def test_architectural_diversity_platform_endpoint_returns_core_scores():
    response = client.get("/governance/architecture/platform")

    assert response.status_code == 200

    data = response.json()

    assert "architectural_diversity_index" in data
    assert "complexity_resilience_ratio" in data
    assert "mononal_risk_score" in data
    assert "architecture_posture" in data
    assert "concentration_risk" in data
    assert "platform_architecture_status" in data


def test_architectural_diversity_platform_endpoint_returns_component_breakdowns():
    response = client.get("/governance/architecture/platform")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["component_type_counts"], dict)
    assert isinstance(data["subsystem_counts"], dict)
    assert isinstance(data["authority_zone_counts"], dict)
    assert isinstance(data["redundancy_group_counts"], dict)
    assert isinstance(data["diversity_breakdown"], dict)


def test_architectural_diversity_platform_endpoint_returns_components_and_diagnostics():
    response = client.get("/governance/architecture/platform")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["components"], list)
    assert isinstance(data["component_diagnostics"], list)
    assert len(data["components"]) == data["component_count"]
    assert len(data["component_diagnostics"]) == data["component_count"]


def test_architectural_diversity_platform_endpoint_contains_kernel_components():
    response = client.get("/governance/architecture/platform")

    assert response.status_code == 200

    data = response.json()

    component_ids = {
        component["component_id"]
        for component in data["components"]
    }

    assert "gagf-kernel" in component_ids
    assert "snapshot-ledger" in component_ids
    assert "decision-ledger" in component_ids
    assert "governance-diagnostic-chain" in component_ids


def test_architectural_diversity_platform_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/platform" in actual_routes

