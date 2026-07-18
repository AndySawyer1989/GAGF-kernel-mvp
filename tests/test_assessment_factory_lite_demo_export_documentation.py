from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_EXPORT_SUMMARY.md")


def test_assessment_factory_lite_demo_export_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_export_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoExportService" in content
    assert (
        "POST /products/assessment-factory-lite/demo-export/summary"
        in content
    )
    assert "assessment_factory_lite_demo_export_summary" in content


def test_assessment_factory_lite_demo_export_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "rows" in content
    assert "diagnostics_result" in content
    assert "Input Mode 1" in content
    assert "Input Mode 2" in content
    assert "Empty Payload Behavior" in content
    assert "add_demo_rows" in content


def test_assessment_factory_lite_demo_export_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "export_type" in content
    assert "package_name" in content
    assert "source_diagnostic_type" in content
    assert "row_count" in content
    assert "report_title" in content
    assert "executive_summary" in content
    assert "sample_data_boundary" in content
    assert "governance_drag_findings" in content
    assert "top_constraints" in content
    assert "recommended_intervention" in content
    assert "next_steps" in content
    assert "compliance_disclaimer" in content
    assert "export_metadata" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_export_document_names_findings_and_constraints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "total_events" in content
    assert "drag_event_count" in content
    assert "critical_or_high_event_count" in content
    assert "total_delay_minutes" in content
    assert "governance_drag_score" in content
    assert "drag_level" in content
    assert "rank" in content
    assert "constraint_label" in content
    assert "priority_score" in content


def test_assessment_factory_lite_demo_export_document_names_interventions_and_next_steps():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "streamline_approval_path" in content
    assert "clarify_ownership_and_handoffs" in content
    assert "stabilize_operational_path" in content
    assert "review_top_constraint" in content
    assert "repair_sample_csv_before_demo" in content
    assert "review_governance_drag_summary" in content
    assert "review_top_constraints" in content
    assert "prepare_buyer_demo_walkthrough" in content


def test_assessment_factory_lite_demo_export_document_names_demo_boundary():
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
    assert "certification_claims_allowed" in content


def test_assessment_factory_lite_demo_export_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Demo Export Summary does not certify "
        "products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content





