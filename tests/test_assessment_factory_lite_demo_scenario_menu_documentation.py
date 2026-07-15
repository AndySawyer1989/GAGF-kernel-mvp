from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_SCENARIO_MENU.md")


def test_assessment_factory_lite_demo_scenario_menu_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_scenario_menu_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoScenarioMenuService" in content
    assert "GET /products/assessment-factory-lite/demo-scenario-menu" in content
    assert "assessment_factory_lite_demo_scenario_menu" in content
    assert "assessment-factory-lite-demo-loader" in content
    assert "1.4.0" in content


def test_assessment_factory_lite_demo_scenario_menu_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "menu_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "default_scenario" in content
    assert "menu_items" in content
    assert "aliases" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_scenario_menu_document_names_menu_item_fields():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "scenario" in content
    assert "label" in content
    assert "description" in content
    assert "recommended_use" in content
    assert "is_valid_sample" in content
    assert "row_count" in content
    assert "expected_top_friction_label" in content
    assert "expected_intervention" in content
    assert "ui_action" in content
    assert "html_payload" in content


def test_assessment_factory_lite_demo_scenario_menu_document_names_standard_item():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Approval Delay and Blocked Work" in content
    assert "buyer_demo_default" in content
    assert "approval_delay" in content
    assert "streamline_approval_path" in content
    assert "load_standard_demo_scenario" in content
    assert "sample_scenario standard" in content


def test_assessment_factory_lite_demo_scenario_menu_document_names_invalid_item():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Unsafe Data Boundary Test" in content
    assert "boundary_rejection_demo" in content
    assert "repair_sample_csv_before_demo" in content
    assert "load_invalid_boundary_test_scenario" in content
    assert "sample_scenario invalid" in content


def test_assessment_factory_lite_demo_scenario_menu_document_names_empty_item_and_aliases():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Empty Demo Starting State" in content
    assert "initial_empty_state" in content
    assert "add_demo_rows" in content
    assert "load_empty_demo_scenario" in content
    assert "sample_scenario empty" in content
    assert "valid maps to standard" in content
    assert "approval_delay maps to standard" in content
    assert "unsafe maps to invalid" in content
    assert "blank maps to empty" in content


def test_assessment_factory_lite_demo_scenario_menu_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo-only" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "live_security_telemetry" in content
    assert (
        "The Assessment Factory Lite Demo Scenario Menu does not certify "
        "products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content