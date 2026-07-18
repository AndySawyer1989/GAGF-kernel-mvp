from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_SCOPE_CALL_AGENDA_MESSAGE_EVENT_RECORD.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_release_story_and_service():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-276 — Assessment Factory Lite Scope Call Agenda Message Event Record Documentation" in content
    assert "AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService" in content
    assert "backend/app/gagf/assessment_factory_lite_scope_call_agenda_message_event_record_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_endpoint_and_event_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/scope-call-agenda-message-event-record" in content
    assert "assessment_factory_lite_scope_call_agenda_message_event_record" in content
    assert "scope_call_agenda_message_event_record" in content
    assert "source_scope_call_agenda_message" in content
    assert "message_channel" in content
    assert "recipient_status" in content
    assert "event_checklist" in content
    assert "event_blockers" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_source_message_and_layering():
    content = read_doc()

    assert "assessment_factory_lite_scope_call_agenda_message" in content
    assert "Source message release:" in content
    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "Source message version:" in content
    assert "2.3.0" in content
    assert "The source message must be draft_ready before the event can be recorded." in content
    assert "This preserves the same conversion-layer contract as the scope-call agenda message." in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_inputs_and_context():
    content = read_doc()

    assert "scope_call_agenda_message" in content
    assert "scope_call_package" in content
    assert "follow_up_event_record" in content
    assert "follow_up_message" in content
    assert "tracker" in content
    assert "event_record" in content
    assert "message" in content
    assert "delivery_package" in content
    assert "export_package" in content
    assert "operator_approval" in content
    assert "scope_call_message_context" in content
    assert "scope_call_message_event_context" in content

    assert "event_id" in content
    assert "recorded_at" in content
    assert "human_operator_confirmed" in content
    assert "agenda_message_sent" in content
    assert "recipient_confirmed" in content
    assert "email_status" in content
    assert "delivery_channel" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_output_fields_and_statuses():
    content = read_doc()

    assert "status" in content
    assert "event_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "event_stage" in content
    assert "event_status" in content
    assert "recorded" in content
    assert "pending_human_confirmation" in content
    assert "pending_agenda_message_completion" in content
    assert "blocked" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_status_conditions():
    content = read_doc()

    assert "message_draft_ready is true" in content
    assert "human_operator_confirmed is true" in content
    assert "agenda_message_sent is true" in content
    assert "recipient_confirmed is true" in content
    assert "automated_send_not_used is true" in content
    assert "calendar_invite_not_created is true" in content
    assert "automatic_scheduling_not_used is true" in content
    assert "source message is draft_ready" in content
    assert "scope-call package is not ready" in content
    assert "upstream proposal export package is invalid" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_summaries_and_snapshots():
    content = read_doc()

    assert "message_type" in content
    assert "message_stage" in content
    assert "message_status" in content
    assert "subject" in content
    assert "recommended_action" in content

    assert "body_available" in content
    assert "body_character_count" in content
    assert "agenda_item_count" in content
    assert "non_binding_notice_included" in content
    assert "no_calendar_invite_notice_included" in content
    assert "human_operator_notice_included" in content

    assert "send_policy_snapshot" in content
    assert "operator_review_snapshot" in content
    assert "scope_call_package_summary" in content
    assert "agenda_summary" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_channel_recipient_and_checklist():
    content = read_doc()

    assert "automated_send_used: false" in content
    assert "calendar_invite_created: false" in content
    assert "automatic_scheduling_used: false" in content
    assert "human_operated: true" in content

    assert "recipient_type" in content
    assert "recipient_role" in content
    assert "email_required" in content
    assert "recipient_confirmed" in content

    assert "message_draft_ready" in content
    assert "human_operator_confirmed" in content
    assert "agenda_message_sent" in content
    assert "automated_send_not_used" in content
    assert "calendar_invite_not_created" in content
    assert "automatic_scheduling_not_used" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_audit_next_and_recommended_actions():
    content = read_doc()

    assert "scope_call_agenda_message_event_recorded" in content
    assert "human_operator_confirmed_agenda_message_action" in content
    assert "automated_scope_call_sending_not_performed" in content
    assert "automatic_scheduling_not_performed" in content
    assert "scope_call_agenda_message_event_pending_human_confirmation" in content
    assert "scope_call_agenda_message_event_pending_completion" in content
    assert "scope_call_agenda_message_event_blocked" in content

    assert "prepare_scope_call_event_record" in content
    assert "build_scope_call_event_record" in content
    assert "confirm_scope_call_agenda_message_event" in content
    assert "complete_scope_call_agenda_message_action" in content
    assert "resolve_scope_call_agenda_message_event_gaps" in content
    assert "rerun_scope_call_agenda_message_event_record" in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_boundaries():
    content = read_doc()

    assert "Human Operator Boundary" in content
    assert "Send Boundary" in content
    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Compliance Boundary" in content
    assert "GAGF Boundary" in content

    assert "It does not approve automatic sending." in content
    assert "It does not approve automatic scheduling." in content
    assert "It does not approve paid assessment start." in content
    assert "The event record can record a human-operated send action, but it must not perform the send action itself." in content
    assert "The event record must preserve that no calendar invite was created automatically." in content
    assert "It is not a contract." in content
    assert "It is not an invoice." in content
    assert "It is not a payment request." in content
    assert "It is not paid assessment authorization." in content


def test_assessment_factory_lite_scope_call_agenda_message_event_record_doc_names_evidence_compliance_release_and_product_meaning():
    content = read_doc()

    assert "non-sensitive sample workflow data" in content
    assert "redacted operational examples" in content
    assert "operator-approved buyer-provided context" in content
    assert "regulated production data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved personal data" in content
    assert "unapproved customer records" in content

    assert "FedRAMP High" in content
    assert "HIPAA compliance" in content
    assert "SOC 2 readiness" in content
    assert "WCAG accessibility" in content
    assert "production readiness" in content

    assert "version: 2.3.0" in content
    assert "release: assessment-factory-lite-scope-call-conversion" in content
    assert "sprint: 5.0" in content
    assert "status: complete" in content

    assert "Product Meaning" in content
    assert "human-operated scope-call agenda communication" in content
    assert "recorded agenda-message action" in content
    assert "US-277 — Assessment Factory Lite Scope Call Agenda Message Event Record Release Marker" in content