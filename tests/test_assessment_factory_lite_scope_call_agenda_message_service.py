from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_scope_call_agenda_message_service import (
    AssessmentFactoryLiteScopeCallAgendaMessageService,
)


def service():
    return AssessmentFactoryLiteScopeCallAgendaMessageService()


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


def test_assessment_factory_lite_scope_call_agenda_message_builds_contract():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_context={
            "package_id": "assessment-scope-call-package-001",
            "created_at": "2026-07-21T12:30:00+00:00",
        },
    )

    assert result["status"] == "ok"
    assert result["message_type"] == "assessment_factory_lite_scope_call_agenda_message"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["message_stage"] == "scope_call_agenda_message_draft"
    assert result["message_status"] == "draft_ready"
    assert result["delivery_channel"] == "email_draft"
    assert result["recommended_action"] == "review_scope_call_agenda_message"


def test_assessment_factory_lite_scope_call_agenda_message_includes_recipient_sender_and_subject():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_context={
            "recipient_role": "founder_operator",
            "sender_name": "Andy Sawyer",
            "subject": "Scope Call Agenda for Assessment Factory Lite",
        },
    )

    assert result["recipient"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_to_provide",
    }

    assert result["sender"] == {
        "sender_type": "operator",
        "sender_name": "Andy Sawyer",
        "signature_required": True,
    }

    assert result["subject"] == "Scope Call Agenda for Assessment Factory Lite"


def test_assessment_factory_lite_scope_call_agenda_message_body_contains_agenda_and_boundaries():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_context={"sender_name": "Andy Sawyer"},
    )

    body = result["message_body"]

    assert "Thank you for your interest in Assessment Factory Lite." in body
    assert "- confirm workflow scope" in body
    assert "- confirm evidence sources" in body
    assert "- confirm evidence boundaries" in body
    assert "- confirm timeline and deliverables" in body
    assert "- confirm commercial terms" in body
    assert "- confirm next approval step" in body
    assert "please do not share regulated production data" in body
    assert "secrets, credentials, unapproved personal data" in body
    assert "scope-call agenda is non-binding" in body
    assert "does not create a contract, invoice, payment request, calendar invite" in body
    assert "I will only schedule the call after human operator review and buyer confirmation." in body
    assert "Current commercial next action: schedule_assessment_scope_call." in body
    assert "Thank you,\nAndy Sawyer" in body


def test_assessment_factory_lite_scope_call_agenda_message_includes_source_package_and_agenda_summary():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_context={
            "package_id": "assessment-scope-call-package-001",
            "created_at": "2026-07-21T12:30:00+00:00",
        },
    )

    assert result["source_scope_call_package"] == {
        "package_type": "assessment_factory_lite_assessment_scope_call_package",
        "package_stage": "assessment_scope_call_package",
        "package_status": "ready",
        "package_id": "assessment-scope-call-package-001",
        "created_at": "2026-07-21T12:30:00+00:00",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "version": "2.2.0",
        "recommended_action": "review_assessment_scope_call_package",
    }

    assert result["agenda_summary"] == {
        "agenda_item_count": 6,
        "agenda_items": [
            "confirm workflow scope",
            "confirm evidence sources",
            "confirm evidence boundaries",
            "confirm timeline and deliverables",
            "confirm commercial terms",
            "confirm next approval step",
        ],
        "all_items_required": True,
        "agenda_owner": "operator",
    }


def test_assessment_factory_lite_scope_call_agenda_message_includes_review_and_send_policy():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["operator_review"] == {
        "package_status": "ready",
        "package_blockers": [],
        "review_required": True,
        "human_operator_required": True,
        "approved_for_sending": False,
        "approved_for_scheduling": False,
        "message_ready": True,
    }

    assert result["send_policy"] == {
        "send_allowed": False,
        "send_blocked_reason": (
            "Human operator review and buyer confirmation are required before "
            "scope-call agenda sending or scheduling."
        ),
        "automated_send_allowed": False,
        "calendar_invite_allowed": False,
        "automatic_scheduling_allowed": False,
        "requires_human_operator": True,
        "send_rule": (
            "Scope-call agenda messages are draft-only and must be reviewed, "
            "approved, and sent by a human operator."
        ),
    }


def test_assessment_factory_lite_scope_call_agenda_message_includes_audit_next_action_and_operator_message():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["audit_notes"] == [
        "scope_call_agenda_message_draft_ready",
        "automated_scope_call_sending_not_performed",
        "automatic_scheduling_not_performed",
    ]

    assert result["next_action"] == {
        "action": "review_scope_call_agenda_message",
        "operator_instruction": (
            "Review the scope-call agenda message, confirm buyer details, "
            "and send or schedule only through a human-operated channel."
        ),
        "future_action": "record_scope_call_agenda_message_event",
    }

    assert result["operator_message"] == (
        "Assessment Factory Lite scope-call agenda message draft is ready "
        "for operator review."
    )


def test_assessment_factory_lite_scope_call_agenda_message_blocks_unready_scope_call_package():
    result = service().build_message(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "buyer_response_status": "questions",
            "response_summary": "Buyer has questions before scheduling.",
        },
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["message_status"] == "blocked"
    assert result["recommended_action"] == "resolve_scope_call_agenda_message_gaps"
    assert result["operator_review"]["message_ready"] is False
    assert "scope_call_action_supported" in result["operator_review"]["package_blockers"]
    assert result["send_policy"]["send_blocked_reason"] == (
        "Scope-call package must be ready before agenda message drafting can proceed."
    )
    assert result["next_action"] == {
        "action": "resolve_scope_call_agenda_message_gaps",
        "operator_instruction": (
            "Resolve scope-call package readiness gaps before preparing a "
            "buyer-facing agenda message."
        ),
        "future_action": "rerun_scope_call_agenda_message",
    }


def test_assessment_factory_lite_scope_call_agenda_message_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().build_message(
        export=export,
        event_context={
            "event_id": "buyer-delivery-event-003",
            "recorded_at": "2026-07-17T12:10:00+00:00",
            "human_operator_confirmed": True,
            "delivery_completed": True,
        },
        follow_up_event_context={
            "event_id": "buyer-follow-up-event-004",
            "recorded_at": "2026-07-21T12:15:00+00:00",
            "human_operator_confirmed": True,
            "follow_up_completed": True,
        },
    )

    assert result["message_status"] == "blocked"
    assert result["source_scope_call_package"]["package_status"] == "blocked"
    assert result["recommended_action"] == "resolve_scope_call_agenda_message_gaps"
    assert result["audit_notes"] == [
        "scope_call_agenda_message_blocked",
        "automated_scope_call_sending_not_performed",
        "automatic_scheduling_not_performed",
    ]
