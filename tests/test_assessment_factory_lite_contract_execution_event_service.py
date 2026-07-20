from backend.app.gagf.assessment_factory_lite_contract_execution_event_service import (
    AssessmentFactoryLiteContractExecutionEventService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
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


def build_executed_event():
    return AssessmentFactoryLiteContractExecutionEventService().record_event(
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
    )


def test_assessment_factory_lite_contract_execution_event_service_builds_contract():
    result = build_executed_event()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_contract_execution_event"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["event_stage"] == "contract_execution_event"
    assert result["event_status"] == "contract_executed"
    assert result["contract_execution_event_id"] == "contract-execution-event-001"
    assert result["recorded_at"] == "2026-07-28T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_invoice_creation_review"


def test_assessment_factory_lite_contract_execution_event_service_summarizes_source_review():
    result = build_executed_event()

    assert result["source_contract_execution_review"] == {
        "event_type": "assessment_factory_lite_contract_execution_review",
        "review_stage": "contract_execution_review",
        "review_status": "ready_for_contract_execution",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "contract_review_id": "contract-execution-review-001",
        "prepared_at": "2026-07-27T12:00:00+00:00",
        "recommended_action": "prepare_contract_execution_event",
    }


def test_assessment_factory_lite_contract_execution_event_service_tracks_execution_evidence():
    result = build_executed_event()

    assert result["execution_evidence"] == {
        "contract_execution_confirmed": True,
        "executed_contract_reference": "contract-ref-001",
        "executed_at": "2026-07-28T11:30:00+00:00",
        "execution_method": "electronic_signature",
        "executed_contract_reference_recorded": True,
        "executed_at_recorded": True,
        "execution_method_recorded": True,
        "contract_executed": True,
    }


def test_assessment_factory_lite_contract_execution_event_service_tracks_signature_record():
    result = build_executed_event()

    assert result["signature_record"] == {
        "buyer_signed": True,
        "provider_signed": True,
        "signature_evidence_recorded": True,
        "all_required_signatures_recorded": True,
        "signature_record_is_not_invoice": True,
        "signature_record_is_not_payment": True,
    }


def test_assessment_factory_lite_contract_execution_event_service_tracks_operator_confirmation_without_downstream_authorization():
    result = build_executed_event()

    assert result["operator_confirmation"] == {
        "human_operator_required": True,
        "human_operator_confirmed_execution": True,
        "operator_name": "Andy Sawyer II",
        "operator_notes": ["Contract execution confirmed."],
        "invoice_creation_approved": False,
        "payment_request_approved": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_contract_execution_event_service_builds_checklist_and_score():
    result = build_executed_event()

    assert result["event_checklist"] == {
        "contract_execution_review_ready": True,
        "contract_execution_confirmed": True,
        "executed_contract_reference_recorded": True,
        "executed_at_recorded": True,
        "execution_method_recorded": True,
        "all_required_signatures_recorded": True,
        "human_operator_confirmed_execution": True,
        "signature_record_is_not_invoice": True,
        "signature_record_is_not_payment": True,
        "invoice_not_created": True,
        "payment_not_requested": True,
        "paid_assessment_not_authorized": True,
        "production_onboarding_not_started": True,
    }

    assert result["event_blockers"] == []
    assert result["execution_score"] == {
        "passed": 13,
        "total": 13,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_contract_execution_event_service_preserves_boundaries():
    result = build_executed_event()

    assert result["commercial_boundary"] == {
        "contract_execution_recorded": True,
        "contract_executed": True,
        "invoice_created": False,
        "payment_requested": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_separate_invoice": True,
        "requires_separate_payment_confirmation": True,
        "requires_final_paid_work_authorization": True,
        "requires_separate_production_onboarding": True,
    }

    assert result["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "executed_contract_reference" in result["evidence_boundary"]["allowed_evidence"]
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "contract_execution_event_is_not_invoice": True,
        "contract_execution_event_is_not_payment": True,
        "contract_execution_event_is_not_paid_work_authorization": True,
    }

    assert result["boundary_notices"] == [
        "contract_execution_event_records_contract_execution_only",
        "contract_execution_event_does_not_create_invoice",
        "contract_execution_event_does_not_request_payment",
        "contract_execution_event_does_not_authorize_paid_work",
        "contract_execution_event_does_not_start_production_onboarding",
        "contract_execution_event_requires_human_operator",
    ]


def test_assessment_factory_lite_contract_execution_event_service_includes_audit_next_action_and_message():
    result = build_executed_event()

    assert result["audit_notes"] == [
        "contract_execution_event_built",
        "invoice_not_created",
        "payment_not_requested",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "contract_execution_event_recorded",
    ]

    assert result["next_action"] == {
        "action": "prepare_invoice_creation_review",
        "operator_instruction": (
            "Prepare invoice creation review. Do not request payment, "
            "authorize paid work, or start production onboarding from "
            "this contract execution event."
        ),
        "future_action": "build_invoice_creation_review",
    }

    assert result["operator_message"] == (
        "Contract execution has been recorded. Invoice creation, payment "
        "request, paid work authorization, and production onboarding remain "
        "blocked."
    )


def test_assessment_factory_lite_contract_execution_event_service_handles_pending_states():
    no_confirmation = dict(CONTRACT_EXECUTION_CONTEXT)
    no_confirmation["contract_execution_confirmed"] = False

    result = AssessmentFactoryLiteContractExecutionEventService().record_event(
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
        contract_execution_context=no_confirmation,
    )

    assert result["event_status"] == "pending_contract_execution_confirmation"
    assert "contract_execution_confirmed" in result["event_blockers"]
    assert result["next_action"]["action"] == "confirm_contract_execution"

    no_evidence = dict(CONTRACT_EXECUTION_CONTEXT)
    no_evidence["executed_contract_reference"] = "not_recorded"

    result = AssessmentFactoryLiteContractExecutionEventService().record_event(
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
        contract_execution_context=no_evidence,
    )

    assert result["event_status"] == "pending_execution_evidence"
    assert "executed_contract_reference_recorded" in result["event_blockers"]
    assert result["next_action"]["action"] == "record_execution_evidence"

    no_signature = dict(CONTRACT_EXECUTION_CONTEXT)
    no_signature["buyer_signed"] = False

    result = AssessmentFactoryLiteContractExecutionEventService().record_event(
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
        contract_execution_context=no_signature,
    )

    assert result["event_status"] == "pending_signature_record"
    assert "all_required_signatures_recorded" in result["event_blockers"]
    assert result["next_action"]["action"] == "record_signature_evidence"

    no_operator = dict(CONTRACT_EXECUTION_CONTEXT)
    no_operator["human_operator_confirmed_execution"] = False

    result = AssessmentFactoryLiteContractExecutionEventService().record_event(
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
        contract_execution_context=no_operator,
    )

    assert result["event_status"] == "pending_operator_confirmation"
    assert "human_operator_confirmed_execution" in result["event_blockers"]
    assert result["next_action"]["action"] == "confirm_operator_contract_execution_event"


def test_assessment_factory_lite_contract_execution_event_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLiteContractExecutionEventService().record_event(
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
    )

    assert result["event_status"] == "blocked"
    assert result["source_contract_execution_review"]["review_status"] == "blocked"
    assert result["recommended_action"] == "resolve_contract_execution_event_gaps"