from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_SCREEN_SAMPLE_LOADER.md")


def test_assessment_factory_lite_demo_screen_sample_loader_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_screen_sample_loader_document_names_services_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoSampleRowsService" in content
    assert "AssessmentFactoryLiteDemoUIViewService" in content
    assert "AssessmentFactoryLiteDemoUIHTMLService" in content
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content
    assert "sample_scenario" in content


def test_assessment_factory_lite_demo_screen_sample_loader_document_names_supported_scenarios():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "standard" in content
    assert "valid" in content
    assert "approval_delay" in content
    assert "invalid" in content
    assert "unsafe" in content
    assert "empty" in content
    assert "blank" in content


def test_assessment_factory_lite_demo_screen_sample_loader_document_names_standard_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Approval Delay and Blocked Work" in content
    assert "sample_rows_result scenario standard" in content
    assert "sample_rows_result row_count 3" in content
    assert "sample_rows_result is_valid_sample true" in content
    assert "diagnostics_result status ok" in content
    assert 'data-sample-scenario="standard"' in content
    assert "streamline_approval_path" in content


def test_assessment_factory_lite_demo_screen_sample_loader_document_names_invalid_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Unsafe Data Boundary Example" in content
    assert "sample_rows_result scenario invalid" in content
    assert "sample_rows_result is_valid_sample false" in content
    assert "diagnostics_result status rejected" in content
    assert "repair_sample_csv_before_demo" in content
    assert "invalid_event_type" in content
    assert "invalid_severity" in content
    assert "real_customer_data_not_allowed" in content


def test_assessment_factory_lite_demo_screen_sample_loader_document_names_empty_and_direct_rows_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Empty Demo Starting State" in content
    assert "sample_rows_result scenario empty" in content
    assert "sample_rows_result row_count 0" in content
    assert "add_synthetic_sample_rows" in content
    assert "Direct Rows Fallback" in content
    assert "No canned sample scenario was loaded" in content
    assert "sample_rows_result is null" in content


def test_assessment_factory_lite_demo_screen_sample_loader_document_names_loader_section_and_output():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Sample Data Loader" in content
    assert "data-sample-scenario" in content
    assert "rows loaded" in content
    assert "boundary" in content
    assert "sample_rows_result" in content
    assert "status" in content
    assert "screen_type" in content
    assert "html" in content
    assert "ui_view" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_screen_sample_loader_document_preserves_boundaries():
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
        "The Assessment Factory Lite Demo Screen Sample Loader does not "
        "certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

