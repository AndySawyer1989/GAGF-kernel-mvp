from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_product_packaging_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_product_packaging_recommendation_endpoint_remains_available_after_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/packaging/recommendation" in actual_routes


def test_product_packaging_dashboard_endpoint_remains_available_after_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/packaging/dashboard" in actual_routes


def test_product_security_portfolio_endpoint_remains_available_after_packaging_release():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-portfolio" in actual_routes


def test_product_security_portfolio_dashboard_endpoint_remains_available_after_packaging_release():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-portfolio/dashboard" in actual_routes


def test_zta_control_mapping_endpoint_remains_available_after_packaging_release():
    actual_routes = {route.path for route in app.routes}

    assert "/products/zta-controls" in actual_routes













