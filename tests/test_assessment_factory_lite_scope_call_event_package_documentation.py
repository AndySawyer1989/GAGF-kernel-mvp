from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_SCOPE_CALL_EVENT_PACKAGE.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_scope_call_event_package_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_scope_call_event_package_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-280 — Assessment Factory Lite Scope Call Event Package Documentation" in content
    assert "AssessmentFactoryLiteScopeCallEventPackageService" in content
    assert "backend/app/gagf/assessment_factory_lite_scope_call_event_package_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_endpoint_and_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/scope-call-event-package" in content
    assert "assessment_factory_lite_scope_call_event_package" in content
    assert "scope_call_event_package" in content
    assert "package_status" in content
    assert "scope_call_id" in content
    assert "prepared_at" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_source_object_and_inputs():
    content = read_doc()

    assert "assessment_factory_lite_scope_call_agenda_message_event_record" in content
    assert "scope_call_agenda_message_event_record" in content
    assert "recorded" in content
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
    assert "scope_call_event_context" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_statuses():
    content = read_doc()

    assert "ready_for_scope_call" in content
    assert "pending_agenda_message_event" in content
    assert "pending_buyer_confirmation" in content
    assert "pending_human_approval" in content
    assert "blocked" in content

    assert "The agenda message event was recorded" in content
    assert "The source agenda message event is not yet recorded." in content
    assert "buyer readiness is not confirmed" in content
    assert "package-level human operator approval is missing" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_ready_conditions():
    content = read_doc()

    assert "agenda_message_event_recorded is true" in content
    assert "agenda_ready is true" in content
    assert "buyer_ready_for_scope_call is true" in content
    assert "recipient_confirmed is true" in content
    assert "human_operator_approved is true" in content
    assert "automated_send_not_used is true" in content
    assert "calendar_invite_not_created is true" in content
    assert "automatic_scheduling_not_used is true" in content
    assert "paid_assessment_not_authorized is true" in content
    assert "contract_not_executed is true" in content
    assert "scope_call_not_scheduled_by_system is true" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_summaries_and_readiness_objects():
    content = read_doc()

    assert "source_scope_call_agenda_message_event_record" in content
    assert "buyer_readiness" in content
    assert "agenda_confirmation" in content
    assert "human_approval" in content
    assert "readiness_checklist" in content
    assert "readiness_blockers" in content
    assert "readiness_score" in content

    assert "buyer_response_status" in content
    assert "buyer_interested" in content
    assert "buyer_questions_count" in content
    assert "agenda_message_sent" in content
    assert "agenda_item_count" in content
    assert "agenda_items_required" in content
    assert "operator_approved" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_readiness_score_and_checklist():
    content = read_doc()

    assert "passed" in content
    assert "total" in content
    assert "score" in content
    assert "ready" in content
    assert "passed: 11" in content
    assert "total: 11" in content
    assert "score: 1.0" in content
    assert "ready: true" in content
    assert "deterministic package_status remains authoritative" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_boundaries():
    content = read_doc()

    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Governance Boundary" in content
    assert "Human Operator Boundary" in content

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
    assert "scope_call_is_non_binding: true" in content

    assert "deterministic_status_required: true" in content
    assert "gagf_kernel_authoritative: true" in content
    assert "ai_override_allowed: false" in content
    assert "human_boundary_required: true" in content
    assert "release_marker_preserved: true" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_evidence_rules_and_boundary_notices():
    content = read_doc()

    assert "non_sensitive_sample_workflow_data" in content
    assert "redacted_operational_examples" in content
    assert "operator_approved_buyer_context" in content
    assert "regulated_production_data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved_personal_data" in content
    assert "unapproved_customer_records" in content
    assert "Evidence review is required before paid assessment authorization." in content

    assert "scope_call_event_package_does_not_schedule_call" in content
    assert "scope_call_event_package_does_not_create_calendar_invite" in content
    assert "scope_call_event_package_does_not_authorize_paid_assessment" in content
    assert "scope_call_event_package_does_not_execute_contract" in content
    assert "scope_call_event_package_requires_human_operator" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_audit_and_next_actions():
    content = read_doc()

    assert "scope_call_event_package_built" in content
    assert "automatic_scheduling_not_performed" in content
    assert "calendar_invite_not_created" in content
    assert "paid_assessment_not_authorized" in content
    assert "contract_not_executed" in content
    assert "scope_call_event_package_ready" in content
    assert "scope_call_event_package_pending_agenda_message_event" in content
    assert "scope_call_event_package_pending_buyer_confirmation" in content
    assert "scope_call_event_package_pending_human_approval" in content
    assert "scope_call_event_package_blocked" in content

    assert "prepare_scope_call_event_record" in content
    assert "build_scope_call_event_record" in content
    assert "record_scope_call_agenda_message_event" in content
    assert "confirm_buyer_scope_call_readiness" in content
    assert "confirm_human_operator_approval" in content
    assert "resolve_scope_call_event_package_gaps" in content
    assert "rerun_scope_call_event_package" in content


def test_assessment_factory_lite_scope_call_event_package_doc_names_gagf_and_product_meaning():
    content = read_doc()

    assert "Evidence → Readiness → Boundary Check → Human Approval → Governed Next Action" in content
    assert "It is a deterministic governance checkpoint." in content
    assert "governed pre-engagement readiness" in content
    assert "final readiness layer before recording the actual human-operated scope call event" in content
    assert "without overclaiming automation, contract authority, or paid assessment authorization" in content
    assert "US-281 — Assessment Factory Lite Scope Call Event Package Release Marker" in content