from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_current_release_marker_reports_product_packaging_complete():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.1.0",
        "release": "assessment-factory-lite-demo-package",
        "sprint": "4.0",
        "status": "complete",
    }


def test_current_release_marker_preserves_governance_diagnostic_routes():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/diagnostics/chain" in actual_routes
    assert "/governance/interventions/candidates" in actual_routes
    assert "/governance/debt/indicators" in actual_routes


def test_current_release_marker_preserves_product_security_portfolio_routes():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/diversity" in actual_routes
    assert "/governance/architecture/platform" in actual_routes

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_current_release_marker_is_product_packaging_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "1.1.0",
        "release": "assessment-factory-lite-demo-package",
        "sprint": "4.0",
        "status": "complete",
    }


def test_current_release_marker_preserves_core_routes():
    actual_routes = {route.path for route in app.routes}

    assert "/version" in actual_routes
    assert "/governance/diagnostics/chain" in actual_routes
    assert "/governance/interventions/candidates" in actual_routes
    assert "/governance/debt/indicators" in actual_routes
    assert "/governance/architecture/diversity" in actual_routes
    assert "/governance/architecture/platform" in actual_routes



