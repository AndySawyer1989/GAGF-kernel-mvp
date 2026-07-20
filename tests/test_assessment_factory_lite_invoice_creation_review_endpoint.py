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
    }


def test_assessment_factory_lite_invoice_creation_review_endpoint_builds_contract():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_invoice_creation_review"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["review_stage"] == "invoice_creation_review"
    assert payload["review_status"] == "ready_for_invoice_creation"
    assert payload["invoice_review_id"] == "invoice-creation-review-001"
    assert payload["prepared_at"] == "2026-07-29T12:00:00+00:00"
    assert payload["recommended_action"] == "prepare_invoice_creation_event"


def test_assessment_factory_lite_invoice_creation_review_endpoint_summarizes_source_event():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_contract_execution_event"] == {
        "event_type": "assessment_factory_lite_contract_execution_event",
        "event_stage": "contract_execution_event",
        "event_status": "contract_executed",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "contract_execution_event_id": "contract-execution-event-001",
        "recorded_at": "2026-07-28T12:00:00+00:00",
        "recommended_action": "prepare_invoice_creation_review",
    }


def test_assessment_factory_lite_invoice_creation_review_endpoint_tracks_invoice_details():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["invoice_details_review"] == {
        "invoice_amount_confirmed": True,
        "invoice_recipient_confirmed": True,
        "invoice_description_confirmed": True,
        "invoice_terms_confirmed": True,
        "invoice_details_ready": True,
        "invoice_creation_required_before_payment_request": True,
        "payment_confirmation_required_before_paid_work": True,
    }


def test_assessment_factory_lite_invoice_creation_review_endpoint_tracks_billing_readiness():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["billing_readiness"] == {
        "billing_system_ready": True,
        "tax_or_business_details_checked": True,
        "payment_instructions_reviewed": True,
        "billing_ready": True,
        "billing_readiness_is_not_payment_request": True,
        "billing_readiness_is_not_paid_work_authorization": True,
    }


def test_assessment_factory_lite_invoice_creation_review_endpoint_tracks_operator_review_without_invoice_creation():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["operator_review"] == {
        "human_operator_required": True,
        "invoice_creation_reviewed_by_operator": True,
        "operator_review_status": "invoice_creation_reviewed",
        "invoice_created": False,
        "payment_request_approved": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_invoice_creation_review_endpoint_builds_checklist_and_score():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_checklist"] == {
        "contract_execution_event_recorded": True,
        "invoice_details_ready": True,
        "billing_ready": True,
        "billing_readiness_is_not_payment_request": True,
        "billing_readiness_is_not_paid_work_authorization": True,
        "invoice_creation_reviewed_by_operator": True,
        "invoice_not_created": True,
        "payment_not_requested": True,
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


def test_assessment_factory_lite_invoice_creation_review_endpoint_preserves_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["commercial_boundary"] == {
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

    assert payload["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "invoice_review_notes" in payload["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in payload["evidence_boundary"]["excluded_evidence"]

    assert payload["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "invoice_creation_review_is_not_invoice": True,
        "invoice_creation_review_is_not_payment_request": True,
        "invoice_creation_review_is_not_paid_work_authorization": True,
    }

    assert payload["boundary_notices"] == [
        "invoice_creation_review_does_not_create_invoice",
        "invoice_creation_review_does_not_request_payment",
        "invoice_creation_review_does_not_authorize_paid_work",
        "invoice_creation_review_does_not_start_production_onboarding",
        "invoice_creation_review_requires_human_operator",
    ]


def test_assessment_factory_lite_invoice_creation_review_endpoint_includes_audit_next_action_and_message():
    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["audit_notes"] == [
        "invoice_creation_review_built",
        "invoice_not_created",
        "payment_not_requested",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "invoice_creation_review_ready",
    ]

    assert payload["next_action"] == {
        "action": "prepare_invoice_creation_event",
        "operator_instruction": (
            "Prepare invoice creation event. Do not request payment, "
            "authorize paid work, or start production onboarding from "
            "this review."
        ),
        "future_action": "build_invoice_creation_event",
    }

    assert payload["operator_message"] == (
        "Invoice creation review is ready for invoice creation event. "
        "Payment request, paid work authorization, and production "
        "onboarding remain blocked."
    )


def test_assessment_factory_lite_invoice_creation_review_endpoint_handles_pending_states():
    no_details = ready_payload()
    no_details["invoice_context"] = dict(INVOICE_CONTEXT)
    no_details["invoice_context"]["invoice_amount_confirmed"] = False

    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=no_details,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "pending_invoice_details_review"
    assert "invoice_details_ready" in payload["review_blockers"]
    assert payload["next_action"]["action"] == "complete_invoice_details_review"

    no_billing = ready_payload()
    no_billing["invoice_context"] = dict(INVOICE_CONTEXT)
    no_billing["invoice_context"]["billing_system_ready"] = False

    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=no_billing,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "pending_billing_readiness"
    assert "billing_ready" in payload["review_blockers"]
    assert payload["next_action"]["action"] == "confirm_billing_readiness"

    no_operator = ready_payload()
    no_operator["invoice_context"] = dict(INVOICE_CONTEXT)
    no_operator["invoice_context"]["invoice_creation_reviewed_by_operator"] = False

    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
        json=no_operator,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "pending_operator_review"
    assert "invoice_creation_reviewed_by_operator" in payload["review_blockers"]
    assert payload["next_action"]["action"] == "complete_operator_invoice_creation_review"


def test_assessment_factory_lite_invoice_creation_review_endpoint_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/invoice-creation-review",
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
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == "blocked"
    assert payload["source_contract_execution_event"]["event_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_invoice_creation_review_gaps"


def test_assessment_factory_lite_invoice_creation_review_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/invoice-creation-review" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }