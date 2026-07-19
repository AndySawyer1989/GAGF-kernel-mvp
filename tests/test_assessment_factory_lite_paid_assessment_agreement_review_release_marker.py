from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_paid_assessment_agreement_review_service import (
    AssessmentFactoryLitePaidAssessmentAgreementReviewService,
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


AGREEMENT_CONTEXT = {
    "agreement_review_id": "paid-assessment-agreement-review-001",
    "prepared_at": "2026-07-26T12:00:00+00:00",
    "service_scope_reviewed": True,
    "price_confirmed": True,
    "deliverables_confirmed": True,
    "limitations_confirmed": True,
    "buyer_acknowledged_scope": True,
    "buyer_acknowledged_price": True,
    "buyer_acknowledged_non_binding_review": True,
    "agreement_reviewed_by_operator": True,
    "operator_review_status": "agreement_reviewed",
}


def build_ready_review():
    return AssessmentFactoryLitePaidAssessmentAgreementReviewService().build_review(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=AGREEMENT_CONTEXT,
    )


def test_assessment_factory_lite_paid_assessment_agreement_review_release_marker_preserves_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_paid_assessment_agreement_review_release_marker_preserves_endpoint_route():
    actual_routes = {route.path for route in app.routes}

    assert (
        "/products/assessment-factory-lite/paid-assessment-agreement-review"
        in actual_routes
    )


def test_assessment_factory_lite_paid_assessment_agreement_review_release_marker_matches_service_contract():
    result = build_ready_review()

    assert result["event_type"] == "assessment_factory_lite_paid_assessment_agreement_review"
    assert result["review_stage"] == "paid_assessment_agreement_review"
    assert result["review_status"] == "ready_for_agreement_execution_review"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["recommended_action"] == "prepare_contract_execution_review"


def test_assessment_factory_lite_paid_assessment_agreement_review_release_marker_matches_endpoint_contract():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-agreement-review",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": INTERESTED_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
            "scope_call_event_context": SCOPE_CALL_EVENT_CONTEXT,
            "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
            "authorization_context": AUTHORIZATION_CONTEXT,
            "agreement_context": AGREEMENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_type"] == "assessment_factory_lite_paid_assessment_agreement_review"
    assert payload["review_stage"] == "paid_assessment_agreement_review"
    assert payload["review_status"] == "ready_for_agreement_execution_review"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["recommended_action"] == "prepare_contract_execution_review"


def test_assessment_factory_lite_paid_assessment_agreement_review_release_marker_preserves_source_layering():
    result = build_ready_review()

    assert result["source_paid_assessment_authorization_package"]["release"] == (
        "assessment-factory-lite-scope-call-conversion"
    )
    assert result["source_paid_assessment_authorization_package"]["version"] == "2.3.0"
    assert result["source_paid_assessment_authorization_package"]["package_status"] == (
        "ready_for_paid_assessment_authorization"
    )

    assert result["buyer_request"]["buyer_request_is_evidence_not_authorization"] is True
    assert result["human_authorization"]["paid_assessment_authorized"] is False
    assert result["operator_review"]["paid_assessment_authorized"] is False


def test_assessment_factory_lite_paid_assessment_agreement_review_release_marker_preserves_governance_and_commercial_boundaries():
    result = build_ready_review()

    assert result["agreement_terms"]["agreement_terms_ready"] is True
    assert result["buyer_acknowledgment"]["buyer_acknowledgment_ready"] is True
    assert result["buyer_acknowledgment"]["buyer_acknowledgment_is_not_signature"] is True
    assert result["buyer_acknowledgment"]["buyer_acknowledgment_is_not_payment"] is True
    assert result["operator_review"]["agreement_reviewed_by_operator"] is True

    assert result["commercial_boundary"]["agreement_review_ready"] is True
    assert result["commercial_boundary"]["contract_created"] is False
    assert result["commercial_boundary"]["contract_executed"] is False
    assert result["commercial_boundary"]["invoice_created"] is False
    assert result["commercial_boundary"]["payment_requested"] is False
    assert result["commercial_boundary"]["paid_assessment_authorized"] is False
    assert result["commercial_boundary"]["production_onboarding_authorized"] is False
    assert result["commercial_boundary"]["requires_separate_contract_execution"] is True
    assert result["commercial_boundary"]["requires_separate_invoice"] is True
    assert result["commercial_boundary"]["requires_separate_payment_confirmation"] is True
    assert result["commercial_boundary"]["requires_final_paid_work_authorization"] is True

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "agreement_review_is_not_execution": True,
    }