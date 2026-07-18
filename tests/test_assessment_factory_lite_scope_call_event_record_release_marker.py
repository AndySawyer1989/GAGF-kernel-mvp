from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_scope_call_event_record_service import (
    AssessmentFactoryLiteScopeCallEventRecordService,
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


SCOPE_CALL_EVENT_CONTEXT = {
    "scope_call_id": "scope-call-event-package-001",
    "prepared_at": "2026-07-23T12:00:00+00:00",
}


SCOPE_CALL_RECORD_CONTEXT = {
    "event_id": "scope-call-event-record-001",
    "recorded_at": "2026-07-24T12:00:00+00:00",
    "human_operator_confirmed": True,
    "call_completed": True,
    "call_confirmed": True,
    "outcome_status": "completed",
    "outcome_summary": "Buyer confirmed the workflow problem and wants paid assessment review.",
    "buyer_needs_summary": "Buyer needs help identifying governance bottlenecks.",
    "assessment_fit": "good_fit",
    "next_step_requested": "paid_assessment_review",
    "buyer_decision_status": "requested_paid_assessment",
    "operator_name": "Andy Sawyer II",
    "operator_notes": ["Buyer confirmed scope-call outcome."],
}


def build_recorded_event():
    return AssessmentFactoryLiteScopeCallEventRecordService().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
    )


def test_assessment_factory_lite_scope_call_event_record_release_marker_preserves_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_scope_call_event_record_release_marker_preserves_endpoint_route():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/scope-call-event-record" in actual_routes


def test_assessment_factory_lite_scope_call_event_record_release_marker_matches_service_contract():
    result = build_recorded_event()

    assert result["event_type"] == "assessment_factory_lite_scope_call_event_record"
    assert result["event_stage"] == "scope_call_event_record"
    assert result["event_status"] == "recorded"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["recommended_action"] == "prepare_paid_assessment_authorization_package"


def test_assessment_factory_lite_scope_call_event_record_release_marker_matches_endpoint_contract():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
            "scope_call_event_context": SCOPE_CALL_EVENT_CONTEXT,
            "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_type"] == "assessment_factory_lite_scope_call_event_record"
    assert payload["event_stage"] == "scope_call_event_record"
    assert payload["event_status"] == "recorded"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["recommended_action"] == "prepare_paid_assessment_authorization_package"


def test_assessment_factory_lite_scope_call_event_record_release_marker_preserves_source_layering():
    result = build_recorded_event()

    assert result["source_scope_call_event_package"]["release"] == (
        "assessment-factory-lite-scope-call-conversion"
    )
    assert result["source_scope_call_event_package"]["version"] == "2.3.0"
    assert result["source_scope_call_event_package"]["package_status"] == (
        "ready_for_scope_call"
    )

    assert result["scope_call_package_summary"]["release"] == (
        "assessment-factory-lite-buyer-delivery-follow-up"
    )
    assert result["scope_call_package_summary"]["version"] == "2.2.0"
    assert result["scope_call_package_summary"]["package_status"] == "ready"


def test_assessment_factory_lite_scope_call_event_record_release_marker_preserves_governance_and_commercial_boundaries():
    result = build_recorded_event()

    assert result["commercial_boundary"]["contract_created"] is False
    assert result["commercial_boundary"]["contract_executed"] is False
    assert result["commercial_boundary"]["invoice_created"] is False
    assert result["commercial_boundary"]["payment_requested"] is False
    assert result["commercial_boundary"]["paid_assessment_authorized"] is False
    assert result["commercial_boundary"]["production_onboarding_authorized"] is False
    assert result["commercial_boundary"]["paid_assessment_requires_authorization_package"] is True

    assert result["operator_confirmation"]["manual_recording_required"] is True
    assert result["operator_confirmation"]["automatic_call_recording_used"] is False
    assert result["operator_confirmation"]["ai_summary_authoritative"] is False

    assert result["buyer_decision"]["buyer_requested_paid_assessment"] is True
    assert result["buyer_decision"]["paid_assessment_authorization_required"] is True
    assert result["buyer_decision"]["paid_assessment_authorized"] is False

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
    }