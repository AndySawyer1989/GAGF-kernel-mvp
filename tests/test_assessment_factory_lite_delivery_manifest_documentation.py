from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DELIVERY_MANIFEST.md")


def test_assessment_factory_lite_delivery_manifest_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_delivery_manifest_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDeliveryManifestService" in content
    assert "GET /products/assessment-factory-lite/delivery/manifest" in content
    assert "assessment_factory_lite_demo_delivery_manifest" in content
    assert "assessment-factory-lite-demo-styling-export" in content
    assert "1.6.0" in content
    assert "demo_delivery_packaging" in content


def test_assessment_factory_lite_delivery_manifest_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "manifest_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "delivery_stage" in content
    assert "package_summary" in content
    assert "included_capabilities" in content
    assert "included_endpoints" in content
    assert "included_documents" in content
    assert "operator_assets" in content
    assert "buyer_demo_assets" in content
    assert "delivery_inputs" in content
    assert "delivery_outputs" in content
    assert "excluded_scope" in content
    assert "demo_boundary" in content
    assert "readiness_inputs" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_delivery_manifest_document_names_package_summary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "sample_data_only_demo" in content
    assert "early_buyer_discovery_and_paid_assessment_setup" in content
    assert "operational friction diagnostic demo" in content
    assert "founder_operator" in content
    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content


def test_assessment_factory_lite_delivery_manifest_document_names_capabilities():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "sample_rows" in content
    assert "scenario_menu" in content
    assert "dataset_contract_validation" in content
    assert "demo_diagnostics" in content
    assert "styled_html_screen" in content
    assert "buyer_export_polish" in content


def test_assessment_factory_lite_delivery_manifest_document_names_included_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "GET /products/assessment-factory-lite/demo-samples/rows" in content
    assert (
        "GET /products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in content
    )
    assert "GET /products/assessment-factory-lite/demo-scenario-menu" in content
    assert "GET /products/assessment-factory-lite/demo-style-tokens" in content
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content
    assert "POST /products/assessment-factory-lite/buyer-export/polish" in content
    assert "GET /products/assessment-factory-lite/delivery/manifest" in content


def test_assessment_factory_lite_delivery_manifest_document_names_documents_and_assets():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ASSESSMENT_FACTORY_LITE_DEMO_STYLING_EXPORT_CLOSEOUT.md" in content
    assert "ASSESSMENT_FACTORY_LITE_DEMO_SAMPLE_ROWS.md" in content
    assert "ASSESSMENT_FACTORY_LITE_DEMO_SCENARIO_MENU.md" in content
    assert "ASSESSMENT_FACTORY_LITE_DEMO_STYLE_TOKENS.md" in content
    assert "ASSESSMENT_FACTORY_LITE_BUYER_EXPORT_POLISH.md" in content
    assert "scenario_menu" in content
    assert "sample_loader" in content
    assert "styled_html_screen" in content
    assert "buyer_export_polish" in content


def test_assessment_factory_lite_delivery_manifest_document_names_buyer_demo_assets():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "standard_demo_scenario" in content
    assert "Approval Delay and Blocked Work" in content
    assert "invalid_boundary_test" in content
    assert "Unsafe Data Boundary Test" in content
    assert "empty_starting_state" in content
    assert "Empty Demo Starting State" in content
    assert "polished_buyer_export" in content
    assert "Buyer-Facing Export Preview" in content


def test_assessment_factory_lite_delivery_manifest_document_names_inputs_outputs_and_readiness():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "sample_scenario" in content
    assert "synthetic_rows" in content
    assert "diagnostics_result" in content
    assert "export_summary" in content
    assert "include_scenario_menu" in content
    assert "include_style_tokens" in content
    assert "scenario_menu" in content
    assert "sample_rows_result" in content
    assert "styled_html" in content
    assert "buyer_headline" in content
    assert "trust_and_boundary_note" in content
    assert "sample_rows_available" in content
    assert "scenario_menu_available" in content
    assert "styled_html_available" in content
    assert "buyer_export_polish_available" in content
    assert "demo_boundary_visible" in content


def test_assessment_factory_lite_delivery_manifest_document_names_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The delivery manifest does not decide readiness by itself." in content
    assert "The future readiness service should verify" in content
    assert "The delivery manifest defines what is in the package." in content
    assert "The future operator runbook should explain how to run the package" in content
    assert "The manifest answers:" in content
    assert "The runbook answers:" in content


def test_assessment_factory_lite_delivery_manifest_document_preserves_boundaries():
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
    assert "production_customer_data_processing" in content
    assert "fedramp_or_hipaa_certification_claims" in content
    assert "pdf_generation" in content
    assert (
        "The Assessment Factory Lite Delivery Manifest does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content