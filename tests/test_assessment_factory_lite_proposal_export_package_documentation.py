from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PROPOSAL_EXPORT_PACKAGE.md")


def test_assessment_factory_lite_proposal_export_package_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_proposal_export_package_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteProposalExportPackageService" in content
    assert "POST /products/assessment-factory-lite/proposal/export-package" in content
    assert "assessment_factory_lite_proposal_export_package" in content
    assert "assessment-factory-lite-proposal-package" in content
    assert "2.0.0" in content
    assert "proposal_export_package" in content
    assert "review_proposal_export_package" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "export" in content
    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "operator_approval" in content

    assert "status" in content
    assert "package_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "package_stage" in content
    assert "package_status" in content
    assert "markdown_export" in content
    assert "pdf_readiness" in content
    assert "pdf_export" in content
    assert "export_manifest" in content
    assert "operator_approval" in content
    assert "boundary_notices" in content
    assert "package_contents" in content
    assert "blocking_issues" in content
    assert "next_action" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_ready_and_blocked_package_states():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Package Status" in content
    assert "ready" in content
    assert "blocked" in content
    assert "package_status: ready" in content
    assert "recommended_action: review_proposal_export_package" in content
    assert "package_status: blocked" in content
    assert "recommended_action: resolve_proposal_export_package_gaps" in content
    assert "Blocked packages preserve the blocking issues" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_markdown_readiness_and_pdf_summaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_formal_proposal_markdown_export" in content
    assert "formal_proposal_markdown_export" in content
    assert "format: markdown" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "section_count: 14" in content
    assert "markdown_present: True" in content

    assert "assessment_factory_lite_formal_proposal_pdf_readiness" in content
    assert "formal_proposal_pdf_readiness_check" in content
    assert "passed_checks: 9" in content
    assert "failed_checks: 0" in content
    assert "readiness_score: 1.0" in content
    assert "ready_for_pdf: True" in content
    assert "prepare_formal_proposal_pdf_export" in content

    assert "assessment_factory_lite_formal_proposal_pdf_export" in content
    assert "formal_proposal_pdf_export" in content
    assert "content_type: application/pdf" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in content
    assert "review_formal_proposal_pdf_export" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_manifest_and_approval_gate():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "proposal_export_package_manifest" in content
    assert "markdown_filename" in content
    assert "pdf_filename" in content
    assert "markdown_export_type" in content
    assert "pdf_export_type" in content
    assert "pdf_export_status: ok" in content
    assert "generated_by: AssessmentFactoryLiteProposalExportPackageService" in content

    assert "approval_status: operator_review_required" in content
    assert "scope_approved: False" in content
    assert "evidence_boundary_approved: False" in content
    assert "commercial_terms_approved: False" in content
    assert "buyer_language_approved: False" in content
    assert "Operator must approve scope, evidence boundary, commercial terms" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_boundaries_contents_and_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "commercial_boundary" in content
    assert "evidence_boundary" in content
    assert "pdf_boundary" in content
    assert "constitutional_boundary" in content
    assert "non-binding until final scope, price, payment terms" in content
    assert "safe, non-sensitive evidence" in content
    assert "does not create a binding quote" in content
    assert "GAGF Kernel remains the authoritative decision" in content

    assert "formal_proposal_markdown_export" in content
    assert "formal_proposal_pdf_readiness" in content
    assert "formal_proposal_pdf_export_object" in content
    assert "operator_approval_gate" in content
    assert "export_manifest" in content
    assert "boundary_notices" in content

    assert "review_and_prepare_buyer_delivery_package" in content
    assert "prepare_buyer_delivery_package" in content
    assert "resolve_export_package_gaps" in content
    assert "rerun_proposal_export_package" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_blocked_commercial_terms_example():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Blocked Commercial Terms Example" in content
    assert "Binding quote: False" in content
    assert "Binding quote: True" in content
    assert "package_status: blocked" in content
    assert "blocking_issues: commercial_terms_present" in content
    assert "pdf_readiness.ready_for_pdf: False" in content
    assert "pdf_readiness.failed_checks: 1" in content
    assert "pdf_export.status: blocked" in content
    assert "pdf_export.export_stage: formal_proposal_pdf_export_blocked" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_relationships_and_buyer_delivery_path():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The Markdown export is the human-readable proposal content source." in content
    assert "The PDF readiness result determines whether the package is ready or blocked." in content
    assert "The PDF export object is the guarded PDF draft representation." in content
    assert "The package does not create a binary PDF file." in content
    assert "The proposal export package is the bridge between proposal generation and buyer delivery." in content
    assert "It does not send anything to the buyer." in content
    assert "future buyer delivery package" in content
    assert "actual generated PDF" in content
    assert "operator approval record" in content
    assert "evidence boundary metadata" in content


def test_assessment_factory_lite_proposal_export_package_doc_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The proposal export package does not create a binding quote" in content
    assert "operator approves final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Proposal Export Package does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG "
        "certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "buyer delivery" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI may later explain or adapt proposal package language" in content
    assert "AI must not override deterministic readiness checks" in content