from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_UI_HTML_SCREEN.md")


def test_assessment_factory_lite_demo_ui_html_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_ui_html_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoUIHTMLService" in content
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content
    assert "assessment_factory_lite_demo_ui_html_screen" in content


def test_assessment_factory_lite_demo_ui_html_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "checkpoint" in content
    assert "rows" in content
    assert "diagnostics_result" in content
    assert "export_summary" in content
    assert "ui_view" in content
    assert "UI View Input" in content


def test_assessment_factory_lite_demo_ui_html_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "screen_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "html" in content
    assert "ui_view" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_ui_html_document_names_html_shell():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "doctype declaration" in content
    assert "html language attribute" in content
    assert "meta charset" in content
    assert "viewport metadata" in content
    assert "body data-screen attribute" in content
    assert "assessment-factory-lite-demo-ui-html-screen" in content
    assert "Assessment Factory Lite Demo" in content
    assert "FIP/GAGF Operator Workstation" in content


def test_assessment_factory_lite_demo_ui_html_document_names_cards_and_warnings():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_readiness_card" in content
    assert "sample_data_boundary_card" in content
    assert "dataset_contract_card" in content
    assert "dataset_validation_card" in content
    assert "governance_drag_summary_card" in content
    assert "top_friction_points_card" in content
    assert "recommended_intervention_card" in content
    assert "export_summary_preview_card" in content
    assert "demo_only_boundary" in content
    assert "no_certification_claims" in content


def test_assessment_factory_lite_demo_ui_html_document_names_export_and_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Buyer-Facing Export Preview" in content
    assert "executive_summary" in content
    assert "compliance_disclaimer" in content
    assert "review_demo_readiness" in content
    assert "review_sample_data_boundary" in content
    assert "review_governance_drag_summary" in content
    assert "review_top_friction_points" in content
    assert "review_recommended_intervention" in content
    assert "review_demo_export_summary" in content
    assert "repair_sample_csv_before_demo" in content


def test_assessment_factory_lite_demo_ui_html_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Demo UI HTML Screen does not certify "
        "products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

