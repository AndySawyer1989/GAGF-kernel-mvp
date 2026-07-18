from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_WALKTHROUGH_HTML_VIEW.md")


def test_assessment_factory_lite_buyer_walkthrough_html_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerWalkthroughHTMLService" in content
    assert "GET /products/assessment-factory-lite/buyer-walkthrough/html" in content
    assert "assessment_factory_lite_buyer_walkthrough_html_view" in content
    assert "assessment-factory-lite-demo-delivery-packaging" in content
    assert "1.7.0" in content
    assert "buyer_demo_conversion" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "view_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "view_stage" in content
    assert "html" in content
    assert "source_script" in content
    assert "view_sections" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_view_sections():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "walkthrough_header" in content
    assert "opening_script" in content
    assert "problem_frame" in content
    assert "scenario_script" in content
    assert "finding_script" in content
    assert "intervention_script" in content
    assert "boundary_script" in content
    assert "buyer_questions" in content
    assert "close_script" in content
    assert "objection_responses" in content
    assert "demo_boundary" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_html_structure_and_buyer_language():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Buyer Walkthrough" in content
    assert "assessment-factory-lite-buyer-walkthrough-html-view" in content
    assert "This is a sample-data-only demo of Assessment Factory Lite." in content
    assert "Most teams feel delays before they can prove them." in content
    assert "Assessment Factory Lite shows where work gets stuck" in content
    assert "Presentation-Ready HTML" in content
    assert "Operator Workstation Buyer Demo View" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_scenarios_finding_and_intervention():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Approval Delay and Blocked Work" in content
    assert "approval_delay" in content
    assert "Unsafe Data Boundary Test" in content
    assert "Empty Demo Starting State" in content
    assert "Approval delays are creating workflow drag." in content
    assert "synthetic approval and blocked-work events" in content
    assert "streamline_approval_path" in content
    assert "reduce waiting time and make approval ownership clearer" in content
    assert "does not mean removing accountability" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_questions_close_and_objections():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "workflow_similarity" in content
    assert "Which part of this sample workflow most resembles where your team gets stuck?" in content
    assert "evidence_source" in content
    assert "What safe, non-sensitive workflow evidence could we inspect first?" in content
    assert "first_test" in content
    assert "buyer_value" in content
    assert "schedule_paid_assessment_conversation" in content
    assert "small, bounded assessment" in content

    assert "we_do_not_want_to_upload_sensitive_data" in content
    assert "we_already_know_where_the_problem_is" in content
    assert "this_looks_like_project_management" in content
    assert "is_this_production_ready" in content
    assert "Project management tracks work. Assessment Factory Lite focuses on governance friction." in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_styling_and_escaping():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "afl-brand-orange" in content
    assert "afl-brand-gold" in content
    assert "afl-brand-purple" in content
    assert "afl-surface" in content
    assert "afl-card-radius" in content
    assert "The HTML renderer escapes dynamic script values." in content
    assert "package name" in content
    assert "operator scripts" in content
    assert "objection text" in content
    assert "boundary values" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_names_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The buyer walkthrough script defines what the operator should say." in content
    assert "The buyer walkthrough HTML view turns that script into a presentation-ready screen." in content
    assert "The Operator Workstation can use this HTML view" in content
    assert "Can we deliver the demo?" in content
    assert "Can the operator present the buyer walkthrough clearly?" in content
    assert "transition from demo to assessment offer" in content


def test_assessment_factory_lite_buyer_walkthrough_html_document_preserves_boundaries():
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
    assert "guaranteed_operational_outcomes" in content
    assert (
        "The Assessment Factory Lite Buyer Walkthrough HTML View does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
