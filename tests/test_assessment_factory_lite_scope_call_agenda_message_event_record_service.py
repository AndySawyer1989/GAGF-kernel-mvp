from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_scope_call_agenda_message_event_record_service import (
    AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService,
)


def service():
    return AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService()


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
}


FOLLOW_UP_EVENT_CONTEXT = {
    "event_id": "buyer-follow-up-event-001",
    "recorded_at": "2026-07-21T12:00:00+00:00",
    "human_operator_confirmed": True,
    "follow_up_completed": True,
}


INTERESTED_CONTEXT = {
    "buyer_response_status": "interested",
    "response_received_at": "2026-07-18T09:00:00+00:00",
    "response_summary": "Buyer wants to schedule a scope call.",
    "buyer_questions": ["Can we start next week?"],
}


AGENDA_EVENT_CONTEXT = {
    "event_id": "scope-call-agenda-message-event-001",
    "recorded_at": "2026-07-22T12:00:00+00:00",
    "human_operator_confirmed": True,
    "agenda_message_sent": True,
    "recipient_confirmed": True,
    "email_status": "operator_confirmed",
    "delivery_channel": "manual_email",
}


def test_assessment_factory_lite_scope_call_agenda_message_event_record_builds_contract():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_scope_call_agenda_message_event_record"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["event_stage"] == "scope_call_agenda_message_event_record"
    assert result["event_status"] == "recorded"
    assert result["event_id"] == "scope-call-agenda-message-event-001"
    assert result["recorded_at"] == "2026-07-22T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_scope_call_event_record"


def test_assessment_factory_lite_scope_call_agenda_message_event_record_includes_source_message_summary():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_context={
            "subject": "Scope Call Agenda for Assessment Factory Lite",
            "delivery_channel": "manual_email",
        },
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["source_scope_call_agenda_message"] == {
        "message_type": "assessment_factory_lite_scope_call_agenda_message",
        "message_stage": "scope_call_agenda_message_draft",
        "message_status": "draft_ready",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "delivery_channel": "manual_email",
        "subject": "Scope Call Agenda for Assessment Factory Lite",
        "recommended_action": "review_scope_call_agenda_message",
    }

    assert result["message_summary"]["subject"] == "Scope Call Agenda for Assessment Factory Lite"
    assert result["message_summary"]["body_available"] is True
    assert result["message_summary"]["agenda_item_count"] == 6
    assert result["message_summary"]["non_binding_notice_included"] is True
    assert result["message_summary"]["no_calendar_invite_notice_included"] is True
    assert result["message_summary"]["human_operator_notice_included"] is True


def test_assessment_factory_lite_scope_call_agenda_message_event_record_includes_channel_and_recipient_status():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_context={
            "recipient_role": "founder_operator",
            "delivery_channel": "manual_email",
        },
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["message_channel"] == {
        "delivery_channel": "manual_email",
        "automated_send_used": False,
        "calendar_invite_created": False,
        "automatic_scheduling_used": False,
        "human_operated": True,
    }

    assert result["recipient_status"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
        "recipient_confirmed": True,
    }


def test_assessment_factory_lite_scope_call_agenda_message_event_record_includes_policy_snapshots_and_boundaries():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["send_policy_snapshot"]["send_allowed"] is False
    assert result["send_policy_snapshot"]["automated_send_allowed"] is False
    assert result["send_policy_snapshot"]["calendar_invite_allowed"] is False
    assert result["send_policy_snapshot"]["automatic_scheduling_allowed"] is False
    assert result["send_policy_snapshot"]["requires_human_operator"] is True

    assert result["operator_review_snapshot"]["review_required"] is True
    assert result["operator_review_snapshot"]["human_operator_required"] is True
    assert result["operator_review_snapshot"]["approved_for_sending"] is False
    assert result["operator_review_snapshot"]["approved_for_scheduling"] is False

    assert result["scope_call_package_summary"]["package_status"] == "ready"
    assert result["agenda_summary"]["agenda_item_count"] == 6


def test_assessment_factory_lite_scope_call_agenda_message_event_record_includes_checklist_and_no_blockers_when_recorded():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["event_checklist"] == {
        "message_draft_ready": True,
        "human_operator_confirmed": True,
        "agenda_message_sent": True,
        "recipient_confirmed": True,
        "automated_send_not_used": True,
        "calendar_invite_not_created": True,
        "automatic_scheduling_not_used": True,
    }

    assert result["event_blockers"] == []


def test_assessment_factory_lite_scope_call_agenda_message_event_record_includes_recorded_audit_next_action_and_message():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["audit_notes"] == [
        "scope_call_agenda_message_event_recorded",
        "human_operator_confirmed_agenda_message_action",
        "automated_scope_call_sending_not_performed",
        "automatic_scheduling_not_performed",
    ]

    assert result["next_action"] == {
        "action": "prepare_scope_call_event_record",
        "operator_instruction": (
            "Use the recorded scope-call agenda message event to prepare "
            "the next human-operated scope-call event record."
        ),
        "future_action": "build_scope_call_event_record",
    }

    assert result["operator_message"] == (
        "Assessment Factory Lite scope-call agenda message event has been "
        "recorded as a human-operated buyer communication action."
    )


def test_assessment_factory_lite_scope_call_agenda_message_event_record_pending_human_confirmation():
    context = dict(AGENDA_EVENT_CONTEXT)
    context["human_operator_confirmed"] = False

    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=context,
    )

    assert result["event_status"] == "pending_human_confirmation"
    assert "human_operator_confirmed" in result["event_blockers"]
    assert result["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"
    assert result["audit_notes"] == [
        "scope_call_agenda_message_event_pending_human_confirmation",
        "automated_scope_call_sending_not_performed",
        "automatic_scheduling_not_performed",
    ]


def test_assessment_factory_lite_scope_call_agenda_message_event_record_pending_completion():
    context = dict(AGENDA_EVENT_CONTEXT)
    context["agenda_message_sent"] = False

    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=context,
    )

    assert result["event_status"] == "pending_agenda_message_completion"
    assert "agenda_message_sent" in result["event_blockers"]
    assert result["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"
    assert result["next_action"] == {
        "action": "complete_scope_call_agenda_message_action",
        "operator_instruction": (
            "Complete or confirm the agenda message action before recording "
            "the event as complete."
        ),
        "future_action": "rerun_scope_call_agenda_message_event_record",
    }


def test_assessment_factory_lite_scope_call_agenda_message_event_record_blocks_unready_message():
    result = service().record_event(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "buyer_response_status": "questions",
            "response_summary": "Buyer has questions before scheduling.",
        },
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["event_status"] == "blocked"
    assert result["source_scope_call_agenda_message"]["message_status"] == "blocked"
    assert "message_draft_ready" in result["event_blockers"]
    assert result["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"
    assert result["audit_notes"] == [
        "scope_call_agenda_message_event_blocked",
        "automated_scope_call_sending_not_performed",
        "automatic_scheduling_not_performed",
    ]


def test_assessment_factory_lite_scope_call_agenda_message_event_record_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().record_event(
        export=export,
        event_context=EVENT_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["event_status"] == "blocked"
    assert result["source_scope_call_agenda_message"]["message_status"] == "blocked"
    assert result["recommended_action"] == "resolve_scope_call_agenda_message_event_gaps"