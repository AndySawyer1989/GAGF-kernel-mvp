from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PAID_ASSESSMENT_AGREEMENT_REVIEW.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-292 — Assessment Factory Lite Paid Assessment Agreement Review Documentation" in content
    assert "AssessmentFactoryLitePaidAssessmentAgreementReviewService" in content
    assert "backend/app/gagf/assessment_factory_lite_paid_assessment_agreement_review_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/paid-assessment-agreement-review" in content
    assert "assessment_factory_lite_paid_assessment_agreement_review" in content
    assert "paid_assessment_agreement_review" in content
    assert "review_status" in content
    assert "agreement_review_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_paid_assessment_authorization_package" in content
    assert "paid_assessment_authorization_package" in content
    assert "ready_for_paid_assessment_authorization" in content
    assert "prepare_paid_assessment_agreement_review" in content

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
    assert "authorization_context" in content
    assert "agreement_context" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_agreement_context_fields():
    content = read_doc()

    assert "service_scope_reviewed" in content
    assert "price_confirmed" in content
    assert "deliverables_confirmed" in content
    assert "limitations_confirmed" in content
    assert "buyer_acknowledged_scope" in content
    assert "buyer_acknowledged_price" in content
    assert "buyer_acknowledged_non_binding_review" in content
    assert "agreement_reviewed_by_operator" in content
    assert "operator_review_status" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_statuses():
    content = read_doc()

    assert "ready_for_agreement_execution_review" in content
    assert "pending_authorization_package" in content
    assert "pending_agreement_terms" in content
    assert "pending_buyer_acknowledgment" in content
    assert "pending_operator_review" in content
    assert "pending_agreement_review" in content
    assert "blocked" in content

    assert "agreement terms are ready" in content
    assert "buyer acknowledgment is ready" in content
    assert "operator reviewed the agreement" in content
    assert "source paid assessment authorization package is not ready" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_ready_conditions():
    content = read_doc()

    assert "authorization_package_ready is true" in content
    assert "agreement_terms_ready is true" in content
    assert "buyer_acknowledgment_ready is true" in content
    assert "buyer_acknowledgment_is_not_signature is true" in content
    assert "buyer_acknowledgment_is_not_payment is true" in content
    assert "agreement_reviewed_by_operator is true" in content
    assert "contract_not_executed is true" in content
    assert "invoice_not_created is true" in content
    assert "payment_not_requested is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_output_objects():
    content = read_doc()

    assert "source_paid_assessment_authorization_package" in content
    assert "agreement_terms" in content
    assert "buyer_acknowledgment" in content
    assert "operator_review" in content
    assert "review_checklist" in content
    assert "review_blockers" in content
    assert "review_score" in content
    assert "buyer_request" in content
    assert "commercial_review" in content
    assert "evidence_review" in content
    assert "human_authorization" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_terms_buyer_and_operator_objects():
    content = read_doc()

    assert "contract_required_before_execution: true" in content
    assert "invoice_required_before_payment: true" in content
    assert "payment_required_before_paid_work: true" in content
    assert "Agreement terms readiness does not execute the agreement." in content

    assert "buyer_acknowledgment_is_not_signature: true" in content
    assert "buyer_acknowledgment_is_not_payment: true" in content
    assert "Buyer acknowledgment is not a signature." in content
    assert "Buyer acknowledgment is not payment." in content

    assert "human_operator_required: true" in content
    assert "contract_execution_approved: false" in content
    assert "invoice_creation_approved: false" in content
    assert "payment_request_approved: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Operator review approves review readiness only." in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_score_and_boundaries():
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
    assert "Agreement Boundary" in content

    assert "agreement_review_ready" in content
    assert "requires_separate_contract_execution: true" in content
    assert "requires_separate_invoice: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "requires_final_paid_work_authorization: true" in content
    assert "agreement_review_is_not_execution: true" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "operator_scope_call_notes" in content
    assert "buyer_approved_scope_call_summary" in content
    assert "redacted_operational_examples" in content
    assert "non_sensitive_workflow_context" in content
    assert "operator_approved_assessment_scope" in content
    assert "agreement_review_notes" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "paid_assessment_agreement_review_does_not_execute_contract" in content
    assert "paid_assessment_agreement_review_does_not_create_invoice" in content
    assert "paid_assessment_agreement_review_does_not_request_payment" in content
    assert "paid_assessment_agreement_review_does_not_authorize_paid_work" in content
    assert "paid_assessment_agreement_review_does_not_start_production_onboarding" in content
    assert "paid_assessment_agreement_review_requires_human_operator" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "paid_assessment_agreement_review_built" in content
    assert "agreement_review_is_not_contract_execution" in content
    assert "invoice_not_created" in content
    assert "payment_not_requested" in content
    assert "paid_assessment_not_authorized" in content
    assert "production_onboarding_not_started" in content
    assert "paid_assessment_agreement_review_ready" in content
    assert "paid_assessment_agreement_review_pending_authorization_package" in content
    assert "paid_assessment_agreement_review_pending_terms" in content
    assert "paid_assessment_agreement_review_pending_buyer_acknowledgment" in content
    assert "paid_assessment_agreement_review_pending_operator_review" in content
    assert "paid_assessment_agreement_review_pending_review" in content
    assert "paid_assessment_agreement_review_blocked" in content

    assert "prepare_contract_execution_review" in content
    assert "build_contract_execution_review" in content
    assert "complete_paid_assessment_authorization_package" in content
    assert "complete_agreement_terms_review" in content
    assert "confirm_buyer_agreement_acknowledgment" in content
    assert "complete_operator_agreement_review" in content
    assert "resolve_agreement_review_gaps" in content
    assert "resolve_paid_assessment_agreement_review_gaps" in content
    assert "rerun_paid_assessment_agreement_review" in content


def test_assessment_factory_lite_paid_assessment_agreement_review_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Authorization Readiness → Agreement Review → Buyer Acknowledgment → Human Review → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for agreement-readiness." in content
    assert "without collapsing agreement review, signature, invoice, payment, and work authorization into one unsafe step" in content
    assert "final preparation layer before contract execution review" in content
    assert "US-293 — Assessment Factory Lite Paid Assessment Agreement Review Release Marker" in content