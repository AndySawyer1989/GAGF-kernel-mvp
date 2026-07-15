from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_delivery_packaging_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.7.0",
        "release": "assessment-factory-lite-demo-delivery-packaging",
        "sprint": "4.6",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_delivery_packaging_release_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/delivery/manifest" in actual_routes
    assert "/products/assessment-factory-lite/delivery/runbook" in actual_routes
    assert "/products/assessment-factory-lite/delivery/readiness" in actual_routes


def test_assessment_factory_lite_demo_delivery_packaging_manifest_remains_on_styling_export_object_contract():
    response = client.get("/products/assessment-factory-lite/delivery/manifest")

    assert response.status_code == 200

    payload = response.json()

    assert payload["manifest_type"] == (
        "assessment_factory_lite_demo_delivery_manifest"
    )
    assert payload["version"] == "1.6.0"
    assert payload["release"] == "assessment-factory-lite-demo-styling-export"
    assert payload["delivery_stage"] == "demo_delivery_packaging"


def test_assessment_factory_lite_demo_delivery_packaging_runbook_remains_on_styling_export_object_contract():
    response = client.get("/products/assessment-factory-lite/delivery/runbook")

    assert response.status_code == 200

    payload = response.json()

    assert payload["runbook_type"] == (
        "assessment_factory_lite_demo_operator_runbook"
    )
    assert payload["version"] == "1.6.0"
    assert payload["release"] == "assessment-factory-lite-demo-styling-export"
    assert payload["runbook_stage"] == "demo_delivery_packaging"


def test_assessment_factory_lite_demo_delivery_packaging_readiness_remains_on_styling_export_object_contract():
    response = client.get("/products/assessment-factory-lite/delivery/readiness")

    assert response.status_code == 200

    payload = response.json()

    assert payload["readiness_type"] == (
        "assessment_factory_lite_demo_delivery_readiness"
    )
    assert payload["version"] == "1.6.0"
    assert payload["release"] == "assessment-factory-lite-demo-styling-export"
    assert payload["delivery_stage"] == "demo_delivery_packaging"
    assert payload["readiness_status"] == "ready"
    assert payload["delivery_decision"]["decision"] == "go"