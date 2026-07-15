from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_DELIVERY_PACKAGING_CLOSEOUT.md")


def test_assessment_factory_lite_demo_delivery_packaging_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_delivery_packaging_closeout_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "1.7.0" in content
    assert "assessment-factory-lite-demo-delivery-packaging" in content
    assert "Sprint:" in content
    assert "4.6" in content
    assert "complete" in content
    assert "GET /version" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_names_completed_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Sample Rows" in content
    assert "Scenario Menu" in content
    assert "Dataset Contract" in content
    assert "Demo Diagnostics" in content
    assert "Demo Export Summary" in content
    assert "Buyer Export Polish" in content
    assert "Styled HTML Demo Screen" in content
    assert "Delivery Manifest" in content
    assert "Operator Runbook" in content
    assert "Delivery Readiness" in content
    assert "Release 1.7.0 Marker" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_names_delivery_artifacts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDeliveryManifestService" in content
    assert "GET /products/assessment-factory-lite/delivery/manifest" in content
    assert "assessment_factory_lite_demo_delivery_manifest" in content

    assert "AssessmentFactoryLiteOperatorRunbookService" in content
    assert "GET /products/assessment-factory-lite/delivery/runbook" in content
    assert "assessment_factory_lite_demo_operator_runbook" in content

    assert "AssessmentFactoryLiteDeliveryReadinessService" in content
    assert "GET /products/assessment-factory-lite/delivery/readiness" in content
    assert "assessment_factory_lite_demo_delivery_readiness" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_names_readiness_checks():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "delivery_manifest_ready" in content
    assert "operator_runbook_ready" in content
    assert "sample_scenarios_ready" in content
    assert "scenario_menu_ready" in content
    assert "styled_html_screen_ready" in content
    assert "buyer_export_polish_ready" in content
    assert "demo_boundary_ready" in content
    assert "operator_stop_conditions_ready" in content
    assert "readiness_status: ready" in content
    assert "delivery_decision: go" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_preserves_object_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "delivery manifest: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "operator runbook: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "delivery readiness: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "UI view object: 1.1.0 / assessment-factory-lite-demo-package" in content
    assert "HTML screen object: 1.2.0 / assessment-factory-lite-demo-ui" in content
    assert "scenario menu object: 1.4.0 / assessment-factory-lite-demo-loader" in content
    assert "style token object: 1.5.0 / assessment-factory-lite-demo-usability" in content
    assert "buyer export polish object: 1.5.0 / assessment-factory-lite-demo-usability" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_names_buyer_workflow_and_scenarios():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Confirm package readiness." in content
    assert "Open the demo with the operational friction problem." in content
    assert "Show the scenario menu." in content
    assert "Load the standard demo scenario." in content
    assert "Present the polished buyer export." in content
    assert "Ask which part resembles the buyer's workflow." in content

    assert "Approval Delay and Blocked Work" in content
    assert "approval_delay" in content
    assert "streamline_approval_path" in content
    assert "Unsafe Data Boundary Test" in content
    assert "repair_sample_csv_before_demo" in content
    assert "Empty Demo Starting State" in content
    assert "add_demo_rows" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_preserves_boundaries_and_exclusions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo-only" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "production_customer_data" in content
    assert "customer_secrets" in content
    assert "live_security_telemetry" in content
    assert "certification_claims_allowed:" in content
    assert "false" in content

    assert "production_customer_data_processing" in content
    assert "fedramp_or_hipaa_certification_claims" in content
    assert "soc_2_audit_claims" in content
    assert "wcag_certification_claims" in content
    assert "pdf_generation" in content
    assert "payment_processing" in content


def test_assessment_factory_lite_demo_delivery_packaging_closeout_names_next_direction_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Buyer Walkthrough Script Service" in content
    assert "US-206 — Assessment Factory Lite Buyer Walkthrough Script Service" in content
    assert "The next bottleneck is buyer communication." in content
    assert (
        "The Assessment Factory Lite Demo Delivery Packaging release does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content