from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_payment_confirmation_event_service import (
    AssessmentFactoryLitePaymentConfirmationEventService,
)


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


PAYMENT_CONFIRMATION_CONTEXT = {
    "payment_confirmation_review_id": "payment-confirmation-review-001",
    "prepared_at": "2026-08-02T12:00:00+00:00",
    "payment_receipt_available": True,
    "payment_reference_available": True,
    "received_amount_reviewed": True,
    "received_at_reviewed": True,
    "amount_matches_request": True,
    "invoice_reference_matches": True,
    "payment_method_reviewed": True,
    "payment_confirmation_reviewed_by_operator": True,
    "operator_review_status": "payment_confirmation_reviewed",
}


PAYMENT_CONFIRMATION_EVENT_CONTEXT = {
    "payment_confirmation_event_id": "payment-confirmation-event-001",
    "recorded_at": "2026-08-03T12:00:00+00:00",
    "payment_confirmed": True,
    "payment_confirmation_reference": "payment-confirmation-ref-001",
    "payment_confirmed_at": "2026-08-03T11:45:00+00:00",
    "confirmed_amount": "2500.00",
    "amount_reconciled": True,
    "invoice_reference_reconciled": True,
    "payment_method_recorded": True,
    "human_operator_confirmed_payment": True,
    "operator_name": "Andy Sawyer II",
    "operator_notes": ["Payment receipt confirmed."],
}


def build_confirmed_event():
    return AssessmentFactoryLitePaymentConfirmationEventService().record_event(
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
        payment_confirmation_context=PAYMENT_CONFIRMATION_CONTEXT,
        payment_confirmation_event_context=PAYMENT_CONFIRMATION_EVENT_CONTEXT,
    )


def test_assessment_factory_lite_payment_confirmation_event_service_builds_contract():
    result = build_confirmed_event()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_payment_confirmation_event"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["event_stage"] == "payment_confirmation_event"
    assert result["event_status"] == "payment_confirmed"
    assert result["payment_confirmation_event_id"] == "payment-confirmation-event-001"
    assert result["recorded_at"] == "2026-08-03T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_paid_assessment_authorization_review"


def test_assessment_factory_lite_payment_confirmation_event_service_summarizes_source_review():
    result = build_confirmed_event()

    assert result["source_payment_confirmation_review"] == {
        "event_type": "assessment_factory_lite_payment_confirmation_review",
        "review_stage": "payment_confirmation_review",
        "review_status": "ready_for_payment_confirmation",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "payment_confirmation_review_id": "payment-confirmation-review-001",
        "prepared_at": "2026-08-02T12:00:00+00:00",
        "recommended_action": "prepare_payment_confirmation_event",
    }


def test_assessment_factory_lite_payment_confirmation_event_service_tracks_payment_confirmation_record():
    result = build_confirmed_event()

    assert result["payment_confirmation_record"] == {
        "payment_confirmed": True,
        "payment_confirmation_reference": "payment-confirmation-ref-001",
        "payment_confirmed_at": "2026-08-03T11:45:00+00:00",
        "confirmed_amount": "2500.00",
        "payment_confirmation_reference_recorded": True,
        "payment_confirmed_at_recorded": True,
        "confirmed_amount_recorded": True,
        "payment_confirmation_record_is_not_paid_work_authorization": True,
        "payment_confirmation_record_is_not_production_onboarding": True,
    }


def test_assessment_factory_lite_payment_confirmation_event_service_tracks_reconciliation_record():
    result = build_confirmed_event()

    assert result["reconciliation_record"] == {
        "amount_reconciled": True,
        "invoice_reference_reconciled": True,
        "payment_method_recorded": True,
        "reconciliation_recorded": True,
        "reconciliation_record_is_not_paid_work_authorization": True,
        "reconciliation_record_is_not_production_onboarding": True,
    }


def test_assessment_factory_lite_payment_confirmation_event_service_tracks_operator_confirmation_without_work_authorization():
    result = build_confirmed_event()

    assert result["operator_confirmation"] == {
        "human_operator_required": True,
        "human_operator_confirmed_payment": True,
        "operator_name": "Andy Sawyer II",
        "operator_notes": ["Payment receipt confirmed."],
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_payment_confirmation_event_service_builds_checklist_and_score():
    result = build_confirmed_event()

    assert result["event_checklist"] == {
        "payment_confirmation_review_ready": True,
        "payment_confirmed": True,
        "payment_confirmation_reference_recorded": True,
        "payment_confirmed_at_recorded": True,
        "confirmed_amount_recorded": True,
        "payment_confirmation_record_is_not_paid_work_authorization": True,
        "payment_confirmation_record_is_not_production_onboarding": True,
        "reconciliation_recorded": True,
        "reconciliation_record_is_not_paid_work_authorization": True,
        "reconciliation_record_is_not_production_onboarding": True,
        "human_operator_confirmed_payment": True,
        "paid_assessment_not_authorized": True,
        "production_onboarding_not_started": True,
    }

    assert result["event_blockers"] == []
    assert result["event_score"] == {
        "passed": 13,
        "total": 13,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_payment_confirmation_event_service_preserves_boundaries():
    result = build_confirmed_event()

    assert result["commercial_boundary"] == {
        "payment_confirmation_recorded": True,
        "payment_confirmed": True,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_final_paid_work_authorization": True,
        "requires_separate_production_onboarding": True,
    }

    assert result["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "payment_confirmation_reference" in result["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "payment_confirmation_event_is_not_paid_work_authorization": True,
        "payment_confirmation_event_is_not_production_onboarding": True,
    }

    assert result["boundary_notices"] == [
        "payment_confirmation_event_records_payment_confirmation_only",
        "payment_confirmation_event_does_not_authorize_paid_work",
        "payment_confirmation_event_does_not_start_production_onboarding",
        "payment_confirmation_event_requires_human_operator",
    ]


def test_assessment_factory_lite_payment_confirmation_event_service_includes_audit_next_action_and_message():
    result = build_confirmed_event()

    assert result["audit_notes"] == [
        "payment_confirmation_event_built",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "payment_confirmation_event_recorded",
    ]

    assert result["next_action"] == {
        "action": "prepare_paid_assessment_authorization_review",
        "operator_instruction": (
            "Prepare paid assessment authorization review. Do not authorize "
            "paid work or start production onboarding from this payment "
            "confirmation event."
        ),
        "future_action": "build_paid_assessment_authorization_review",
    }

    assert result["operator_message"] == (
        "Payment confirmation has been recorded. Paid assessment "
        "authorization and production onboarding remain blocked."
    )


def test_assessment_factory_lite_payment_confirmation_event_service_handles_pending_states():
    no_confirmation = dict(PAYMENT_CONFIRMATION_EVENT_CONTEXT)
    no_confirmation["payment_confirmed"] = False

    result = AssessmentFactoryLitePaymentConfirmationEventService().record_event(
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
        payment_confirmation_context=PAYMENT_CONFIRMATION_CONTEXT,
        payment_confirmation_event_context=no_confirmation,
    )

    assert result["event_status"] == "pending_payment_confirmation"
    assert "payment_confirmed" in result["event_blockers"]
    assert result["next_action"]["action"] == "confirm_payment_received"

    no_record = dict(PAYMENT_CONFIRMATION_EVENT_CONTEXT)
    no_record["payment_confirmation_reference"] = "not_recorded"

    result = AssessmentFactoryLitePaymentConfirmationEventService().record_event(
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
        payment_confirmation_context=PAYMENT_CONFIRMATION_CONTEXT,
        payment_confirmation_event_context=no_record,
    )

    assert result["event_status"] == "pending_payment_confirmation_record"
    assert "payment_confirmation_reference_recorded" in result["event_blockers"]
    assert result["next_action"]["action"] == "record_payment_confirmation_reference"

    no_reconciliation = dict(PAYMENT_CONFIRMATION_EVENT_CONTEXT)
    no_reconciliation["amount_reconciled"] = False

    result = AssessmentFactoryLitePaymentConfirmationEventService().record_event(
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
        payment_confirmation_context=PAYMENT_CONFIRMATION_CONTEXT,
        payment_confirmation_event_context=no_reconciliation,
    )

    assert result["event_status"] == "pending_reconciliation_record"
    assert "reconciliation_recorded" in result["event_blockers"]
    assert result["next_action"]["action"] == "record_payment_reconciliation"

    no_operator = dict(PAYMENT_CONFIRMATION_EVENT_CONTEXT)
    no_operator["human_operator_confirmed_payment"] = False

    result = AssessmentFactoryLitePaymentConfirmationEventService().record_event(
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
        payment_confirmation_context=PAYMENT_CONFIRMATION_CONTEXT,
        payment_confirmation_event_context=no_operator,
    )

    assert result["event_status"] == "pending_operator_confirmation"
    assert "human_operator_confirmed_payment" in result["event_blockers"]
    assert result["next_action"]["action"] == "confirm_operator_payment_confirmation_event"


def test_assessment_factory_lite_payment_confirmation_event_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLitePaymentConfirmationEventService().record_event(
        export=export,
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=AGREEMENT_CONTEXT,
        contract_context=CONTRACT_CONTEXT,
        contract_execution_context=CONTRACT_EXECUTION_CONTEXT,
        invoice_context=INVOICE_CONTEXT,
        invoice_creation_context=INVOICE_CREATION_CONTEXT,
        payment_request_context=PAYMENT_REQUEST_CONTEXT,
        payment_request_event_context=PAYMENT_REQUEST_EVENT_CONTEXT,
        payment_confirmation_context=PAYMENT_CONFIRMATION_CONTEXT,
        payment_confirmation_event_context=PAYMENT_CONFIRMATION_EVENT_CONTEXT,
    )

    assert result["event_status"] == "blocked"
    assert result["source_payment_confirmation_review"]["review_status"] == "blocked"
    assert result["recommended_action"] == "resolve_payment_confirmation_event_gaps"