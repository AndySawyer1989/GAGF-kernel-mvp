from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_LOADER_CLOSEOUT.md")


def test_assessment_factory_lite_demo_loader_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_loader_closeout_document_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Release 1.4.0" in content
    assert "assessment-factory-lite-demo-loader" in content
    assert "Sprint" in content
    assert "4.3" in content
    assert "complete" in content


def test_assessment_factory_lite_demo_loader_closeout_document_names_capability_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Demo Package" in content
    assert "Demo Sample Rows Service" in content
    assert "Demo Sample Rows API" in content
    assert "Demo Sample Rows Documentation" in content
    assert "Demo UI HTML Service" in content
    assert "sample_scenario integration" in content
    assert "Sample Data Loader section" in content
    assert "Visible HTML Demo Screen" in content
    assert "Demo Loader Release Marker" in content


def test_assessment_factory_lite_demo_loader_closeout_document_names_services_and_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoSampleRowsService" in content
    assert "AssessmentFactoryLiteDemoUIHTMLService" in content
    assert "GET /products/assessment-factory-lite/demo-samples/rows" in content
    assert (
        "GET /products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in content
    )
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content


def test_assessment_factory_lite_demo_loader_closeout_document_names_supported_scenarios():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "standard" in content
    assert "valid" in content
    assert "approval_delay" in content
    assert "invalid" in content
    assert "unsafe" in content
    assert "empty" in content
    assert "blank" in content


def test_assessment_factory_lite_demo_loader_closeout_document_names_scenario_outcomes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Approval Delay and Blocked Work" in content
    assert "Unsafe Data Boundary Example" in content
    assert "Empty Demo Starting State" in content
    assert "validation_status passed" in content
    assert "validation_status failed" in content
    assert "top_friction_label approval_delay" in content
    assert "streamline_approval_path" in content
    assert "repair_sample_csv_before_demo" in content
    assert "add_synthetic_sample_rows" in content


def test_assessment_factory_lite_demo_loader_closeout_document_names_loader_section_and_priority():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Sample Data Loader" in content
    assert "data-sample-scenario" in content
    assert "sample_rows_result is null" in content
    assert "No canned sample scenario was loaded" in content
    assert "ui_view is not provided" in content
    assert "rows is not provided" in content
    assert "sample_scenario is provided" in content


def test_assessment_factory_lite_demo_loader_closeout_document_names_next_track():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Demo Screen Usability Layer" in content
    assert "US-181 Assessment Factory Lite Demo Screen Scenario Menu Service" in content
    assert "US-182 Assessment Factory Lite Demo Screen Scenario Menu Endpoint" in content
    assert "US-183 Assessment Factory Lite Demo Screen Scenario Menu Documentation" in content
    assert "US-184 Assessment Factory Lite Demo Screen Scenario Menu Integration" in content
    assert "US-185 Assessment Factory Lite Demo Screen Usability Release Marker" in content


def test_assessment_factory_lite_demo_loader_closeout_document_preserves_boundaries():
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
        "The Assessment Factory Lite Demo Loader does not certify products "
        "as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
