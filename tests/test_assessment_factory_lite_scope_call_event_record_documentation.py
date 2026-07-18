from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_SCOPE_CALL_EVENT_RECORD.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_scope_call_event_record_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_scope_call_event_record_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-284 — Assessment Factory Lite Scope Call Event Record Documentation" in content
    assert "AssessmentFactoryLiteScopeCallEventRecordService" in content
    assert "backend/app/gagf/assessment_factory_lite_scope_call_event_record_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/scope-call-event-record" in content
    assert "assessment_factory_lite_scope_call_event_record" in content
    assert "scope_call_event_record" in content
    assert "event_status" in content
    assert "event_id" in content
    assert "recorded_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_scope_call_event_package" in content
    assert "scope_call_event_package" in content
    assert "ready_for_scope_call" in content
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
    assert "scope_call_message_event_context" in content
    assert "scope_call_record_context" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_record_context_fields():
    content = read_doc()

    assert "human_operator_confirmed" in content
    assert "call_completed" in content
    assert "call_confirmed" in content
    assert "outcome_status" in content
    assert "outcome_summary" in content
    assert "buyer_needs_summary" in content
    assert "assessment_fit" in content
    assert "next_step_requested" in content
    assert "buyer_decision_status" in content
    assert "operator_name" in content
    assert "operator_notes" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_statuses():
    content = read_doc()

    assert "recorded" in content
    assert "pending_scope_call_event_package" in content
    assert "pending_human_confirmation" in content
    assert "pending_scope_call_completion" in content
    assert "blocked" in content

    assert "The scope-call event package is ready" in content
    assert "The source Scope Call Event Package is not ready_for_scope_call." in content
    assert "the human operator has not confirmed the scope-call event record" in content
    assert "the call has not been completed" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_recorded_conditions():
    content = read_doc()

    assert "scope_call_event_package_ready is true" in content
    assert "call_completed is true" in content
    assert "call_confirmed is true" in content
    assert "human_operator_confirmed is true" in content
    assert "outcome_summary_recorded is true" in content
    assert "buyer_decision_recorded is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "automatic_call_recording_not_used is true" in content
    assert "ai_summary_not_authoritative is true" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_outputs_and_summaries():
    content = read_doc()

    assert "source_scope_call_event_package" in content
    assert "call_outcome" in content
    assert "operator_confirmation" in content
    assert "buyer_decision" in content
    assert "event_checklist" in content
    assert "event_blockers" in content
    assert "scope_call_package_summary" in content
    assert "agenda_summary" in content
    assert "buyer_readiness" in content
    assert "readiness_score" in content

    assert "event_type" in content
    assert "package_stage" in content
    assert "package_status" in content
    assert "scope_call_id" in content
    assert "prepared_at" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_call_outcome_operator_and_buyer_decision():
    content = read_doc()

    assert "call_completed" in content
    assert "call_confirmed" in content
    assert "outcome_summary" in content
    assert "buyer_needs_summary" in content
    assert "assessment_fit" in content
    assert "next_step_requested" in content

    assert "manual_recording_required: true" in content
    assert "automatic_call_recording_used: false" in content
    assert "ai_summary_authoritative: false" in content
    assert "AI summaries may assist in a future version" in content

    assert "requested_paid_assessment" in content
    assert "needs_follow_up" in content
    assert "undecided" in content
    assert "declined" in content
    assert "paid_assessment_authorization_required: true" in content
    assert "paid_assessment_authorized: false" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_commercial_next_actions():
    content = read_doc()

    assert "prepare_paid_assessment_authorization_package" in content
    assert "paid_assessment_authorization_package" in content
    assert "prepare_post_scope_call_follow_up" in content
    assert "post_scope_call_follow_up" in content
    assert "close_buyer_opportunity" in content
    assert "closed_lost_record" in content
    assert "resolve_scope_call_event_record_gaps" in content
    assert "scope_call_event_record_review" in content
    assert "automatic_execution_allowed: false" in content
    assert "human_operator_required: true" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_boundaries():
    content = read_doc()

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content
    assert "Paid Assessment Boundary" in content

    assert "scope_call_scheduled_by_system: false" in content
    assert "calendar_invite_created: false" in content
    assert "automatic_scheduling_allowed: false" in content
    assert "manual_scheduling_required: true" in content
    assert "scheduling_authority: human_operator" in content

    assert "contract_created: false" in content
    assert "contract_executed: false" in content
    assert "invoice_created: false" in content
    assert "payment_requested: false" in content
    assert "paid_assessment_authorized: false" in content
    assert "production_onboarding_authorized: false" in content
    assert "paid_assessment_requires_authorization_package: true" in content

    assert "deterministic_status_required: true" in content
    assert "gagf_kernel_authoritative: true" in content
    assert "ai_override_allowed: false" in content
    assert "human_boundary_required: true" in content
    assert "release_marker_preserved: true" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "operator_scope_call_notes" in content
    assert "buyer_approved_scope_call_summary" in content
    assert "redacted_operational_examples" in content
    assert "non_sensitive_workflow_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Evidence review is required before paid assessment authorization." in content

    assert "scope_call_event_record_does_not_authorize_paid_assessment" in content
    assert "scope_call_event_record_does_not_execute_contract" in content
    assert "scope_call_event_record_does_not_create_invoice" in content
    assert "scope_call_event_record_does_not_start_production_onboarding" in content
    assert "scope_call_event_record_requires_human_operator" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "scope_call_event_record_built" in content
    assert "paid_assessment_not_authorized" in content
    assert "contract_not_executed" in content
    assert "invoice_not_created" in content
    assert "production_onboarding_not_started" in content
    assert "scope_call_event_record_recorded" in content
    assert "scope_call_event_record_pending_package" in content
    assert "scope_call_event_record_pending_human_confirmation" in content
    assert "scope_call_event_record_pending_completion" in content
    assert "scope_call_event_record_blocked" in content
    assert "buyer_requested_paid_assessment_authorization_review" in content
    assert "buyer_declined_after_scope_call" in content
    assert "buyer_requires_post_scope_call_follow_up" in content

    assert "build_paid_assessment_authorization_package" in content
    assert "build_post_scope_call_follow_up" in content
    assert "build_closed_lost_record" in content
    assert "complete_scope_call_event_package" in content
    assert "confirm_scope_call_event_record" in content
    assert "complete_scope_call" in content
    assert "rerun_scope_call_event_record" in content


def test_assessment_factory_lite_scope_call_event_record_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Readiness → Human Event → Outcome Evidence → Boundary Preservation → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint for the buyer conversion path." in content
    assert "human buyer engagement and paid assessment authorization review" in content
    assert "preserving evidence, commercial, scheduling, and governance boundaries" in content
    assert "US-285 — Assessment Factory Lite Scope Call Event Record Release Marker" in content