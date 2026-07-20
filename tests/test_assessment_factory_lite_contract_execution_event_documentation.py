from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_CONTRACT_EXECUTION_EVENT.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_contract_execution_event_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_contract_execution_event_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-300 — Assessment Factory Lite Contract Execution Event Documentation" in content
    assert "AssessmentFactoryLiteContractExecutionEventService" in content
    assert "backend/app/gagf/assessment_factory_lite_contract_execution_event_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/contract-execution-event" in content
    assert "assessment_factory_lite_contract_execution_event" in content
    assert "contract_execution_event" in content
    assert "event_status" in content
    assert "contract_execution_event_id" in content
    assert "recorded_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_contract_execution_review" in content
    assert "contract_execution_review" in content
    assert "ready_for_contract_execution" in content
    assert "prepare_contract_execution_event" in content

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
    assert "contract_context" in content
    assert "contract_execution_context" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_contract_execution_context_fields():
    content = read_doc()

    assert "contract_execution_confirmed" in content
    assert "executed_contract_reference" in content
    assert "executed_at" in content
    assert "execution_method" in content
    assert "buyer_signed" in content
    assert "provider_signed" in content
    assert "signature_evidence_recorded" in content
    assert "human_operator_confirmed_execution" in content
    assert "operator_name" in content
    assert "operator_notes" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_statuses():
    content = read_doc()

    assert "contract_executed" in content
    assert "pending_contract_execution_review" in content
    assert "pending_contract_execution_confirmation" in content
    assert "pending_execution_evidence" in content
    assert "pending_signature_record" in content
    assert "pending_operator_confirmation" in content
    assert "pending_contract_execution_event_review" in content
    assert "blocked" in content

    assert "contract execution is confirmed" in content
    assert "executed contract reference is recorded" in content
    assert "all required signatures are recorded" in content
    assert "human operator confirmation exists" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_executed_conditions():
    content = read_doc()

    assert "contract_execution_review_ready is true" in content
    assert "contract_execution_confirmed is true" in content
    assert "executed_contract_reference_recorded is true" in content
    assert "executed_at_recorded is true" in content
    assert "execution_method_recorded is true" in content
    assert "all_required_signatures_recorded is true" in content
    assert "human_operator_confirmed_execution is true" in content
    assert "signature_record_is_not_invoice is true" in content
    assert "signature_record_is_not_payment is true" in content
    assert "invoice_not_created is true" in content
    assert "payment_not_requested is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_output_objects():
    content = read_doc()

    assert "source_contract_execution_review" in content
    assert "execution_evidence" in content
    assert "signature_record" in content
    assert "operator_confirmation" in content
    assert "event_checklist" in content
    assert "event_blockers" in content
    assert "execution_score" in content
    assert "contract_document_review" in content
    assert "signature_readiness" in content
    assert "agreement_terms" in content
    assert "buyer_acknowledgment" in content
    assert "buyer_request" in content
    assert "commercial_review" in content
    assert "evidence_review" in content
    assert "human_authorization" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_execution_signature_and_operator_objects():
    content = read_doc()

    assert "contract_executed" in content
    assert "The execution evidence records that the contract was executed." in content
    assert "It does not create an invoice." in content
    assert "It does not request payment." in content
    assert "It does not authorize paid work." in content

    assert "signature_record_is_not_invoice: true" in content
    assert "signature_record_is_not_payment: true" in content
    assert "Signature evidence is not an invoice." in content
    assert "Signature evidence is not payment." in content

    assert "human_operator_required: true" in content
    assert "invoice_creation_approved: false" in content
    assert "payment_request_approved: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator confirmation records contract execution only." in content


def test_assessment_factory_lite_contract_execution_event_doc_names_score_and_boundaries():
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
    assert "Contract Execution Boundary" in content

    assert "contract_execution_recorded: true" in content
    assert "contract_executed: true" in content
    assert "invoice_created: false" in content
    assert "payment_requested: false" in content
    assert "requires_separate_invoice: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "requires_separate_production_onboarding: true" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "operator_scope_call_notes" in content
    assert "buyer_approved_scope_call_summary" in content
    assert "redacted_operational_examples" in content
    assert "non_sensitive_workflow_context" in content
    assert "operator_approved_assessment_scope" in content
    assert "agreement_review_notes" in content
    assert "contract_review_notes" in content
    assert "executed_contract_reference" in content
    assert "signature_evidence" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "contract_execution_event_records_contract_execution_only" in content
    assert "contract_execution_event_does_not_create_invoice" in content
    assert "contract_execution_event_does_not_request_payment" in content
    assert "contract_execution_event_does_not_authorize_paid_work" in content
    assert "contract_execution_event_does_not_start_production_onboarding" in content
    assert "contract_execution_event_requires_human_operator" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "contract_execution_event_built" in content
    assert "invoice_not_created" in content
    assert "payment_not_requested" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "contract_execution_event_recorded" in content
    assert "contract_execution_event_pending_review" in content
    assert "contract_execution_event_pending_execution_confirmation" in content
    assert "contract_execution_event_pending_execution_evidence" in content
    assert "contract_execution_event_pending_signature_record" in content
    assert "contract_execution_event_pending_operator_confirmation" in content
    assert "contract_execution_event_pending_event_review" in content
    assert "contract_execution_event_blocked" in content

    assert "prepare_invoice_creation_review" in content
    assert "build_invoice_creation_review" in content
    assert "complete_contract_execution_review" in content
    assert "confirm_contract_execution" in content
    assert "record_execution_evidence" in content
    assert "record_signature_evidence" in content
    assert "confirm_operator_contract_execution_event" in content
    assert "resolve_contract_execution_event_gaps" in content
    assert "rerun_contract_execution_event" in content


def test_assessment_factory_lite_contract_execution_event_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Contract Readiness → Execution Evidence → Signature Evidence → Human Confirmation → Boundary Preservation → Governed Next Action" in content
    assert "deterministic governance checkpoint for recording contract execution without overclaiming downstream commercial authority" in content
    assert "record a real commercial event while preserving invoice, payment, paid-work authorization, and onboarding boundaries" in content
    assert "first object in the workflow that may confirm an actual executed contract" in content
    assert "US-301 — Assessment Factory Lite Contract Execution Event Release Marker" in content