from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_invoice_creation_review_service import (
    AssessmentFactoryLiteInvoiceCreationReviewService,
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


def build_ready_review():
    return AssessmentFactoryLiteInvoiceCreationReviewService().build_review(
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
    )


def test_assessment_factory_lite_invoice_creation_review_release_marker_preserves_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_invoice_creation_review_release_marker_preserves_endpoint_route():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/invoice-creation-review" in actual_routes


def test_assessment_factory_lite_invoice_creation_review_release_marker_matches_service_contract():
    result = build_ready_review()

    assert result["event_type"] == "assessment_factory_lite_invoice_creation_review"
    assert result["review_stage"] == "invoice_creation_review"
    assert result["review_status"] == "ready_for_invoice_creation"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["recommended_action"] == "prepare_invoice_creation_event"


def test_assessment_factory_lite_invoice_creation_review_release_marker_matches_endpoint_contract():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
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
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_type"] == "assessment_factory_lite_invoice_creation_review"
    assert payload["review_stage"] == "invoice_creation_review"
    assert payload["review_status"] == "ready_for_invoice_creation"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["recommended_action"] == "prepare_invoice_creation_event"


def test_assessment_factory_lite_invoice_creation_review_release_marker_preserves_source_layering():
    result = build_ready_review()

    assert result["source_contract_execution_event"]["release"] == (
        "assessment-factory-lite-scope-call-conversion"
    )
    assert result["source_contract_execution_event"]["version"] == "2.3.0"
    assert result["source_contract_execution_event"]["event_status"] == "contract_executed"

    assert result["execution_evidence"]["contract_executed"] is True
    assert result["signature_record"]["all_required_signatures_recorded"] is True
    assert result["contract_document_review"]["contract_document_ready"] is True
    assert result["agreement_terms"]["agreement_terms_ready"] is True


def test_assessment_factory_lite_invoice_creation_review_release_marker_preserves_invoice_and_downstream_boundaries():
    result = build_ready_review()

    assert result["invoice_details_review"]["invoice_details_ready"] is True
    assert result["invoice_details_review"][
        "invoice_creation_required_before_payment_request"
    ] is True
    assert result["invoice_details_review"][
        "payment_confirmation_required_before_paid_work"
    ] is True

    assert result["billing_readiness"]["billing_ready"] is True
    assert result["billing_readiness"]["billing_readiness_is_not_payment_request"] is True
    assert result["billing_readiness"][
        "billing_readiness_is_not_paid_work_authorization"
    ] is True

    assert result["operator_review"]["invoice_creation_reviewed_by_operator"] is True
    assert result["operator_review"]["invoice_created"] is False
    assert result["operator_review"]["payment_request_approved"] is False
    assert result["operator_review"]["paid_assessment_authorized"] is False
    assert result["operator_review"]["production_onboarding_approved"] is False

    assert result["commercial_boundary"] == {
        "invoice_creation_ready": True,
        "invoice_created": False,
        "payment_requested": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_actual_invoice_creation": True,
        "requires_separate_payment_request": True,
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
        "invoice_creation_review_is_not_invoice": True,
        "invoice_creation_review_is_not_payment_request": True,
        "invoice_creation_review_is_not_paid_work_authorization": True,
    }