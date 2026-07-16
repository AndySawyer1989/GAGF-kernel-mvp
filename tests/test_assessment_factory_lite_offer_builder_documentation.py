from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_OFFER_BUILDER.md")


def test_assessment_factory_lite_offer_builder_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_offer_builder_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteOfferBuilderService" in content
    assert "POST /products/assessment-factory-lite/assessment-offer" in content
    assert "assessment_factory_lite_paid_assessment_offer" in content
    assert "assessment-factory-lite-buyer-conversion" in content
    assert "1.8.0" in content
    assert "paid_assessment_conversion" in content


def test_assessment_factory_lite_offer_builder_document_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "buyer_context" in content
    assert "walkthrough_script" in content
    assert "primary_buyer" in content
    assert "workflow_area" in content
    assert "requested_sources" in content
    assert "price_low" in content
    assert "price_high" in content

    assert "status" in content
    assert "offer_type" in content
    assert "target_buyer" in content
    assert "problem_statement" in content
    assert "safe_evidence_request" in content
    assert "assessment_scope" in content
    assert "excluded_scope" in content
    assert "deliverable" in content
    assert "recommended_price_band" in content
    assert "buyer_commitment" in content
    assert "qualification_questions" in content
    assert "risk_controls" in content
    assert "next_action" in content
    assert "demo_boundary" in content


def test_assessment_factory_lite_offer_builder_document_names_target_buyer_and_problem():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content
    assert "approval and handoff workflow" in content
    assert "approval_delay" in content
    assert "highest-friction constraint" in content
    assert "traceable evidence" in content


def test_assessment_factory_lite_offer_builder_document_names_safe_evidence_and_scope():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "safe_non_sensitive_workflow_evidence" in content
    assert "sanitized_workflow_export" in content
    assert "approval_timestamps" in content
    assert "handoff_log" in content
    assert "blocked_work_items" in content
    assert "sanitized_csv" in content
    assert "redacted_export" in content
    assert "regulated_health_data" in content
    assert "federal_sensitive_data" in content
    assert "bounded_friction_assessment" in content
    assert "3_to_5_business_days" in content
    assert "review_safe_workflow_evidence" in content
    assert "recommend_one_focused_intervention" in content


def test_assessment_factory_lite_offer_builder_document_names_exclusions_deliverable_and_price():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content

    assert "assessment_factory_lite_buyer_summary" in content
    assert "markdown_or_pdf_ready_summary" in content
    assert "executive_summary" in content
    assert "workflow_friction_finding" in content
    assert "recommended_intervention" in content

    assert "USD" in content
    assert "500" in content
    assert "2500" in content
    assert "fixed_fee_discovery_assessment" in content
    assert "automated binding quote" in content


def test_assessment_factory_lite_offer_builder_document_names_commitment_questions_and_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "small_bounded_assessment" in content
    assert "one_workflow_to_assess" in content
    assert "safe_non_sensitive_evidence" in content
    assert "workflow_owner_contact" in content
    assert "review_time_for_findings" in content

    assert "workflow_similarity" in content
    assert "evidence_source" in content
    assert "first_test" in content
    assert "buyer_value" in content
    assert "Used for offer:" in content
    assert "true" in content

    assert "sample_or_redacted_data_only" in content
    assert "operator_price_approval" in content
    assert "excluded_scope_visibility" in content
    assert "human_review_before_delivery" in content


def test_assessment_factory_lite_offer_builder_document_names_next_action_source_and_custom_context():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "schedule_paid_assessment_conversation" in content
    assert "small bounded assessment focused on one workflow" in content
    assert "approve final price" in content

    assert "assessment_factory_lite_buyer_walkthrough_script" in content
    assert "buyer_demo_conversion" in content
    assert "use_buyer_walkthrough_script" in content

    assert "security review workflow" in content
    assert "5_to_7_business_days" in content
    assert "1500" in content
    assert "3500" in content


def test_assessment_factory_lite_offer_builder_document_preserves_boundaries():
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


def test_assessment_factory_lite_offer_builder_document_names_relationships_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The buyer walkthrough script explains the demo." in content
    assert "The assessment offer builder converts buyer interest" in content
    assert "The buyer conversion release made the demo presentable." in content
    assert "A future proposal builder may turn the offer into a polished proposal" in content
    assert "The assessment offer builder does not create a binding quote." in content

    assert (
        "The Assessment Factory Lite Assessment Offer Builder does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content