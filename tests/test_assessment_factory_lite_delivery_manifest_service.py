from backend.app.gagf.assessment_factory_lite_delivery_manifest_service import (
    AssessmentFactoryLiteDeliveryManifestService,
)


def service():
    return AssessmentFactoryLiteDeliveryManifestService()


def test_assessment_factory_lite_delivery_manifest_builds_contract():
    result = service().build_manifest()

    assert result["status"] == "ok"
    assert result["manifest_type"] == (
        "assessment_factory_lite_demo_delivery_manifest"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-styling-export"
    assert result["version"] == "1.6.0"
    assert result["delivery_stage"] == "demo_delivery_packaging"
    assert result["recommended_action"] == "prepare_demo_delivery_package"


def test_assessment_factory_lite_delivery_manifest_package_summary():
    result = service().build_manifest()
    summary = result["package_summary"]

    assert summary["delivery_mode"] == "sample_data_only_demo"
    assert summary["commercial_use"] == "early_buyer_discovery_and_paid_assessment_setup"
    assert "operational friction diagnostic demo" in summary["positioning"]
    assert summary["primary_audience"] == [
        "founder_operator",
        "operations_leader",
        "it_manager",
        "workflow_owner",
    ]


def test_assessment_factory_lite_delivery_manifest_included_capabilities():
    result = service().build_manifest()

    capabilities = {
        item["capability"]: item for item in result["included_capabilities"]
    }

    assert set(capabilities) == {
        "sample_rows",
        "scenario_menu",
        "dataset_contract_validation",
        "demo_diagnostics",
        "styled_html_screen",
        "buyer_export_polish",
    }

    assert capabilities["buyer_export_polish"]["status"] == "included"


def test_assessment_factory_lite_delivery_manifest_included_endpoints():
    result = service().build_manifest()

    endpoint_paths = {endpoint["path"] for endpoint in result["included_endpoints"]}

    assert "/products/assessment-factory-lite/demo-samples/rows" in endpoint_paths
    assert (
        "/products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in endpoint_paths
    )
    assert "/products/assessment-factory-lite/demo-scenario-menu" in endpoint_paths
    assert "/products/assessment-factory-lite/demo-style-tokens" in endpoint_paths
    assert "/products/assessment-factory-lite/demo-ui/html" in endpoint_paths
    assert "/products/assessment-factory-lite/buyer-export/polish" in endpoint_paths


def test_assessment_factory_lite_delivery_manifest_included_documents():
    result = service().build_manifest()

    assert "ASSESSMENT_FACTORY_LITE_DEMO_STYLING_EXPORT_CLOSEOUT.md" in (
        result["included_documents"]
    )
    assert "ASSESSMENT_FACTORY_LITE_DEMO_SAMPLE_ROWS.md" in (
        result["included_documents"]
    )
    assert "ASSESSMENT_FACTORY_LITE_DEMO_SCENARIO_MENU.md" in (
        result["included_documents"]
    )
    assert "ASSESSMENT_FACTORY_LITE_DEMO_STYLE_TOKENS.md" in (
        result["included_documents"]
    )
    assert "ASSESSMENT_FACTORY_LITE_BUYER_EXPORT_POLISH.md" in (
        result["included_documents"]
    )


def test_assessment_factory_lite_delivery_manifest_operator_and_buyer_assets():
    result = service().build_manifest()

    operator_assets = {asset["asset"] for asset in result["operator_assets"]}
    buyer_assets = {asset["asset"] for asset in result["buyer_demo_assets"]}

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


def test_assessment_factory_lite_delivery_manifest_inputs_outputs_and_readiness():
    result = service().build_manifest()

    assert "sample_scenario" in result["delivery_inputs"]
    assert "include_scenario_menu" in result["delivery_inputs"]
    assert "include_style_tokens" in result["delivery_inputs"]

    assert "styled_html" in result["delivery_outputs"]
    assert "buyer_headline" in result["delivery_outputs"]
    assert "trust_and_boundary_note" in result["delivery_outputs"]

    readiness_checks = {item["check"] for item in result["readiness_inputs"]}

    assert readiness_checks == {
        "sample_rows_available",
        "scenario_menu_available",
        "styled_html_available",
        "buyer_export_polish_available",
        "demo_boundary_visible",
    }


def test_assessment_factory_lite_delivery_manifest_preserves_demo_boundary():
    result = service().build_manifest()
    boundary = result["demo_boundary"]

    assert boundary["boundary_type"] == "demo_only_sample_data"
    assert boundary["allowed_data"] == [
        "sample_csv",
        "synthetic_workflow_events",
        "mock_approval_events",
        "mock_delay_events",
    ]
    assert boundary["prohibited_data"] == [
        "real_customer_data",
        "regulated_data",
        "federal_data",
        "production_customer_data",
        "customer_secrets",
        "live_security_telemetry",
    ]
    assert boundary["certification_claims_allowed"] is False

    assert "production_customer_data_processing" in result["excluded_scope"]
    assert "fedramp_or_hipaa_certification_claims" in result["excluded_scope"]
    assert "pdf_generation" in result["excluded_scope"]
