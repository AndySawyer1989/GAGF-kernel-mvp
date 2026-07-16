from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PROPOSAL_HTML_VIEW.md")


def test_assessment_factory_lite_proposal_html_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_proposal_html_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteProposalHTMLService" in content
    assert "POST /products/assessment-factory-lite/proposal/html" in content
    assert "assessment_factory_lite_paid_assessment_proposal_html_view" in content
    assert "assessment-factory-lite-commercial-offer" in content
    assert "1.9.0" in content
    assert "proposal_ready_presentation" in content
    assert "present_proposal_html_view" in content


def test_assessment_factory_lite_proposal_html_document_names_request_and_response_contracts():
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
    assert "view_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "view_stage" in content
    assert "html" in content
    assert "source_proposal" in content
    assert "view_sections" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_proposal_html_document_names_view_sections_and_structure():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "proposal_header" in content
    assert "buyer_context" in content
    assert "problem_statement" in content
    assert "proposed_scope" in content
    assert "evidence_boundary" in content
    assert "deliverables" in content
    assert "timeline" in content
    assert "commercial_terms_placeholder" in content
    assert "approval_requirements" in content
    assert "proposal_risk_controls" in content
    assert "excluded_scope" in content
    assert "next_action" in content

    assert "Assessment Factory Lite Proposal" in content
    assert "assessment-factory-lite-paid-assessment-proposal-html-view" in content
    assert "Proposal-Ready Artifact" in content


def test_assessment_factory_lite_proposal_html_document_names_buyer_problem_and_scope():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Proposal for approval and handoff workflow" in content
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


def test_assessment_factory_lite_proposal_html_document_names_evidence_boundary_and_deliverables():
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


def test_assessment_factory_lite_proposal_html_document_names_timeline_terms_approvals_and_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "estimated duration" in content
    assert "intake" in content
    assert "evidence_review" in content
    assert "diagnostic_summary" in content
    assert "recommendation_review" in content

    assert "USD 500 - 2500" in content
    assert "fixed_fee_discovery_assessment" in content
    assert "operator_to_define" in content
    assert "Binding quote:" in content
    assert "automated binding quote" in content

    assert "evidence_boundary_approval" in content
    assert "commercial_terms_approval" in content
    assert "buyer_scope_acknowledgement" in content
    assert "Confirm proposed evidence is safe for assessment intake." in content
    assert "Confirm final price, scope, and payment terms." in content
    assert "Confirm workflow boundary and excluded scope." in content

    assert "non_binding_proposal_until_operator_approval" in content
    assert "safe_evidence_boundary_required" in content
    assert "excluded_scope_must_be_visible" in content
    assert "human_review_before_sending" in content


def test_assessment_factory_lite_proposal_html_document_names_exclusions_next_action_and_custom_context():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "live_system_integration" in content
    assert "autonomous_remediation" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content

    assert "review_and_prepare_proposal" in content
    assert "confirm evidence boundary" in content
    assert "approve commercial terms" in content
    assert "generate_formal_proposal" in content

    assert "security review workflow" in content
    assert "5_to_7_business_days" in content
    assert "USD 1500 - 3500" in content


def test_assessment_factory_lite_proposal_html_document_names_styling_and_escaping():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "afl-brand-orange" in content
    assert "afl-brand-gold" in content
    assert "afl-brand-purple" in content
    assert "afl-proposal-header" in content
    assert "afl-card" in content
    assert "afl-pill" in content
    assert "afl-boundary" in content
    assert "afl-price" in content
    assert "afl-phase" in content

    assert "The proposal HTML renderer escapes dynamic proposal values." in content
    assert "custom buyer context" in content
    assert "custom offer content" in content
    assert "custom proposal content" in content
    assert "timeline phase values" in content
    assert "commercial terms values" in content
    assert "risk control values" in content


def test_assessment_factory_lite_proposal_html_document_names_relationships_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The proposal builder creates the deterministic proposal-ready artifact." in content
    assert "The proposal HTML view turns that artifact into a presentation-ready screen." in content
    assert "What should the proposal contain?" in content
    assert "How should the operator present the proposal?" in content
    assert "The offer HTML view presents the paid-assessment offer." in content
    assert "The proposal HTML view presents the proposal-ready artifact." in content
    assert "A future formal proposal generator may create a polished proposal" in content
    assert "The proposal HTML view does not create a binding quote" in content

    assert (
        "The Assessment Factory Lite Proposal HTML View does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content