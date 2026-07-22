from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PAYMENT_CONFIRMATION_REVIEW.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_payment_confirmation_review_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_payment_confirmation_review_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-320 — Assessment Factory Lite Payment Confirmation Review Documentation" in content
    assert "AssessmentFactoryLitePaymentConfirmationReviewService" in content
    assert "backend/app/gagf/assessment_factory_lite_payment_confirmation_review_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/payment-confirmation-review" in content
    assert "assessment_factory_lite_payment_confirmation_review" in content
    assert "payment_confirmation_review" in content
    assert "review_status" in content
    assert "payment_confirmation_review_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_payment_request_event" in content
    assert "payment_request_event" in content
    assert "payment_requested" in content
    assert "prepare_payment_confirmation_review" in content

    assert "payment_request_event" in content
    assert "payment_request_review" in content
    assert "invoice_creation_event" in content
    assert "invoice_creation_review" in content
    assert "contract_execution_event" in content
    assert "contract_execution_review" in content
    assert "paid_assessment_agreement_review" in content
    assert "paid_assessment_authorization_package" in content
    assert "scope_call_event_record" in content
    assert "scope_call_event_package" in content
    assert "scope_call_agenda_message_event_record" in content
    assert "scope_call_agenda_message" in content
    assert "scope_call_package" in content
    assert "follow_up_event_record" in content
    assert "follow_up_message" in content
    assert "tracker" in content
    assert "delivery_package" in content
    assert "export_package" in content
    assert "operator_approval" in content
    assert "payment_request_event_context" in content
    assert "payment_confirmation_context" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_payment_confirmation_context_fields():
    content = read_doc()

    assert "payment_receipt_available" in content
    assert "payment_reference_available" in content
    assert "received_amount_reviewed" in content
    assert "received_at_reviewed" in content
    assert "amount_matches_request" in content
    assert "invoice_reference_matches" in content
    assert "payment_method_reviewed" in content
    assert "payment_confirmation_reviewed_by_operator" in content
    assert "operator_review_status" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_statuses():
    content = read_doc()

    assert "ready_for_payment_confirmation" in content
    assert "pending_payment_request_event" in content
    assert "pending_payment_evidence_review" in content
    assert "pending_reconciliation_review" in content
    assert "pending_operator_review" in content
    assert "pending_payment_confirmation_review" in content
    assert "blocked" in content

    assert "payment evidence is ready" in content
    assert "reconciliation is complete" in content
    assert "operator payment confirmation review exists" in content
    assert "source payment request event is not payment_requested" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_ready_conditions():
    content = read_doc()

    assert "payment_request_event_recorded is true" in content
    assert "payment_evidence_ready is true" in content
    assert "payment_evidence_review_is_not_payment_confirmation is true" in content
    assert "payment_evidence_review_is_not_paid_work_authorization is true" in content
    assert "reconciliation_ready is true" in content
    assert "reconciliation_is_not_payment_confirmation is true" in content
    assert "reconciliation_is_not_paid_work_authorization is true" in content
    assert "payment_confirmation_reviewed_by_operator is true" in content
    assert "payment_not_confirmed is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_output_objects():
    content = read_doc()

    assert "source_payment_request_event" in content
    assert "payment_evidence_review" in content
    assert "reconciliation_review" in content
    assert "operator_review" in content
    assert "review_checklist" in content
    assert "review_blockers" in content
    assert "review_score" in content
    assert "payment_request_record" in content
    assert "payment_request_delivery_record" in content
    assert "payment_request_details" in content
    assert "buyer_notice_readiness" in content
    assert "invoice_record" in content
    assert "invoice_delivery_record" in content
    assert "invoice_details_review" in content
    assert "billing_readiness" in content
    assert "execution_evidence" in content
    assert "signature_record" in content
    assert "contract_document_review" in content
    assert "agreement_terms" in content
    assert "buyer_request" in content
    assert "commercial_review" in content
    assert "evidence_review" in content
    assert "human_authorization" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_evidence_reconciliation_and_operator_objects():
    content = read_doc()

    assert "payment_evidence_review_is_not_payment_confirmation: true" in content
    assert "payment_evidence_review_is_not_paid_work_authorization: true" in content
    assert "Payment evidence review does not confirm payment." in content
    assert "Payment evidence review does not authorize paid work." in content

    assert "reconciliation_is_not_payment_confirmation: true" in content
    assert "reconciliation_is_not_paid_work_authorization: true" in content
    assert "Reconciliation review does not confirm payment." in content
    assert "Reconciliation review does not authorize paid work." in content

    assert "human_operator_required: true" in content
    assert "payment_confirmed: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator review approves payment confirmation readiness only." in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_score_and_boundaries():
    content = read_doc()

    assert "passed: 11" in content
    assert "total: 11" in content
    assert "score: 1.0" in content
    assert "ready: true" in content
    assert "deterministic review_status remains authoritative" in content

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content
    assert "Payment Confirmation Boundary" in content

    assert "payment_confirmation_ready: true" in content
    assert "payment_confirmed: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_authorized: false" in content
    assert "requires_actual_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "requires_separate_production_onboarding: true" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "payment_request_reference" in content
    assert "payment_request_delivery_reference" in content
    assert "payment_receipt_reference" in content
    assert "received_amount_review_notes" in content
    assert "payment_reconciliation_notes" in content
    assert "non_sensitive_workflow_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "payment_confirmation_review_does_not_confirm_payment" in content
    assert "payment_confirmation_review_does_not_authorize_paid_work" in content
    assert "payment_confirmation_review_does_not_start_production_onboarding" in content
    assert "payment_confirmation_review_requires_human_operator" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "payment_confirmation_review_built" in content
    assert "payment_not_confirmed" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "payment_confirmation_review_ready" in content
    assert "payment_confirmation_review_pending_payment_request_event" in content
    assert "payment_confirmation_review_pending_payment_evidence" in content
    assert "payment_confirmation_review_pending_reconciliation" in content
    assert "payment_confirmation_review_pending_operator_review" in content
    assert "payment_confirmation_review_pending_review" in content
    assert "payment_confirmation_review_blocked" in content

    assert "prepare_payment_confirmation_event" in content
    assert "build_payment_confirmation_event" in content
    assert "complete_payment_request_event" in content
    assert "complete_payment_evidence_review" in content
    assert "complete_payment_reconciliation_review" in content
    assert "complete_operator_payment_confirmation_review" in content
    assert "resolve_payment_confirmation_review_gaps" in content
    assert "rerun_payment_confirmation_review" in content


def test_assessment_factory_lite_payment_confirmation_review_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Payment Request Evidence → Payment Evidence Review → Reconciliation Review → Human Review → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for payment-confirmation readiness." in content
    assert "without collapsing payment confirmation, paid-work authorization, and onboarding into one unsafe step" in content
    assert "final review layer before the payment confirmation event" in content
    assert "US-321 — Assessment Factory Lite Payment Confirmation Review Release Marker" in content