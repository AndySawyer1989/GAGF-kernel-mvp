from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_INVOICE_CREATION_EVENT.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_invoice_creation_event_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_invoice_creation_event_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-308 — Assessment Factory Lite Invoice Creation Event Documentation" in content
    assert "AssessmentFactoryLiteInvoiceCreationEventService" in content
    assert "backend/app/gagf/assessment_factory_lite_invoice_creation_event_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/invoice-creation-event" in content
    assert "assessment_factory_lite_invoice_creation_event" in content
    assert "invoice_creation_event" in content
    assert "event_status" in content
    assert "invoice_creation_event_id" in content
    assert "recorded_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_invoice_creation_review" in content
    assert "invoice_creation_review" in content
    assert "ready_for_invoice_creation" in content
    assert "prepare_invoice_creation_event" in content

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
    assert "invoice_context" in content
    assert "invoice_creation_context" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_invoice_creation_context_fields():
    content = read_doc()

    assert "invoice_created" in content
    assert "invoice_reference" in content
    assert "invoice_created_at" in content
    assert "invoice_amount" in content
    assert "invoice_delivered_to_buyer" in content
    assert "delivery_channel" in content
    assert "delivery_reference" in content
    assert "human_operator_confirmed_invoice_creation" in content
    assert "operator_name" in content
    assert "operator_notes" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_statuses():
    content = read_doc()

    assert "invoice_created" in content
    assert "pending_invoice_creation_review" in content
    assert "pending_invoice_creation_confirmation" in content
    assert "pending_invoice_record" in content
    assert "pending_invoice_delivery" in content
    assert "pending_operator_confirmation" in content
    assert "pending_invoice_creation_event_review" in content
    assert "blocked" in content

    assert "invoice creation is confirmed" in content
    assert "invoice reference is recorded" in content
    assert "invoice delivery is recorded" in content
    assert "human operator confirmation exists" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_created_conditions():
    content = read_doc()

    assert "invoice_creation_review_ready is true" in content
    assert "invoice_created is true" in content
    assert "invoice_reference_recorded is true" in content
    assert "invoice_created_at_recorded is true" in content
    assert "invoice_amount_recorded is true" in content
    assert "invoice_record_is_not_payment_request is true" in content
    assert "invoice_record_is_not_payment_confirmation is true" in content
    assert "invoice_record_is_not_paid_work_authorization is true" in content
    assert "invoice_delivered_to_buyer is true" in content
    assert "delivery_channel_recorded is true" in content
    assert "delivery_reference_recorded is true" in content
    assert "invoice_delivery_is_not_payment_request is true" in content
    assert "human_operator_confirmed_invoice_creation is true" in content
    assert "payment_not_requested is true" in content
    assert "payment_not_confirmed is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_output_objects():
    content = read_doc()

    assert "source_invoice_creation_review" in content
    assert "invoice_record" in content
    assert "delivery_record" in content
    assert "operator_confirmation" in content
    assert "event_checklist" in content
    assert "event_blockers" in content
    assert "event_score" in content
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


def test_assessment_factory_lite_invoice_creation_event_doc_names_invoice_delivery_and_operator_objects():
    content = read_doc()

    assert "invoice_record_is_not_payment_request: true" in content
    assert "invoice_record_is_not_payment_confirmation: true" in content
    assert "invoice_record_is_not_paid_work_authorization: true" in content
    assert "The invoice record records invoice creation only." in content
    assert "It is not a payment request." in content
    assert "It is not payment confirmation." in content
    assert "It is not paid-work authorization." in content

    assert "invoice_delivery_is_not_payment_request: true" in content
    assert "Invoice delivery is not a payment request." in content
    assert "Invoice delivery is not payment confirmation." in content
    assert "Invoice delivery is not paid-work authorization." in content

    assert "human_operator_required: true" in content
    assert "payment_requested: false" in content
    assert "payment_confirmed: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator confirmation records invoice creation only." in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_score_and_boundaries():
    content = read_doc()

    assert "passed: 17" in content
    assert "total: 17" in content
    assert "score: 1.0" in content
    assert "ready: true" in content
    assert "deterministic event_status remains authoritative" in content

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content
    assert "Invoice Creation Boundary" in content

    assert "invoice_creation_recorded: true" in content
    assert "invoice_created: true" in content
    assert "payment_requested: false" in content
    assert "payment_confirmed: false" in content
    assert "requires_separate_payment_request: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "requires_separate_production_onboarding: true" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "executed_contract_reference" in content
    assert "signature_evidence" in content
    assert "invoice_review_notes" in content
    assert "billing_readiness_notes" in content
    assert "invoice_reference" in content
    assert "invoice_delivery_reference" in content
    assert "non_sensitive_workflow_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "invoice_creation_event_records_invoice_creation_only" in content
    assert "invoice_creation_event_does_not_request_payment" in content
    assert "invoice_creation_event_does_not_confirm_payment" in content
    assert "invoice_creation_event_does_not_authorize_paid_work" in content
    assert "invoice_creation_event_does_not_start_production_onboarding" in content
    assert "invoice_creation_event_requires_human_operator" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "invoice_creation_event_built" in content
    assert "payment_not_requested" in content
    assert "payment_not_confirmed" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "invoice_creation_event_recorded" in content
    assert "invoice_creation_event_pending_review" in content
    assert "invoice_creation_event_pending_creation_confirmation" in content
    assert "invoice_creation_event_pending_invoice_record" in content
    assert "invoice_creation_event_pending_invoice_delivery" in content
    assert "invoice_creation_event_pending_operator_confirmation" in content
    assert "invoice_creation_event_pending_event_review" in content
    assert "invoice_creation_event_blocked" in content

    assert "prepare_payment_request_review" in content
    assert "build_payment_request_review" in content
    assert "complete_invoice_creation_review" in content
    assert "confirm_invoice_creation" in content
    assert "record_invoice_reference" in content
    assert "record_invoice_delivery" in content
    assert "confirm_operator_invoice_creation_event" in content
    assert "resolve_invoice_creation_event_gaps" in content
    assert "rerun_invoice_creation_event" in content


def test_assessment_factory_lite_invoice_creation_event_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Invoice Readiness → Invoice Record → Buyer Delivery → Human Confirmation → Boundary Preservation → Governed Next Action" in content
    assert "deterministic governance checkpoint for recording invoice creation without overclaiming downstream payment or work authority" in content
    assert "record a real invoice event while preserving payment request, payment confirmation, paid-work authorization, and onboarding boundaries" in content
    assert "first object in the workflow that may confirm an actual created invoice" in content
    assert "US-309 — Assessment Factory Lite Invoice Creation Event Release Marker" in content