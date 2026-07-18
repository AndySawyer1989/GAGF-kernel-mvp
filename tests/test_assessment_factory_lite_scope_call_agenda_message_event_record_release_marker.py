from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_scope_call_agenda_message_event_record_service import (
    AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService,
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


def test_assessment_factory_lite_scope_call_agenda_message_event_record_release_marker_preserves_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_scope_call_agenda_message_event_record_release_marker_preserves_endpoint_route():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/scope-call-agenda-message-event-record" in actual_routes


def test_assessment_factory_lite_scope_call_agenda_message_event_record_release_marker_matches_service_contract():
    result = AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["event_type"] == "assessment_factory_lite_scope_call_agenda_message_event_record"
    assert result["event_stage"] == "scope_call_agenda_message_event_record"
    assert result["event_status"] == "recorded"


def test_assessment_factory_lite_scope_call_agenda_message_event_record_release_marker_preserves_source_message_layering():
    result = AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["source_scope_call_agenda_message"]["release"] == (
        "assessment-factory-lite-scope-call-conversion"
    )
    assert result["source_scope_call_agenda_message"]["version"] == "2.3.0"
    assert result["source_scope_call_agenda_message"]["message_status"] == "draft_ready"

    assert result["scope_call_package_summary"]["release"] == (
        "assessment-factory-lite-buyer-delivery-follow-up"
    )
    assert result["scope_call_package_summary"]["version"] == "2.2.0"
    assert result["scope_call_package_summary"]["package_status"] == "ready"


def test_assessment_factory_lite_scope_call_agenda_message_event_record_release_marker_preserves_human_boundaries():
    result = AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["message_channel"]["automated_send_used"] is False
    assert result["message_channel"]["calendar_invite_created"] is False
    assert result["message_channel"]["automatic_scheduling_used"] is False
    assert result["message_channel"]["human_operated"] is True

    assert result["send_policy_snapshot"]["send_allowed"] is False
    assert result["send_policy_snapshot"]["automated_send_allowed"] is False
    assert result["send_policy_snapshot"]["calendar_invite_allowed"] is False
    assert result["send_policy_snapshot"]["automatic_scheduling_allowed"] is False
    assert result["send_policy_snapshot"]["requires_human_operator"] is True