from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_loader_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.4.0",
        "release": "assessment-factory-lite-demo-loader",
        "sprint": "4.3",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_loader_release_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-samples/rows" in actual_routes
    assert (
        "/products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in actual_routes
    )
    assert "/products/assessment-factory-lite/demo-ui/html" in actual_routes
    assert "/products/assessment-factory-lite/demo-ui/view" in actual_routes
    assert (
        "/products/assessment-factory-lite/demo-export/summary"
        in actual_routes
    )


def test_assessment_factory_lite_demo_loader_release_standard_sample_endpoint_works():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/standard"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["scenario"] == "standard"
    assert payload["scenario_label"] == "Approval Delay and Blocked Work"
    assert payload["row_count"] == 3
    assert payload["is_valid_sample"] is True
    assert payload["recommended_action"] == "load_sample_rows_into_demo"


def test_assessment_factory_lite_demo_loader_release_html_loads_standard_scenario():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "standard"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["screen_type"] == (
        "assessment_factory_lite_demo_ui_html_screen"
    )
    assert payload["sample_rows_result"]["scenario"] == "standard"
    assert payload["sample_rows_result"]["row_count"] == 3
    assert payload["ui_view"]["source_payloads"]["diagnostics_result"][
        "status"
    ] == "ok"
    assert "Sample Data Loader" in payload["html"]
    assert 'data-sample-scenario="standard"' in payload["html"]
    assert "Approval Delay and Blocked Work" in payload["html"]


def test_assessment_factory_lite_demo_loader_release_html_loads_invalid_boundary_test():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "invalid"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["sample_rows_result"]["scenario"] == "invalid"
    assert payload["sample_rows_result"]["is_valid_sample"] is False
    assert payload["ui_view"]["source_payloads"]["diagnostics_result"][
        "status"
    ] == "rejected"
    assert "Unsafe Data Boundary Example" in payload["html"]
    assert "repair_sample_csv_before_demo" in payload["html"]

