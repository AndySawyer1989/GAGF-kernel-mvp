from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["manifest_type"] == (
        "assessment_factory_lite_demo_delivery_manifest"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-styling-export"
    assert payload["version"] == "1.6.0"
    assert payload["delivery_stage"] == "demo_delivery_packaging"
    assert payload["recommended_action"] == "prepare_demo_delivery_package"


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_package_summary():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    payload = response.json()
    summary = payload["package_summary"]

    assert summary["delivery_mode"] == "sample_data_only_demo"
    assert summary["commercial_use"] == (
        "early_buyer_discovery_and_paid_assessment_setup"
    )
    assert "operational friction diagnostic demo" in summary["positioning"]
    assert summary["primary_audience"] == [
        "founder_operator",
        "operations_leader",
        "it_manager",
        "workflow_owner",
    ]


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_capabilities():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    payload = response.json()

    capabilities = {
        item["capability"]: item for item in payload["included_capabilities"]
    }

    assert set(capabilities) == {
        "sample_rows",
        "scenario_menu",
        "dataset_contract_validation",
        "demo_diagnostics",
        "styled_html_screen",
        "buyer_export_polish",
    }

    assert capabilities["sample_rows"]["status"] == "included"
    assert capabilities["styled_html_screen"]["status"] == "included"
    assert capabilities["buyer_export_polish"]["status"] == "included"


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_endpoints():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    payload = response.json()
    endpoint_paths = {endpoint["path"] for endpoint in payload["included_endpoints"]}

    assert "/products/assessment-factory-lite/demo-samples/rows" in endpoint_paths
    assert (
        "/products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in endpoint_paths
    )
    assert "/products/assessment-factory-lite/demo-scenario-menu" in endpoint_paths
    assert "/products/assessment-factory-lite/demo-style-tokens" in endpoint_paths
    assert "/products/assessment-factory-lite/demo-ui/html" in endpoint_paths
    assert "/products/assessment-factory-lite/buyer-export/polish" in endpoint_paths


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_documents():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    payload = response.json()
    documents = payload["included_documents"]

    assert "ASSESSMENT_FACTORY_LITE_DEMO_STYLING_EXPORT_CLOSEOUT.md" in documents
    assert "ASSESSMENT_FACTORY_LITE_DEMO_SAMPLE_ROWS.md" in documents
    assert "ASSESSMENT_FACTORY_LITE_DEMO_SCENARIO_MENU.md" in documents
    assert "ASSESSMENT_FACTORY_LITE_DEMO_STYLE_TOKENS.md" in documents
    assert "ASSESSMENT_FACTORY_LITE_BUYER_EXPORT_POLISH.md" in documents


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_assets():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    payload = response.json()

    operator_assets = {asset["asset"] for asset in payload["operator_assets"]}
    buyer_assets = {asset["asset"] for asset in payload["buyer_demo_assets"]}

    assert operator_assets == {
        "scenario_menu",
        "sample_loader",
        "styled_html_screen",
        "buyer_export_polish",
    }

    assert buyer_assets == {
        "standard_demo_scenario",
        "invalid_boundary_test",
        "empty_starting_state",
        "polished_buyer_export",
    }


def test_assessment_factory_lite_delivery_manifest_endpoint_returns_inputs_outputs_and_readiness():
    response = client.get(
        "/products/assessment-factory-lite/delivery/manifest"
    )

    payload = response.json()

    assert "sample_scenario" in payload["delivery_inputs"]
    assert "include_scenario_menu" in payload["delivery_inputs"]
    assert "include_style_tokens" in payload["delivery_inputs"]

    assert "styled_html" in payload["delivery_outputs"]
    assert "buyer_headline" in payload["delivery_outputs"]
    assert "trust_and_boundary_note" in payload["delivery_outputs"]

    readiness_checks = {item["check"] for item in payload["readiness_inputs"]}

    assert readiness_checks == {
        "sample_rows_available",
        "scenario_menu_available",
        "styled_html_available",
        "buyer_export_polish_available",
        "demo_boundary_visible",
    }


def test_assessment_factory_lite_delivery_manifest_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/delivery/manifest" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.0.0",
        "release": "assessment-factory-lite-proposal-package",
        "sprint": "4.9",
        "status": "complete",
    }



