from backend.app.gagf.assessment_factory_lite_buyer_delivery_event_record_service import (
    AssessmentFactoryLiteBuyerDeliveryEventRecordService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


def service():
    return AssessmentFactoryLiteBuyerDeliveryEventRecordService()


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
    "approval_note": "Operator approved package for buyer delivery.",
}


RECORDED_EVENT_CONTEXT = {
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


def test_assessment_factory_lite_buyer_delivery_event_record_builds_contract():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=RECORDED_EVENT_CONTEXT,
    )

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_buyer_delivery_event_record"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-export-package"
    assert result["version"] == "2.1.0"
    assert result["event_stage"] == "buyer_delivery_event_record"
    assert result["event_status"] == "recorded"
    assert result["event_id"] == "buyer-delivery-event-001"
    assert result["recorded_at"] == "2026-07-17T12:00:00+00:00"
    assert result["recommended_action"] == "review_buyer_delivery_event_record"


def test_assessment_factory_lite_buyer_delivery_event_record_includes_source_message():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=RECORDED_EVENT_CONTEXT,
    )

    assert result["source_message"] == {
        "message_type": "assessment_factory_lite_buyer_delivery_message",
        "message_stage": "buyer_delivery_message_draft",
        "message_status": "send_ready_draft",
        "delivery_channel": "email_draft",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_delivery_message",
    }


def test_assessment_factory_lite_buyer_delivery_event_record_includes_delivery_channel_and_recipient_status():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=RECORDED_EVENT_CONTEXT,
        message_context={"recipient_role": "founder_operator"},
    )

    assert result["delivery_channel"] == {
        "channel": "email_draft",
        "channel_status": "operator_recorded",
        "automated_send_used": False,
        "human_operated": True,
        "send_reference": "manual-send-log-001",
    }

    assert result["recipient_status"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
        "recipient_confirmed": True,
    }


def test_assessment_factory_lite_buyer_delivery_event_record_includes_attachment_summary():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=RECORDED_EVENT_CONTEXT,
    )

    assert result["attachment_summary"]["attachment_count"] == 3
    assert result["attachment_summary"]["ready_attachment_count"] == 3
    assert result["attachment_summary"]["buyer_facing_attachment_count"] == 0

    attachments = {
        item["attachment"]: item
        for item in result["attachment_summary"]["attachments"]
    }

    assert attachments["proposal_markdown_export"]["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
    )
    assert attachments["proposal_pdf_export_object"]["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )
    assert attachments["proposal_export_manifest"]["format"] == "json"


def test_assessment_factory_lite_buyer_delivery_event_record_includes_policy_and_approval_snapshots():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=RECORDED_EVENT_CONTEXT,
    )

    assert result["send_policy_snapshot"] == {
        "send_allowed": True,
        "send_blocked_reason": "",
        "send_rule": (
            "Buyer delivery is allowed only when export package is ready and "
            "scope, evidence boundary, commercial terms, and buyer language "
            "are operator-approved."
        ),
        "automated_send_allowed": False,
        "requires_human_operator": True,
    }

    assert result["operator_approval_snapshot"] == {
        "approval_status": "operator_approved",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "commercial_terms_approved": True,
        "buyer_language_approved": True,
        "delivery_blockers": [],
        "review_required": False,
    }


def test_assessment_factory_lite_buyer_delivery_event_record_includes_delivery_outcome_audit_and_next_action():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context=RECORDED_EVENT_CONTEXT,
    )

    assert result["delivery_outcome"] == {
        "delivery_completed": True,
        "delivery_result": "delivered",
        "message_status": "send_ready_draft",
        "send_allowed": True,
        "human_operator_confirmed": True,
        "outcome_note": "Human operator sent the approved buyer delivery message.",
    }

    assert result["audit_notes"] == [
        "operator_review_completed",
        "human_operated_delivery_recorded",
        "automated_send_not_performed",
    ]

    assert result["next_action"] == {
        "action": "review_delivery_event_record",
        "operator_instruction": (
            "Review the buyer delivery event record, confirm delivery "
            "metadata, and preserve the record for future follow-up."
        ),
        "future_action": "prepare_buyer_follow_up_tracker",
    }

    assert result["operator_message"] == (
        "Assessment Factory Lite buyer delivery event record has been "
        "created for a human-operated delivery action."
    )


def test_assessment_factory_lite_buyer_delivery_event_record_pending_human_confirmation():
    result = service().build_event_record(
        operator_approval=APPROVAL,
        event_context={
            "event_id": "buyer-delivery-event-002",
            "recorded_at": "2026-07-17T12:05:00+00:00",
            "human_operator_confirmed": False,
            "delivery_completed": True,
        },
    )

    assert result["event_status"] == "pending_human_confirmation"
    assert result["recommended_action"] == "resolve_buyer_delivery_event_record_gaps"
    assert "human_operator_confirmation_required" in result["audit_notes"]
    assert result["next_action"] == {
        "action": "confirm_human_operator_delivery",
        "operator_instruction": (
            "Confirm that a human operator reviewed and controlled the "
            "delivery action before recording completion."
        ),
        "future_action": "record_buyer_delivery_event",
    }


def test_assessment_factory_lite_buyer_delivery_event_record_blocks_not_send_ready_message():
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
    )

    assert result["event_status"] == "blocked"
    assert result["recommended_action"] == "resolve_buyer_delivery_event_record_gaps"
    assert result["source_message"]["message_status"] == "blocked"
    assert result["delivery_outcome"]["send_allowed"] is False
    assert "send_ready_message_required" in result["audit_notes"]
    assert result["next_action"] == {
        "action": "resolve_buyer_delivery_event_record_gaps",
        "operator_instruction": (
            "Resolve message readiness, delivery approval, or send-policy gaps "
            "before recording buyer delivery."
        ),
        "future_action": "rerun_buyer_delivery_event_record",
    }