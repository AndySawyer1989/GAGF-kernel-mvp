from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_buyer_delivery_package_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["delivery_type"] == "assessment_factory_lite_buyer_delivery_package"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["delivery_stage"] == "buyer_delivery_package"
    assert payload["delivery_status"] == "review_ready"
    assert payload["recommended_action"] == "review_buyer_delivery_package"


def test_assessment_factory_lite_buyer_delivery_package_endpoint_includes_source_export_package():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={},
    )

    payload = response.json()

    assert payload["source_export_package"] == {
        "package_type": "assessment_factory_lite_proposal_export_package",
        "package_stage": "proposal_export_package",
        "package_status": "ready",
        "release": "assessment-factory-lite-proposal-package",
        "version": "2.0.0",
        "recommended_action": "review_proposal_export_package",
    }


def test_assessment_factory_lite_buyer_delivery_package_endpoint_includes_buyer_facing_deliverables():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={},
    )

    payload = response.json()
    deliverables = {
        item["deliverable"]: item for item in payload["buyer_facing_deliverables"]
    }

    assert set(deliverables) == {
        "proposal_markdown_export",
        "proposal_pdf_export_object",
        "proposal_export_manifest",
    }

    assert deliverables["proposal_markdown_export"]["format"] == "markdown"
    assert deliverables["proposal_markdown_export"]["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
    )
    assert deliverables["proposal_markdown_export"]["ready"] is True
    assert deliverables["proposal_markdown_export"]["buyer_facing"] is False

    assert deliverables["proposal_pdf_export_object"]["format"] == "pdf"
    assert deliverables["proposal_pdf_export_object"]["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )
    assert deliverables["proposal_pdf_export_object"]["ready"] is True
    assert deliverables["proposal_pdf_export_object"]["buyer_facing"] is False

    assert deliverables["proposal_export_manifest"]["format"] == "json"
    assert deliverables["proposal_export_manifest"]["ready"] is True
    assert deliverables["proposal_export_manifest"]["buyer_facing"] is False


def test_assessment_factory_lite_buyer_delivery_package_endpoint_includes_operator_approval_and_checklist():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={},
    )

    payload = response.json()

    assert payload["operator_approval"] == {
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

    checks = {item["check"]: item for item in payload["delivery_checklist"]}

    assert set(checks) == {
        "export_package_ready",
        "markdown_export_present",
        "pdf_export_object_ready",
        "readiness_passed",
        "scope_approved",
        "evidence_boundary_approved",
        "commercial_terms_approved",
        "buyer_language_approved",
    }

    assert checks["export_package_ready"]["passed"] is True
    assert checks["markdown_export_present"]["passed"] is True
    assert checks["pdf_export_object_ready"]["passed"] is True
    assert checks["readiness_passed"]["passed"] is True
    assert checks["scope_approved"]["passed"] is False
    assert checks["evidence_boundary_approved"]["passed"] is False
    assert checks["commercial_terms_approved"]["passed"] is False
    assert checks["buyer_language_approved"]["passed"] is False


def test_assessment_factory_lite_buyer_delivery_package_endpoint_review_ready_blockers_and_send_readiness():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={},
    )

    payload = response.json()

    assert payload["delivery_blockers"] == [
        "buyer_language_approved",
        "commercial_terms_approved",
        "evidence_boundary_approved",
        "scope_approved",
    ]

    assert payload["send_readiness"] == {
        "send_ready": False,
        "review_ready": True,
        "blocked": False,
        "blocker_count": 4,
        "requires_operator_approval": True,
        "send_rule": (
            "Buyer delivery is allowed only when export package is ready and "
            "scope, evidence boundary, commercial terms, and buyer language "
            "are operator-approved."
        ),
    }


def test_assessment_factory_lite_buyer_delivery_package_endpoint_includes_manifest_and_next_action():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={},
    )

    payload = response.json()

    assert payload["delivery_manifest"] == {
        "delivery_manifest_type": "buyer_delivery_package_manifest",
        "source_package_type": "assessment_factory_lite_proposal_export_package",
        "source_package_status": "ready",
        "delivery_status": "review_ready",
        "markdown_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
        ),
        "pdf_filename": (
            "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
        ),
        "ready_for_pdf": True,
        "readiness_score": 1.0,
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "generated_by": "AssessmentFactoryLiteBuyerDeliveryPackageService",
    }

    assert payload["next_action"] == {
        "action": "complete_operator_delivery_approval",
        "operator_instruction": (
            "Review deliverables, approve scope, evidence boundary, "
            "commercial terms, and buyer-facing language before delivery."
        ),
        "future_action": "prepare_buyer_delivery_message",
    }

    assert payload["operator_message"] == (
        "Assessment Factory Lite buyer delivery package is ready for "
        "operator approval review."
    )


def test_assessment_factory_lite_buyer_delivery_package_endpoint_send_ready_with_full_operator_approval():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={
            "operator_approval": {
                "approval_status": "operator_approved",
                "scope_approved": True,
                "evidence_boundary_approved": True,
                "commercial_terms_approved": True,
                "buyer_language_approved": True,
                "approval_note": "Operator approved package for buyer delivery.",
            }
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["delivery_status"] == "send_ready"
    assert payload["delivery_blockers"] == []
    assert payload["send_readiness"]["send_ready"] is True
    assert payload["send_readiness"]["requires_operator_approval"] is False
    assert payload["next_action"] == {
        "action": "prepare_buyer_delivery_message",
        "operator_instruction": (
            "Prepare the buyer-facing delivery message and verify final "
            "send channel before delivery."
        ),
        "future_action": "generate_buyer_delivery_message",
    }
    assert payload["operator_message"] == (
        "Assessment Factory Lite buyer delivery package is send-ready "
        "after operator approval."
    )


def test_assessment_factory_lite_buyer_delivery_package_endpoint_blocks_failed_export_package_and_preserves_route():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-package",
        json={"export": export},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["delivery_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_buyer_delivery_package_gaps"
    assert "commercial_terms_present" in payload["delivery_blockers"]
    assert "export_package_ready" in payload["delivery_blockers"]
    assert "pdf_export_object_ready" in payload["delivery_blockers"]
    assert "readiness_passed" in payload["delivery_blockers"]
    assert payload["send_readiness"]["blocked"] is True
    assert payload["next_action"] == {
        "action": "resolve_buyer_delivery_package_gaps",
        "operator_instruction": (
            "Resolve export package or readiness gaps before buyer delivery review."
        ),
        "future_action": "rerun_buyer_delivery_package",
    }

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-delivery-package" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.1.0",
        "release": "assessment-factory-lite-proposal-export-package",
        "sprint": "5.0",
        "status": "complete",
    }
