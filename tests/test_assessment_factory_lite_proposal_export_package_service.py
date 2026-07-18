from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_proposal_export_package_service import (
    AssessmentFactoryLiteProposalExportPackageService,
)


def service():
    return AssessmentFactoryLiteProposalExportPackageService()


def test_assessment_factory_lite_proposal_export_package_builds_contract():
    result = service().build_package()

    assert result["status"] == "ok"
    assert result["package_type"] == "assessment_factory_lite_proposal_export_package"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-package"
    assert result["version"] == "2.0.0"
    assert result["package_stage"] == "proposal_export_package"
    assert result["package_status"] == "ready"
    assert result["recommended_action"] == "review_proposal_export_package"


def test_assessment_factory_lite_proposal_export_package_includes_markdown_summary():
    result = service().build_package()

    assert result["markdown_export"] == {
        "export_type": "assessment_factory_lite_formal_proposal_markdown_export",
        "export_stage": "formal_proposal_markdown_export",
        "format": "markdown",
        "filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
        ),
        "release": "assessment-factory-lite-proposal-package",
        "version": "2.0.0",
        "recommended_action": "review_formal_proposal_markdown_export",
        "section_count": 14,
        "markdown_present": True,
    }


def test_assessment_factory_lite_proposal_export_package_includes_pdf_readiness_summary():
    result = service().build_package()

    assert result["pdf_readiness"] == {
        "readiness_type": "assessment_factory_lite_formal_proposal_pdf_readiness",
        "readiness_stage": "formal_proposal_pdf_readiness_check",
        "passed_checks": 9,
        "failed_checks": 0,
        "readiness_score": 1.0,
        "ready_for_pdf": True,
        "blocking_issues": [],
        "recommended_action": "prepare_formal_proposal_pdf_export",
    }


def test_assessment_factory_lite_proposal_export_package_includes_pdf_export_summary():
    result = service().build_package()

    assert result["pdf_export"] == {
        "status": "ok",
        "export_type": "assessment_factory_lite_formal_proposal_pdf_export",
        "export_stage": "formal_proposal_pdf_export",
        "format": "pdf",
        "content_type": "application/pdf",
        "filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
        ),
        "source_markdown_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
        ),
        "recommended_action": "review_formal_proposal_pdf_export",
    }


def test_assessment_factory_lite_proposal_export_package_includes_manifest():
    result = service().build_package()

    assert result["export_manifest"] == {
        "package_manifest_type": "proposal_export_package_manifest",
        "markdown_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
        ),
        "pdf_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
        ),
        "markdown_export_type": (
            "assessment_factory_lite_formal_proposal_markdown_export"
        ),
        "pdf_export_type": "assessment_factory_lite_formal_proposal_pdf_export",
        "pdf_export_status": "ok",
        "readiness_score": 1.0,
        "ready_for_pdf": True,
        "release": "assessment-factory-lite-proposal-package",
        "version": "2.0.0",
        "generated_by": "AssessmentFactoryLiteProposalExportPackageService",
    }


def test_assessment_factory_lite_proposal_export_package_includes_approval_gate_and_boundaries():
    result = service().build_package()

    assert result["operator_approval"] == {
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

    notices = {item["notice"]: item for item in result["boundary_notices"]}

    assert set(notices) == {
        "commercial_boundary",
        "evidence_boundary",
        "pdf_boundary",
        "constitutional_boundary",
    }
    assert all(item["required"] is True for item in notices.values())
    assert "non-binding" in notices["commercial_boundary"]["message"]
    assert "safe, non-sensitive evidence" in notices["evidence_boundary"]["message"]
    assert "does not create a binding quote" in notices["pdf_boundary"]["message"]
    assert "GAGF Kernel remains the authoritative decision" in (
        notices["constitutional_boundary"]["message"]
    )


def test_assessment_factory_lite_proposal_export_package_includes_contents_and_next_action():
    result = service().build_package()

    assert result["package_contents"] == [
        "formal_proposal_markdown_export",
        "formal_proposal_pdf_readiness",
        "formal_proposal_pdf_export_object",
        "operator_approval_gate",
        "export_manifest",
        "boundary_notices",
        "blocking_issues",
        "next_action",
    ]

    assert result["blocking_issues"] == []
    assert result["next_action"] == {
        "action": "review_and_prepare_buyer_delivery_package",
        "operator_instruction": (
            "Review Markdown export, PDF export object, approval gate, "
            "manifest, and boundary notices before preparing buyer delivery."
        ),
        "future_action": "prepare_buyer_delivery_package",
    }
    assert result["operator_message"] == (
        "Assessment Factory Lite proposal export package is ready for "
        "operator review."
    )


def test_assessment_factory_lite_proposal_export_package_blocks_failed_readiness():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().build_package(export=export)

    assert result["package_status"] == "blocked"
    assert result["recommended_action"] == "resolve_proposal_export_package_gaps"
    assert result["blocking_issues"] == ["commercial_terms_present"]
    assert result["pdf_readiness"]["ready_for_pdf"] is False
    assert result["pdf_readiness"]["failed_checks"] == 1
    assert result["pdf_export"]["status"] == "blocked"
    assert result["pdf_export"]["export_stage"] == "formal_proposal_pdf_export_blocked"
    assert result["next_action"] == {
        "action": "resolve_export_package_gaps",
        "operator_instruction": (
            "Resolve readiness or boundary gaps before preparing buyer delivery."
        ),
        "future_action": "rerun_proposal_export_package",
    }
