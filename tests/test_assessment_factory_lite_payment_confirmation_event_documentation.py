from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PAYMENT_CONFIRMATION_EVENT.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_payment_confirmation_event_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_payment_confirmation_event_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-324 — Assessment Factory Lite Payment Confirmation Event Documentation" in content
    assert "AssessmentFactoryLitePaymentConfirmationEventService" in content
    assert "backend/app/gagf/assessment_factory_lite_payment_confirmation_event_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/payment-confirmation-event" in content
    assert "assessment_factory_lite_payment_confirmation_event" in content
    assert "payment_confirmation_event" in content
    assert "event_status" in content
    assert "payment_confirmation_event_id" in content
    assert "recorded_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_payment_confirmation_review" in content
    assert "payment_confirmation_review" in content
    assert "ready_for_payment_confirmation" in content
    assert "prepare_payment_confirmation_event" in content

    assert "payment_confirmation_review" in content
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
    assert "payment_confirmation_context" in content
    assert "payment_confirmation_event_context" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_event_context_fields():
    content = read_doc()

    assert "payment_confirmed" in content
    assert "payment_confirmation_reference" in content
    assert "payment_confirmed_at" in content
    assert "confirmed_amount" in content
    assert "amount_reconciled" in content
    assert "invoice_reference_reconciled" in content
    assert "payment_method_recorded" in content
    assert "human_operator_confirmed_payment" in content
    assert "operator_name" in content
    assert "operator_notes" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_statuses():
    content = read_doc()

    assert "payment_confirmed" in content
    assert "pending_payment_confirmation_review" in content
    assert "pending_payment_confirmation" in content
    assert "pending_payment_confirmation_record" in content
    assert "pending_reconciliation_record" in content
    assert "pending_operator_confirmation" in content
    assert "pending_payment_confirmation_event_review" in content
    assert "blocked" in content

    assert "payment confirmation review is ready" in content
    assert "payment confirmation reference is recorded" in content
    assert "reconciliation record is complete" in content
    assert "human operator confirmation exists" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_confirmed_conditions():
    content = read_doc()

    assert "payment_confirmation_review_ready is true" in content
    assert "payment_confirmed is true" in content
    assert "payment_confirmation_reference_recorded is true" in content
    assert "payment_confirmed_at_recorded is true" in content
    assert "confirmed_amount_recorded is true" in content
    assert "payment_confirmation_record_is_not_paid_work_authorization is true" in content
    assert "payment_confirmation_record_is_not_production_onboarding is true" in content
    assert "reconciliation_recorded is true" in content
    assert "reconciliation_record_is_not_paid_work_authorization is true" in content
    assert "reconciliation_record_is_not_production_onboarding is true" in content
    assert "human_operator_confirmed_payment is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_output_objects():
    content = read_doc()

    assert "source_payment_confirmation_review" in content
    assert "payment_confirmation_record" in content
    assert "reconciliation_record" in content
    assert "operator_confirmation" in content
    assert "event_checklist" in content
    assert "event_blockers" in content
    assert "event_score" in content
    assert "payment_evidence_review" in content
    assert "reconciliation_review" in content
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


def test_assessment_factory_lite_payment_confirmation_event_doc_names_records_and_operator_boundary():
    content = read_doc()

    assert "payment_confirmation_record_is_not_paid_work_authorization: true" in content
    assert "payment_confirmation_record_is_not_production_onboarding: true" in content
    assert "The payment confirmation record records confirmed payment only." in content
    assert "It is not paid-work authorization." in content
    assert "It is not production onboarding." in content

    assert "reconciliation_record_is_not_paid_work_authorization: true" in content
    assert "reconciliation_record_is_not_production_onboarding: true" in content
    assert "Reconciliation record does not authorize paid work." in content
    assert "Reconciliation record does not start production onboarding." in content

    assert "human_operator_required: true" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator confirmation records payment confirmation only." in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_score_and_boundaries():
    content = read_doc()

    assert "passed: 13" in content
    assert "total: 13" in content
    assert "score: 1.0" in content
    assert "ready: true" in content
    assert "deterministic event_status remains authoritative" in content

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content
    assert "Paid Work Boundary" in content
    assert "Production Onboarding Boundary" in content

    assert "payment_confirmation_recorded: true" in content
    assert "payment_confirmed: true" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_authorized: false" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "requires_separate_production_onboarding: true" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "payment_request_reference" in content
    assert "payment_request_delivery_reference" in content
    assert "payment_receipt_reference" in content
    assert "payment_confirmation_reference" in content
    assert "received_amount_review_notes" in content
    assert "payment_reconciliation_notes" in content
    assert "non_sensitive_workflow_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "payment_confirmation_event_records_payment_confirmation_only" in content
    assert "payment_confirmation_event_does_not_authorize_paid_work" in content
    assert "payment_confirmation_event_does_not_start_production_onboarding" in content
    assert "payment_confirmation_event_requires_human_operator" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "payment_confirmation_event_built" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "payment_confirmation_event_recorded" in content
    assert "payment_confirmation_event_pending_review" in content
    assert "payment_confirmation_event_pending_confirmation" in content
    assert "payment_confirmation_event_pending_record" in content
    assert "payment_confirmation_event_pending_reconciliation" in content
    assert "payment_confirmation_event_pending_operator_confirmation" in content
    assert "payment_confirmation_event_pending_event_review" in content
    assert "payment_confirmation_event_blocked" in content

    assert "prepare_paid_assessment_authorization_review" in content
    assert "build_paid_assessment_authorization_review" in content
    assert "complete_payment_confirmation_review" in content
    assert "confirm_payment_received" in content
    assert "record_payment_confirmation_reference" in content
    assert "record_payment_reconciliation" in content
    assert "confirm_operator_payment_confirmation_event" in content
    assert "resolve_payment_confirmation_event_gaps" in content
    assert "rerun_payment_confirmation_event" in content


def test_assessment_factory_lite_payment_confirmation_event_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Payment Confirmation Review → Payment Confirmation Record → Reconciliation Record → Human Confirmation → Boundary Preservation → Governed Next Action" in content
    assert "deterministic governance checkpoint for recording confirmed payment without overclaiming paid-work authorization or production onboarding" in content
    assert "acknowledge payment while preserving downstream execution gates" in content
    assert "first object in the workflow that may record actual payment confirmation" in content
    assert "US-325 — Assessment Factory Lite Payment Confirmation Event Release Marker" in content