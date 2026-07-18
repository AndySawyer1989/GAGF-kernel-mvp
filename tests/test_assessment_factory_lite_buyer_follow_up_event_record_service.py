from backend.app.gagf.assessment_factory_lite_buyer_follow_up_event_record_service import (
    AssessmentFactoryLiteBuyerFollowUpEventRecordService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


def service():
    return AssessmentFactoryLiteBuyerFollowUpEventRecordService()


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
    "approval_note": "Operator approved package for buyer delivery.",
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
    "delivery_channel": "email_draft",
    "channel_status": "operator_recorded",
    "send_reference": "manual-send-log-001",
    "email_status": "operator_confirmed",
    "recipient_confirmed": True,
    "delivery_result": "delivered",
    "outcome_note": "Human operator sent the approved buyer delivery message.",
    "audit_notes": ["operator_review_completed"],
}


RECORDED_FOLLOW_UP_CONTEXT = {
    "event_id": "buyer-follow-up-event-001",
    "recorded_at": "2026-07-21T12:00:00+00:00",
    "human_operator_confirmed": True,
    "follow_up_completed": True,
    "follow_up_channel": "email_draft",
    "channel_status": "operator_recorded",
    "send_reference": "manual-follow-up-log-001",
    "email_status": "operator_confirmed",
    "recipient_confirmed": True,
    "follow_up_result": "sent",
    "outcome_note": "Human operator sent the approved buyer follow-up message.",
    "audit_notes": ["follow_up_message_review_completed"],
}


def test_assessment_factory_lite_buyer_follow_up_event_record_builds_contract():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "created_at": "2026-07-17T12:15:00+00:00",
        },
        follow_up_event_context=RECORDED_FOLLOW_UP_CONTEXT,
    )

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_buyer_follow_up_event_record"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-export-package"
    assert result["version"] == "2.1.0"
    assert result["event_stage"] == "buyer_follow_up_event_record"
    assert result["event_status"] == "recorded"
    assert result["event_id"] == "buyer-follow-up-event-001"
    assert result["recorded_at"] == "2026-07-21T12:00:00+00:00"
    assert result["recommended_action"] == "review_buyer_follow_up_event_record"


def test_assessment_factory_lite_buyer_follow_up_event_record_includes_source_message():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_event_context=RECORDED_FOLLOW_UP_CONTEXT,
    )

    assert result["source_follow_up_message"] == {
        "message_type": "assessment_factory_lite_buyer_follow_up_message",
        "message_stage": "buyer_follow_up_message_draft",
        "message_status": "draft_ready",
        "delivery_channel": "email_draft",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_follow_up_message",
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_includes_channel_and_recipient_status():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_message_context={"recipient_role": "founder_operator"},
        follow_up_event_context=RECORDED_FOLLOW_UP_CONTEXT,
    )

    assert result["follow_up_channel"] == {
        "channel": "email_draft",
        "channel_status": "operator_recorded",
        "automated_follow_up_used": False,
        "human_operated": True,
        "send_reference": "manual-follow-up-log-001",
    }

    assert result["recipient_status"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
        "recipient_confirmed": True,
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_includes_message_summary_and_snapshots():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "buyer_response_status": "interested",
            "response_summary": "Buyer wants to schedule a scope call.",
        },
        follow_up_event_context=RECORDED_FOLLOW_UP_CONTEXT,
    )

    assert result["message_summary"] == {
        "subject": "Next Step: Assessment Factory Lite Scope Call",
        "message_status": "response_reply_draft_ready",
        "message_stage": "buyer_follow_up_message_draft",
        "message_type": "assessment_factory_lite_buyer_follow_up_message",
        "commercial_next_action": "schedule_assessment_scope_call",
        "buyer_response_status": "interested",
    }

    assert result["send_policy_snapshot"] == {
        "send_allowed": False,
        "send_blocked_reason": (
            "Human operator review and approval are required before follow-up sending."
        ),
        "automated_send_allowed": False,
        "requires_human_operator": True,
        "send_rule": (
            "Buyer follow-up messages are draft-only and must be reviewed, "
            "approved, and sent by a human operator."
        ),
    }

    assert result["operator_review_snapshot"] == {
        "tracker_status": "response_received",
        "follow_up_blockers": [],
        "review_required": True,
        "human_operator_required": True,
        "approved_for_sending": False,
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_includes_outcome_audit_and_next_action():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_event_context=RECORDED_FOLLOW_UP_CONTEXT,
    )

    assert result["follow_up_outcome"] == {
        "follow_up_completed": True,
        "follow_up_result": "sent",
        "message_status": "draft_ready",
        "send_allowed": False,
        "human_operator_confirmed": True,
        "outcome_note": "Human operator sent the approved buyer follow-up message.",
    }

    assert result["audit_notes"] == [
        "follow_up_message_review_completed",
        "human_operated_follow_up_recorded",
        "automated_follow_up_not_performed",
    ]

    assert result["next_action"] == {
        "action": "review_follow_up_event_record",
        "operator_instruction": (
            "Review the buyer follow-up event record, confirm follow-up "
            "metadata, and preserve the record for commercial tracking."
        ),
        "future_action": "prepare_assessment_scope_call_package",
    }

    assert result["operator_message"] == (
        "Assessment Factory Lite buyer follow-up event record has been "
        "created for a human-operated follow-up action."
    )


def test_assessment_factory_lite_buyer_follow_up_event_record_pending_human_confirmation():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_event_context={
            "event_id": "buyer-follow-up-event-002",
            "recorded_at": "2026-07-21T12:05:00+00:00",
            "human_operator_confirmed": False,
            "follow_up_completed": True,
        },
    )

    assert result["event_status"] == "pending_human_confirmation"
    assert result["recommended_action"] == "resolve_buyer_follow_up_event_record_gaps"
    assert "human_operator_confirmation_required" in result["audit_notes"]
    assert result["next_action"] == {
        "action": "confirm_human_operator_follow_up",
        "operator_instruction": (
            "Confirm that a human operator reviewed and controlled the "
            "follow-up action before recording completion."
        ),
        "future_action": "record_buyer_follow_up_event",
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_pending_follow_up_completion():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_event_context={
            "event_id": "buyer-follow-up-event-003",
            "recorded_at": "2026-07-21T12:10:00+00:00",
            "human_operator_confirmed": True,
            "follow_up_completed": False,
        },
    )

    assert result["event_status"] == "pending_follow_up_completion"
    assert result["recommended_action"] == "resolve_buyer_follow_up_event_record_gaps"
    assert "follow_up_completion_required" in result["audit_notes"]
    assert result["next_action"] == {
        "action": "complete_follow_up_before_recording",
        "operator_instruction": (
            "Complete the human-operated follow-up action before marking "
            "the event as recorded."
        ),
        "future_action": "record_buyer_follow_up_event",
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_blocks_invalid_message():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().build_event_record(
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

    assert result["event_status"] == "blocked"
    assert result["recommended_action"] == "resolve_buyer_follow_up_event_record_gaps"
    assert result["source_follow_up_message"]["message_status"] == "blocked"
    assert "valid_follow_up_message_required" in result["audit_notes"]
    assert result["next_action"] == {
        "action": "resolve_buyer_follow_up_event_record_gaps",
        "operator_instruction": (
            "Resolve follow-up message readiness or human confirmation gaps "
            "before recording buyer follow-up."
        ),
        "future_action": "rerun_buyer_follow_up_event_record",
    }