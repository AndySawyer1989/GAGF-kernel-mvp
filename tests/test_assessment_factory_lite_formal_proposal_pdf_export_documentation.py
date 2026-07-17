from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_FORMAL_PROPOSAL_PDF_EXPORT.md")


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteFormalProposalPDFExportService" in content
    assert "POST /products/assessment-factory-lite/proposal/document/pdf" in content
    assert "assessment_factory_lite_formal_proposal_pdf_export" in content
    assert "assessment-factory-lite-proposal-package" in content
    assert "2.0.0" in content
    assert "formal_proposal_pdf_export" in content
    assert "review_formal_proposal_pdf_export" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "export" in content
    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "operator_approval" in content

    assert "status" in content
    assert "export_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "export_stage" in content
    assert "format" in content
    assert "content_type" in content
    assert "filename" in content
    assert "source_markdown_filename" in content
    assert "readiness" in content
    assert "pdf_document" in content
    assert "export_manifest" in content
    assert "boundary_notice" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_filename_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in content
    assert "assessment-factory-lite-proposal-security-review-workflow.md" in content
    assert "assessment-factory-lite-proposal-security-review-workflow.pdf" in content
    assert "assessment-factory-lite-proposal-workflow.pdf" in content
    assert "If the Markdown filename ends with .md" in content
    assert "the service replaces .md with .pdf" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_readiness_gate_and_summary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The PDF export service calls the PDF readiness service" in content
    assert "ready_for_pdf: True" in content
    assert "readiness_score: 1.0" in content
    assert "failed_checks: 0" in content
    assert "blocking_issues: []" in content

    assert "readiness_type: assessment_factory_lite_formal_proposal_pdf_readiness" in content
    assert "readiness_stage: formal_proposal_pdf_readiness_check" in content
    assert "passed_checks: 9" in content
    assert "recommended_action: prepare_formal_proposal_pdf_export" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_blocked_export_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Blocked Export Behavior" in content
    assert "status: blocked" in content
    assert "formal_proposal_pdf_export_blocked" in content
    assert "resolve_formal_proposal_pdf_readiness_gaps" in content
    assert "Binding quote: False" in content
    assert "Binding quote: True" in content
    assert "failed_checks: 1" in content
    assert "readiness_score: 0.89" in content
    assert "blocking_issues: commercial_terms_present" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_operator_approval_gate():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Default Operator Approval Gate" in content
    assert "approval_status: operator_review_required" in content
    assert "scope_approved: False" in content
    assert "evidence_boundary_approved: False" in content
    assert "commercial_terms_approved: False" in content
    assert "buyer_language_approved: False" in content
    assert "Operator must approve scope, evidence boundary, commercial terms" in content
    assert "prevents a generated PDF export object from being treated as buyer-approved or send-ready" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_pdf_document_model_and_sections():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "PDF Document Model" in content
    assert "buyer_facing_pdf_proposal_draft" in content
    assert "formal_proposal_markdown_export" in content
    assert "pdf_export_object_ready" in content
    assert "markdown_sections_to_pdf_pages" in content
    assert "Draft - Operator Review Required" in content
    assert "Non-binding proposal draft" in content

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


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_manifest_boundary_and_success_result():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Export Manifest" in content
    assert "pdf_filename" in content
    assert "source_markdown_filename" in content
    assert "source_export_type" in content
    assert "source_export_stage" in content
    assert "source_release" in content
    assert "source_version" in content
    assert "generated_by" in content
    assert "AssessmentFactoryLiteFormalProposalPDFExportService" in content

    assert "Boundary Notice" in content
    assert "non_binding: True" in content
    assert "operator_review_required: True" in content
    assert "not_a_contract: True" in content
    assert "not_an_invoice: True" in content
    assert "not_a_compliance_certification: True" in content
    assert "not_production_onboarding: True" in content
    assert "does not create a binding quote" in content
    assert "GAGF Kernel remains the authoritative decision" in content

    assert "Successful Export Result" in content
    assert "status: ok" in content
    assert "content_type: application/pdf" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_custom_context_and_future_binary_pdf_generation():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "founder_operator" in content
    assert "security review workflow" in content
    assert "5_to_7_business_days" in content
    assert "1500" in content
    assert "3500" in content

    assert "The current PDF export object is not a binary PDF file." in content
    assert "future binary PDF generator" in content
    assert "filename" in content
    assert "source_markdown_filename" in content
    assert "pdf_document" in content
    assert "export_manifest" in content
    assert "operator_approval" in content
    assert "readiness" in content


def test_assessment_factory_lite_formal_proposal_pdf_export_doc_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The PDF export service does not create a binding quote" in content
    assert "generated PDF export object is a draft artifact" in content
    assert "operator must approve final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Formal Proposal PDF Export layer does "
        "not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "operator approval" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI must not override deterministic readiness checks" in content