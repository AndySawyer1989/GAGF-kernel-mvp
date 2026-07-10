from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_sprint_3_5_release_marker_version_contract():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "0.6.0",
        "release": "governance-diagnostic-chain",
        "sprint": "3.5",
        "status": "complete",
    }


def test_sprint_3_5_release_marker_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/version" in actual_routes


def test_sprint_3_5_release_marker_preserves_diagnostic_chain_route():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/diagnostics/chain" in actual_routes


def test_sprint_3_5_release_marker_preserves_intervention_candidate_route():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/interventions/candidates" in actual_routes


def test_sprint_3_5_release_marker_preserves_governance_debt_route():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/debt/indicators" in actual_routes