from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_invoice_creation_event_service import (
    AssessmentFactoryLiteInvoiceCreationEventService,
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


def build_created_event():
    return AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
    )


def test_assessment_factory_lite_invoice_creation_event_service_builds_contract():
    result = build_created_event()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_invoice_creation_event"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["event_stage"] == "invoice_creation_event"
    assert result["event_status"] == "invoice_created"
    assert result["invoice_creation_event_id"] == "invoice-creation-event-001"
    assert result["recorded_at"] == "2026-07-30T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_payment_request_review"


def test_assessment_factory_lite_invoice_creation_event_service_summarizes_source_review():
    result = build_created_event()

    assert result["source_invoice_creation_review"] == {
        "event_type": "assessment_factory_lite_invoice_creation_review",
        "review_stage": "invoice_creation_review",
        "review_status": "ready_for_invoice_creation",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "invoice_review_id": "invoice-creation-review-001",
        "prepared_at": "2026-07-29T12:00:00+00:00",
        "recommended_action": "prepare_invoice_creation_event",
    }


def test_assessment_factory_lite_invoice_creation_event_service_tracks_invoice_record():
    result = build_created_event()

    assert result["invoice_record"] == {
        "invoice_created": True,
        "invoice_reference": "invoice-ref-001",
        "invoice_created_at": "2026-07-30T11:45:00+00:00",
        "invoice_amount": "2500.00",
        "invoice_reference_recorded": True,
        "invoice_created_at_recorded": True,
        "invoice_amount_recorded": True,
        "invoice_record_is_not_payment_request": True,
        "invoice_record_is_not_payment_confirmation": True,
        "invoice_record_is_not_paid_work_authorization": True,
    }


def test_assessment_factory_lite_invoice_creation_event_service_tracks_delivery_record():
    result = build_created_event()

    assert result["delivery_record"] == {
        "invoice_delivered_to_buyer": True,
        "delivery_channel": "manual_email",
        "delivery_reference": "email-thread-001",
        "delivery_channel_recorded": True,
        "delivery_reference_recorded": True,
        "invoice_delivery_is_not_payment_request": True,
    }


def test_assessment_factory_lite_invoice_creation_event_service_tracks_operator_confirmation_without_payment_or_work_authorization():
    result = build_created_event()

    assert result["operator_confirmation"] == {
        "human_operator_required": True,
        "human_operator_confirmed_invoice_creation": True,
        "operator_name": "Andy Sawyer II",
        "operator_notes": ["Invoice creation confirmed."],
        "payment_requested": False,
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_invoice_creation_event_service_builds_checklist_and_score():
    result = build_created_event()

    assert result["event_checklist"] == {
        "invoice_creation_review_ready": True,
        "invoice_created": True,
        "invoice_reference_recorded": True,
        "invoice_created_at_recorded": True,
        "invoice_amount_recorded": True,
        "invoice_record_is_not_payment_request": True,
        "invoice_record_is_not_payment_confirmation": True,
        "invoice_record_is_not_paid_work_authorization": True,
        "invoice_delivered_to_buyer": True,
        "delivery_channel_recorded": True,
        "delivery_reference_recorded": True,
        "invoice_delivery_is_not_payment_request": True,
        "human_operator_confirmed_invoice_creation": True,
        "payment_not_requested": True,
        "payment_not_confirmed": True,
        "paid_assessment_not_authorized": True,
        "production_onboarding_not_started": True,
    }

    assert result["event_blockers"] == []
    assert result["event_score"] == {
        "passed": 17,
        "total": 17,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_invoice_creation_event_service_preserves_boundaries():
    result = build_created_event()

    assert result["commercial_boundary"] == {
        "invoice_creation_recorded": True,
        "invoice_created": True,
        "payment_requested": False,
        "payment_confirmed": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_separate_payment_request": True,
        "requires_separate_payment_confirmation": True,
        "requires_final_paid_work_authorization": True,
        "requires_separate_production_onboarding": True,
    }

    assert result["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "invoice_reference" in result["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "invoice_creation_event_is_not_payment_request": True,
        "invoice_creation_event_is_not_payment_confirmation": True,
        "invoice_creation_event_is_not_paid_work_authorization": True,
    }

    assert result["boundary_notices"] == [
        "invoice_creation_event_records_invoice_creation_only",
        "invoice_creation_event_does_not_request_payment",
        "invoice_creation_event_does_not_confirm_payment",
        "invoice_creation_event_does_not_authorize_paid_work",
        "invoice_creation_event_does_not_start_production_onboarding",
        "invoice_creation_event_requires_human_operator",
    ]


def test_assessment_factory_lite_invoice_creation_event_service_includes_audit_next_action_and_message():
    result = build_created_event()

    assert result["audit_notes"] == [
        "invoice_creation_event_built",
        "payment_not_requested",
        "payment_not_confirmed",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "invoice_creation_event_recorded",
    ]

    assert result["next_action"] == {
        "action": "prepare_payment_request_review",
        "operator_instruction": (
            "Prepare payment request review. Do not confirm payment, "
            "authorize paid work, or start production onboarding from "
            "this invoice creation event."
        ),
        "future_action": "build_payment_request_review",
    }

    assert result["operator_message"] == (
        "Invoice creation has been recorded. Payment request, payment "
        "confirmation, paid work authorization, and production onboarding "
        "remain blocked."
    )


def test_assessment_factory_lite_invoice_creation_event_service_handles_pending_states():
    no_creation = dict(INVOICE_CREATION_CONTEXT)
    no_creation["invoice_created"] = False

    result = AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
        invoice_creation_context=no_creation,
    )

    assert result["event_status"] == "pending_invoice_creation_confirmation"
    assert "invoice_created" in result["event_blockers"]
    assert result["next_action"]["action"] == "confirm_invoice_creation"

    no_record = dict(INVOICE_CREATION_CONTEXT)
    no_record["invoice_reference"] = "not_recorded"

    result = AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
        invoice_creation_context=no_record,
    )

    assert result["event_status"] == "pending_invoice_record"
    assert "invoice_reference_recorded" in result["event_blockers"]
    assert result["next_action"]["action"] == "record_invoice_reference"

    no_delivery = dict(INVOICE_CREATION_CONTEXT)
    no_delivery["invoice_delivered_to_buyer"] = False

    result = AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
        invoice_creation_context=no_delivery,
    )

    assert result["event_status"] == "pending_invoice_delivery"
    assert "invoice_delivered_to_buyer" in result["event_blockers"]
    assert result["next_action"]["action"] == "record_invoice_delivery"

    no_operator = dict(INVOICE_CREATION_CONTEXT)
    no_operator["human_operator_confirmed_invoice_creation"] = False

    result = AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
        invoice_creation_context=no_operator,
    )

    assert result["event_status"] == "pending_operator_confirmation"
    assert "human_operator_confirmed_invoice_creation" in result["event_blockers"]
    assert result["next_action"]["action"] == "confirm_operator_invoice_creation_event"


def test_assessment_factory_lite_invoice_creation_event_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
    )

    assert result["event_status"] == "blocked"
    assert result["source_invoice_creation_review"]["review_status"] == "blocked"
    assert result["recommended_action"] == "resolve_invoice_creation_event_gaps"