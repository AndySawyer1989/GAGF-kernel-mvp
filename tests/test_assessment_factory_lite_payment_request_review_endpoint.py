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


def ready_payload():
    return {
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
    }


def test_assessment_factory_lite_payment_request_review_endpoint_builds_contract():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_payment_request_review"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["review_stage"] == "payment_request_review"
    assert payload["review_status"] == "ready_for_payment_request"
    assert payload["payment_request_review_id"] == "payment-request-review-001"
    assert payload["prepared_at"] == "2026-07-31T12:00:00+00:00"
    assert payload["recommended_action"] == "prepare_payment_request_event"


def test_assessment_factory_lite_payment_request_review_endpoint_summarizes_source_event():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_invoice_creation_event"] == {
        "event_type": "assessment_factory_lite_invoice_creation_event",
        "event_stage": "invoice_creation_event",
        "event_status": "invoice_created",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "invoice_creation_event_id": "invoice-creation-event-001",
        "recorded_at": "2026-07-30T12:00:00+00:00",
        "recommended_action": "prepare_payment_request_review",
    }


def test_assessment_factory_lite_payment_request_review_endpoint_tracks_payment_request_details():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["payment_request_details"] == {
        "payment_amount_confirmed": True,
        "invoice_reference_confirmed": True,
        "payment_due_date_confirmed": True,
        "payment_request_language_reviewed": True,
        "payment_request_details_ready": True,
        "payment_request_required_before_payment_confirmation": True,
        "payment_confirmation_required_before_paid_work": True,
    }


def test_assessment_factory_lite_payment_request_review_endpoint_tracks_buyer_notice_readiness():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["buyer_notice_readiness"] == {
        "buyer_notice_prepared": True,
        "buyer_notice_channel_confirmed": True,
        "payment_instructions_included": True,
        "buyer_notice_ready": True,
        "buyer_notice_is_not_payment_confirmation": True,
        "buyer_notice_is_not_paid_work_authorization": True,
    }


def test_assessment_factory_lite_payment_request_review_endpoint_tracks_operator_review_without_payment_request():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["operator_review"] == {
        "human_operator_required": True,
        "payment_request_reviewed_by_operator": True,
        "operator_review_status": "payment_request_reviewed",
        "payment_requested": False,
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_payment_request_review_endpoint_builds_checklist_and_score():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_checklist"] == {
        "invoice_creation_event_recorded": True,
        "payment_request_details_ready": True,
        "buyer_notice_ready": True,
        "buyer_notice_is_not_payment_confirmation": True,
        "buyer_notice_is_not_paid_work_authorization": True,
        "payment_request_reviewed_by_operator": True,
        "payment_not_requested": True,
        "payment_not_confirmed": True,
        "paid_assessment_not_authorized": True,
        "production_onboarding_not_started": True,
    }

    assert payload["review_blockers"] == []
    assert payload["review_score"] == {
        "passed": 10,
        "total": 10,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_payment_request_review_endpoint_preserves_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["commercial_boundary"] == {
        "payment_request_ready": True,
        "payment_requested": False,
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_actual_payment_request": True,
        "requires_separate_payment_confirmation": True,
        "requires_final_paid_work_authorization": True,
        "requires_separate_production_onboarding": True,
    }

    assert payload["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "payment_request_review_notes" in payload["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in payload["evidence_boundary"]["excluded_evidence"]

    assert payload["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "payment_request_review_is_not_payment_request": True,
        "payment_request_review_is_not_payment_confirmation": True,
        "payment_request_review_is_not_paid_work_authorization": True,
    }

    assert payload["boundary_notices"] == [
        "payment_request_review_does_not_request_payment",
        "payment_request_review_does_not_confirm_payment",
        "payment_request_review_does_not_authorize_paid_work",
        "payment_request_review_does_not_start_production_onboarding",
        "payment_request_review_requires_human_operator",
    ]


def test_assessment_factory_lite_payment_request_review_endpoint_includes_audit_next_action_and_message():
    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["audit_notes"] == [
        "payment_request_review_built",
        "payment_not_requested",
        "payment_not_confirmed",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "payment_request_review_ready",
    ]

    assert payload["next_action"] == {
        "action": "prepare_payment_request_event",
        "operator_instruction": (
            "Prepare payment request event. Do not confirm payment, "
            "authorize paid work, or start production onboarding from "
            "this review."
        ),
        "future_action": "build_payment_request_event",
    }

    assert payload["operator_message"] == (
        "Payment request review is ready for payment request event. "
        "Payment confirmation, paid work authorization, and production "
        "onboarding remain blocked."
    )


def test_assessment_factory_lite_payment_request_review_endpoint_handles_pending_states():
    no_details = ready_payload()
    no_details["payment_request_context"] = dict(PAYMENT_REQUEST_CONTEXT)
    no_details["payment_request_context"]["payment_amount_confirmed"] = False

    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=no_details,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "pending_payment_request_details_review"
    assert "payment_request_details_ready" in payload["review_blockers"]
    assert payload["next_action"]["action"] == "complete_payment_request_details_review"

    no_notice = ready_payload()
    no_notice["payment_request_context"] = dict(PAYMENT_REQUEST_CONTEXT)
    no_notice["payment_request_context"]["buyer_notice_prepared"] = False

    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=no_notice,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "pending_buyer_notice_readiness"
    assert "buyer_notice_ready" in payload["review_blockers"]
    assert payload["next_action"]["action"] == "confirm_buyer_notice_readiness"

    no_operator = ready_payload()
    no_operator["payment_request_context"] = dict(PAYMENT_REQUEST_CONTEXT)
    no_operator["payment_request_context"]["payment_request_reviewed_by_operator"] = False

    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json=no_operator,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "pending_operator_review"
    assert "payment_request_reviewed_by_operator" in payload["review_blockers"]
    assert payload["next_action"]["action"] == "complete_operator_payment_request_review"


def test_assessment_factory_lite_payment_request_review_endpoint_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/payment-request-review",
        json={
            "export": export,
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
            "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
            "authorization_context": AUTHORIZATION_CONTEXT,
            "agreement_context": AGREEMENT_CONTEXT,
            "contract_context": CONTRACT_CONTEXT,
            "contract_execution_context": CONTRACT_EXECUTION_CONTEXT,
            "invoice_context": INVOICE_CONTEXT,
            "invoice_creation_context": INVOICE_CREATION_CONTEXT,
            "payment_request_context": PAYMENT_REQUEST_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "blocked"
    assert payload["source_invoice_creation_event"]["event_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_payment_request_review_gaps"


def test_assessment_factory_lite_payment_request_review_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/payment-request-review" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }