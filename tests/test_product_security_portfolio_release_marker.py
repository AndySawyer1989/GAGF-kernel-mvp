from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_product_packaging_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.0.0",
        "release": "product-packaging-checkpoint",
        "sprint": "3.9",
        "status": "complete",
    }


def test_product_security_tier_endpoint_remains_available_after_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-tier" in actual_routes


def test_zta_control_mapping_endpoint_remains_available_after_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/zta-controls" in actual_routes


def test_product_security_portfolio_endpoint_remains_available_after_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-portfolio" in actual_routes


def test_product_security_portfolio_dashboard_endpoint_remains_available_after_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-portfolio/dashboard" in actual_routes

