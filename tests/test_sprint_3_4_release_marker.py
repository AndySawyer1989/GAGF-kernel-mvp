from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_current_release_marker_is_product_security_portfolio_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "0.8.0",
        "release": "product-security-portfolio",
        "sprint": "3.7",
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
