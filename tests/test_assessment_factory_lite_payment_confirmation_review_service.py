from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_payment_confirmation_review_service import (
    AssessmentFactoryLitePaymentConfirmationReviewService,
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


def build_ready_review():
    return AssessmentFactoryLitePaymentConfirmationReviewService().build_review(
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
    )


def test_assessment_factory_lite_payment_confirmation_review_service_builds_contract():
    result = build_ready_review()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_payment_confirmation_review"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["review_stage"] == "payment_confirmation_review"
    assert result["review_status"] == "ready_for_payment_confirmation"
    assert result["payment_confirmation_review_id"] == "payment-confirmation-review-001"
    assert result["prepared_at"] == "2026-08-02T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_payment_confirmation_event"


def test_assessment_factory_lite_payment_confirmation_review_service_summarizes_source_event():
    result = build_ready_review()

    assert result["source_payment_request_event"] == {
        "event_type": "assessment_factory_lite_payment_request_event",
        "event_stage": "payment_request_event",
        "event_status": "payment_requested",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "payment_request_event_id": "payment-request-event-001",
        "recorded_at": "2026-08-01T12:00:00+00:00",
        "recommended_action": "prepare_payment_confirmation_review",
    }


def test_assessment_factory_lite_payment_confirmation_review_service_tracks_payment_evidence_review():
    result = build_ready_review()

    assert result["payment_evidence_review"] == {
        "payment_receipt_available": True,
        "payment_reference_available": True,
        "received_amount_reviewed": True,
        "received_at_reviewed": True,
        "payment_evidence_ready": True,
        "payment_evidence_review_is_not_payment_confirmation": True,
        "payment_evidence_review_is_not_paid_work_authorization": True,
    }


def test_assessment_factory_lite_payment_confirmation_review_service_tracks_reconciliation_review():
    result = build_ready_review()

    assert result["reconciliation_review"] == {
        "amount_matches_request": True,
        "invoice_reference_matches": True,
        "payment_method_reviewed": True,
        "reconciliation_ready": True,
        "reconciliation_is_not_payment_confirmation": True,
        "reconciliation_is_not_paid_work_authorization": True,
    }


def test_assessment_factory_lite_payment_confirmation_review_service_tracks_operator_review_without_confirmation_or_authorization():
    result = build_ready_review()

    assert result["operator_review"] == {
        "human_operator_required": True,
        "payment_confirmation_reviewed_by_operator": True,
        "operator_review_status": "payment_confirmation_reviewed",
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_payment_confirmation_review_service_builds_checklist_and_score():
    result = build_ready_review()

    assert result["review_checklist"] == {
        "payment_request_event_recorded": True,
        "payment_evidence_ready": True,
        "payment_evidence_review_is_not_payment_confirmation": True,
        "payment_evidence_review_is_not_paid_work_authorization": True,
        "reconciliation_ready": True,
        "reconciliation_is_not_payment_confirmation": True,
        "reconciliation_is_not_paid_work_authorization": True,
        "payment_confirmation_reviewed_by_operator": True,
        "payment_not_confirmed": True,
        "paid_assessment_not_authorized": True,
        "production_onboarding_not_started": True,
    }

    assert result["review_blockers"] == []
    assert result["review_score"] == {
        "passed": 11,
        "total": 11,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_payment_confirmation_review_service_preserves_boundaries():
    result = build_ready_review()

    assert result["commercial_boundary"] == {
        "payment_confirmation_ready": True,
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_actual_payment_confirmation": True,
        "requires_final_paid_work_authorization": True,
        "requires_separate_production_onboarding": True,
    }

    assert result["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "payment_receipt_reference" in result["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "payment_confirmation_review_is_not_payment_confirmation": True,
        "payment_confirmation_review_is_not_paid_work_authorization": True,
    }

    assert result["boundary_notices"] == [
        "payment_confirmation_review_does_not_confirm_payment",
        "payment_confirmation_review_does_not_authorize_paid_work",
        "payment_confirmation_review_does_not_start_production_onboarding",
        "payment_confirmation_review_requires_human_operator",
    ]


def test_assessment_factory_lite_payment_confirmation_review_service_includes_audit_next_action_and_message():
    result = build_ready_review()

    assert result["audit_notes"] == [
        "payment_confirmation_review_built",
        "payment_not_confirmed",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "payment_confirmation_review_ready",
    ]

    assert result["next_action"] == {
        "action": "prepare_payment_confirmation_event",
        "operator_instruction": (
            "Prepare payment confirmation event. Do not authorize paid "
            "work or start production onboarding from this review."
        ),
        "future_action": "build_payment_confirmation_event",
    }

    assert result["operator_message"] == (
        "Payment confirmation review is ready for payment confirmation "
        "event. Paid work authorization and production onboarding remain "
        "blocked."
    )


def test_assessment_factory_lite_payment_confirmation_review_service_handles_pending_states():
    no_evidence = dict(PAYMENT_CONFIRMATION_CONTEXT)
    no_evidence["payment_receipt_available"] = False

    result = AssessmentFactoryLitePaymentConfirmationReviewService().build_review(
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
        payment_confirmation_context=no_evidence,
    )

    assert result["review_status"] == "pending_payment_evidence_review"
    assert "payment_evidence_ready" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_payment_evidence_review"

    no_reconciliation = dict(PAYMENT_CONFIRMATION_CONTEXT)
    no_reconciliation["amount_matches_request"] = False

    result = AssessmentFactoryLitePaymentConfirmationReviewService().build_review(
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
        payment_confirmation_context=no_reconciliation,
    )

    assert result["review_status"] == "pending_reconciliation_review"
    assert "reconciliation_ready" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_payment_reconciliation_review"

    no_operator = dict(PAYMENT_CONFIRMATION_CONTEXT)
    no_operator["payment_confirmation_reviewed_by_operator"] = False

    result = AssessmentFactoryLitePaymentConfirmationReviewService().build_review(
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
        payment_confirmation_context=no_operator,
    )

    assert result["review_status"] == "pending_operator_review"
    assert "payment_confirmation_reviewed_by_operator" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_operator_payment_confirmation_review"


def test_assessment_factory_lite_payment_confirmation_review_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLitePaymentConfirmationReviewService().build_review(
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
    )

    assert result["review_status"] == "blocked"
    assert result["source_payment_request_event"]["event_status"] == "blocked"
    assert result["recommended_action"] == "resolve_payment_confirmation_review_gaps"