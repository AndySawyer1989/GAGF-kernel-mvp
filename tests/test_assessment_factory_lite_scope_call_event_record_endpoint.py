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


def ready_payload():
    return {
        "operator_approval": APPROVAL,
        "event_context": EVENT_CONTEXT,
        "follow_up_context": INTERESTED_CONTEXT,
        "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
        "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        "scope_call_event_context": SCOPE_CALL_EVENT_CONTEXT,
        "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
    }


def test_assessment_factory_lite_scope_call_event_record_endpoint_builds_contract():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_scope_call_event_record"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["event_stage"] == "scope_call_event_record"
    assert payload["event_status"] == "recorded"
    assert payload["event_id"] == "scope-call-event-record-001"
    assert payload["recorded_at"] == "2026-07-24T12:00:00+00:00"
    assert payload["recommended_action"] == "prepare_paid_assessment_authorization_package"


def test_assessment_factory_lite_scope_call_event_record_endpoint_summarizes_source_package():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_scope_call_event_package"] == {
        "event_type": "assessment_factory_lite_scope_call_event_package",
        "package_stage": "scope_call_event_package",
        "package_status": "ready_for_scope_call",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "scope_call_id": "scope-call-event-package-001",
        "prepared_at": "2026-07-23T12:00:00+00:00",
        "recommended_action": "prepare_scope_call_event_record",
    }


def test_assessment_factory_lite_scope_call_event_record_endpoint_tracks_call_outcome():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["call_outcome"] == {
        "call_completed": True,
        "call_confirmed": True,
        "outcome_status": "completed",
        "outcome_summary": "Buyer confirmed the workflow problem and wants paid assessment review.",
        "buyer_needs_summary": "Buyer needs help identifying governance bottlenecks.",
        "assessment_fit": "good_fit",
        "next_step_requested": "paid_assessment_review",
    }


def test_assessment_factory_lite_scope_call_event_record_endpoint_tracks_operator_confirmation():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["operator_confirmation"] == {
        "human_operator_confirmed": True,
        "operator_name": "Andy Sawyer II",
        "operator_notes": ["Buyer confirmed scope-call outcome."],
        "manual_recording_required": True,
        "automatic_call_recording_used": False,
        "ai_summary_authoritative": False,
    }


def test_assessment_factory_lite_scope_call_event_record_endpoint_tracks_buyer_decision_without_authorization():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["buyer_decision"] == {
        "buyer_decision_status": "requested_paid_assessment",
        "buyer_requested_paid_assessment": True,
        "buyer_declined": False,
        "buyer_needs_follow_up": False,
        "paid_assessment_authorization_required": True,
        "paid_assessment_authorized": False,
    }


def test_assessment_factory_lite_scope_call_event_record_endpoint_builds_event_checklist():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_checklist"] == {
        "scope_call_event_package_ready": True,
        "call_completed": True,
        "call_confirmed": True,
        "human_operator_confirmed": True,
        "outcome_summary_recorded": True,
        "buyer_decision_recorded": True,
        "paid_assessment_not_authorized": True,
        "automatic_call_recording_not_used": True,
        "ai_summary_not_authoritative": True,
    }

    assert payload["event_blockers"] == []


def test_assessment_factory_lite_scope_call_event_record_endpoint_preserves_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scheduling_boundary"] == {
        "scope_call_scheduled_by_system": False,
        "calendar_invite_created": False,
        "automatic_scheduling_allowed": False,
        "manual_scheduling_required": True,
        "scheduling_authority": "human_operator",
    }

    assert payload["commercial_boundary"] == {
        "contract_created": False,
        "contract_executed": False,
        "invoice_created": False,
        "payment_requested": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "paid_assessment_requires_authorization_package": True,
    }

    assert payload["evidence_boundary"]["evidence_review_required_before_paid_assessment"] is True
    assert "regulated_production_data" in payload["evidence_boundary"]["excluded_evidence"]

    assert payload["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
    }

    assert payload["boundary_notices"] == [
        "scope_call_event_record_does_not_authorize_paid_assessment",
        "scope_call_event_record_does_not_execute_contract",
        "scope_call_event_record_does_not_create_invoice",
        "scope_call_event_record_does_not_start_production_onboarding",
        "scope_call_event_record_requires_human_operator",
    ]


def test_assessment_factory_lite_scope_call_event_record_endpoint_includes_audit_next_action_and_message():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["audit_notes"] == [
        "scope_call_event_record_built",
        "paid_assessment_not_authorized",
        "contract_not_executed",
        "invoice_not_created",
        "production_onboarding_not_started",
        "scope_call_event_record_recorded",
        "buyer_requested_paid_assessment_authorization_review",
    ]

    assert payload["commercial_next_action"] == {
        "action": "prepare_paid_assessment_authorization_package",
        "allowed_next_stage": "paid_assessment_authorization_package",
        "automatic_execution_allowed": False,
        "human_operator_required": True,
    }

    assert payload["next_action"] == {
        "action": "prepare_paid_assessment_authorization_package",
        "operator_instruction": (
            "Prepare the paid assessment authorization package. Do not "
            "authorize paid work until the authorization package is "
            "explicitly approved."
        ),
        "future_action": "build_paid_assessment_authorization_package",
    }

    assert payload["operator_message"] == (
        "Scope-call event recorded. Buyer requested paid assessment review, "
        "but paid assessment work is not authorized until a later "
        "authorization package is explicitly approved."
    )


def test_assessment_factory_lite_scope_call_event_record_endpoint_handles_pending_and_declined_states():
    pending_human = ready_payload()
    pending_human["scope_call_record_context"] = dict(SCOPE_CALL_RECORD_CONTEXT)
    pending_human["scope_call_record_context"]["human_operator_confirmed"] = False

    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=pending_human,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_human_confirmation"
    assert "human_operator_confirmed" in payload["event_blockers"]
    assert payload["recommended_action"] == "resolve_scope_call_event_record_gaps"

    pending_call = ready_payload()
    pending_call["scope_call_record_context"] = dict(SCOPE_CALL_RECORD_CONTEXT)
    pending_call["scope_call_record_context"]["call_completed"] = False

    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=pending_call,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_scope_call_completion"
    assert "call_completed" in payload["event_blockers"]
    assert payload["next_action"]["action"] == "complete_scope_call"

    declined = ready_payload()
    declined["scope_call_record_context"] = dict(SCOPE_CALL_RECORD_CONTEXT)
    declined["scope_call_record_context"]["buyer_decision_status"] = "declined"

    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json=declined,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "recorded"
    assert payload["buyer_decision"]["buyer_declined"] is True
    assert payload["recommended_action"] == "close_buyer_opportunity"
    assert payload["next_action"]["action"] == "close_buyer_opportunity"


def test_assessment_factory_lite_scope_call_event_record_endpoint_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/scope-call-event-record",
        json={
            "export": export,
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
            "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "blocked"
    assert payload["source_scope_call_event_package"]["package_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_scope_call_event_record_gaps"


def test_assessment_factory_lite_scope_call_event_record_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/scope-call-event-record" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }