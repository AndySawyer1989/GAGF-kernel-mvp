from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_FORMAL_PROPOSAL_PDF_READINESS.md")


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteFormalProposalPDFReadinessService" in content
    assert "POST /products/assessment-factory-lite/proposal/document/pdf-readiness" in content
    assert "assessment_factory_lite_formal_proposal_pdf_readiness" in content
    assert "assessment-factory-lite-proposal-package" in content
    assert "2.0.0" in content
    assert "formal_proposal_pdf_readiness_check" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "export" in content
    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content

    assert "status" in content
    assert "readiness_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "readiness_stage" in content
    assert "source_export" in content
    assert "required_sections" in content
    assert "checks" in content
    assert "passed_checks" in content
    assert "failed_checks" in content
    assert "readiness_score" in content
    assert "ready_for_pdf" in content
    assert "recommendation" in content
    assert "blocking_issues" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_source_export_and_sections():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "export_type: assessment_factory_lite_formal_proposal_markdown_export" in content
    assert "export_stage: formal_proposal_markdown_export" in content
    assert "format: markdown" in content
    assert "filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "recommended_action: review_formal_proposal_markdown_export" in content

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


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_required_markdown_headings():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "## Proposal Metadata" in content
    assert "## Buyer Summary" in content
    assert "## Problem Statement" in content
    assert "## Assessment Scope" in content
    assert "## Evidence Boundary" in content
    assert "## Deliverables" in content
    assert "## Timeline" in content
    assert "## Commercial Terms" in content
    assert "## Assumptions" in content
    assert "## Approval Requirements" in content
    assert "## Exclusions" in content
    assert "## Operator Notes" in content
    assert "## Next Action" in content
    assert "## Boundary Notice" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_all_checks():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "export_contract_present" in content
    assert "export_format_is_markdown" in content
    assert "filename_present" in content
    assert "required_sections_present" in content
    assert "commercial_terms_present" in content
    assert "evidence_boundary_present" in content
    assert "approval_requirements_present" in content
    assert "operator_notes_present" in content
    assert "boundary_notice_present" in content

    assert "assessment_factory_lite_formal_proposal_markdown_export" in content
    assert "markdown" in content
    assert ".md" in content
    assert "Binding quote: False" in content
    assert "operator_to_finalize" in content
    assert "safe_non_sensitive_workflow_evidence" in content
    assert "Certification claims allowed: False" in content
    assert "evidence_boundary_approval" in content
    assert "commercial_terms_approval" in content
    assert "buyer_scope_acknowledgement" in content
    assert "review_scope_before_sending" in content
    assert "review_evidence_boundary_before_sending" in content
    assert "review_terms_before_sending" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_passing_and_failing_results():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "passed_checks: 9" in content
    assert "failed_checks: 0" in content
    assert "readiness_score: 1.0" in content
    assert "ready_for_pdf: True" in content
    assert "blocking_issues: []" in content
    assert "prepare_formal_proposal_pdf_export" in content
    assert "Markdown export is ready for operator-reviewed PDF generation." in content

    assert "ready_for_pdf: False" in content
    assert "resolve_formal_proposal_pdf_readiness_gaps" in content
    assert "Markdown export is not ready for PDF generation." in content
    assert "blocking PDF readiness gaps" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_score_logic_and_blocking_examples():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "passed checks divided by total checks" in content
    assert "rounded to two decimal places" in content
    assert "There are nine total checks." in content
    assert "readiness_score == 1.0" in content
    assert "every readiness check must pass" in content

    assert "Missing Boundary Notice Example" in content
    assert "required_sections_present" in content
    assert "boundary_notice_present" in content
    assert "Expected readiness score:" in content
    assert "0.78" in content

    assert "Binding Quote Language Example" in content
    assert "commercial_terms_present" in content
    assert "0.89" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_custom_context_and_future_pdf_path():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "founder_operator" in content
    assert "security review workflow" in content
    assert "5_to_7_business_days" in content
    assert "1500" in content
    assert "3500" in content
    assert "assessment-factory-lite-proposal-security-review-workflow.md" in content

    assert "The PDF readiness layer is a gate before actual PDF export." in content
    assert "ready_for_pdf is True" in content
    assert "readiness_score is 1.0" in content
    assert "blocking_issues is empty" in content
    assert "recommended_action is prepare_formal_proposal_pdf_export" in content
    assert "operator approval metadata" in content
    assert "evidence boundary metadata" in content


def test_assessment_factory_lite_formal_proposal_pdf_readiness_doc_names_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The PDF readiness service does not create a binding quote" in content
    assert "operator-approved and non-binding" in content
    assert "operator must approve final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Formal Proposal PDF Readiness layer does "
        "not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert "deterministic readiness gate before future PDF generation" in content

    assert "does not autonomously approve production launch" in content
    assert "buyer delivery" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI must not override deterministic readiness checks" in content