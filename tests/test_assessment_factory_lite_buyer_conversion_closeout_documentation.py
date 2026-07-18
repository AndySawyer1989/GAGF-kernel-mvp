from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_CONVERSION_CLOSEOUT.md")


def test_assessment_factory_lite_buyer_conversion_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_conversion_closeout_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "1.8.0" in content
    assert "assessment-factory-lite-buyer-conversion" in content
    assert "Sprint:" in content
    assert "4.7" in content
    assert "complete" in content
    assert "GET /version" in content


def test_assessment_factory_lite_buyer_conversion_closeout_names_completed_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Delivery Packaging Release" in content
    assert "Buyer Walkthrough Script" in content
    assert "Buyer Walkthrough Script Endpoint" in content
    assert "Buyer Walkthrough Script Documentation" in content
    assert "Buyer Walkthrough HTML View" in content
    assert "Buyer Walkthrough HTML Endpoint" in content
    assert "Buyer Walkthrough HTML Documentation" in content
    assert "Buyer Conversion Release Marker" in content


def test_assessment_factory_lite_buyer_conversion_closeout_names_artifacts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerWalkthroughScriptService" in content
    assert "GET /products/assessment-factory-lite/buyer-walkthrough/script" in content
    assert "assessment_factory_lite_buyer_walkthrough_script" in content

    assert "AssessmentFactoryLiteBuyerWalkthroughHTMLService" in content
    assert "GET /products/assessment-factory-lite/buyer-walkthrough/html" in content
    assert "assessment_factory_lite_buyer_walkthrough_html_view" in content


def test_assessment_factory_lite_buyer_conversion_closeout_preserves_object_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "buyer walkthrough script: 1.7.0 / assessment-factory-lite-demo-delivery-packaging" in content
    assert "buyer walkthrough HTML view: 1.7.0 / assessment-factory-lite-demo-delivery-packaging" in content
    assert "delivery manifest: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "operator runbook: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "delivery readiness: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "UI view object: 1.1.0 / assessment-factory-lite-demo-package" in content
    assert "HTML screen object: 1.2.0 / assessment-factory-lite-demo-ui" in content
    assert "scenario menu object: 1.4.0 / assessment-factory-lite-demo-loader" in content
    assert "style token object: 1.5.0 / assessment-factory-lite-demo-usability" in content
    assert "buyer export polish object: 1.5.0 / assessment-factory-lite-demo-usability" in content


def test_assessment_factory_lite_buyer_conversion_closeout_names_script_content():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "This is a sample-data-only demo of Assessment Factory Lite." in content
    assert "Most teams feel delays before they can prove them." in content
    assert "Approval Delay and Blocked Work" in content
    assert "approval_delay" in content
    assert "streamline_approval_path" in content
    assert "Approval delays are creating workflow drag." in content
    assert "synthetic approval and blocked-work events" in content
    assert "does not mean removing accountability" in content


def test_assessment_factory_lite_buyer_conversion_closeout_names_questions_objections_and_html_view():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Which part of this sample workflow most resembles where your team gets stuck?" in content
    assert "What safe, non-sensitive workflow evidence could we inspect first?" in content
    assert "If approval delay is the issue, what is the smallest approval-path test worth trying?" in content
    assert "If we could show your top workflow constraint clearly, who would need to see that result?" in content

    assert "we_do_not_want_to_upload_sensitive_data" in content
    assert "we_already_know_where_the_problem_is" in content
    assert "this_looks_like_project_management" in content
    assert "is_this_production_ready" in content

    assert "walkthrough_header" in content
    assert "opening_script" in content
    assert "buyer_questions" in content
    assert "objection_responses" in content
    assert "demo_boundary" in content
    assert "The buyer walkthrough HTML renderer escapes dynamic script values." in content


def test_assessment_factory_lite_buyer_conversion_closeout_preserves_boundaries_and_exclusions():
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
    assert "guaranteed_sales_conversion" in content
    assert "binding_pricing_terms" in content


def test_assessment_factory_lite_buyer_conversion_closeout_names_next_direction_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Offer Builder Service" in content
    assert "US-214 — Assessment Factory Lite Assessment Offer Builder Service" in content
    assert "The next bottleneck is converting buyer interest into a specific assessment offer." in content
    assert "target buyer" in content
    assert "safe evidence request" in content
    assert "recommended price band" in content

    assert (
        "The Assessment Factory Lite Buyer Conversion release does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
