from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PROPOSAL_EXPORT_PACKAGE_CLOSEOUT.md")


def test_assessment_factory_lite_proposal_export_package_closeout_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_proposal_export_package_closeout_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "2.1.0" in content
    assert "assessment-factory-lite-proposal-export-package" in content
    assert "Sprint:" in content
    assert "5.0" in content
    assert "complete" in content
    assert "GET /version" in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_completed_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Formal Proposal Document" in content
    assert "Markdown Export" in content
    assert "Markdown Export Endpoint" in content
    assert "Markdown Export Documentation" in content
    assert "PDF Readiness" in content
    assert "PDF Readiness Endpoint" in content
    assert "PDF Readiness Documentation" in content
    assert "PDF Export Object" in content
    assert "PDF Export Endpoint" in content
    assert "PDF Export Documentation" in content
    assert "Proposal Export Package" in content
    assert "Proposal Export Package Endpoint" in content
    assert "Proposal Export Package Documentation" in content
    assert "Proposal Export Package Release Marker" in content


def test_assessment_factory_lite_proposal_export_package_closeout_preserves_object_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "proposal export package object: 2.0.0 / assessment-factory-lite-proposal-package" in content
    assert "PDF export object: 2.0.0 / assessment-factory-lite-proposal-package" in content
    assert "PDF readiness object: 2.0.0 / assessment-factory-lite-proposal-package" in content
    assert "Markdown export object: 2.0.0 / assessment-factory-lite-proposal-package" in content
    assert "formal proposal document object: 2.0.0 / assessment-factory-lite-proposal-package" in content

    assert "proposal builder: 1.9.0 / assessment-factory-lite-commercial-offer" in content
    assert "proposal HTML view: 1.9.0 / assessment-factory-lite-commercial-offer" in content
    assert "assessment offer builder: 1.8.0 / assessment-factory-lite-buyer-conversion" in content
    assert "assessment offer HTML view: 1.8.0 / assessment-factory-lite-buyer-conversion" in content
    assert "buyer walkthrough script: 1.7.0 / assessment-factory-lite-demo-delivery-packaging" in content
    assert "buyer walkthrough HTML view: 1.7.0 / assessment-factory-lite-demo-delivery-packaging" in content
    assert "delivery manifest: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "operator runbook: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "delivery readiness: 1.6.0 / assessment-factory-lite-demo-styling-export" in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_completed_components():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteFormalProposalDocumentService" in content
    assert "POST /products/assessment-factory-lite/proposal/document" in content
    assert "assessment_factory_lite_formal_proposal_document" in content

    assert "AssessmentFactoryLiteFormalProposalMarkdownExportService" in content
    assert "POST /products/assessment-factory-lite/proposal/document/markdown" in content
    assert "assessment_factory_lite_formal_proposal_markdown_export" in content

    assert "AssessmentFactoryLiteFormalProposalPDFReadinessService" in content
    assert "POST /products/assessment-factory-lite/proposal/document/pdf-readiness" in content
    assert "assessment_factory_lite_formal_proposal_pdf_readiness" in content

    assert "AssessmentFactoryLiteFormalProposalPDFExportService" in content
    assert "POST /products/assessment-factory-lite/proposal/document/pdf" in content
    assert "assessment_factory_lite_formal_proposal_pdf_export" in content

    assert "AssessmentFactoryLiteProposalExportPackageService" in content
    assert "POST /products/assessment-factory-lite/proposal/export-package" in content
    assert "assessment_factory_lite_proposal_export_package" in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_readiness_checks_and_passing_result():
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

    assert "passed_checks: 9" in content
    assert "failed_checks: 0" in content
    assert "readiness_score: 1.0" in content
    assert "ready_for_pdf: True" in content
    assert "blocking_issues: []" in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_package_contents_manifest_and_gate():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "formal_proposal_markdown_export" in content
    assert "formal_proposal_pdf_readiness" in content
    assert "formal_proposal_pdf_export_object" in content
    assert "operator_approval_gate" in content
    assert "export_manifest" in content
    assert "boundary_notices" in content
    assert "blocking_issues" in content
    assert "next_action" in content

    assert "package_manifest_type" in content
    assert "markdown_filename" in content
    assert "pdf_filename" in content
    assert "markdown_export_type" in content
    assert "pdf_export_type" in content
    assert "pdf_export_status" in content
    assert "generated_by" in content
    assert "AssessmentFactoryLiteProposalExportPackageService" in content

    assert "approval_status: operator_review_required" in content
    assert "scope_approved: False" in content
    assert "evidence_boundary_approved: False" in content
    assert "commercial_terms_approved: False" in content
    assert "buyer_language_approved: False" in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_boundaries_and_delivery_status():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "commercial_boundary" in content
    assert "evidence_boundary" in content
    assert "pdf_boundary" in content
    assert "constitutional_boundary" in content
    assert "non-binding until final scope, price, payment terms" in content
    assert "safe, non-sensitive evidence" in content
    assert "does not create a binding quote" in content
    assert "deterministic GAGF Kernel remains the authoritative decision" in content

    assert "Buyer delivery is not complete yet." in content
    assert "It does not send anything to the buyer." in content
    assert "It does not create a binary PDF." in content
    assert "It does not create a signed proposal." in content
    assert "It does not create a contract." in content
    assert "It does not create an invoice." in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_future_work_and_next_story():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "buyer delivery package service" in content
    assert "buyer delivery package endpoint" in content
    assert "buyer delivery package documentation" in content
    assert "actual binary PDF generator" in content
    assert "DOCX export service" in content
    assert "operator approval record service" in content
    assert "signed approval workflow" in content
    assert "buyer-facing email/message generator" in content
    assert "lead capture workflow" in content
    assert "CRM-ready export" in content
    assert "statement of work generator" in content
    assert "pricing approval workflow" in content

    assert "Buyer Delivery Package" in content
    assert "US-247 — Assessment Factory Lite Buyer Delivery Package Service" in content
    assert "buyer-facing deliverables" in content
    assert "delivery checklist" in content
    assert "send-readiness status" in content


def test_assessment_factory_lite_proposal_export_package_closeout_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The proposal export package does not create a binding quote" in content
    assert "operator approves final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Proposal Export Package release does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "buyer delivery" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI may later explain or adapt proposal package language" in content
    assert "AI must not override deterministic readiness checks" in content
