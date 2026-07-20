from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_INVOICE_CREATION_REVIEW.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_invoice_creation_review_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_invoice_creation_review_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-304 — Assessment Factory Lite Invoice Creation Review Documentation" in content
    assert "AssessmentFactoryLiteInvoiceCreationReviewService" in content
    assert "backend/app/gagf/assessment_factory_lite_invoice_creation_review_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/invoice-creation-review" in content
    assert "assessment_factory_lite_invoice_creation_review" in content
    assert "invoice_creation_review" in content
    assert "review_status" in content
    assert "invoice_review_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_contract_execution_event" in content
    assert "contract_execution_event" in content
    assert "contract_executed" in content
    assert "prepare_invoice_creation_review" in content

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
    assert "contract_execution_context" in content
    assert "invoice_context" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_invoice_context_fields():
    content = read_doc()

    assert "invoice_amount_confirmed" in content
    assert "invoice_recipient_confirmed" in content
    assert "invoice_description_confirmed" in content
    assert "invoice_terms_confirmed" in content
    assert "billing_system_ready" in content
    assert "tax_or_business_details_checked" in content
    assert "payment_instructions_reviewed" in content
    assert "invoice_creation_reviewed_by_operator" in content
    assert "operator_review_status" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_statuses():
    content = read_doc()

    assert "ready_for_invoice_creation" in content
    assert "pending_contract_execution_event" in content
    assert "pending_invoice_details_review" in content
    assert "pending_billing_readiness" in content
    assert "pending_operator_review" in content
    assert "pending_invoice_creation_review" in content
    assert "blocked" in content

    assert "invoice details are ready" in content
    assert "billing readiness is complete" in content
    assert "operator invoice creation review exists" in content
    assert "source contract execution event is not contract_executed" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_ready_conditions():
    content = read_doc()

    assert "contract_execution_event_recorded is true" in content
    assert "invoice_details_ready is true" in content
    assert "billing_ready is true" in content
    assert "billing_readiness_is_not_payment_request is true" in content
    assert "billing_readiness_is_not_paid_work_authorization is true" in content
    assert "invoice_creation_reviewed_by_operator is true" in content
    assert "invoice_not_created is true" in content
    assert "payment_not_requested is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_output_objects():
    content = read_doc()

    assert "source_contract_execution_event" in content
    assert "invoice_details_review" in content
    assert "billing_readiness" in content
    assert "operator_review" in content
    assert "review_checklist" in content
    assert "review_blockers" in content
    assert "review_score" in content
    assert "execution_evidence" in content
    assert "signature_record" in content
    assert "contract_document_review" in content
    assert "agreement_terms" in content
    assert "buyer_request" in content
    assert "commercial_review" in content
    assert "evidence_review" in content
    assert "human_authorization" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_invoice_billing_and_operator_objects():
    content = read_doc()

    assert "invoice_creation_required_before_payment_request: true" in content
    assert "payment_confirmation_required_before_paid_work: true" in content
    assert "Invoice details readiness does not create an invoice." in content
    assert "Invoice details readiness does not request payment." in content
    assert "Invoice details readiness does not authorize paid work." in content

    assert "billing_readiness_is_not_payment_request: true" in content
    assert "billing_readiness_is_not_paid_work_authorization: true" in content
    assert "Billing readiness is not a payment request." in content
    assert "Billing readiness is not paid-work authorization." in content

    assert "human_operator_required: true" in content
    assert "invoice_created: false" in content
    assert "payment_request_approved: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator review approves invoice creation readiness only." in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_score_and_boundaries():
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
    assert "Invoice Creation Boundary" in content

    assert "invoice_creation_ready: true" in content
    assert "requires_actual_invoice_creation: true" in content
    assert "requires_separate_payment_request: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "requires_separate_production_onboarding: true" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "executed_contract_reference" in content
    assert "signature_evidence" in content
    assert "contract_review_notes" in content
    assert "invoice_review_notes" in content
    assert "billing_readiness_notes" in content
    assert "non_sensitive_workflow_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "invoice_creation_review_does_not_create_invoice" in content
    assert "invoice_creation_review_does_not_request_payment" in content
    assert "invoice_creation_review_does_not_authorize_paid_work" in content
    assert "invoice_creation_review_does_not_start_production_onboarding" in content
    assert "invoice_creation_review_requires_human_operator" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "invoice_creation_review_built" in content
    assert "invoice_not_created" in content
    assert "payment_not_requested" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "invoice_creation_review_ready" in content
    assert "invoice_creation_review_pending_contract_execution_event" in content
    assert "invoice_creation_review_pending_invoice_details" in content
    assert "invoice_creation_review_pending_billing_readiness" in content
    assert "invoice_creation_review_pending_operator_review" in content
    assert "invoice_creation_review_pending_review" in content
    assert "invoice_creation_review_blocked" in content

    assert "prepare_invoice_creation_event" in content
    assert "build_invoice_creation_event" in content
    assert "complete_contract_execution_event" in content
    assert "complete_invoice_details_review" in content
    assert "confirm_billing_readiness" in content
    assert "complete_operator_invoice_creation_review" in content
    assert "resolve_invoice_creation_review_gaps" in content
    assert "rerun_invoice_creation_review" in content


def test_assessment_factory_lite_invoice_creation_review_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Contract Execution Evidence → Invoice Detail Review → Billing Readiness → Human Review → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for invoice-creation readiness." in content
    assert "without collapsing invoice creation, payment request, payment confirmation, paid-work authorization, and onboarding into one unsafe step" in content
    assert "final review layer before the invoice creation event" in content
    assert "US-305 — Assessment Factory Lite Invoice Creation Review Release Marker" in content