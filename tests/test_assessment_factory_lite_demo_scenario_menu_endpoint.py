from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_scenario_menu_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/demo-scenario-menu"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["menu_type"] == "assessment_factory_lite_demo_scenario_menu"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-loader"
    assert payload["version"] == "1.4.0"
    assert payload["default_scenario"] == "standard"
    assert payload["recommended_action"] == "render_demo_scenario_menu"


def test_assessment_factory_lite_demo_scenario_menu_endpoint_returns_menu_items():
    response = client.get(
        "/products/assessment-factory-lite/demo-scenario-menu"
    )

    payload = response.json()

    assert [item["scenario"] for item in payload["menu_items"]] == [
        "standard",
        "invalid",
        "empty",
    ]

    assert [item["ui_action"] for item in payload["menu_items"]] == [
        "load_standard_demo_scenario",
        "load_invalid_boundary_test_scenario",
        "load_empty_demo_scenario",
    ]


def test_assessment_factory_lite_demo_scenario_menu_endpoint_standard_item_is_html_ready():
    response = client.get(
        "/products/assessment-factory-lite/demo-scenario-menu"
    )

    payload = response.json()
    items = {item["scenario"]: item for item in payload["menu_items"]}

    assert items["standard"]["label"] == "Approval Delay and Blocked Work"
    assert items["standard"]["recommended_use"] == "buyer_demo_default"
    assert items["standard"]["is_valid_sample"] is True
    assert items["standard"]["row_count"] == 3
    assert items["standard"]["expected_top_friction_label"] == "approval_delay"
    assert items["standard"]["expected_intervention"] == (
        "streamline_approval_path"
    )
    assert items["standard"]["html_payload"] == {"sample_scenario": "standard"}


def test_assessment_factory_lite_demo_scenario_menu_endpoint_invalid_item_is_html_ready():
    response = client.get(
        "/products/assessment-factory-lite/demo-scenario-menu"
    )

    payload = response.json()
    items = {item["scenario"]: item for item in payload["menu_items"]}

    assert items["invalid"]["label"] == "Unsafe Data Boundary Test"
    assert items["invalid"]["recommended_use"] == "boundary_rejection_demo"
    assert items["invalid"]["is_valid_sample"] is False
    assert items["invalid"]["row_count"] == 1
    assert items["invalid"]["expected_top_friction_label"] == "none"
    assert items["invalid"]["expected_intervention"] == (
        "repair_sample_csv_before_demo"
    )
    assert items["invalid"]["html_payload"] == {"sample_scenario": "invalid"}


def test_assessment_factory_lite_demo_scenario_menu_endpoint_empty_item_is_html_ready():
    response = client.get(
        "/products/assessment-factory-lite/demo-scenario-menu"
    )

    payload = response.json()
    items = {item["scenario"]: item for item in payload["menu_items"]}

    assert items["empty"]["label"] == "Empty Demo Starting State"
    assert items["empty"]["recommended_use"] == "initial_empty_state"
    assert items["empty"]["is_valid_sample"] is True
    assert items["empty"]["row_count"] == 0
    assert items["empty"]["expected_top_friction_label"] == "none"
    assert items["empty"]["expected_intervention"] == "add_demo_rows"
    assert items["empty"]["html_payload"] == {"sample_scenario": "empty"}


def test_assessment_factory_lite_demo_scenario_menu_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-scenario-menu" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }








