from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_SAMPLE_ROWS.md")


def test_assessment_factory_lite_demo_sample_rows_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_sample_rows_document_names_service_and_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoSampleRowsService" in content
    assert "GET /products/assessment-factory-lite/demo-samples/rows" in content
    assert (
        "GET /products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in content
    )
    assert "assessment_factory_lite_demo_sample_rows" in content


def test_assessment_factory_lite_demo_sample_rows_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "sample_type" in content
    assert "scenario" in content
    assert "scenario_label" in content
    assert "boundary_type" in content
    assert "is_valid_sample" in content
    assert "rows" in content
    assert "row_count" in content
    assert "expected_demo_outcome" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_sample_rows_document_names_available_scenarios():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "standard" in content
    assert "valid" in content
    assert "approval_delay" in content
    assert "invalid" in content
    assert "unsafe" in content
    assert "empty" in content
    assert "blank" in content


def test_assessment_factory_lite_demo_sample_rows_document_names_standard_scenario():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Approval Delay and Blocked Work" in content
    assert "approval_requested" in content
    assert "approval_delayed" in content
    assert "work_blocked" in content
    assert "load_sample_rows_into_demo" in content
    assert "streamline_approval_path" in content
    assert "run_demo_diagnostics" in content


def test_assessment_factory_lite_demo_sample_rows_document_names_invalid_scenario():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Unsafe Data Boundary Example" in content
    assert "real_customer_incident" in content
    assert "urgent" in content
    assert "contains_real_customer_data true" in content
    assert "invalid_event_type" in content
    assert "invalid_severity" in content
    assert "real_customer_data_not_allowed" in content
    assert "repair_sample_csv_before_demo" in content


def test_assessment_factory_lite_demo_sample_rows_document_names_empty_and_unknown_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Empty Demo Starting State" in content
    assert "initialize_empty_demo_screen" in content
    assert "add_demo_rows" in content
    assert "add_synthetic_sample_rows" in content
    assert "not_found" in content
    assert "choose_available_sample_scenario" in content


def test_assessment_factory_lite_demo_sample_rows_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_only_sample_data" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "live_security_telemetry" in content
    assert (
        "The Assessment Factory Lite Demo Sample Rows layer does not "
        "certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

