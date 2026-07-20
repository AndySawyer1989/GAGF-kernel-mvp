from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_invoice_creation_review_service import (
    AssessmentFactoryLiteInvoiceCreationReviewService,
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


def test_assessment_factory_lite_invoice_creation_review_service_builds_contract():
    result = build_ready_review()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_invoice_creation_review"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["review_stage"] == "invoice_creation_review"
    assert result["review_status"] == "ready_for_invoice_creation"
    assert result["invoice_review_id"] == "invoice-creation-review-001"
    assert result["prepared_at"] == "2026-07-29T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_invoice_creation_event"


def test_assessment_factory_lite_invoice_creation_review_service_summarizes_source_event():
    result = build_ready_review()

    assert result["source_contract_execution_event"] == {
        "event_type": "assessment_factory_lite_contract_execution_event",
        "event_stage": "contract_execution_event",
        "event_status": "contract_executed",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "contract_execution_event_id": "contract-execution-event-001",
        "recorded_at": "2026-07-28T12:00:00+00:00",
        "recommended_action": "prepare_invoice_creation_review",
    }


def test_assessment_factory_lite_invoice_creation_review_service_tracks_invoice_details():
    result = build_ready_review()

    assert result["invoice_details_review"] == {
        "invoice_amount_confirmed": True,
        "invoice_recipient_confirmed": True,
        "invoice_description_confirmed": True,
        "invoice_terms_confirmed": True,
        "invoice_details_ready": True,
        "invoice_creation_required_before_payment_request": True,
        "payment_confirmation_required_before_paid_work": True,
    }


def test_assessment_factory_lite_invoice_creation_review_service_tracks_billing_readiness():
    result = build_ready_review()

    assert result["billing_readiness"] == {
        "billing_system_ready": True,
        "tax_or_business_details_checked": True,
        "payment_instructions_reviewed": True,
        "billing_ready": True,
        "billing_readiness_is_not_payment_request": True,
        "billing_readiness_is_not_paid_work_authorization": True,
    }


def test_assessment_factory_lite_invoice_creation_review_service_tracks_operator_review_without_invoice_creation():
    result = build_ready_review()

    assert result["operator_review"] == {
        "human_operator_required": True,
        "invoice_creation_reviewed_by_operator": True,
        "operator_review_status": "invoice_creation_reviewed",
        "invoice_created": False,
        "payment_request_approved": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_invoice_creation_review_service_builds_checklist_and_score():
    result = build_ready_review()

    assert result["review_checklist"] == {
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

    assert result["review_blockers"] == []
    assert result["review_score"] == {
        "passed": 10,
        "total": 10,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_invoice_creation_review_service_preserves_boundaries():
    result = build_ready_review()

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

    assert result["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "invoice_review_notes" in result["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

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

    assert result["boundary_notices"] == [
        "invoice_creation_review_does_not_create_invoice",
        "invoice_creation_review_does_not_request_payment",
        "invoice_creation_review_does_not_authorize_paid_work",
        "invoice_creation_review_does_not_start_production_onboarding",
        "invoice_creation_review_requires_human_operator",
    ]


def test_assessment_factory_lite_invoice_creation_review_service_includes_audit_next_action_and_message():
    result = build_ready_review()

    assert result["audit_notes"] == [
        "invoice_creation_review_built",
        "invoice_not_created",
        "payment_not_requested",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "invoice_creation_review_ready",
    ]

    assert result["next_action"] == {
        "action": "prepare_invoice_creation_event",
        "operator_instruction": (
            "Prepare invoice creation event. Do not request payment, "
            "authorize paid work, or start production onboarding from "
            "this review."
        ),
        "future_action": "build_invoice_creation_event",
    }

    assert result["operator_message"] == (
        "Invoice creation review is ready for invoice creation event. "
        "Payment request, paid work authorization, and production "
        "onboarding remain blocked."
    )


def test_assessment_factory_lite_invoice_creation_review_service_handles_pending_states():
    no_details = dict(INVOICE_CONTEXT)
    no_details["invoice_amount_confirmed"] = False

    result = AssessmentFactoryLiteInvoiceCreationReviewService().build_review(
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
        invoice_context=no_details,
    )

    assert result["review_status"] == "pending_invoice_details_review"
    assert "invoice_details_ready" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_invoice_details_review"

    no_billing = dict(INVOICE_CONTEXT)
    no_billing["billing_system_ready"] = False

    result = AssessmentFactoryLiteInvoiceCreationReviewService().build_review(
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
        invoice_context=no_billing,
    )

    assert result["review_status"] == "pending_billing_readiness"
    assert "billing_ready" in result["review_blockers"]
    assert result["next_action"]["action"] == "confirm_billing_readiness"

    no_operator = dict(INVOICE_CONTEXT)
    no_operator["invoice_creation_reviewed_by_operator"] = False

    result = AssessmentFactoryLiteInvoiceCreationReviewService().build_review(
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
        invoice_context=no_operator,
    )

    assert result["review_status"] == "pending_operator_review"
    assert "invoice_creation_reviewed_by_operator" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_operator_invoice_creation_review"


def test_assessment_factory_lite_invoice_creation_review_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLiteInvoiceCreationReviewService().build_review(
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
    )

    assert result["review_status"] == "blocked"
    assert result["source_contract_execution_event"]["event_status"] == "blocked"
    assert result["recommended_action"] == "resolve_invoice_creation_review_gaps"