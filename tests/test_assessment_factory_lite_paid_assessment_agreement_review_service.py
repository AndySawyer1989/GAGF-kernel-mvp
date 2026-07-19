from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_paid_assessment_agreement_review_service import (
    AssessmentFactoryLitePaidAssessmentAgreementReviewService,
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


def test_assessment_factory_lite_paid_assessment_agreement_review_service_builds_contract():
    result = build_ready_review()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_paid_assessment_agreement_review"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["review_stage"] == "paid_assessment_agreement_review"
    assert result["review_status"] == "ready_for_agreement_execution_review"
    assert result["agreement_review_id"] == "paid-assessment-agreement-review-001"
    assert result["prepared_at"] == "2026-07-26T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_contract_execution_review"


def test_assessment_factory_lite_paid_assessment_agreement_review_service_summarizes_source_package():
    result = build_ready_review()

    assert result["source_paid_assessment_authorization_package"] == {
        "event_type": "assessment_factory_lite_paid_assessment_authorization_package",
        "package_stage": "paid_assessment_authorization_package",
        "package_status": "ready_for_paid_assessment_authorization",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "authorization_id": "paid-assessment-authorization-package-001",
        "prepared_at": "2026-07-25T12:00:00+00:00",
        "recommended_action": "prepare_paid_assessment_agreement_review",
    }


def test_assessment_factory_lite_paid_assessment_agreement_review_service_tracks_agreement_terms():
    result = build_ready_review()

    assert result["agreement_terms"] == {
        "service_scope_reviewed": True,
        "price_confirmed": True,
        "deliverables_confirmed": True,
        "limitations_confirmed": True,
        "agreement_terms_ready": True,
        "contract_required_before_execution": True,
        "invoice_required_before_payment": True,
        "payment_required_before_paid_work": True,
    }


def test_assessment_factory_lite_paid_assessment_agreement_review_service_tracks_buyer_acknowledgment():
    result = build_ready_review()

    assert result["buyer_acknowledgment"] == {
        "buyer_acknowledged_scope": True,
        "buyer_acknowledged_price": True,
        "buyer_acknowledged_non_binding_review": True,
        "buyer_acknowledgment_ready": True,
        "buyer_acknowledgment_is_not_signature": True,
        "buyer_acknowledgment_is_not_payment": True,
    }


def test_assessment_factory_lite_paid_assessment_agreement_review_service_tracks_operator_review_without_execution():
    result = build_ready_review()

    assert result["operator_review"] == {
        "human_operator_required": True,
        "agreement_reviewed_by_operator": True,
        "operator_review_status": "agreement_reviewed",
        "contract_execution_approved": False,
        "invoice_creation_approved": False,
        "payment_request_approved": False,
        "paid_assessment_authorized": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_paid_assessment_agreement_review_service_builds_checklist_and_score():
    result = build_ready_review()

    assert result["review_checklist"] == {
        "authorization_package_ready": True,
        "agreement_terms_ready": True,
        "buyer_acknowledgment_ready": True,
        "buyer_acknowledgment_is_not_signature": True,
        "buyer_acknowledgment_is_not_payment": True,
        "agreement_reviewed_by_operator": True,
        "contract_not_executed": True,
        "invoice_not_created": True,
        "payment_not_requested": True,
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


def test_assessment_factory_lite_paid_assessment_agreement_review_service_preserves_boundaries():
    result = build_ready_review()

    assert result["commercial_boundary"] == {
        "agreement_review_ready": True,
        "contract_created": False,
        "contract_executed": False,
        "invoice_created": False,
        "payment_requested": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "requires_separate_contract_execution": True,
        "requires_separate_invoice": True,
        "requires_separate_payment_confirmation": True,
        "requires_final_paid_work_authorization": True,
    }

    assert result["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "agreement_review_is_not_execution": True,
    }

    assert result["boundary_notices"] == [
        "paid_assessment_agreement_review_does_not_execute_contract",
        "paid_assessment_agreement_review_does_not_create_invoice",
        "paid_assessment_agreement_review_does_not_request_payment",
        "paid_assessment_agreement_review_does_not_authorize_paid_work",
        "paid_assessment_agreement_review_does_not_start_production_onboarding",
        "paid_assessment_agreement_review_requires_human_operator",
    ]


def test_assessment_factory_lite_paid_assessment_agreement_review_service_includes_audit_next_action_and_message():
    result = build_ready_review()

    assert result["audit_notes"] == [
        "paid_assessment_agreement_review_built",
        "agreement_review_is_not_contract_execution",
        "invoice_not_created",
        "payment_not_requested",
        "paid_assessment_not_authorized",
        "production_onboarding_not_started",
        "paid_assessment_agreement_review_ready",
    ]

    assert result["next_action"] == {
        "action": "prepare_contract_execution_review",
        "operator_instruction": (
            "Prepare contract execution review. Do not execute a contract, "
            "create an invoice, request payment, authorize paid work, or "
            "start production onboarding from this agreement review."
        ),
        "future_action": "build_contract_execution_review",
    }

    assert result["operator_message"] == (
        "Paid assessment agreement review is ready for contract execution "
        "review. Contract execution, invoice creation, payment request, "
        "paid work authorization, and production onboarding remain blocked."
    )


def test_assessment_factory_lite_paid_assessment_agreement_review_service_handles_pending_states():
    no_terms = dict(AGREEMENT_CONTEXT)
    no_terms["price_confirmed"] = False

    result = AssessmentFactoryLitePaidAssessmentAgreementReviewService().build_review(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=no_terms,
    )

    assert result["review_status"] == "pending_agreement_terms"
    assert "agreement_terms_ready" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_agreement_terms_review"

    no_buyer = dict(AGREEMENT_CONTEXT)
    no_buyer["buyer_acknowledged_scope"] = False

    result = AssessmentFactoryLitePaidAssessmentAgreementReviewService().build_review(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=no_buyer,
    )

    assert result["review_status"] == "pending_buyer_acknowledgment"
    assert "buyer_acknowledgment_ready" in result["review_blockers"]
    assert result["next_action"]["action"] == "confirm_buyer_agreement_acknowledgment"

    no_operator = dict(AGREEMENT_CONTEXT)
    no_operator["agreement_reviewed_by_operator"] = False

    result = AssessmentFactoryLitePaidAssessmentAgreementReviewService().build_review(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=no_operator,
    )

    assert result["review_status"] == "pending_operator_review"
    assert "agreement_reviewed_by_operator" in result["review_blockers"]
    assert result["next_action"]["action"] == "complete_operator_agreement_review"


def test_assessment_factory_lite_paid_assessment_agreement_review_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLitePaidAssessmentAgreementReviewService().build_review(
        export=export,
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_record_context=SCOPE_CALL_RECORD_CONTEXT,
        authorization_context=AUTHORIZATION_CONTEXT,
        agreement_context=AGREEMENT_CONTEXT,
    )

    assert result["review_status"] == "blocked"
    assert result["source_paid_assessment_authorization_package"]["package_status"] == "blocked"
    assert result["recommended_action"] == "resolve_paid_assessment_agreement_review_gaps"