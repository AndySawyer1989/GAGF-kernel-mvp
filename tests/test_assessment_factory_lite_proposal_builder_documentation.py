from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PROPOSAL_BUILDER.md")


def test_assessment_factory_lite_proposal_builder_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_proposal_builder_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteProposalBuilderService" in content
    assert "POST /products/assessment-factory-lite/proposal" in content
    assert "AssessmentFactoryLiteOfferBuilderService" in content
    assert "assessment_factory_lite_paid_assessment_proposal" in content
    assert "assessment-factory-lite-commercial-offer" in content
    assert "1.9.0" in content
    assert "proposal_ready_artifact" in content
    assert "review_proposal_ready_artifact" in content


def test_assessment_factory_lite_proposal_builder_document_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "offer" in content
    assert "buyer_context" in content
    assert "primary_buyer" in content
    assert "workflow_area" in content
    assert "duration" in content
    assert "price_low" in content
    assert "price_high" in content

    assert "status" in content
    assert "proposal_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "proposal_stage" in content
    assert "proposal_title" in content
    assert "buyer_context" in content
    assert "problem_statement" in content
    assert "proposed_scope" in content
    assert "evidence_boundary" in content
    assert "deliverables" in content
    assert "timeline" in content
    assert "commercial_terms_placeholder" in content
    assert "excluded_scope" in content
    assert "assumptions" in content
    assert "approval_requirements" in content
    assert "proposal_risk_controls" in content
    assert "source_offer" in content
    assert "next_action" in content


def test_assessment_factory_lite_proposal_builder_document_names_title_buyer_and_problem():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Proposal for approval and handoff workflow" in content
    assert "Assessment Factory Lite Proposal for security review workflow" in content

    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content

    assert "approval and handoff workflow" in content
    assert "approval_delay" in content
    assert "workflow friction hypothesis" in content


def test_assessment_factory_lite_proposal_builder_document_names_scope_and_evidence_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "bounded_friction_assessment" in content
    assert "3_to_5_business_days" in content
    assert "review_safe_workflow_evidence" in content
    assert "validate_sample_or_redacted_rows" in content
    assert "identify_top_friction_point" in content
    assert "summarize_governance_drag" in content
    assert "recommend_one_focused_intervention" in content
    assert "prepare_buyer_summary" in content
    assert "one bounded workflow assessment using safe, non-sensitive evidence only" in content

    assert "safe_non_sensitive_workflow_evidence" in content
    assert "sanitized_workflow_export" in content
    assert "approval_timestamps" in content
    assert "handoff_log" in content
    assert "blocked_work_items" in content
    assert "sanitized_csv" in content
    assert "synthetic_sample" in content
    assert "redacted_export" in content
    assert "manual_summary" in content
    assert "redacted_workflow_export" in content
    assert "regulated_health_data" in content
    assert "federal_sensitive_data" in content
    assert "certification_claims_allowed:" in content
    assert "binding_price_quote_allowed:" in content
    assert "false" in content


def test_assessment_factory_lite_proposal_builder_document_names_deliverables_and_timeline():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_summary" in content
    assert "markdown_or_pdf_ready_summary" in content
    assert "executive_summary" in content
    assert "evidence_boundary" in content
    assert "workflow_friction_finding" in content
    assert "top_constraint" in content
    assert "recommended_intervention" in content
    assert "next_test" in content

    assert "recommended_next_test" in content
    assert "short_action_plan" in content
    assert "owner_or_stakeholder" in content

    assert "estimated_duration" in content
    assert "intake" in content
    assert "evidence_review" in content
    assert "diagnostic_summary" in content
    assert "recommendation_review" in content


def test_assessment_factory_lite_proposal_builder_document_names_terms_exclusions_and_assumptions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "fixed_fee_discovery_assessment" in content
    assert "USD" in content
    assert "low: 500" in content
    assert "high: 2500" in content
    assert "operator_to_define" in content
    assert "binding_quote" in content
    assert "automated binding quote" in content

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "live_system_integration" in content
    assert "autonomous_remediation" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content

    assert "buyer_selects_one_workflow_for_assessment" in content
    assert "buyer_provides_safe_non_sensitive_evidence_only" in content
    assert "operator_reviews_evidence_boundary_before_analysis" in content
    assert "assessment_output_is_reviewed_before_buyer_delivery" in content
    assert "final_price_and_terms_are_operator_approved" in content


def test_assessment_factory_lite_proposal_builder_document_names_approvals_and_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "evidence_boundary_approval" in content
    assert "commercial_terms_approval" in content
    assert "buyer_scope_acknowledgement" in content
    assert "Confirm proposed evidence is safe for assessment intake." in content
    assert "Confirm final price, scope, and payment terms." in content
    assert "Confirm workflow boundary and excluded scope." in content
    assert "Required:" in content
    assert "true" in content

    assert "non_binding_proposal_until_operator_approval" in content
    assert "safe_evidence_boundary_required" in content
    assert "excluded_scope_must_be_visible" in content
    assert "human_review_before_sending" in content
    assert "Prevent automated commitment to pricing or terms." in content
    assert "Prevent regulated, federal, secret, or live telemetry intake." in content
    assert "Make production, compliance, and legal exclusions clear." in content


def test_assessment_factory_lite_proposal_builder_document_names_source_offer_next_action_and_custom_context():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_paid_assessment_offer" in content
    assert "paid_assessment_conversion" in content
    assert "assessment-factory-lite-buyer-conversion" in content
    assert "version: 1.8.0" in content
    assert "present_paid_assessment_offer" in content

    assert "review_and_prepare_proposal" in content
    assert "confirm evidence boundary" in content
    assert "approve commercial terms" in content
    assert "generate_formal_proposal" in content

    assert "security review workflow" in content
    assert "5_to_7_business_days" in content
    assert "1500" in content
    assert "3500" in content


def test_assessment_factory_lite_proposal_builder_document_names_relationships_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The assessment offer builder creates the bounded paid-assessment offer." in content
    assert "The proposal builder converts that offer into a proposal-ready artifact." in content
    assert "What paid assessment should we offer?" in content
    assert "How should that offer be structured as a reviewable proposal draft?" in content
    assert "A future proposal HTML view may render the proposal" in content
    assert "The proposal-ready artifact is not yet a formal proposal document." in content
    assert "The proposal builder does not create a binding quote" in content

    assert (
        "The Assessment Factory Lite Proposal Builder does not certify products "
        "as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, "
        "or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
