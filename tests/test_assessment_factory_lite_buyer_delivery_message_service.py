from backend.app.gagf.assessment_factory_lite_buyer_delivery_message_service import (
    AssessmentFactoryLiteBuyerDeliveryMessageService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


def service():
    return AssessmentFactoryLiteBuyerDeliveryMessageService()


def test_assessment_factory_lite_buyer_delivery_message_builds_contract():
    result = service().build_message()

    assert result["status"] == "ok"
    assert result["message_type"] == "assessment_factory_lite_buyer_delivery_message"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-export-package"
    assert result["version"] == "2.1.0"
    assert result["message_stage"] == "buyer_delivery_message_draft"
    assert result["message_status"] == "draft_ready"
    assert result["delivery_channel"] == "email_draft"
    assert result["recommended_action"] == "review_buyer_delivery_message"


def test_assessment_factory_lite_buyer_delivery_message_includes_recipient_sender_and_subject():
    result = service().build_message(
        message_context={
            "recipient_role": "founder_operator",
            "sender_name": "Andy Sawyer",
            "delivery_channel": "email_draft",
        }
    )

    assert result["recipient"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_to_provide",
    }

    assert result["sender"] == {
        "sender_type": "operator",
        "sender_name": "Andy Sawyer",
        "signature_required": True,
    }

    assert result["subject"] == (
        "Assessment Factory Lite Proposal Package Ready for Review - "
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )


def test_assessment_factory_lite_buyer_delivery_message_body_is_non_binding_and_review_gated():
    result = service().build_message(
        message_context={"sender_name": "Andy Sawyer"}
    )

    body = result["message_body"]

    assert "Hello," in body
    assert "Assessment Factory Lite proposal package" in body
    assert "Primary proposal artifact:" in body
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in body
    assert "bounded paid-assessment workflow" in body
    assert "non-binding" in body
    assert "does not create a contract" in body
    assert "requires operator approval before it can be sent" in body
    assert "Thank you,\nAndy Sawyer" in body


def test_assessment_factory_lite_buyer_delivery_message_includes_source_and_delivery_summary():
    result = service().build_message()

    assert result["source_delivery_package"] == {
        "delivery_type": "assessment_factory_lite_buyer_delivery_package",
        "delivery_stage": "buyer_delivery_package",
        "delivery_status": "review_ready",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_delivery_package",
    }

    assert result["delivery_summary"] == {
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


def test_assessment_factory_lite_buyer_delivery_message_includes_attachments():
    result = service().build_message()

    attachments = {item["attachment"]: item for item in result["attachments"]}

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


def test_assessment_factory_lite_buyer_delivery_message_includes_operator_review_and_send_policy():
    result = service().build_message()

    assert result["operator_review"] == {
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

    assert result["send_policy"] == {
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


def test_assessment_factory_lite_buyer_delivery_message_send_ready_with_full_operator_approval():
    result = service().build_message(
        operator_approval={
            "approval_status": "operator_approved",
            "scope_approved": True,
            "evidence_boundary_approved": True,
            "commercial_terms_approved": True,
            "buyer_language_approved": True,
            "approval_note": "Operator approved package for buyer delivery.",
        },
        message_context={
            "sender_name": "Andy Sawyer",
            "recipient_role": "operations_leader",
        },
    )

    assert result["message_status"] == "send_ready_draft"
    assert result["delivery_summary"]["send_ready"] is True
    assert result["operator_review"]["review_required"] is False
    assert result["send_policy"]["send_allowed"] is True
    assert result["send_policy"]["send_blocked_reason"] == ""
    assert "Please review the proposal package" in result["message_body"]
    assert result["next_action"] == {
        "action": "review_and_send_buyer_delivery_message",
        "operator_instruction": (
            "Review the buyer delivery message, verify recipient details, "
            "confirm approved attachments, and send only through an approved "
            "human-operated channel."
        ),
        "future_action": "record_buyer_delivery_event",
    }


def test_assessment_factory_lite_buyer_delivery_message_blocks_failed_delivery_package():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().build_message(export=export)

    assert result["message_status"] == "blocked"
    assert result["recommended_action"] == "resolve_buyer_delivery_message_gaps"
    assert result["delivery_summary"]["blocked"] is True
    assert "commercial_terms_present" in result["delivery_summary"]["delivery_blockers"]
    assert result["send_policy"]["send_allowed"] is False
    assert result["next_action"] == {
        "action": "resolve_buyer_delivery_message_gaps",
        "operator_instruction": (
            "Resolve delivery package blockers before preparing a buyer-facing "
            "message."
        ),
        "future_action": "rerun_buyer_delivery_message",
    }

