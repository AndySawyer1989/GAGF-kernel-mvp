from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_pdf_readiness_service import (
    AssessmentFactoryLiteFormalProposalPDFReadinessService,
)


def service():
    return AssessmentFactoryLiteFormalProposalPDFReadinessService()


def test_assessment_factory_lite_formal_proposal_pdf_readiness_builds_contract():
    result = service().check_readiness()

    assert result["status"] == "ok"
    assert result["readiness_type"] == (
        "assessment_factory_lite_formal_proposal_pdf_readiness"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-package"
    assert result["version"] == "2.0.0"
    assert result["readiness_stage"] == "formal_proposal_pdf_readiness_check"


def test_assessment_factory_lite_formal_proposal_pdf_readiness_passes_default_export():
    result = service().check_readiness()

    assert result["passed_checks"] == 9
    assert result["failed_checks"] == 0
    assert result["readiness_score"] == 1.0
    assert result["ready_for_pdf"] is True
    assert result["blocking_issues"] == []
    assert result["recommended_action"] == "prepare_formal_proposal_pdf_export"
    assert result["recommendation"] == (
        "Markdown export is ready for operator-reviewed PDF generation."
    )


def test_assessment_factory_lite_formal_proposal_pdf_readiness_returns_source_export():
    result = service().check_readiness()

    assert result["source_export"] == {
        "export_type": "assessment_factory_lite_formal_proposal_markdown_export",
        "export_stage": "formal_proposal_markdown_export",
        "format": "markdown",
        "filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
        ),
        "release": "assessment-factory-lite-proposal-package",
        "version": "2.0.0",
        "recommended_action": "review_formal_proposal_markdown_export",
    }


def test_assessment_factory_lite_formal_proposal_pdf_readiness_lists_required_sections():
    result = service().check_readiness()

    assert result["required_sections"] == [
        "proposal_metadata",
        "buyer_summary",
        "problem_statement",
        "assessment_scope",
        "evidence_boundary",
        "deliverables",
        "timeline",
        "commercial_terms",
        "assumptions",
        "approval_requirements",
        "exclusions",
        "operator_notes",
        "next_action",
        "boundary_notice",
    ]


def test_assessment_factory_lite_formal_proposal_pdf_readiness_returns_all_named_checks():
    result = service().check_readiness()
    checks = {check["check"]: check for check in result["checks"]}

    assert set(checks) == {
        "export_contract_present",
        "export_format_is_markdown",
        "filename_present",
        "required_sections_present",
        "commercial_terms_present",
        "evidence_boundary_present",
        "approval_requirements_present",
        "operator_notes_present",
        "boundary_notice_present",
    }

    assert all(check["passed"] is True for check in checks.values())


def test_assessment_factory_lite_formal_proposal_pdf_readiness_blocks_missing_boundary_notice():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace("## Boundary Notice", "")

    result = service().check_readiness(export=export)

    assert result["ready_for_pdf"] is False
    assert result["failed_checks"] == 2
    assert result["readiness_score"] == 0.78
    assert "required_sections_present" in result["blocking_issues"]
    assert "boundary_notice_present" in result["blocking_issues"]
    assert result["recommended_action"] == (
        "resolve_formal_proposal_pdf_readiness_gaps"
    )


def test_assessment_factory_lite_formal_proposal_pdf_readiness_blocks_binding_quote_language():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().check_readiness(export=export)

    assert result["ready_for_pdf"] is False
    assert result["failed_checks"] == 1
    assert result["readiness_score"] == 0.89
    assert result["blocking_issues"] == ["commercial_terms_present"]
    assert result["recommended_action"] == (
        "resolve_formal_proposal_pdf_readiness_gaps"
    )


def test_assessment_factory_lite_formal_proposal_pdf_readiness_accepts_custom_context():
    result = service().check_readiness(
        buyer_context={
            "primary_buyer": "founder_operator",
            "workflow_area": "security review workflow",
            "duration": "5_to_7_business_days",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    assert result["ready_for_pdf"] is True
    assert result["readiness_score"] == 1.0
    assert result["source_export"]["filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.md"
    )