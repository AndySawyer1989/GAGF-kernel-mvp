from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_FORMAL_PROPOSAL_MARKDOWN_EXPORT.md")


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteFormalProposalMarkdownExportService" in content
    assert "POST /products/assessment-factory-lite/proposal/document/markdown" in content
    assert "assessment_factory_lite_formal_proposal_markdown_export" in content
    assert "assessment-factory-lite-proposal-package" in content
    assert "2.0.0" in content
    assert "formal_proposal_markdown_export" in content
    assert "review_formal_proposal_markdown_export" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "primary_buyer" in content
    assert "workflow_area" in content
    assert "duration" in content
    assert "price_low" in content
    assert "price_high" in content

    assert "status" in content
    assert "export_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "export_stage" in content
    assert "format" in content
    assert "filename" in content
    assert "markdown" in content
    assert "source_document" in content
    assert "export_sections" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_filename_and_source_document():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "assessment-factory-lite-proposal-security-review-workflow.md" in content
    assert "assessment-factory-lite-proposal-workflow.md" in content
    assert "lowercases the workflow area" in content
    assert "replaces spaces and underscores with hyphens" in content
    assert "removes unsafe characters" in content

    assert "document_type: assessment_factory_lite_formal_proposal_document" in content
    assert "document_stage: formal_proposal_document_draft" in content
    assert "release: assessment-factory-lite-proposal-package" in content
    assert "version: 2.0.0" in content
    assert "recommended_action: review_formal_proposal_document" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_export_sections_and_markdown_structure():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "proposal_metadata" in content
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
    assert "next_action" in content
    assert "boundary_notice" in content

    assert "# Formal Assessment Factory Lite Proposal for approval and handoff workflow" in content
    assert "# Formal Assessment Factory Lite Proposal for security review workflow" in content
    assert "## Proposal Metadata Section" in content
    assert "## Buyer Summary Section" in content
    assert "## Problem Statement Section" in content
    assert "## Assessment Scope Section" in content
    assert "## Evidence Boundary Section" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_buyer_problem_scope_and_evidence():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content
    assert "approval and handoff workflow" in content
    assert "approval_delay" in content

    assert "bounded_friction_assessment" in content
    assert "3_to_5_business_days" in content
    assert "review_safe_workflow_evidence" in content
    assert "validate_sample_or_redacted_rows" in content
    assert "identify_top_friction_point" in content
    assert "summarize_governance_drag" in content
    assert "recommend_one_focused_intervention" in content
    assert "prepare_buyer_summary" in content

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
    assert "Certification claims allowed:" in content
    assert "Binding price quote allowed:" in content
    assert "False" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_deliverables_timeline_terms_and_assumptions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_summary" in content
    assert "recommended_next_test" in content
    assert "markdown_or_pdf_ready_summary" in content
    assert "workflow_friction_finding" in content
    assert "recommended_intervention" in content
    assert "short_action_plan" in content
    assert "owner_or_stakeholder" in content

    assert "intake" in content
    assert "evidence_review" in content
    assert "diagnostic_summary" in content
    assert "recommendation_review" in content

    assert "fixed_fee_discovery_assessment" in content
    assert "USD 500 - 2500" in content
    assert "operator_to_define" in content
    assert "operator_to_finalize" in content
    assert "automated binding quote" in content

    assert "buyer_selects_one_workflow_for_assessment" in content
    assert "buyer_provides_safe_non_sensitive_evidence_only" in content
    assert "operator_reviews_evidence_boundary_before_analysis" in content
    assert "assessment_output_is_reviewed_before_buyer_delivery" in content
    assert "final_price_and_terms_are_operator_approved" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_approvals_exclusions_notes_and_boundary_notice():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "evidence_boundary_approval" in content
    assert "commercial_terms_approval" in content
    assert "buyer_scope_acknowledgement" in content
    assert "required_by, purpose, and required" in content

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "live_system_integration" in content
    assert "autonomous_remediation" in content
    assert "security_certification" in content
    assert "compliance_audit" in content
    assert "soc_2_audit_claims" in content
    assert "fedramp_or_hipaa_certification_claims" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content
    assert "binding_price_quote" in content
    assert "binding_sales_contract" in content
    assert "production_service_commitment" in content
    assert "legal_or_compliance_certification" in content

    assert "review_scope_before_sending" in content
    assert "review_evidence_boundary_before_sending" in content
    assert "review_terms_before_sending" in content
    assert "operator review before the Markdown export is used as buyer-facing material" in content

    assert "not a binding quote, sales contract, invoice, legal agreement" in content
    assert "operator must review scope, pricing, evidence boundaries" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_relationships_and_future_exports():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The formal proposal document service creates a structured document object." in content
    assert "The Markdown export service renders that document object into Markdown." in content
    assert "What should the formal proposal document contain?" in content
    assert "How should the formal proposal document be rendered as Markdown?" in content

    assert "The Markdown export is a bridge format." in content
    assert "future PDF export service" in content
    assert "future DOCX export service" in content
    assert "proposal package exporter" in content
    assert "Markdown, PDF, DOCX, operator notes, evidence boundary metadata, and approval records" in content


def test_assessment_factory_lite_formal_proposal_markdown_export_doc_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The Markdown export service does not create a binding quote" in content
    assert "recommended price band remains operator-approved and non-binding" in content
    assert "operator must approve final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Formal Proposal Markdown Export does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "live integrations" in content
    assert "AI may later explain or adapt Markdown proposal language" in content
    assert "AI must not override deterministic assessment boundaries" in content