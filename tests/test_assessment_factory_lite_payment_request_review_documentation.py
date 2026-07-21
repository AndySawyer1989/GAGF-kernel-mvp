from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PAYMENT_REQUEST_REVIEW.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_payment_request_review_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_payment_request_review_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-312 — Assessment Factory Lite Payment Request Review Documentation" in content
    assert "AssessmentFactoryLitePaymentRequestReviewService" in content
    assert "backend/app/gagf/assessment_factory_lite_payment_request_review_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_payment_request_review_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/payment-request-review" in content
    assert "assessment_factory_lite_payment_request_review" in content
    assert "payment_request_review" in content
    assert "review_status" in content
    assert "payment_request_review_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_payment_request_review_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_invoice_creation_event" in content
    assert "invoice_creation_event" in content
    assert "invoice_created" in content
    assert "prepare_payment_request_review" in content

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
    assert "invoice_creation_context" in content
    assert "payment_request_context" in content


def test_assessment_factory_lite_payment_request_review_doc_names_payment_request_context_fields():
    content = read_doc()

    assert "payment_amount_confirmed" in content
    assert "invoice_reference_confirmed" in content
    assert "payment_due_date_confirmed" in content
    assert "payment_request_language_reviewed" in content
    assert "buyer_notice_prepared" in content
    assert "buyer_notice_channel_confirmed" in content
    assert "payment_instructions_included" in content
    assert "payment_request_reviewed_by_operator" in content
    assert "operator_review_status" in content


def test_assessment_factory_lite_payment_request_review_doc_names_statuses():
    content = read_doc()

    assert "ready_for_payment_request" in content
    assert "pending_invoice_creation_event" in content
    assert "pending_payment_request_details_review" in content
    assert "pending_buyer_notice_readiness" in content
    assert "pending_operator_review" in content
    assert "pending_payment_request_review" in content
    assert "blocked" in content

    assert "payment request details are ready" in content
    assert "buyer notice readiness is complete" in content
    assert "operator payment request review exists" in content
    assert "source invoice creation event is not invoice_created" in content


def test_assessment_factory_lite_payment_request_review_doc_names_ready_conditions():
    content = read_doc()

    assert "invoice_creation_event_recorded is true" in content
    assert "payment_request_details_ready is true" in content
    assert "buyer_notice_ready is true" in content
    assert "buyer_notice_is_not_payment_confirmation is true" in content
    assert "buyer_notice_is_not_paid_work_authorization is true" in content
    assert "payment_request_reviewed_by_operator is true" in content
    assert "payment_not_requested is true" in content
    assert "payment_not_confirmed is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_payment_request_review_doc_names_output_objects():
    content = read_doc()

    assert "source_invoice_creation_event" in content
    assert "payment_request_details" in content
    assert "buyer_notice_readiness" in content
    assert "operator_review" in content
    assert "review_checklist" in content
    assert "review_blockers" in content
    assert "review_score" in content
    assert "invoice_record" in content
    assert "delivery_record" in content
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


def test_assessment_factory_lite_payment_request_review_doc_names_payment_notice_and_operator_objects():
    content = read_doc()

    assert "payment_request_required_before_payment_confirmation: true" in content
    assert "payment_confirmation_required_before_paid_work: true" in content
    assert "Payment request details readiness does not request payment." in content
    assert "Payment request details readiness does not confirm payment." in content
    assert "Payment request details readiness does not authorize paid work." in content

    assert "buyer_notice_is_not_payment_confirmation: true" in content
    assert "buyer_notice_is_not_paid_work_authorization: true" in content
    assert "Buyer notice readiness is not payment confirmation." in content
    assert "Buyer notice readiness is not paid-work authorization." in content

    assert "human_operator_required: true" in content
    assert "payment_requested: false" in content
    assert "payment_confirmed: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator review approves payment request readiness only." in content


def test_assessment_factory_lite_payment_request_review_doc_names_score_and_boundaries():
    content = read_doc()

    assert "passed: 10" in content
    assert "total: 10" in content
    assert "score: 1.0" in content
    assert "ready: true" in content
    assert "deterministic review_status remains authoritative" in content

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content
    assert "Payment Request Boundary" in content

    assert "payment_request_ready: true" in content
    assert "requires_actual_payment_request: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "requires_separate_production_onboarding: true" in content


def test_assessment_factory_lite_payment_request_review_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "invoice_reference" in content
    assert "invoice_delivery_reference" in content
    assert "invoice_review_notes" in content
    assert "billing_readiness_notes" in content
    assert "payment_request_review_notes" in content
    assert "buyer_notice_notes" in content
    assert "non_sensitive_workflow_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "payment_request_review_does_not_request_payment" in content
    assert "payment_request_review_does_not_confirm_payment" in content
    assert "payment_request_review_does_not_authorize_paid_work" in content
    assert "payment_request_review_does_not_start_production_onboarding" in content
    assert "payment_request_review_requires_human_operator" in content


def test_assessment_factory_lite_payment_request_review_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "payment_request_review_built" in content
    assert "payment_not_requested" in content
    assert "payment_not_confirmed" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "payment_request_review_ready" in content
    assert "payment_request_review_pending_invoice_creation_event" in content
    assert "payment_request_review_pending_payment_request_details" in content
    assert "payment_request_review_pending_buyer_notice_readiness" in content
    assert "payment_request_review_pending_operator_review" in content
    assert "payment_request_review_pending_review" in content
    assert "payment_request_review_blocked" in content

    assert "prepare_payment_request_event" in content
    assert "build_payment_request_event" in content
    assert "complete_invoice_creation_event" in content
    assert "complete_payment_request_details_review" in content
    assert "confirm_buyer_notice_readiness" in content
    assert "complete_operator_payment_request_review" in content
    assert "resolve_payment_request_review_gaps" in content
    assert "rerun_payment_request_review" in content


def test_assessment_factory_lite_payment_request_review_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Invoice Creation Evidence → Payment Request Detail Review → Buyer Notice Readiness → Human Review → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for payment-request readiness." in content
    assert "without collapsing payment request, payment confirmation, paid-work authorization, and onboarding into one unsafe step" in content
    assert "final review layer before the payment request event" in content
    assert "US-313 — Assessment Factory Lite Payment Request Review Release Marker" in content