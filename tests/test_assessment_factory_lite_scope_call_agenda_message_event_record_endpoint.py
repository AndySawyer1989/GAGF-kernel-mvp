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


AGENDA_EVENT_CONTEXT = {
    "event_id": "scope-call-agenda-message-event-001",
    "recorded_at": "2026-07-22T12:00:00+00:00",
    "human_operator_confirmed": True,
    "agenda_message_sent": True,
    "recipient_confirmed": True,
    "email_status": "operator_confirmed",
    "delivery_channel": "manual_email",
}


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_builds_contract():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_scope_call_agenda_message_event_record"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["event_stage"] == "scope_call_agenda_message_event_record"
    assert payload["event_status"] == "recorded"
    assert payload["event_id"] == "scope-call-agenda-message-event-001"
    assert payload["recorded_at"] == "2026-07-22T12:00:00+00:00"
    assert payload["recommended_action"] == "prepare_scope_call_event_record"


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_includes_source_message_summary():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_context": {
                "subject": "Scope Call Agenda for Assessment Factory Lite",
                "delivery_channel": "manual_email",
            },
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_scope_call_agenda_message"] == {
        "message_type": "assessment_factory_lite_scope_call_agenda_message",
        "message_stage": "scope_call_agenda_message_draft",
        "message_status": "draft_ready",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "delivery_channel": "manual_email",
        "subject": "Scope Call Agenda for Assessment Factory Lite",
        "recommended_action": "review_scope_call_agenda_message",
    }

    assert payload["message_summary"]["subject"] == "Scope Call Agenda for Assessment Factory Lite"
    assert payload["message_summary"]["body_available"] is True
    assert payload["message_summary"]["agenda_item_count"] == 6
    assert payload["message_summary"]["non_binding_notice_included"] is True
    assert payload["message_summary"]["no_calendar_invite_notice_included"] is True
    assert payload["message_summary"]["human_operator_notice_included"] is True


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_includes_channel_and_recipient_status():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_context": {
                "recipient_role": "founder_operator",
                "delivery_channel": "manual_email",
            },
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_channel"] == {
        "delivery_channel": "manual_email",
        "automated_send_used": False,
        "calendar_invite_created": False,
        "automatic_scheduling_used": False,
        "human_operated": True,
    }

    assert payload["recipient_status"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
        "recipient_confirmed": True,
    }


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_includes_policy_snapshots_and_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["send_policy_snapshot"]["send_allowed"] is False
    assert payload["send_policy_snapshot"]["automated_send_allowed"] is False
    assert payload["send_policy_snapshot"]["calendar_invite_allowed"] is False
    assert payload["send_policy_snapshot"]["automatic_scheduling_allowed"] is False
    assert payload["send_policy_snapshot"]["requires_human_operator"] is True

    assert payload["operator_review_snapshot"]["review_required"] is True
    assert payload["operator_review_snapshot"]["human_operator_required"] is True
    assert payload["operator_review_snapshot"]["approved_for_sending"] is False
    assert payload["operator_review_snapshot"]["approved_for_scheduling"] is False

    assert payload["scope_call_package_summary"]["package_status"] == "ready"
    assert payload["agenda_summary"]["agenda_item_count"] == 6


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_includes_checklist_and_no_blockers_when_recorded():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_checklist"] == {
        "message_draft_ready": True,
        "human_operator_confirmed": True,
        "agenda_message_sent": True,
        "recipient_confirmed": True,
        "automated_send_not_used": True,
        "calendar_invite_not_created": True,
        "automatic_scheduling_not_used": True,
    }

    assert payload["event_blockers"] == []


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_handles_pending_states():
    pending_human = dict(AGENDA_EVENT_CONTEXT)
    pending_human["human_operator_confirmed"] = False

    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": pending_human,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_human_confirmation"
    assert "human_operator_confirmed" in payload["event_blockers"]
    assert payload["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"

    pending_completion = dict(AGENDA_EVENT_CONTEXT)
    pending_completion["agenda_message_sent"] = False

    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": pending_completion,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_agenda_message_completion"
    assert "agenda_message_sent" in payload["event_blockers"]
    assert payload["next_action"] == {
        "action": "complete_scope_call_agenda_message_action",
        "operator_instruction": (
            "Complete or confirm the agenda message action before recording "
            "the event as complete."
        ),
        "future_action": "rerun_scope_call_agenda_message_event_record",
    }


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_blocks_unready_message():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "buyer_response_status": "questions",
                "response_summary": "Buyer has questions before scheduling.",
            },
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "blocked"
    assert payload["source_scope_call_agenda_message"]["message_status"] == "blocked"
    assert "message_draft_ready" in payload["event_blockers"]
    assert payload["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/scope-call-agenda-message-event-record" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_scope_call_agenda_message_event_record_endpoint_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message-event-record",
        json={
            "export": export,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "blocked"
    assert payload["source_scope_call_agenda_message"]["message_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"