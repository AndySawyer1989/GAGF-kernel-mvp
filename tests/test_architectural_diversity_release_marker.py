from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_product_packaging_release_marker_version_contract():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.2.0",
        "release": "assessment-factory-lite-demo-ui",
        "sprint": "4.1",
        "status": "complete",
    }


def test_product_packaging_release_marker_preserves_manual_architecture_route():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/diversity" in actual_routes


def test_product_packaging_release_marker_preserves_platform_architecture_route():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/platform" in actual_routes


def test_product_packaging_release_marker_preserves_diagnostic_chain_route():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/diagnostics/chain" in actual_routes


def test_product_packaging_release_marker_preserves_version_route():
    actual_routes = {route.path for route in app.routes}

    assert "/version" in actual_routes




