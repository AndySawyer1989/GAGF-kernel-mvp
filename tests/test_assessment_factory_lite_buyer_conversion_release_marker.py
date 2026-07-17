from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_buyer_conversion_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.1.0",
        "release": "assessment-factory-lite-proposal-export-package",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_buyer_conversion_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-walkthrough/script" in actual_routes
    assert "/products/assessment-factory-lite/buyer-walkthrough/html" in actual_routes


def test_assessment_factory_lite_buyer_conversion_script_remains_on_delivery_packaging_object_contract():
    response = client.get("/products/assessment-factory-lite/buyer-walkthrough/script")

    assert response.status_code == 200

    payload = response.json()

    assert payload["script_type"] == (
        "assessment_factory_lite_buyer_walkthrough_script"
    )
    assert payload["version"] == "1.7.0"
    assert payload["release"] == "assessment-factory-lite-demo-delivery-packaging"
    assert payload["script_stage"] == "buyer_demo_conversion"
    assert payload["recommended_action"] == "use_buyer_walkthrough_script"


def test_assessment_factory_lite_buyer_conversion_html_remains_on_delivery_packaging_object_contract():
    response = client.get("/products/assessment-factory-lite/buyer-walkthrough/html")

    assert response.status_code == 200

    payload = response.json()

    assert payload["view_type"] == (
        "assessment_factory_lite_buyer_walkthrough_html_view"
    )
    assert payload["version"] == "1.7.0"
    assert payload["release"] == "assessment-factory-lite-demo-delivery-packaging"
    assert payload["view_stage"] == "buyer_demo_conversion"
    assert payload["recommended_action"] == "present_buyer_walkthrough_html_view"


def test_assessment_factory_lite_buyer_conversion_html_contains_conversion_assets():
    response = client.get("/products/assessment-factory-lite/buyer-walkthrough/html")

    assert response.status_code == 200

    html = response.json()["html"]

    assert "Assessment Factory Lite Buyer Walkthrough" in html
    assert "This is a sample-data-only demo of Assessment Factory Lite." in html
    assert "Most teams feel delays before they can prove them." in html
    assert "Approval Delay and Blocked Work" in html
    assert "Approval delays are creating workflow drag." in html
    assert "streamline_approval_path" in html
    assert "schedule_paid_assessment_conversation" in html
    assert "Demo-Only Boundary" in html


