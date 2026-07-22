from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_payment_request_event_service import (
    AssessmentFactoryLitePaymentRequestEventService,
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


CONTRACT_CONTEXT = {
    "contract_review_id": "contract-execution-review-001",
    "prepared_at": "2026-07-27T12:00:00+00:00",
    "contract_document_prepared": True,
    "contract_terms_reviewed": True,
    "legal_language_reviewed": True,
    "scope_matches_agreement": True,
    "buyer_signature_ready": True,
    "provider_signature_ready": True,
    "signature_method_confirmed": True,
    "contract_execution_reviewed_by_operator": True,
    "operator_review_status": "contract_execution_reviewed",
}


CONTRACT_EXECUTION_CONTEXT = {
    "contract_execution_event_id": "contract-execution-event-001",
    "recorded_at": "2026-07-28T12:00:00+00:00",
    "contract_execution_confirmed": True,
    "executed_contract_reference": "contract-ref-001",
    "executed_at": "2026-07-28T11:30:00+00:00",
    "execution_method": "electronic_signature",
    "buyer_signed": True,
    "provider_signed": True,
    "signature_evidence_recorded": True,
    "human_operator_confirmed_execution": True,
    "operator_name": "Andy Sawyer II",
    "operator_notes": ["Contract execution confirmed."],
}


INVOICE_CONTEXT = {
    "invoice_review_id": "invoice-creation-review-001",
    "prepared_at": "2026-07-29T12:00:00+00:00",
    "invoice_amount_confirmed": True,
    "invoice_recipient_confirmed": True,
    "invoice_description_confirmed": True,
    "invoice_terms_confirmed": True,
    "billing_system_ready": True,
    "tax_or_business_details_checked": True,
    "payment_instructions_reviewed": True,
    "invoice_creation_reviewed_by_operator": True,
    "operator_review_status": "invoice_creation_reviewed",
}


INVOICE_CREATION_CONTEXT = {
    "invoice_creation_event_id": "invoice-creation-event-001",
    "recorded_at": "2026-07-30T12:00:00+00:00",
    "invoice_created": True,
    "invoice_reference": "invoice-ref-001",
    "invoice_created_at": "2026-07-30T11:45:00+00:00",
    "invoice_amount": "2500.00",
    "invoice_delivered_to_buyer": True,
    "delivery_channel": "manual_email",
    "delivery_reference": "email-thread-001",
    "human_operator_confirmed_invoice_creation": True,
    "operator_name": "Andy Sawyer II",
    "operator_notes": ["Invoice creation confirmed."],
}


PAYMENT_REQUEST_CONTEXT = {
    "payment_request_review_id": "payment-request-review-001",
    "prepared_at": "2026-07-31T12:00:00+00:00",
    "payment_amount_confirmed": True,
    "invoice_reference_confirmed": True,
    "payment_due_date_confirmed": True,
    "payment_request_language_reviewed": True,
    "buyer_notice_prepared": True,
    "buyer_notice_channel_confirmed": True,
    "payment_instructions_included": True,
    "payment_request_reviewed_by_operator": True,
    "operator_review_status": "payment_request_reviewed",
}


PAYMENT_REQUEST_EVENT_CONTEXT = {
    "payment_request_event_id": "payment-request-event-001",
    "recorded_at": "2026-08-01T12:00:00+00:00",
    "payment_requested": True,
    "payment_request_reference": "payment-request-ref-001",
    "payment_requested_at": "2026-08-01T11:45:00+00:00",
    "requested_amount": "2500.00",
    "payment_request_delivered_to_buyer": True,
    "delivery_channel": "manual_email",
    "delivery_reference": "payment-request-email-thread-001",
    "human_operator_confirmed_payment_request": True,
    "operator_name": "Andy Sawyer II",
    "operator_notes": ["Payment request confirmed."],
}


def build_requested_event():
    return AssessmentFactoryLitePaymentRequestEventService().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=AGREEMENT_CONTEXT,
        contract_context=CONTRACT_CONTEXT,
        contract_execution_context=CONTRACT_EXECUTION_CONTEXT,
        invoice_context=INVOICE_CONTEXT,
        invoice_creation_context=INVOICE_CREATION_CONTEXT,
        payment_request_context=PAYMENT_REQUEST_CONTEXT,
        payment_request_event_context=PAYMENT_REQUEST_EVENT_CONTEXT,
    )


def test_assessment_factory_lite_payment_request_event_release_marker_preserves_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_payment_request_event_release_marker_preserves_endpoint_route():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/payment-request-event" in actual_routes


def test_assessment_factory_lite_payment_request_event_release_marker_matches_service_contract():
    result = build_requested_event()

    assert result["event_type"] == "assessment_factory_lite_payment_request_event"
    assert result["event_stage"] == "payment_request_event"
    assert result["event_status"] == "payment_requested"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["recommended_action"] == "prepare_payment_confirmation_review"


def test_assessment_factory_lite_payment_request_event_release_marker_matches_endpoint_contract():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-event",
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
            "contract_context": CONTRACT_CONTEXT,
            "contract_execution_context": CONTRACT_EXECUTION_CONTEXT,
            "invoice_context": INVOICE_CONTEXT,
            "invoice_creation_context": INVOICE_CREATION_CONTEXT,
            "payment_request_context": PAYMENT_REQUEST_CONTEXT,
            "payment_request_event_context": PAYMENT_REQUEST_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_type"] == "assessment_factory_lite_payment_request_event"
    assert payload["event_stage"] == "payment_request_event"
    assert payload["event_status"] == "payment_requested"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["recommended_action"] == "prepare_payment_confirmation_review"


def test_assessment_factory_lite_payment_request_event_release_marker_preserves_source_layering():
    result = build_requested_event()

    assert result["source_payment_request_review"]["release"] == (
        "assessment-factory-lite-scope-call-conversion"
    )
    assert result["source_payment_request_review"]["version"] == "2.3.0"
    assert result["source_payment_request_review"]["review_status"] == (
        "ready_for_payment_request"
    )

    assert result["payment_request_details"]["payment_request_details_ready"] is True
    assert result["buyer_notice_readiness"]["buyer_notice_ready"] is True
    assert result["invoice_record"]["invoice_created"] is True
    assert result["delivery_source_record"]["invoice_delivered_to_buyer"] is True


def test_assessment_factory_lite_payment_request_event_release_marker_preserves_payment_request_and_downstream_boundaries():
    result = build_requested_event()

    assert result["payment_request_record"]["payment_requested"] is True
    assert result["payment_request_record"]["payment_request_reference_recorded"] is True
    assert result["payment_request_record"]["payment_requested_at_recorded"] is True
    assert result["payment_request_record"]["requested_amount_recorded"] is True
    assert result["payment_request_record"][
        "payment_request_record_is_not_payment_confirmation"
    ] is True
    assert result["payment_request_record"][
        "payment_request_record_is_not_paid_work_authorization"
    ] is True

    assert result["delivery_record"]["payment_request_delivered_to_buyer"] is True
    assert result["delivery_record"]["delivery_channel_recorded"] is True
    assert result["delivery_record"]["delivery_reference_recorded"] is True
    assert result["delivery_record"][
        "payment_request_delivery_is_not_payment_confirmation"
    ] is True
    assert result["delivery_record"][
        "payment_request_delivery_is_not_paid_work_authorization"
    ] is True

    assert result["operator_confirmation"]["human_operator_confirmed_payment_request"] is True
    assert result["operator_confirmation"]["payment_confirmed"] is False
    assert result["operator_confirmation"]["paid_assessment_authorized"] is False
    assert result["operator_confirmation"]["production_onboarding_approved"] is False

    assert result["commercial_boundary"] == {
        "payment_request_recorded": True,
        "payment_requested": True,
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_separate_payment_confirmation": True,
        "requires_final_paid_work_authorization": True,
        "requires_separate_production_onboarding": True,
    }

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "payment_request_event_is_not_payment_confirmation": True,
        "payment_request_event_is_not_paid_work_authorization": True,
    }