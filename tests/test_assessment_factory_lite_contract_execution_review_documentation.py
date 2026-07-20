from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_CONTRACT_EXECUTION_REVIEW.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_contract_execution_review_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_contract_execution_review_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-296 — Assessment Factory Lite Contract Execution Review Documentation" in content
    assert "AssessmentFactoryLiteContractExecutionReviewService" in content
    assert "backend/app/gagf/assessment_factory_lite_contract_execution_review_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/contract-execution-review" in content
    assert "assessment_factory_lite_contract_execution_review" in content
    assert "contract_execution_review" in content
    assert "review_status" in content
    assert "contract_review_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_paid_assessment_agreement_review" in content
    assert "paid_assessment_agreement_review" in content
    assert "ready_for_agreement_execution_review" in content
    assert "prepare_contract_execution_review" in content

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
    assert "agreement_context" in content
    assert "contract_context" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_contract_context_fields():
    content = read_doc()

    assert "contract_document_prepared" in content
    assert "contract_terms_reviewed" in content
    assert "legal_language_reviewed" in content
    assert "scope_matches_agreement" in content
    assert "buyer_signature_ready" in content
    assert "provider_signature_ready" in content
    assert "signature_method_confirmed" in content
    assert "contract_execution_reviewed_by_operator" in content
    assert "operator_review_status" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_statuses():
    content = read_doc()

    assert "ready_for_contract_execution" in content
    assert "pending_agreement_review" in content
    assert "pending_contract_document_review" in content
    assert "pending_signature_readiness" in content
    assert "pending_operator_review" in content
    assert "pending_contract_execution_review" in content
    assert "blocked" in content

    assert "contract document is ready" in content
    assert "signature readiness is confirmed" in content
    assert "human operator reviewed the contract execution step" in content
    assert "source paid assessment agreement review is not ready" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_ready_conditions():
    content = read_doc()

    assert "agreement_review_ready is true" in content
    assert "contract_document_ready is true" in content
    assert "signature_readiness_confirmed is true" in content
    assert "signature_readiness_is_not_execution is true" in content
    assert "contract_execution_reviewed_by_operator is true" in content
    assert "contract_not_executed is true" in content
    assert "invoice_not_created is true" in content
    assert "payment_not_requested is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_output_objects():
    content = read_doc()

    assert "source_paid_assessment_agreement_review" in content
    assert "contract_document_review" in content
    assert "signature_readiness" in content
    assert "operator_review" in content
    assert "review_checklist" in content
    assert "review_blockers" in content
    assert "review_score" in content
    assert "agreement_terms" in content
    assert "buyer_acknowledgment" in content
    assert "buyer_request" in content
    assert "commercial_review" in content
    assert "evidence_review" in content
    assert "human_authorization" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_contract_document_signature_and_operator_objects():
    content = read_doc()

    assert "contract_execution_required_before_invoice: true" in content
    assert "invoice_required_before_payment: true" in content
    assert "payment_required_before_paid_work: true" in content
    assert "Contract document readiness does not execute the contract." in content
    assert "Contract document readiness does not create an invoice." in content
    assert "Contract document readiness does not request payment." in content

    assert "signature_readiness_is_not_execution: true" in content
    assert "contract_executed: false" in content
    assert "Signature readiness is not execution." in content
    assert "Signature readiness is not a signed contract." in content
    assert "Signature readiness is not authorization to begin paid work." in content

    assert "human_operator_required: true" in content
    assert "contract_execution_approved: false" in content
    assert "invoice_creation_approved: false" in content
    assert "payment_request_approved: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator review approves contract execution readiness only." in content


def test_assessment_factory_lite_contract_execution_review_doc_names_score_and_boundaries():
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
    assert "Contract Execution Boundary" in content

    assert "contract_execution_ready" in content
    assert "requires_actual_contract_execution: true" in content
    assert "requires_separate_invoice: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "contract_execution_review_is_not_execution: true" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "operator_scope_call_notes" in content
    assert "buyer_approved_scope_call_summary" in content
    assert "redacted_operational_examples" in content
    assert "non_sensitive_workflow_context" in content
    assert "operator_approved_assessment_scope" in content
    assert "agreement_review_notes" in content
    assert "contract_review_notes" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "contract_execution_review_does_not_execute_contract" in content
    assert "contract_execution_review_does_not_create_invoice" in content
    assert "contract_execution_review_does_not_request_payment" in content
    assert "contract_execution_review_does_not_authorize_paid_work" in content
    assert "contract_execution_review_does_not_start_production_onboarding" in content
    assert "contract_execution_review_requires_human_operator" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "contract_execution_review_built" in content
    assert "contract_execution_review_is_not_contract_execution" in content
    assert "invoice_not_created" in content
    assert "payment_not_requested" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "contract_execution_review_ready" in content
    assert "contract_execution_review_pending_agreement_review" in content
    assert "contract_execution_review_pending_document_review" in content
    assert "contract_execution_review_pending_signature_readiness" in content
    assert "contract_execution_review_pending_operator_review" in content
    assert "contract_execution_review_pending_review" in content
    assert "contract_execution_review_blocked" in content

    assert "prepare_contract_execution_event" in content
    assert "build_contract_execution_event" in content
    assert "complete_paid_assessment_agreement_review" in content
    assert "complete_contract_document_review" in content
    assert "confirm_signature_readiness" in content
    assert "complete_operator_contract_execution_review" in content
    assert "resolve_contract_execution_review_gaps" in content
    assert "rerun_contract_execution_review" in content


def test_assessment_factory_lite_contract_execution_review_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Agreement Readiness → Contract Document Review → Signature Readiness → Human Review → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for contract-execution readiness." in content
    assert "without collapsing review, signature, invoice, payment, and work authorization into one unsafe step" in content
    assert "final review layer before the contract execution event" in content
    assert "US-297 — Assessment Factory Lite Contract Execution Review Release Marker" in content