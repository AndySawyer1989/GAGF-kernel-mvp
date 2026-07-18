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
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
}


FOLLOW_UP_EVENT_CONTEXT = {
    "event_id": "buyer-follow-up-event-001",
    "recorded_at": "2026-07-21T12:00:00+00:00",
    "human_operator_confirmed": True,
    "follow_up_completed": True,
}


INTERESTED_CONTEXT = {
    "buyer_response_status": "interested",
    "response_received_at": "2026-07-18T09:00:00+00:00",
    "response_summary": "Buyer wants to schedule a scope call.",
    "buyer_questions": ["Can we start next week?"],
}


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_builds_contract():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_context": {
                "package_id": "assessment-scope-call-package-001",
                "created_at": "2026-07-21T12:30:00+00:00",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["message_type"] == "assessment_factory_lite_scope_call_agenda_message"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["message_stage"] == "scope_call_agenda_message_draft"
    assert payload["message_status"] == "draft_ready"
    assert payload["delivery_channel"] == "email_draft"
    assert payload["recommended_action"] == "review_scope_call_agenda_message"


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_accepts_custom_message_context():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_context": {
                "recipient_role": "founder_operator",
                "sender_name": "Andy Sawyer",
                "subject": "Scope Call Agenda for Assessment Factory Lite",
                "email_status": "operator_confirmed",
                "delivery_channel": "manual_email",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["delivery_channel"] == "manual_email"

    assert payload["recipient"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
    }

    assert payload["sender"] == {
        "sender_type": "operator",
        "sender_name": "Andy Sawyer",
        "signature_required": True,
    }

    assert payload["subject"] == "Scope Call Agenda for Assessment Factory Lite"
    assert "Thank you,\nAndy Sawyer" in payload["message_body"]


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_includes_source_package_and_agenda_summary():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_context": {
                "package_id": "assessment-scope-call-package-001",
                "created_at": "2026-07-21T12:30:00+00:00",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_scope_call_package"] == {
        "package_type": "assessment_factory_lite_assessment_scope_call_package",
        "package_stage": "assessment_scope_call_package",
        "package_status": "ready",
        "package_id": "assessment-scope-call-package-001",
        "created_at": "2026-07-21T12:30:00+00:00",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "version": "2.2.0",
        "recommended_action": "review_assessment_scope_call_package",
    }

    assert payload["agenda_summary"] == {
        "agenda_item_count": 6,
        "agenda_items": [
            "confirm workflow scope",
            "confirm evidence sources",
            "confirm evidence boundaries",
            "confirm timeline and deliverables",
            "confirm commercial terms",
            "confirm next approval step",
        ],
        "all_items_required": True,
        "agenda_owner": "operator",
    }


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_includes_message_body_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    body = response.json()["message_body"]

    assert "Thank you for your interest in Assessment Factory Lite." in body
    assert "- confirm workflow scope" in body
    assert "- confirm evidence sources" in body
    assert "- confirm evidence boundaries" in body
    assert "- confirm timeline and deliverables" in body
    assert "- confirm commercial terms" in body
    assert "- confirm next approval step" in body
    assert "please do not share regulated production data" in body
    assert "secrets, credentials, unapproved personal data" in body
    assert "scope-call agenda is non-binding" in body
    assert "does not create a contract, invoice, payment request, calendar invite" in body
    assert "I will only schedule the call after human operator review and buyer confirmation." in body
    assert "Current commercial next action: schedule_assessment_scope_call." in body


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_includes_review_and_send_policy():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["operator_review"] == {
        "package_status": "ready",
        "package_blockers": [],
        "review_required": True,
        "human_operator_required": True,
        "approved_for_sending": False,
        "approved_for_scheduling": False,
        "message_ready": True,
    }

    assert payload["send_policy"] == {
        "send_allowed": False,
        "send_blocked_reason": (
            "Human operator review and buyer confirmation are required before "
            "scope-call agenda sending or scheduling."
        ),
        "automated_send_allowed": False,
        "calendar_invite_allowed": False,
        "automatic_scheduling_allowed": False,
        "requires_human_operator": True,
        "send_rule": (
            "Scope-call agenda messages are draft-only and must be reviewed, "
            "approved, and sent by a human operator."
        ),
    }


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_blocks_unready_scope_call_package():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "buyer_response_status": "questions",
                "response_summary": "Buyer has questions before scheduling.",
            },
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_scope_call_agenda_message_gaps"
    assert payload["operator_review"]["message_ready"] is False
    assert "scope_call_action_supported" in payload["operator_review"]["package_blockers"]
    assert payload["send_policy"]["send_blocked_reason"] == (
        "Scope-call package must be ready before agenda message drafting can proceed."
    )
    assert payload["next_action"] == {
        "action": "resolve_scope_call_agenda_message_gaps",
        "operator_instruction": (
            "Resolve scope-call package readiness gaps before preparing a "
            "buyer-facing agenda message."
        ),
        "future_action": "rerun_scope_call_agenda_message",
    }


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "export": export,
            "event_context": {
                "event_id": "buyer-delivery-event-003",
                "recorded_at": "2026-07-17T12:10:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-004",
                "recorded_at": "2026-07-21T12:15:00+00:00",
                "human_operator_confirmed": True,
                "follow_up_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_status"] == "blocked"
    assert payload["source_scope_call_package"]["package_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_scope_call_agenda_message_gaps"
    assert payload["audit_notes"] == [
        "scope_call_agenda_message_blocked",
        "automated_scope_call_sending_not_performed",
        "automatic_scheduling_not_performed",
    ]


def test_assessment_factory_lite_scope_call_agenda_message_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/scope-call-agenda-message" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }