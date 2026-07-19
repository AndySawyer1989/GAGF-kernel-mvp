from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_paid_assessment_authorization_package_service import (
    AssessmentFactoryLitePaidAssessmentAuthorizationPackageService,
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


AUTHORIZATION_CONTEXT = {
    "authorization_id": "paid-assessment-authorization-package-001",
    "prepared_at": "2026-07-25T12:00:00+00:00",
    "buyer_request_summary": "Buyer requested paid assessment review after scope call.",
    "pricing_reviewed": True,
    "scope_reviewed": True,
    "terms_reviewed": True,
    "evidence_reviewed": True,
    "evidence_boundary_approved": True,
    "human_operator_authorized_package": True,
    "authorization_status": "package_authorized_for_agreement_review",
}


def build_ready_package():
    return AssessmentFactoryLitePaidAssessmentAuthorizationPackageService().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
    )


def test_assessment_factory_lite_paid_assessment_authorization_package_release_marker_preserves_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_paid_assessment_authorization_package_release_marker_preserves_endpoint_route():
    actual_routes = {route.path for route in app.routes}

    assert (
        "/products/assessment-factory-lite/paid-assessment-authorization-package"
        in actual_routes
    )


def test_assessment_factory_lite_paid_assessment_authorization_package_release_marker_matches_service_contract():
    result = build_ready_package()

    assert result["event_type"] == (
        "assessment_factory_lite_paid_assessment_authorization_package"
    )
    assert result["package_stage"] == "paid_assessment_authorization_package"
    assert result["package_status"] == "ready_for_paid_assessment_authorization"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["recommended_action"] == "prepare_paid_assessment_agreement_review"


def test_assessment_factory_lite_paid_assessment_authorization_package_release_marker_matches_endpoint_contract():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
            "scope_call_event_context": SCOPE_CALL_EVENT_CONTEXT,
            "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
            "authorization_context": AUTHORIZATION_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_type"] == (
        "assessment_factory_lite_paid_assessment_authorization_package"
    )
    assert payload["package_stage"] == "paid_assessment_authorization_package"
    assert payload["package_status"] == "ready_for_paid_assessment_authorization"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["recommended_action"] == "prepare_paid_assessment_agreement_review"


def test_assessment_factory_lite_paid_assessment_authorization_package_release_marker_preserves_source_layering():
    result = build_ready_package()

    assert result["source_scope_call_event_record"]["release"] == (
        "assessment-factory-lite-scope-call-conversion"
    )
    assert result["source_scope_call_event_record"]["version"] == "2.3.0"
    assert result["source_scope_call_event_record"]["event_status"] == "recorded"

    assert result["scope_call_package_summary"]["release"] == (
        "assessment-factory-lite-buyer-delivery-follow-up"
    )
    assert result["scope_call_package_summary"]["version"] == "2.2.0"
    assert result["scope_call_package_summary"]["package_status"] == "ready"


def test_assessment_factory_lite_paid_assessment_authorization_package_release_marker_preserves_governance_and_commercial_boundaries():
    result = build_ready_package()

    assert result["buyer_request"]["buyer_requested_paid_assessment"] is True
    assert result["buyer_request"]["buyer_request_is_evidence_not_authorization"] is True

    assert result["commercial_boundary"]["authorization_package_ready"] is True
    assert result["commercial_boundary"]["paid_assessment_authorized"] is False
    assert result["commercial_boundary"]["contract_created"] is False
    assert result["commercial_boundary"]["contract_executed"] is False
    assert result["commercial_boundary"]["invoice_created"] is False
    assert result["commercial_boundary"]["payment_requested"] is False
    assert result["commercial_boundary"]["production_onboarding_authorized"] is False
    assert result["commercial_boundary"]["requires_separate_contract"] is True
    assert result["commercial_boundary"]["requires_separate_invoice"] is True
    assert result["commercial_boundary"]["requires_separate_payment_confirmation"] is True

    assert result["human_authorization"]["human_operator_required"] is True
    assert result["human_authorization"]["human_operator_authorized_package"] is True
    assert result["human_authorization"]["paid_assessment_authorized"] is False
    assert result["human_authorization"]["contract_execution_approved"] is False
    assert result["human_authorization"]["invoice_creation_approved"] is False
    assert result["human_authorization"]["payment_request_approved"] is False
    assert result["human_authorization"]["production_onboarding_approved"] is False

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "authorization_is_package_readiness_only": True,
    }