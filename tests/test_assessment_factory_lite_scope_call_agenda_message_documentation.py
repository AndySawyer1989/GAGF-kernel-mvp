from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_SCOPE_CALL_AGENDA_MESSAGE.md")


def read_doc():
    return DOC_PATH.read_text(encoding="utf-8")


def test_assessment_factory_lite_scope_call_agenda_message_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_release_and_story():
    content = read_doc()

    assert "assessment-factory-lite-scope-call-conversion" in content
    assert "2.3.0" in content
    assert "US-272 — Assessment Factory Lite Scope Call Agenda Message Documentation" in content
    assert "AssessmentFactoryLiteScopeCallAgendaMessageService" in content
    assert "backend/app/gagf/assessment_factory_lite_scope_call_agenda_message_service.py" in content
    assert "backend/app/main.py" in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_endpoint_and_message_contract():
    content = read_doc()

    assert "POST /products/assessment-factory-lite/scope-call-agenda-message" in content
    assert "assessment_factory_lite_scope_call_agenda_message" in content
    assert "scope_call_agenda_message_draft" in content
    assert "source_scope_call_package" in content
    assert "agenda_summary" in content
    assert "send_policy" in content
    assert "operator_review" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_source_package_and_layering():
    content = read_doc()

    assert "assessment_factory_lite_assessment_scope_call_package" in content
    assert "assessment-factory-lite-buyer-delivery-follow-up" in content
    assert "Source package version:" in content
    assert "2.2.0" in content
    assert "The source scope call package must be ready before the agenda message can become draft_ready." in content
    assert "This preserves layered object versioning." in content
    assert "The source scope call package remains on release assessment-factory-lite-buyer-delivery-follow-up and version 2.2.0." in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_inputs_and_context():
    content = read_doc()

    assert "scope_call_package" in content
    assert "follow_up_event_record" in content
    assert "follow_up_message" in content
    assert "tracker" in content
    assert "event_record" in content
    assert "message" in content
    assert "delivery_package" in content
    assert "export_package" in content
    assert "operator_approval" in content
    assert "scope_call_context" in content
    assert "scope_call_message_context" in content

    assert "recipient_role" in content
    assert "email_status" in content
    assert "sender_name" in content
    assert "subject" in content
    assert "delivery_channel" in content
    assert "operations_leader" in content
    assert "operator_to_provide" in content
    assert "Assessment Factory Lite Operator" in content
    assert "Assessment Factory Lite Scope Call Agenda" in content
    assert "email_draft" in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_statuses_and_conditions():
    content = read_doc()

    assert "draft_ready" in content
    assert "blocked" in content
    assert "package_status: ready" in content
    assert "buyer response is interested" in content
    assert "commercial next action supports schedule_assessment_scope_call" in content
    assert "follow-up event was recorded" in content
    assert "source delivery event was recorded" in content
    assert "buyer not interested" in content
    assert "commercial action does not support scope-call preparation" in content
    assert "upstream proposal export package invalid" in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_agenda_and_body_content():
    content = read_doc()

    assert "agenda_item_count" in content
    assert "agenda_items" in content
    assert "all_items_required" in content
    assert "agenda_owner" in content
    assert "confirm workflow scope" in content
    assert "confirm evidence sources" in content
    assert "confirm evidence boundaries" in content
    assert "confirm timeline and deliverables" in content
    assert "confirm commercial terms" in content
    assert "confirm next approval step" in content
    assert "thank-you language" in content
    assert "current commercial next action" in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_recipient_sender_source_and_review_contracts():
    content = read_doc()

    assert "recipient_type" in content
    assert "recipient_role" in content
    assert "email_required" in content
    assert "email_status" in content
    assert "sender_type" in content
    assert "sender_name" in content
    assert "signature_required" in content

    assert "package_type" in content
    assert "package_stage" in content
    assert "package_status" in content
    assert "package_id" in content
    assert "created_at" in content

    assert "approved_for_sending" in content
    assert "approved_for_scheduling" in content
    assert "message_ready" in content
    assert "The message is never automatically approved for sending." in content
    assert "The message is never automatically approved for scheduling." in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_send_policy_audit_and_next_action():
    content = read_doc()

    assert "send_allowed" in content
    assert "send_blocked_reason" in content
    assert "automated_send_allowed" in content
    assert "calendar_invite_allowed" in content
    assert "automatic_scheduling_allowed" in content
    assert "requires_human_operator" in content
    assert "send_rule" in content

    assert "scope_call_agenda_message_draft_ready" in content
    assert "automated_scope_call_sending_not_performed" in content
    assert "automatic_scheduling_not_performed" in content
    assert "scope_call_agenda_message_blocked" in content

    assert "review_scope_call_agenda_message" in content
    assert "record_scope_call_agenda_message_event" in content
    assert "resolve_scope_call_agenda_message_gaps" in content
    assert "rerun_scope_call_agenda_message" in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_boundaries():
    content = read_doc()

    assert "Human Operator Boundary" in content
    assert "Scheduling Boundary" in content
    assert "Commercial Boundary" in content
    assert "Evidence Boundary" in content
    assert "Compliance Boundary" in content
    assert "GAGF Boundary" in content

    assert "The message does not send email." in content
    assert "The message does not schedule a meeting." in content
    assert "The message does not create a calendar invite." in content
    assert "A human operator must review it before any buyer-facing action." in content
    assert "A human operator must approve the final message." in content
    assert "A human operator must send the message." in content
    assert "It is not a contract." in content
    assert "It is not an invoice." in content
    assert "It is not a payment request." in content
    assert "It is not paid assessment authorization." in content
    assert "It is not production onboarding." in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_evidence_compliance_and_release_marker_boundary():
    content = read_doc()

    assert "regulated production data" in content
    assert "secrets" in content
    assert "credentials" in content
    assert "unapproved personal data" in content
    assert "unapproved customer records" in content
    assert "non-sensitive sample workflow data" in content
    assert "redacted operational examples" in content
    assert "operator-approved buyer-provided context" in content

    assert "FedRAMP High" in content
    assert "HIPAA compliance" in content
    assert "SOC 2 readiness" in content
    assert "WCAG accessibility" in content
    assert "production readiness" in content

    assert "Route Preservation" in content
    assert "version: 2.3.0" in content
    assert "release: assessment-factory-lite-scope-call-conversion" in content
    assert "sprint: 5.0" in content
    assert "status: complete" in content
    assert "The new message object may use version 2.3.0 without changing the system release marker until a later release-marker story." in content


def test_assessment_factory_lite_scope_call_agenda_message_doc_names_product_meaning_and_next_story():
    content = read_doc()

    assert "Product Meaning" in content
    assert "This story starts the scope-call conversion layer." in content
    assert "Assessment Factory Lite can now prepare a scope-call agenda message after buyer interest has been recorded." in content
    assert "This turns buyer follow-up into a practical next commercial step while preserving human approval." in content
    assert "US-273 — Assessment Factory Lite Scope Call Agenda Message Release Marker" in content

