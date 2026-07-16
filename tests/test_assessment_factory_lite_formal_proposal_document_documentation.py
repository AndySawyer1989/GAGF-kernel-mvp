from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_FORMAL_PROPOSAL_DOCUMENT.md")


def test_assessment_factory_lite_formal_proposal_document_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_formal_proposal_document_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteFormalProposalDocumentService" in content
    assert "POST /products/assessment-factory-lite/proposal/document" in content
    assert "assessment_factory_lite_formal_proposal_document" in content
    assert "assessment-factory-lite-proposal-package" in content
    assert "2.0.0" in content
    assert "formal_proposal_document_draft" in content
    assert "review_formal_proposal_document" in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "primary_buyer" in content
    assert "workflow_area" in content
    assert "duration" in content
    assert "price_low" in content
    assert "price_high" in content

    assert "status" in content
    assert "document_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "document_stage" in content
    assert "document_title" in content
    assert "buyer_summary" in content
    assert "problem_statement" in content
    assert "assessment_scope" in content
    assert "evidence_boundary" in content
    assert "deliverables" in content
    assert "timeline" in content
    assert "commercial_terms" in content
    assert "assumptions" in content
    assert "approval_requirements" in content
    assert "exclusions" in content
    assert "operator_notes" in content
    assert "source_proposal" in content
    assert "document_sections" in content
    assert "next_action" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_title_buyer_problem_and_scope():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Formal Assessment Factory Lite Proposal for approval and handoff workflow" in content
    assert "Formal Assessment Factory Lite Proposal for security review workflow" in content

    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content
    assert "approval and handoff workflow" in content
    assert "approval_delay" in content
    assert "workflow friction hypothesis" in content

    assert "bounded_friction_assessment" in content
    assert "3_to_5_business_days" in content
    assert "review_safe_workflow_evidence" in content
    assert "validate_sample_or_redacted_rows" in content
    assert "identify_top_friction_point" in content
    assert "summarize_governance_drag" in content
    assert "recommend_one_focused_intervention" in content
    assert "prepare_buyer_summary" in content
    assert "one bounded workflow assessment using safe, non-sensitive evidence only" in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_evidence_and_deliverables():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "safe_non_sensitive_workflow_evidence" in content
    assert "sanitized_workflow_export" in content
    assert "approval_timestamps" in content
    assert "handoff_log" in content
    assert "blocked_work_items" in content
    assert "sanitized_csv" in content
    assert "synthetic_sample" in content
    assert "redacted_export" in content
    assert "manual_summary" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "redacted_workflow_export" in content
    assert "manual_workflow_summary" in content
    assert "regulated_health_data" in content
    assert "federal_sensitive_data" in content
    assert "live_security_telemetry" in content
    assert "certification_claims_allowed:" in content
    assert "binding_price_quote_allowed:" in content
    assert "False" in content

    assert "assessment_summary" in content
    assert "recommended_next_test" in content
    assert "markdown_or_pdf_ready_summary" in content
    assert "workflow_friction_finding" in content
    assert "recommended_intervention" in content
    assert "short_action_plan" in content
    assert "owner_or_stakeholder" in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_timeline_terms_and_assumptions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "estimated_duration" in content
    assert "intake" in content
    assert "evidence_review" in content
    assert "diagnostic_summary" in content
    assert "recommendation_review" in content

    assert "fixed_fee_discovery_assessment" in content
    assert "USD" in content
    assert "low: 500" in content
    assert "high: 2500" in content
    assert "operator_to_define" in content
    assert "binding_quote" in content
    assert "operator_to_finalize" in content
    assert "automated binding quote" in content

    assert "buyer_selects_one_workflow_for_assessment" in content
    assert "buyer_provides_safe_non_sensitive_evidence_only" in content
    assert "operator_reviews_evidence_boundary_before_analysis" in content
    assert "assessment_output_is_reviewed_before_buyer_delivery" in content
    assert "final_price_and_terms_are_operator_approved" in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_approvals_exclusions_and_notes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "evidence_boundary_approval" in content
    assert "commercial_terms_approval" in content
    assert "buyer_scope_acknowledgement" in content
    assert "Confirm proposed evidence is safe for assessment intake." in content
    assert "Confirm final price, scope, and payment terms." in content
    assert "Confirm workflow boundary and excluded scope." in content

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "live_system_integration" in content
    assert "autonomous_remediation" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content
    assert "binding_price_quote" in content
    assert "binding_sales_contract" in content
    assert "production_service_commitment" in content
    assert "legal_or_compliance_certification" in content

    assert "review_scope_before_sending" in content
    assert "review_evidence_boundary_before_sending" in content
    assert "review_terms_before_sending" in content
    assert "Confirm only safe, non-sensitive evidence is requested." in content
    assert "Finalize payment terms, proposal expiration, and pricing before buyer delivery." in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_source_next_action_and_custom_context():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_paid_assessment_proposal" in content
    assert "proposal_ready_artifact" in content
    assert "assessment-factory-lite-commercial-offer" in content
    assert "version: 1.9.0" in content
    assert "review_proposal_ready_artifact" in content

    assert "review_and_finalize_formal_proposal_document" in content
    assert "finalize commercial terms" in content
    assert "confirm evidence boundaries" in content
    assert "export_formal_proposal_document" in content

    assert "security review workflow" in content
    assert "5_to_7_business_days" in content
    assert "1500" in content
    assert "3500" in content


def test_assessment_factory_lite_formal_proposal_document_doc_names_relationships_and_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The proposal builder creates the deterministic proposal-ready artifact." in content
    assert "The formal proposal document service converts that artifact into a structured formal document draft." in content
    assert "What should the proposal contain?" in content
    assert "How should that proposal be organized as a formal document object?" in content
    assert "The proposal HTML view presents the proposal-ready artifact inside the Operator Workstation." in content
    assert "The formal proposal document object prepares the structure for a future buyer-facing export." in content
    assert "A future export service may convert the formal proposal document object" in content
    assert "The formal proposal document service does not create a binding quote" in content

    assert (
        "The Assessment Factory Lite Formal Proposal Document does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG "
        "certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content