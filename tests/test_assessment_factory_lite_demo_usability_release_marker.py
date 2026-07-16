from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_usability_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.0.0",
        "release": "assessment-factory-lite-proposal-package",
        "sprint": "4.9",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_usability_release_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-scenario-menu" in actual_routes
    assert "/products/assessment-factory-lite/demo-samples/rows" in actual_routes
    assert (
        "/products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in actual_routes
    )
    assert "/products/assessment-factory-lite/demo-ui/html" in actual_routes
    assert "/products/assessment-factory-lite/demo-ui/view" in actual_routes


def test_assessment_factory_lite_demo_usability_release_menu_endpoint_works():
    response = client.get(
        "/products/assessment-factory-lite/demo-scenario-menu"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["menu_type"] == "assessment_factory_lite_demo_scenario_menu"
    assert payload["release"] == "assessment-factory-lite-demo-loader"
    assert payload["version"] == "1.4.0"
    assert payload["default_scenario"] == "standard"
    assert [item["scenario"] for item in payload["menu_items"]] == [
        "standard",
        "invalid",
        "empty",
    ]


def test_assessment_factory_lite_demo_usability_release_html_screen_renders_menu():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "standard"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["release"] == "assessment-factory-lite-demo-ui"
    assert payload["version"] == "1.2.0"
    assert payload["scenario_menu"]["default_scenario"] == "standard"
    assert [item["scenario"] for item in payload["scenario_menu"]["menu_items"]] == [
        "standard",
        "invalid",
        "empty",
    ]
    assert "Demo Scenario Menu" in payload["html"]
    assert 'data-scenario="standard"' in payload["html"]
    assert "HTML payload: sample_scenario=standard" in payload["html"]


def test_assessment_factory_lite_demo_usability_release_html_screen_renders_sample_loader():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "invalid"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["sample_rows_result"]["scenario"] == "invalid"
    assert payload["sample_rows_result"]["is_valid_sample"] is False
    assert payload["ui_view"]["source_payloads"]["diagnostics_result"][
        "status"
    ] == "rejected"
    assert "Sample Data Loader" in payload["html"]
    assert 'data-sample-scenario="invalid"' in payload["html"]
    assert "Unsafe Data Boundary Test" in payload["html"]


def test_assessment_factory_lite_demo_usability_release_empty_scenario_works():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "empty"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["sample_rows_result"]["scenario"] == "empty"
    assert payload["sample_rows_result"]["row_count"] == 0
    assert payload["scenario_menu"]["default_scenario"] == "standard"
    assert "Empty Demo Starting State" in payload["html"]
    assert "add_synthetic_sample_rows" in payload["html"]







