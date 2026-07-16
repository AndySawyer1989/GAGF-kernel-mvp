from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_commercial_offer_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.9.0",
        "release": "assessment-factory-lite-commercial-offer",
        "sprint": "4.8",
        "status": "complete",
    }


def test_assessment_factory_lite_commercial_offer_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/assessment-offer" in actual_routes
    assert "/products/assessment-factory-lite/assessment-offer/html" in actual_routes


def test_assessment_factory_lite_commercial_offer_builder_remains_on_buyer_conversion_object_contract():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    assert response.status_code == 200

    payload = response.json()

    assert payload["offer_type"] == "assessment_factory_lite_paid_assessment_offer"
    assert payload["version"] == "1.8.0"
    assert payload["release"] == "assessment-factory-lite-buyer-conversion"
    assert payload["offer_stage"] == "paid_assessment_conversion"
    assert payload["recommended_action"] == "present_paid_assessment_offer"


def test_assessment_factory_lite_commercial_offer_html_remains_on_buyer_conversion_object_contract():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["view_type"] == (
        "assessment_factory_lite_paid_assessment_offer_html_view"
    )
    assert payload["version"] == "1.8.0"
    assert payload["release"] == "assessment-factory-lite-buyer-conversion"
    assert payload["view_stage"] == "paid_assessment_conversion"
    assert payload["recommended_action"] == "present_paid_assessment_offer_html_view"


def test_assessment_factory_lite_commercial_offer_html_contains_commercial_assets():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    assert response.status_code == 200

    html = response.json()["html"]

    assert "Assessment Factory Lite Paid Assessment Offer" in html
    assert "operations_leader" in html
    assert "approval and handoff workflow" in html
    assert "safe_non_sensitive_workflow_evidence" in html
    assert "bounded_friction_assessment" in html
    assert "USD 500 - 2500" in html
    assert "schedule_paid_assessment_conversation" in html
    assert "Demo and Assessment Intake Boundary" in html