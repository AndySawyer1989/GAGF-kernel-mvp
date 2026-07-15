from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_OPERATOR_RUNBOOK.md")


def test_assessment_factory_lite_operator_runbook_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_operator_runbook_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteOperatorRunbookService" in content
    assert "GET /products/assessment-factory-lite/delivery/runbook" in content
    assert "assessment_factory_lite_demo_operator_runbook" in content
    assert "assessment-factory-lite-demo-styling-export" in content
    assert "1.6.0" in content
    assert "demo_delivery_packaging" in content


def test_assessment_factory_lite_operator_runbook_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "runbook_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "runbook_stage" in content
    assert "runbook_summary" in content
    assert "pre_demo_checklist" in content
    assert "live_demo_sequence" in content
    assert "scenario_talking_points" in content
    assert "operator_safety_rules" in content
    assert "stop_conditions" in content
    assert "buyer_follow_up" in content
    assert "success_criteria" in content
    assert "demo_boundary" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_operator_runbook_document_names_summary_and_checklist():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "founder_operator" in content
    assert "live_walkthrough" in content
    assert "10_to_20_minutes" in content
    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "early_buyer" in content
    assert "version_endpoint_ready" in content
    assert "delivery_manifest_available" in content
    assert "scenario_menu_available" in content
    assert "styled_html_screen_available" in content
    assert "buyer_export_polish_available" in content
    assert "demo_boundary_visible" in content


def test_assessment_factory_lite_operator_runbook_document_names_live_demo_sequence():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Open with the problem" in content
    assert "Show the scenario menu" in content
    assert "Load the standard demo" in content
    assert "Explain the finding" in content
    assert "Show buyer export polish" in content
    assert "Show boundary protection" in content
    assert "Close with next evidence question" in content
    assert "GET /products/assessment-factory-lite/demo-scenario-menu" in content
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content
    assert "POST /products/assessment-factory-lite/buyer-export/polish" in content


def test_assessment_factory_lite_operator_runbook_document_names_scenario_talking_points():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Approval Delay and Blocked Work" in content
    assert "Unsafe Data Boundary Test" in content
    assert "Empty Demo Starting State" in content
    assert "Approval delays are creating workflow drag." in content
    assert "Sample data needs repair before buyer presentation." in content
    assert "Add synthetic sample rows before running the demo." in content
    assert "streamline_approval_path" in content
    assert "repair_sample_csv_before_demo" in content
    assert "add_demo_rows" in content


def test_assessment_factory_lite_operator_runbook_document_names_safety_rules_and_stop_conditions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "use_sample_data_only" in content
    assert "avoid_certification_claims" in content
    assert "do_not_overstate_automation" in content
    assert "preserve_traceability" in content
    assert "ask_for_workflow_similarity" in content
    assert "buyer_requests_real_data_upload" in content
    assert "regulated_or_federal_data_is_offered" in content
    assert "certification_claim_requested" in content
    assert "unsafe_sample_rows_detected" in content
    assert "do_not_accept_real_customer_data" in content
    assert "reject_regulated_or_federal_data" in content


def test_assessment_factory_lite_operator_runbook_document_names_buyer_follow_up_and_success_criteria():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "workflow_similarity_question" in content
    assert "Which part of this sample workflow most resembles where your team gets stuck?" in content
    assert "evidence_source_question" in content
    assert "What safe, non-sensitive workflow evidence could we inspect first?" in content
    assert "first_intervention_question" in content
    assert "operator_can_explain_problem_in_plain_language" in content
    assert "scenario_menu_is_visible" in content
    assert "standard_demo_renders_successfully" in content
    assert "buyer_export_polish_is_presented" in content
    assert "no_real_customer_data_is_used" in content


def test_assessment_factory_lite_operator_runbook_document_names_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The delivery manifest answers:" in content
    assert "What is included in the package?" in content
    assert "The operator runbook answers:" in content
    assert "How should the operator deliver the demo?" in content
    assert "The future delivery readiness service should verify" in content
    assert "The operator runbook helps the founder or operator" in content


def test_assessment_factory_lite_operator_runbook_document_preserves_boundaries():
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
    assert "pdf_generation" in content
    assert (
        "The Assessment Factory Lite Operator Runbook does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content