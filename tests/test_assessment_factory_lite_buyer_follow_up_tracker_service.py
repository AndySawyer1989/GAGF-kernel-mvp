from backend.app.gagf.assessment_factory_lite_buyer_follow_up_tracker_service import (
    AssessmentFactoryLiteBuyerFollowUpTrackerService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


def service():
    return AssessmentFactoryLiteBuyerFollowUpTrackerService()


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


def test_assessment_factory_lite_buyer_follow_up_tracker_builds_contract():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "tracker_id": "buyer-follow-up-tracker-001",
            "created_at": "2026-07-17T12:15:00+00:00",
        },
    )

    assert result["status"] == "ok"
    assert result["tracker_type"] == "assessment_factory_lite_buyer_follow_up_tracker"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-export-package"
    assert result["version"] == "2.1.0"
    assert result["tracker_stage"] == "buyer_follow_up_tracker"
    assert result["tracker_status"] == "active"
    assert result["tracker_id"] == "buyer-follow-up-tracker-001"
    assert result["created_at"] == "2026-07-17T12:15:00+00:00"
    assert result["recommended_action"] == "review_buyer_follow_up_tracker"


def test_assessment_factory_lite_buyer_follow_up_tracker_includes_source_event_record():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
    )

    assert result["source_event_record"] == {
        "event_type": "assessment_factory_lite_buyer_delivery_event_record",
        "event_stage": "buyer_delivery_event_record",
        "event_status": "recorded",
        "event_id": "buyer-delivery-event-001",
        "recorded_at": "2026-07-17T12:00:00+00:00",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_delivery_event_record",
    }


def test_assessment_factory_lite_buyer_follow_up_tracker_defaults_to_no_response_and_schedule():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "created_at": "2026-07-17T12:15:00+00:00",
        },
    )

    assert result["buyer_response"] == {
        "response_status": "no_response",
        "response_received": False,
        "response_received_at": "",
        "response_summary": "",
        "buyer_questions": [],
        "buyer_objections": [],
    }

    assert result["follow_up_schedule"] == {
        "follow_up_required": True,
        "follow_up_due_at": "2026-07-20T12:15:00+00:00",
        "follow_up_channel": "email",
        "follow_up_owner": "operator",
        "reminder_status": "pending",
    }


def test_assessment_factory_lite_buyer_follow_up_tracker_includes_commercial_next_action_for_no_response():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
    )

    assert result["commercial_next_action"] == {
        "action": "send_follow_up_if_no_response",
        "description": (
            "No buyer response recorded. Prepare a human-operated follow-up "
            "message after the due date."
        ),
    }


def test_assessment_factory_lite_buyer_follow_up_tracker_includes_checklist_and_no_blockers_when_recorded():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
    )

    checks = {item["check"]: item for item in result["follow_up_checklist"]}

    assert set(checks) == {
        "delivery_event_recorded",
        "recipient_confirmed",
        "delivery_completed",
        "follow_up_owner_assigned",
        "buyer_response_classified",
    }

    assert checks["delivery_event_recorded"]["passed"] is True
    assert checks["recipient_confirmed"]["passed"] is True
    assert checks["delivery_completed"]["passed"] is True
    assert checks["follow_up_owner_assigned"]["passed"] is True
    assert checks["buyer_response_classified"]["passed"] is True
    assert result["follow_up_blockers"] == []


def test_assessment_factory_lite_buyer_follow_up_tracker_includes_audit_next_action_and_message():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
    )

    assert result["audit_notes"] == [
        "buyer_follow_up_tracker_active",
        "automated_follow_up_not_performed",
    ]

    assert result["next_action"] == {
        "action": "monitor_for_buyer_response",
        "operator_instruction": (
            "Monitor for buyer response and prepare follow-up after the "
            "due date if no response is recorded."
        ),
        "future_action": "prepare_buyer_follow_up_message",
    }

    assert result["operator_message"] == (
        "Assessment Factory Lite buyer follow-up tracker is active and "
        "waiting for buyer response."
    )


def test_assessment_factory_lite_buyer_follow_up_tracker_records_interested_response():
    result = service().build_tracker(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "buyer_response_status": "interested",
            "response_received_at": "2026-07-18T09:00:00+00:00",
            "response_summary": "Buyer wants to schedule a scope call.",
            "buyer_questions": ["Can we start next week?"],
        },
    )

    assert result["tracker_status"] == "response_received"
    assert result["buyer_response"] == {
        "response_status": "interested",
        "response_received": True,
        "response_received_at": "2026-07-18T09:00:00+00:00",
        "response_summary": "Buyer wants to schedule a scope call.",
        "buyer_questions": ["Can we start next week?"],
        "buyer_objections": [],
    }
    assert result["commercial_next_action"] == {
        "action": "schedule_assessment_scope_call",
        "description": (
            "Buyer expressed interest. Schedule a scope call for the "
            "bounded paid assessment."
        ),
    }
    assert "buyer_response_recorded" in result["audit_notes"]


def test_assessment_factory_lite_buyer_follow_up_tracker_blocks_unrecorded_delivery_event():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().build_tracker(
        export=export,
        event_context={
            "event_id": "buyer-delivery-event-003",
            "recorded_at": "2026-07-17T12:10:00+00:00",
            "human_operator_confirmed": True,
            "delivery_completed": True,
        },
    )

    assert result["tracker_status"] == "blocked"
    assert result["recommended_action"] == "resolve_buyer_follow_up_tracker_gaps"
    assert result["source_event_record"]["event_status"] == "blocked"
    assert "delivery_event_recorded" in result["follow_up_blockers"]
    assert "recipient_confirmed" in result["follow_up_blockers"]
    assert "recorded_delivery_event_required" in result["audit_notes"]
    assert result["next_action"] == {
        "action": "resolve_buyer_follow_up_tracker_gaps",
        "operator_instruction": (
            "Resolve delivery event, recipient, or completion gaps before "
            "tracking buyer follow-up."
        ),
        "future_action": "rerun_buyer_follow_up_tracker",
    }

