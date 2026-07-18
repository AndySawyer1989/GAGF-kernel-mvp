from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_WALKTHROUGH_SCRIPT.md")


def test_assessment_factory_lite_buyer_walkthrough_script_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerWalkthroughScriptService" in content
    assert "GET /products/assessment-factory-lite/buyer-walkthrough/script" in content
    assert "assessment_factory_lite_buyer_walkthrough_script" in content
    assert "assessment-factory-lite-demo-delivery-packaging" in content
    assert "1.7.0" in content
    assert "buyer_demo_conversion" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "script_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "script_stage" in content
    assert "script_summary" in content
    assert "opening_script" in content
    assert "problem_frame" in content
    assert "scenario_script" in content
    assert "finding_script" in content
    assert "intervention_script" in content
    assert "boundary_script" in content
    assert "buyer_questions" in content
    assert "close_script" in content
    assert "objection_responses" in content
    assert "success_criteria" in content
    assert "demo_boundary" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_summary_and_opening():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "founder_operator" in content
    assert "guided_buyer_walkthrough" in content
    assert "10_to_20_minutes" in content
    assert "move_from_demo_interest_to_paid_assessment_conversation" in content
    assert "Assessment Factory Lite shows where work gets stuck" in content
    assert "Open with operational friction" in content
    assert "This is a sample-data-only demo of Assessment Factory Lite." in content
    assert "1_to_2_minutes" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_problem_and_scenarios():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Most teams feel delays before they can prove them." in content
    assert "sample workflow events become a ranked friction finding" in content
    assert "Approval Delay and Blocked Work" in content
    assert "default_buyer_demo" in content
    assert "approval_delay" in content
    assert "Unsafe Data Boundary Test" in content
    assert "trust_and_safety_explanation" in content
    assert "Empty Demo Starting State" in content
    assert "screen_initialization_explanation" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_finding_and_intervention():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Explain the top friction finding" in content
    assert "Approval delays are creating workflow drag." in content
    assert "synthetic approval and blocked-work events" in content
    assert "Explain the recommended intervention" in content
    assert "streamline_approval_path" in content
    assert "reduce waiting time and make approval ownership clearer" in content
    assert "does not mean removing accountability" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_boundary_questions_and_close():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Explain the demo-only boundary" in content
    assert "This demo uses synthetic sample data only." in content
    assert "workflow_similarity" in content
    assert "Which part of this sample workflow most resembles where your team gets stuck?" in content
    assert "evidence_source" in content
    assert "What safe, non-sensitive workflow evidence could we inspect first?" in content
    assert "first_test" in content
    assert "buyer_value" in content
    assert "Close with the assessment offer" in content
    assert "schedule_paid_assessment_conversation" in content
    assert "small, bounded assessment" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_objections_and_success_criteria():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "we_do_not_want_to_upload_sensitive_data" in content
    assert "we_already_know_where_the_problem_is" in content
    assert "this_looks_like_project_management" in content
    assert "is_this_production_ready" in content
    assert "sample-data-only buyer demo" in content
    assert "governance friction" in content
    assert "buyer_understands_sample_data_only_boundary" in content
    assert "buyer_understands_operational_friction_problem" in content
    assert "buyer_understands_recommended_intervention" in content
    assert "operator_can_transition_to_assessment_offer" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_names_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The operator runbook explains how to deliver the demo." in content
    assert "The buyer walkthrough script explains what to say" in content
    assert "The delivery readiness service verifies whether the demo package is ready." in content
    assert "Can we deliver the demo?" in content
    assert "How do we explain the demo to a buyer?" in content
    assert "move from demo interest to a paid assessment conversation" in content


def test_assessment_factory_lite_buyer_walkthrough_script_document_preserves_boundaries():
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
        "The Assessment Factory Lite Buyer Walkthrough Script does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
