from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_buyer_delivery_message_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["message_type"] == "assessment_factory_lite_buyer_delivery_message"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["message_stage"] == "buyer_delivery_message_draft"
    assert payload["message_status"] == "draft_ready"
    assert payload["delivery_channel"] == "email_draft"
    assert payload["recommended_action"] == "review_buyer_delivery_message"


def test_assessment_factory_lite_buyer_delivery_message_endpoint_includes_recipient_sender_and_subject():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={
            "message_context": {
                "recipient_role": "founder_operator",
                "sender_name": "Andy Sawyer",
                "delivery_channel": "email_draft",
            }
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["recipient"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_to_provide",
    }

    assert payload["sender"] == {
        "sender_type": "operator",
        "sender_name": "Andy Sawyer",
        "signature_required": True,
    }

    assert payload["subject"] == (
        "Assessment Factory Lite Proposal Package Ready for Review - "
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )


def test_assessment_factory_lite_buyer_delivery_message_endpoint_body_is_non_binding_and_review_gated():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={"message_context": {"sender_name": "Andy Sawyer"}},
    )

    assert response.status_code == 200

    body = response.json()["message_body"]

    assert "Hello," in body
    assert "Assessment Factory Lite proposal package" in body
    assert "Primary proposal artifact:" in body
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in body
    assert "bounded paid-assessment workflow" in body
    assert "non-binding" in body
    assert "does not create a contract" in body
    assert "requires operator approval before it can be sent" in body
    assert "Thank you,\nAndy Sawyer" in body


def test_assessment_factory_lite_buyer_delivery_message_endpoint_includes_source_and_delivery_summary():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={},
    )

    payload = response.json()

    assert payload["source_delivery_package"] == {
        "delivery_type": "assessment_factory_lite_buyer_delivery_package",
        "delivery_stage": "buyer_delivery_package",
        "delivery_status": "review_ready",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_delivery_package",
    }

    assert payload["delivery_summary"] == {
        "send_ready": False,
        "review_ready": True,
        "blocked": False,
        "blocker_count": 4,
        "delivery_blockers": [
            "buyer_language_approved",
            "commercial_terms_approved",
            "evidence_boundary_approved",
            "scope_approved",
        ],
    }


def test_assessment_factory_lite_buyer_delivery_message_endpoint_includes_attachments():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={},
    )

    payload = response.json()
    attachments = {item["attachment"]: item for item in payload["attachments"]}

    assert set(attachments) == {
        "proposal_markdown_export",
        "proposal_pdf_export_object",
        "proposal_export_manifest",
    }

    assert attachments["proposal_markdown_export"] == {
        "attachment": "proposal_markdown_export",
        "filename": "assessment-factory-lite-proposal-approval-and-handoff-workflow.md",
        "format": "markdown",
        "ready": True,
        "buyer_facing": False,
        "attachment_status": "operator_review_required",
    }

    assert attachments["proposal_pdf_export_object"] == {
        "attachment": "proposal_pdf_export_object",
        "filename": "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf",
        "format": "pdf",
        "ready": True,
        "buyer_facing": False,
        "attachment_status": "operator_review_required",
    }


def test_assessment_factory_lite_buyer_delivery_message_endpoint_includes_operator_review_and_send_policy():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={},
    )

    payload = response.json()

    assert payload["operator_review"] == {
        "approval_status": "operator_review_required",
        "scope_approved": False,
        "evidence_boundary_approved": False,
        "commercial_terms_approved": False,
        "buyer_language_approved": False,
        "delivery_blockers": [
            "buyer_language_approved",
            "commercial_terms_approved",
            "evidence_boundary_approved",
            "scope_approved",
        ],
        "review_required": True,
    }

    assert payload["send_policy"] == {
        "send_allowed": False,
        "send_blocked_reason": (
            "Operator approval and delivery readiness are required before sending."
        ),
        "send_rule": (
            "Buyer delivery is allowed only when export package is ready and "
            "scope, evidence boundary, commercial terms, and buyer language "
            "are operator-approved."
        ),
        "automated_send_allowed": False,
        "requires_human_operator": True,
    }


def test_assessment_factory_lite_buyer_delivery_message_endpoint_send_ready_with_full_operator_approval():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={
            "operator_approval": {
                "approval_status": "operator_approved",
                "scope_approved": True,
                "evidence_boundary_approved": True,
                "commercial_terms_approved": True,
                "buyer_language_approved": True,
                "approval_note": "Operator approved package for buyer delivery.",
            },
            "message_context": {
                "sender_name": "Andy Sawyer",
                "recipient_role": "operations_leader",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "send_ready_draft"
    assert payload["delivery_summary"]["send_ready"] is True
    assert payload["operator_review"]["review_required"] is False
    assert payload["send_policy"]["send_allowed"] is True
    assert payload["send_policy"]["send_blocked_reason"] == ""
    assert "Please review the proposal package" in payload["message_body"]
    assert payload["next_action"] == {
        "action": "review_and_send_buyer_delivery_message",
        "operator_instruction": (
            "Review the buyer delivery message, verify recipient details, "
            "confirm approved attachments, and send only through an approved "
            "human-operated channel."
        ),
        "future_action": "record_buyer_delivery_event",
    }


def test_assessment_factory_lite_buyer_delivery_message_endpoint_blocks_failed_delivery_package_and_preserves_route():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-message",
        json={"export": export},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_buyer_delivery_message_gaps"
    assert payload["delivery_summary"]["blocked"] is True
    assert "commercial_terms_present" in payload["delivery_summary"]["delivery_blockers"]
    assert payload["send_policy"]["send_allowed"] is False
    assert payload["next_action"] == {
        "action": "resolve_buyer_delivery_message_gaps",
        "operator_instruction": (
            "Resolve delivery package blockers before preparing a buyer-facing "
            "message."
        ),
        "future_action": "rerun_buyer_delivery_message",
    }

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-delivery-message" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.1.0",
        "release": "assessment-factory-lite-proposal-export-package",
        "sprint": "5.0",
        "status": "complete",
    }