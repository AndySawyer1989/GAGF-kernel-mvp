from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PAID_ASSESSMENT_AUTHORIZATION_PACKAGE.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-288 — Assessment Factory Lite Paid Assessment Authorization Package Documentation" in content
    assert "AssessmentFactoryLitePaidAssessmentAuthorizationPackageService" in content
    assert "backend/app/gagf/assessment_factory_lite_paid_assessment_authorization_package_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/paid-assessment-authorization-package" in content
    assert "assessment_factory_lite_paid_assessment_authorization_package" in content
    assert "paid_assessment_authorization_package" in content
    assert "package_status" in content
    assert "authorization_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_scope_call_event_record" in content
    assert "scope_call_event_record" in content
    assert "recorded" in content
    assert "prepare_paid_assessment_authorization_package" in content

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
    assert "scope_call_record_context" in content
    assert "authorization_context" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_authorization_context_fields():
    content = read_doc()

    assert "buyer_request_summary" in content
    assert "requested_package_type" in content
    assert "pricing_reviewed" in content
    assert "scope_reviewed" in content
    assert "terms_reviewed" in content
    assert "evidence_reviewed" in content
    assert "evidence_boundary_approved" in content
    assert "human_operator_authorized_package" in content
    assert "authorization_status" in content
    assert "buyer_requested_paid_assessment" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_statuses():
    content = read_doc()

    assert "ready_for_paid_assessment_authorization" in content
    assert "pending_scope_call_event_record" in content
    assert "pending_buyer_request" in content
    assert "pending_human_authorization" in content
    assert "pending_authorization_review" in content
    assert "blocked" in content

    assert "commercial terms are ready" in content
    assert "buyer paid assessment request evidence is missing" in content
    assert "package-level human authorization is missing" in content
    assert "commercial or evidence review is incomplete" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_ready_conditions():
    content = read_doc()

    assert "scope_call_event_recorded is true" in content
    assert "buyer_requested_paid_assessment is true" in content
    assert "buyer_request_is_evidence_not_authorization is true" in content
    assert "commercial_terms_ready is true" in content
    assert "evidence_ready_for_paid_assessment is true" in content
    assert "human_operator_authorized_package is true" in content
    assert "paid_assessment_not_authorized_by_package is true" in content
    assert "contract_not_executed is true" in content
    assert "invoice_not_created is true" in content
    assert "payment_not_requested is true" in content
    assert "production_onboarding_not_started is true" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_output_objects():
    content = read_doc()

    assert "source_scope_call_event_record" in content
    assert "buyer_request" in content
    assert "commercial_review" in content
    assert "evidence_review" in content
    assert "human_authorization" in content
    assert "package_checklist" in content
    assert "package_blockers" in content
    assert "authorization_score" in content
    assert "call_outcome" in content
    assert "buyer_decision" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_buyer_commercial_evidence_and_human_reviews():
    content = read_doc()

    assert "buyer_request_is_evidence_not_authorization: true" in content
    assert "A buyer request does not authorize paid work." in content

    assert "contract_required_before_execution: true" in content
    assert "invoice_required_before_payment: true" in content
    assert "payment_required_before_paid_work: true" in content

    assert "production_data_approved: false" in content
    assert "secrets_approved: false" in content
    assert "credentials_approved: false" in content

    assert "human_operator_required: true" in content
    assert "paid_assessment_authorized: false" in content
    assert "contract_execution_approved: false" in content
    assert "invoice_creation_approved: false" in content
    assert "payment_request_approved: false" in content
    assert "production_onboarding_approved: false" in content
    assert "Human package authorization approves package readiness only." in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_score_and_boundaries():
    content = read_doc()

    assert "passed: 11" in content
    assert "total: 11" in content
    assert "score: 1.0" in content
    assert "ready: true" in content
    assert "deterministic package_status remains authoritative" in content

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content
    assert "Paid Assessment Boundary" in content

    assert "authorization_package_ready" in content
    assert "requires_separate_contract: true" in content
    assert "requires_separate_invoice: true" in content
    assert "requires_separate_payment_confirmation: true" in content
    assert "authorization_is_package_readiness_only: true" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "operator_scope_call_notes" in content
    assert "buyer_approved_scope_call_summary" in content
    assert "redacted_operational_examples" in content
    assert "non_sensitive_workflow_context" in content
    assert "operator_approved_assessment_scope" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Production data requires separate approval." in content

    assert "paid_assessment_authorization_package_does_not_authorize_paid_work" in content
    assert "paid_assessment_authorization_package_does_not_execute_contract" in content
    assert "paid_assessment_authorization_package_does_not_create_invoice" in content
    assert "paid_assessment_authorization_package_does_not_request_payment" in content
    assert "paid_assessment_authorization_package_does_not_start_production_onboarding" in content
    assert "paid_assessment_authorization_package_requires_human_operator" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "paid_assessment_authorization_package_built" in content
    assert "buyer_request_treated_as_evidence_not_authorization" in content
    assert "paid_assessment_not_authorized" in content
    assert "contract_not_executed" in content
    assert "invoice_not_created" in content
    assert "payment_not_requested" in content
    assert "production_onboarding_not_started" in content
    assert "paid_assessment_authorization_package_ready" in content
    assert "paid_assessment_authorization_pending_scope_call_event_record" in content
    assert "paid_assessment_authorization_pending_buyer_request" in content
    assert "paid_assessment_authorization_pending_human_authorization" in content
    assert "paid_assessment_authorization_pending_review" in content
    assert "paid_assessment_authorization_package_blocked" in content
    assert "buyer_requested_paid_assessment_review" in content

    assert "prepare_paid_assessment_agreement_review" in content
    assert "build_paid_assessment_agreement_review" in content
    assert "complete_scope_call_event_record" in content
    assert "confirm_buyer_paid_assessment_request" in content
    assert "confirm_human_authorization_package_review" in content
    assert "complete_authorization_review" in content
    assert "resolve_paid_assessment_authorization_package_gaps" in content
    assert "rerun_paid_assessment_authorization_package" in content


def test_assessment_factory_lite_paid_assessment_authorization_package_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Outcome Evidence → Buyer Request Evidence → Commercial Review → Evidence Review → Human Package Authorization → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for commercial authorization readiness." in content
    assert "move toward revenue without collapsing request, review, contract, payment, and authorization into one unsafe step" in content
    assert "governed paid-work readiness" in content
    assert "US-289 — Assessment Factory Lite Paid Assessment Authorization Package Release Marker" in content