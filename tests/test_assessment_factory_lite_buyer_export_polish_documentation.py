from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_EXPORT_POLISH.md")


def test_assessment_factory_lite_buyer_export_polish_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_export_polish_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerExportPolishService" in content
    assert "POST /products/assessment-factory-lite/buyer-export/polish" in content
    assert "assessment_factory_lite_buyer_export_polish" in content
    assert "assessment-factory-lite-demo-usability" in content
    assert "1.5.0" in content


def test_assessment_factory_lite_buyer_export_polish_document_names_inputs():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "rows" in content
    assert "diagnostics_result" in content
    assert "export_summary" in content
    assert "dataset validation" in content
    assert "buyer export polish" in content


def test_assessment_factory_lite_buyer_export_polish_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "polish_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "buyer_headline" in content
    assert "buyer_summary" in content
    assert "key_findings" in content
    assert "recommended_intervention" in content
    assert "next_steps" in content
    assert "trust_and_boundary_note" in content
    assert "source_export_summary" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_buyer_export_polish_document_names_successful_copy_fields():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Operational drag is slowing work in the demo workflow." in content
    assert "Approval delays are creating workflow drag" in content
    assert "approval_delay" in content
    assert "streamline_approval_path" in content
    assert "Streamline the approval path" in content
    assert "Reduce waiting time and make approval ownership clearer." in content
    assert "present_polished_buyer_export" in content


def test_assessment_factory_lite_buyer_export_polish_document_names_next_steps():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Review the top friction point with the workflow owner." in content
    assert "Choose one narrow intervention to test first." in content
    assert (
        "Use the demo output to decide what evidence should be collected next."
        in content
    )


def test_assessment_factory_lite_buyer_export_polish_document_names_rejected_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Sample data needs repair before buyer presentation." in content
    assert "sample_data_boundary_failure" in content
    assert "Unsafe or invalid sample rows detected" in content
    assert "Repair the demo sample data" in content
    assert "repair_sample_csv_before_demo" in content
    assert "Regenerate the polished buyer export after validation passes." in content


def test_assessment_factory_lite_buyer_export_polish_document_preserves_traceability():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "does not bypass dataset validation" in content
    assert "does not replace diagnostics" in content
    assert "does not replace the source export summary" in content
    assert "source_export_summary" in content
    assert "traceable to the underlying deterministic export" in content


def test_assessment_factory_lite_buyer_export_polish_document_preserves_boundaries():
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
        "The Assessment Factory Lite Buyer Export Polish layer does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
