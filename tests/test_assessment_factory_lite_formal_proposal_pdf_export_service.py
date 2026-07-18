from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_pdf_export_service import (
    AssessmentFactoryLiteFormalProposalPDFExportService,
)


def service():
    return AssessmentFactoryLiteFormalProposalPDFExportService()


def test_assessment_factory_lite_formal_proposal_pdf_export_builds_contract():
    result = service().export_pdf()

    assert result["status"] == "ok"
    assert result["export_type"] == (
        "assessment_factory_lite_formal_proposal_pdf_export"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-package"
    assert result["version"] == "2.0.0"
    assert result["export_stage"] == "formal_proposal_pdf_export"
    assert result["format"] == "pdf"
    assert result["content_type"] == "application/pdf"
    assert result["recommended_action"] == "review_formal_proposal_pdf_export"


def test_assessment_factory_lite_formal_proposal_pdf_export_uses_pdf_filename():
    result = service().export_pdf()

    assert result["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )
    assert result["source_markdown_filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
    )


def test_assessment_factory_lite_formal_proposal_pdf_export_includes_readiness_summary():
    result = service().export_pdf()

    assert result["readiness"] == {
        "readiness_type": "assessment_factory_lite_formal_proposal_pdf_readiness",
        "readiness_stage": "formal_proposal_pdf_readiness_check",
        "passed_checks": 9,
        "failed_checks": 0,
        "readiness_score": 1.0,
        "ready_for_pdf": True,
        "blocking_issues": [],
        "recommended_action": "prepare_formal_proposal_pdf_export",
    }


def test_assessment_factory_lite_formal_proposal_pdf_export_includes_default_operator_approval_gate():
    result = service().export_pdf()

    approval = result["operator_approval"]

    assert approval == {
        "approval_status": "operator_review_required",
        "scope_approved": False,
        "evidence_boundary_approved": False,
        "commercial_terms_approved": False,
        "buyer_language_approved": False,
        "approval_note": (
            "PDF export object is generated for review only. Operator must "
            "approve scope, evidence boundary, commercial terms, and buyer-facing "
            "language before sending."
        ),
    }


def test_assessment_factory_lite_formal_proposal_pdf_export_includes_pdf_document_model():
    result = service().export_pdf()

    pdf_document = result["pdf_document"]

    assert pdf_document["document_kind"] == "buyer_facing_pdf_proposal_draft"
    assert pdf_document["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )
    assert pdf_document["render_source"] == "formal_proposal_markdown_export"
    assert pdf_document["render_status"] == "pdf_export_object_ready"
    assert pdf_document["page_model"] == "markdown_sections_to_pdf_pages"
    assert pdf_document["watermark"] == "Draft - Operator Review Required"
    assert "Non-binding proposal draft" in pdf_document["footer_notice"]
    assert "proposal_metadata" in pdf_document["required_sections"]
    assert "boundary_notice" in pdf_document["required_sections"]


def test_assessment_factory_lite_formal_proposal_pdf_export_includes_export_manifest():
    result = service().export_pdf()

    assert result["export_manifest"] == {
        "pdf_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
        ),
        "source_markdown_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
        ),
        "source_export_type": (
            "assessment_factory_lite_formal_proposal_markdown_export"
        ),
        "source_export_stage": "formal_proposal_markdown_export",
        "source_release": "assessment-factory-lite-proposal-package",
        "source_version": "2.0.0",
        "readiness_score": 1.0,
        "ready_for_pdf": True,
        "generated_by": "AssessmentFactoryLiteFormalProposalPDFExportService",
    }


def test_assessment_factory_lite_formal_proposal_pdf_export_includes_boundary_notice():
    result = service().export_pdf()

    boundary = result["boundary_notice"]

    assert boundary["non_binding"] is True
    assert boundary["operator_review_required"] is True
    assert boundary["not_a_contract"] is True
    assert boundary["not_an_invoice"] is True
    assert boundary["not_a_compliance_certification"] is True
    assert boundary["not_production_onboarding"] is True
    assert "does not create a binding quote" in boundary["message"]
    assert "GAGF Kernel remains the authoritative decision" in (
        boundary["constitutional_rule"]
    )


def test_assessment_factory_lite_formal_proposal_pdf_export_blocks_failed_readiness():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().export_pdf(export=export)

    assert result["status"] == "blocked"
    assert result["export_stage"] == "formal_proposal_pdf_export_blocked"
    assert result["readiness"]["ready_for_pdf"] is False
    assert result["readiness"]["failed_checks"] == 1
    assert result["readiness"]["readiness_score"] == 0.89
    assert result["blocking_issues"] == ["commercial_terms_present"]
    assert result["recommended_action"] == (
        "resolve_formal_proposal_pdf_readiness_gaps"
    )
    assert "blocked because readiness checks failed" in result["operator_message"]


def test_assessment_factory_lite_formal_proposal_pdf_export_accepts_custom_context():
    result = service().export_pdf(
        buyer_context={
            "primary_buyer": "founder_operator",
            "workflow_area": "security review workflow",
            "duration": "5_to_7_business_days",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    assert result["status"] == "ok"
    assert result["filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.pdf"
    )
    assert result["source_markdown_filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.md"
    )
    assert result["readiness"]["ready_for_pdf"] is True
    assert result["readiness"]["readiness_score"] == 1.0
