from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["readiness_type"] == (
        "assessment_factory_lite_formal_proposal_pdf_readiness"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-package"
    assert payload["version"] == "2.0.0"
    assert payload["readiness_stage"] == "formal_proposal_pdf_readiness_check"


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_passes_default_export():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={},
    )

    payload = response.json()

    assert payload["passed_checks"] == 9
    assert payload["failed_checks"] == 0
    assert payload["readiness_score"] == 1.0
    assert payload["ready_for_pdf"] is True
    assert payload["blocking_issues"] == []
    assert payload["recommended_action"] == "prepare_formal_proposal_pdf_export"
    assert payload["recommendation"] == (
        "Markdown export is ready for operator-reviewed PDF generation."
    )


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_returns_source_export():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={},
    )

    payload = response.json()

    assert payload["source_export"] == {
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


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_lists_required_sections():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={},
    )

    payload = response.json()

    assert payload["required_sections"] == [
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


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_returns_all_named_checks():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={},
    )

    payload = response.json()
    checks = {check["check"]: check for check in payload["checks"]}

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


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_blocks_missing_boundary_notice():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace("## Boundary Notice", "")

    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={"export": export},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["ready_for_pdf"] is False
    assert payload["failed_checks"] == 2
    assert payload["readiness_score"] == 0.78
    assert "required_sections_present" in payload["blocking_issues"]
    assert "boundary_notice_present" in payload["blocking_issues"]
    assert payload["recommended_action"] == (
        "resolve_formal_proposal_pdf_readiness_gaps"
    )


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_blocks_binding_quote_language():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={"export": export},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["ready_for_pdf"] is False
    assert payload["failed_checks"] == 1
    assert payload["readiness_score"] == 0.89
    assert payload["blocking_issues"] == ["commercial_terms_present"]
    assert payload["recommended_action"] == (
        "resolve_formal_proposal_pdf_readiness_gaps"
    )


def test_assessment_factory_lite_formal_proposal_pdf_readiness_endpoint_accepts_custom_context_and_preserves_release_marker():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={
            "buyer_context": {
                "primary_buyer": "founder_operator",
                "workflow_area": "security review workflow",
                "duration": "5_to_7_business_days",
                "price_low": 1500,
                "price_high": 3500,
            }
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["ready_for_pdf"] is True
    assert payload["readiness_score"] == 1.0
    assert payload["source_export"]["filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.md"
    )

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/proposal/document/pdf-readiness" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }

