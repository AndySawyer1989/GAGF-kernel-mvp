from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
    "approval_note": "Operator approved package for buyer delivery.",
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
    "delivery_channel": "email_draft",
    "channel_status": "operator_recorded",
    "send_reference": "manual-send-log-001",
    "email_status": "operator_confirmed",
    "recipient_confirmed": True,
    "delivery_result": "delivered",
    "outcome_note": "Human operator sent the approved buyer delivery message.",
    "audit_notes": ["operator_review_completed"],
}


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "tracker_id": "buyer-follow-up-tracker-001",
                "created_at": "2026-07-17T12:15:00+00:00",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["message_type"] == "assessment_factory_lite_buyer_follow_up_message"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["message_stage"] == "buyer_follow_up_message_draft"
    assert payload["message_status"] == "draft_ready"
    assert payload["delivery_channel"] == "email_draft"
    assert payload["recommended_action"] == "review_buyer_follow_up_message"


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_includes_recipient_sender_and_subject():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_message_context": {
                "recipient_role": "founder_operator",
                "sender_name": "Andy Sawyer",
                "delivery_channel": "email_draft",
            },
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
        "Following Up on the Assessment Factory Lite Proposal Package"
    )


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_body_for_no_response():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {"created_at": "2026-07-17T12:15:00+00:00"},
            "follow_up_message_context": {"sender_name": "Andy Sawyer"},
        },
    )

    assert response.status_code == 200

    body = response.json()["message_body"]

    assert "Hello," in body
    assert "follow up on the Assessment Factory Lite proposal package" in body
    assert "tracked due date of 2026-07-20T12:15:00+00:00" in body
    assert "bounded assessment scope and next steps" in body
    assert "non-binding" in body
    assert "does not create a contract" in body
    assert "Current commercial next action: send_follow_up_if_no_response." in body
    assert "Thank you,\nAndy Sawyer" in body


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_includes_source_tracker_and_summary():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "tracker_id": "buyer-follow-up-tracker-001",
                "created_at": "2026-07-17T12:15:00+00:00",
            },
        },
    )

    payload = response.json()

    assert payload["source_follow_up_tracker"] == {
        "tracker_type": "assessment_factory_lite_buyer_follow_up_tracker",
        "tracker_stage": "buyer_follow_up_tracker",
        "tracker_status": "active",
        "tracker_id": "buyer-follow-up-tracker-001",
        "created_at": "2026-07-17T12:15:00+00:00",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_follow_up_tracker",
    }

    assert payload["buyer_response_summary"] == {
        "response_status": "no_response",
        "response_received": False,
        "response_received_at": "",
        "response_summary": "",
        "buyer_questions": [],
        "buyer_objections": [],
    }

    assert payload["commercial_next_action"]["action"] == "send_follow_up_if_no_response"


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_includes_operator_review_and_send_policy():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["operator_review"] == {
        "tracker_status": "active",
        "follow_up_blockers": [],
        "review_required": True,
        "human_operator_required": True,
        "approved_for_sending": False,
    }

    assert payload["send_policy"] == {
        "send_allowed": False,
        "send_blocked_reason": (
            "Human operator review and approval are required before follow-up sending."
        ),
        "automated_send_allowed": False,
        "requires_human_operator": True,
        "send_rule": (
            "Buyer follow-up messages are draft-only and must be reviewed, "
            "approved, and sent by a human operator."
        ),
    }


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_response_reply_for_interested_buyer():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "buyer_response_status": "interested",
                "response_received_at": "2026-07-18T09:00:00+00:00",
                "response_summary": "Buyer wants to schedule a scope call.",
                "buyer_questions": ["Can we start next week?"],
            },
            "follow_up_message_context": {"sender_name": "Andy Sawyer"},
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "response_reply_draft_ready"
    assert payload["subject"] == "Next Step: Assessment Factory Lite Scope Call"
    assert "Thank you for your interest" in payload["message_body"]
    assert "schedule a bounded assessment scope call" in payload["message_body"]
    assert "Current commercial next action: schedule_assessment_scope_call." in payload[
        "message_body"
    ]
    assert payload["next_action"] == {
        "action": "review_buyer_response_reply",
        "operator_instruction": (
            "Review the response-based follow-up draft, verify buyer response "
            "context, and send only through a human-operated channel."
        ),
        "future_action": "record_buyer_follow_up_event",
    }


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_response_reply_for_questions():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "buyer_response_status": "questions",
                "response_summary": "Buyer has questions before approving next step.",
                "buyer_questions": ["Can you clarify evidence sources?"],
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "response_reply_draft_ready"
    assert payload["subject"] == "Re: Assessment Factory Lite Proposal Questions"
    assert "I received your questions" in payload["message_body"]
    assert "preserving the approved commercial, evidence, and scope boundaries" in payload[
        "message_body"
    ]
    assert payload["commercial_next_action"]["action"] == "answer_buyer_questions"


def test_assessment_factory_lite_buyer_follow_up_message_endpoint_blocks_invalid_tracker_and_preserves_route():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
        json={
            "export": export,
            "event_context": {
                "event_id": "buyer-delivery-event-003",
                "recorded_at": "2026-07-17T12:10:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_buyer_follow_up_message_gaps"
    assert payload["source_follow_up_tracker"]["tracker_status"] == "blocked"
    assert payload["send_policy"]["send_allowed"] is False
    assert payload["send_policy"]["send_blocked_reason"] == (
        "Follow-up tracker must be active or response-received before drafting can proceed."
    )
    assert payload["next_action"] == {
        "action": "resolve_buyer_follow_up_message_gaps",
        "operator_instruction": (
            "Resolve follow-up tracker gaps before preparing a buyer follow-up "
            "message draft."
        ),
        "future_action": "rerun_buyer_follow_up_message",
    }

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-follow-up-message" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }



