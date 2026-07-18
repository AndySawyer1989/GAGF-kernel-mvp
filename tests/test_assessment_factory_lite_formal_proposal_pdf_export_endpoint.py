from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["export_type"] == (
        "assessment_factory_lite_formal_proposal_pdf_export"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-package"
    assert payload["version"] == "2.0.0"
    assert payload["export_stage"] == "formal_proposal_pdf_export"
    assert payload["format"] == "pdf"
    assert payload["content_type"] == "application/pdf"
    assert payload["recommended_action"] == "review_formal_proposal_pdf_export"


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_uses_pdf_filename():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    payload = response.json()

    assert payload["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )
    assert payload["source_markdown_filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
    )


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_includes_readiness_summary():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    payload = response.json()

    assert payload["readiness"] == {
        "readiness_type": "assessment_factory_lite_formal_proposal_pdf_readiness",
        "readiness_stage": "formal_proposal_pdf_readiness_check",
        "passed_checks": 9,
        "failed_checks": 0,
        "readiness_score": 1.0,
        "ready_for_pdf": True,
        "blocking_issues": [],
        "recommended_action": "prepare_formal_proposal_pdf_export",
    }


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_includes_default_operator_approval_gate():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    payload = response.json()
    approval = payload["operator_approval"]

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


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_includes_pdf_document_model():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    payload = response.json()
    pdf_document = payload["pdf_document"]

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


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_includes_export_manifest():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    payload = response.json()

    assert payload["export_manifest"] == {
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


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_includes_boundary_notice():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    payload = response.json()
    boundary = payload["boundary_notice"]

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


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_blocks_failed_readiness():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={"export": export},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "blocked"
    assert payload["export_stage"] == "formal_proposal_pdf_export_blocked"
    assert payload["readiness"]["ready_for_pdf"] is False
    assert payload["readiness"]["failed_checks"] == 1
    assert payload["readiness"]["readiness_score"] == 0.89
    assert payload["blocking_issues"] == ["commercial_terms_present"]
    assert payload["recommended_action"] == (
        "resolve_formal_proposal_pdf_readiness_gaps"
    )
    assert "blocked because readiness checks failed" in payload["operator_message"]


def test_assessment_factory_lite_formal_proposal_pdf_export_endpoint_accepts_custom_context_and_preserves_release_marker():
    response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
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

    assert payload["status"] == "ok"
    assert payload["filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.pdf"
    )
    assert payload["source_markdown_filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.md"
    )
    assert payload["readiness"]["ready_for_pdf"] is True
    assert payload["readiness"]["readiness_score"] == 1.0

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/proposal/document/pdf" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


