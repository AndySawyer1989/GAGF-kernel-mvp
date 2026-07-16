from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_OFFER_HTML_VIEW.md")


def test_assessment_factory_lite_offer_html_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_offer_html_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteOfferHTMLService" in content
    assert "POST /products/assessment-factory-lite/assessment-offer/html" in content
    assert "assessment_factory_lite_paid_assessment_offer_html_view" in content
    assert "assessment-factory-lite-buyer-conversion" in content
    assert "1.8.0" in content
    assert "paid_assessment_conversion" in content


def test_assessment_factory_lite_offer_html_document_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "offer" in content
    assert "buyer_context" in content
    assert "primary_buyer" in content
    assert "workflow_area" in content
    assert "price_low" in content
    assert "price_high" in content

    assert "status" in content
    assert "view_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "view_stage" in content
    assert "html" in content
    assert "source_offer" in content
    assert "view_sections" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_offer_html_document_names_view_sections():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "offer_header" in content
    assert "target_buyer" in content
    assert "problem_statement" in content
    assert "safe_evidence_request" in content
    assert "assessment_scope" in content
    assert "deliverable" in content
    assert "recommended_price_band" in content
    assert "buyer_commitment" in content
    assert "qualification_questions" in content
    assert "risk_controls" in content
    assert "next_action" in content
    assert "demo_boundary" in content
    assert "excluded_scope" in content


def test_assessment_factory_lite_offer_html_document_names_html_structure_and_target_buyer():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Paid Assessment Offer" in content
    assert "assessment-factory-lite-paid-assessment-offer-html-view" in content
    assert "Paid Assessment Offer" in content
    assert "assessment_factory_lite_paid_assessment_offer" in content
    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content


def test_assessment_factory_lite_offer_html_document_names_problem_evidence_scope_and_deliverable():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "approval and handoff workflow" in content
    assert "approval_delay" in content
    assert "safe_non_sensitive_workflow_evidence" in content
    assert "sanitized_workflow_export" in content
    assert "approval_timestamps" in content
    assert "handoff_log" in content
    assert "blocked_work_items" in content
    assert "sanitized_csv" in content
    assert "redacted_export" in content
    assert "bounded_friction_assessment" in content
    assert "3_to_5_business_days" in content
    assert "review_safe_workflow_evidence" in content
    assert "assessment_factory_lite_buyer_summary" in content
    assert "markdown_or_pdf_ready_summary" in content


def test_assessment_factory_lite_offer_html_document_names_price_commitment_questions_and_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "USD 500 - 2500" in content
    assert "fixed_fee_discovery_assessment" in content
    assert "automated binding quote" in content

    assert "one_workflow_to_assess" in content
    assert "safe_non_sensitive_evidence" in content
    assert "workflow_owner_contact" in content
    assert "review_time_for_findings" in content

    assert "workflow_similarity" in content
    assert "evidence_source" in content
    assert "first_test" in content
    assert "buyer_value" in content

    assert "sample_or_redacted_data_only" in content
    assert "operator_price_approval" in content
    assert "excluded_scope_visibility" in content
    assert "human_review_before_delivery" in content


def test_assessment_factory_lite_offer_html_document_preserves_boundaries_and_exclusions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_and_assessment_intake_boundary" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "sanitized_csv" in content
    assert "redacted_workflow_export" in content
    assert "manual_workflow_summary" in content

    assert "real_customer_secrets" in content
    assert "regulated_health_data" in content
    assert "federal_sensitive_data" in content
    assert "production_customer_data_without_review" in content
    assert "credentials" in content
    assert "live_security_telemetry" in content
    assert "certification_claims_allowed:" in content
    assert "binding_price_quote_allowed:" in content
    assert "false" in content

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content


def test_assessment_factory_lite_offer_html_document_names_custom_context_styling_and_escaping():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "security review workflow" in content
    assert "USD 1500 - 3500" in content

    assert "afl-brand-orange" in content
    assert "afl-brand-gold" in content
    assert "afl-brand-purple" in content
    assert "afl-price" in content

    assert "The HTML renderer escapes dynamic offer values." in content
    assert "buyer fields" in content
    assert "workflow area" in content
    assert "price values" in content
    assert "excluded scope values" in content


def test_assessment_factory_lite_offer_html_document_names_relationships_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The assessment offer builder creates the deterministic offer structure." in content
    assert "The assessment offer HTML view turns that offer into a presentation-ready screen." in content
    assert "What should we offer?" in content
    assert "How should the operator present the offer?" in content
    assert "A future proposal builder may turn the offer into a formal proposal" in content
    assert "The assessment offer HTML view does not create a binding quote." in content

    assert (
        "The Assessment Factory Lite Assessment Offer HTML View does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content