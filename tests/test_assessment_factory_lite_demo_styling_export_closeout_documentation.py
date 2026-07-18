from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_STYLING_EXPORT_CLOSEOUT.md")


def test_assessment_factory_lite_demo_styling_export_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Release 1.6.0" in content
    assert "assessment-factory-lite-demo-styling-export" in content
    assert "Sprint" in content
    assert "4.5" in content
    assert "complete" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_capability_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Demo Package" in content
    assert "Style Token Service" in content
    assert "Style Token Endpoint" in content
    assert "HTML Style Integration" in content
    assert "Buyer Export Polish Service" in content
    assert "Buyer Export Polish Endpoint" in content
    assert "Buyer Export Polish Documentation" in content
    assert "Styling and Export Release Marker" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_services_and_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoStyleTokenService" in content
    assert "AssessmentFactoryLiteDemoUIHTMLService" in content
    assert "AssessmentFactoryLiteBuyerExportPolishService" in content
    assert "GET /products/assessment-factory-lite/demo-style-tokens" in content
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content
    assert "POST /products/assessment-factory-lite/buyer-export/polish" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_style_tokens():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_demo_style_tokens" in content
    assert "clean_efficient_trustworthy_operator_screen" in content
    assert "operations_leaders_and_it_managers" in content
    assert "orange" in content
    assert "white" in content
    assert "gold" in content
    assert "purple" in content
    assert "brand_orange #F97316" in content
    assert "brand_gold #D6A21E" in content
    assert "brand_purple #6D28D9" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_html_style_integration():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert 'style data-style-token-type="assessment_factory_lite_demo_style_tokens"' in content
    assert "--afl-brand-orange" in content
    assert "--afl-brand-gold" in content
    assert "--afl-brand-purple" in content
    assert "Demo Scenario Menu" in content
    assert "Sample Data Loader" in content
    assert "Buyer-Facing Export Preview" in content
    assert "include_style_tokens" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_buyer_export_polish():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_buyer_export_polish" in content
    assert "buyer_headline" in content
    assert "buyer_summary" in content
    assert "key_findings" in content
    assert "recommended_intervention" in content
    assert "next_steps" in content
    assert "trust_and_boundary_note" in content
    assert "source_export_summary" in content
    assert "Approval delays are creating workflow drag" in content
    assert "Streamline the approval path" in content
    assert "Reduce waiting time and make approval ownership clearer." in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_rejected_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status rejected" in content
    assert "Sample data needs repair before buyer presentation." in content
    assert "repair_sample_csv_before_demo" in content
    assert "sample_data_boundary_failure" in content
    assert "prevents unsafe rows from becoming buyer-facing findings" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_internal_contract_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "System release marker:" in content
    assert "1.6.0" in content
    assert "Style token object contract:" in content
    assert "Buyer export polish object contract:" in content
    assert "1.5.0" in content
    assert "Scenario menu object contract:" in content
    assert "1.4.0" in content
    assert "HTML screen object contract:" in content
    assert "1.2.0" in content
    assert "UI view object contract:" in content
    assert "1.1.0" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_names_next_track():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Demo Delivery Packaging" in content
    assert "US-196 Assessment Factory Lite Demo Delivery Package Manifest Service" in content
    assert "US-197 Assessment Factory Lite Demo Delivery Package Manifest Endpoint" in content
    assert "US-198 Assessment Factory Lite Demo Delivery Package Manifest Documentation" in content
    assert "US-199 Assessment Factory Lite Demo Operator Runbook Service" in content
    assert "US-200 Assessment Factory Lite Demo Operator Runbook Endpoint" in content
    assert "US-201 Assessment Factory Lite Demo Operator Runbook Documentation" in content
    assert "US-202 Assessment Factory Lite Demo Delivery Readiness Service" in content
    assert "US-203 Assessment Factory Lite Demo Delivery Readiness Endpoint" in content
    assert "US-204 Assessment Factory Lite Demo Delivery Packaging Release Marker" in content


def test_assessment_factory_lite_demo_styling_export_closeout_document_preserves_boundaries():
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
        "The Assessment Factory Lite Demo Styling and Export layer does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
