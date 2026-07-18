from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


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


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "created_at": "2026-07-17T12:15:00+00:00",
            },
            "follow_up_event_context": RECORDED_FOLLOW_UP_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_buyer_follow_up_event_record"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["event_stage"] == "buyer_follow_up_event_record"
    assert payload["event_status"] == "recorded"
    assert payload["event_id"] == "buyer-follow-up-event-001"
    assert payload["recorded_at"] == "2026-07-21T12:00:00+00:00"
    assert payload["recommended_action"] == "review_buyer_follow_up_event_record"


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_includes_source_message():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": RECORDED_FOLLOW_UP_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["source_follow_up_message"] == {
        "message_type": "assessment_factory_lite_buyer_follow_up_message",
        "message_stage": "buyer_follow_up_message_draft",
        "message_status": "draft_ready",
        "delivery_channel": "email_draft",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_follow_up_message",
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_includes_channel_and_recipient_status():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_message_context": {"recipient_role": "founder_operator"},
            "follow_up_event_context": RECORDED_FOLLOW_UP_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["follow_up_channel"] == {
        "channel": "email_draft",
        "channel_status": "operator_recorded",
        "automated_follow_up_used": False,
        "human_operated": True,
        "send_reference": "manual-follow-up-log-001",
    }

    assert payload["recipient_status"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
        "recipient_confirmed": True,
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_includes_message_summary_and_snapshots():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_context": {
                "buyer_response_status": "interested",
                "response_summary": "Buyer wants to schedule a scope call.",
            },
            "follow_up_event_context": RECORDED_FOLLOW_UP_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["message_summary"] == {
        "subject": "Next Step: Assessment Factory Lite Scope Call",
        "message_status": "response_reply_draft_ready",
        "message_stage": "buyer_follow_up_message_draft",
        "message_type": "assessment_factory_lite_buyer_follow_up_message",
        "commercial_next_action": "schedule_assessment_scope_call",
        "buyer_response_status": "interested",
    }

    assert payload["send_policy_snapshot"] == {
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

    assert payload["operator_review_snapshot"] == {
        "tracker_status": "response_received",
        "follow_up_blockers": [],
        "review_required": True,
        "human_operator_required": True,
        "approved_for_sending": False,
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_includes_outcome_audit_and_next_action():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": RECORDED_FOLLOW_UP_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["follow_up_outcome"] == {
        "follow_up_completed": True,
        "follow_up_result": "sent",
        "message_status": "draft_ready",
        "send_allowed": False,
        "human_operator_confirmed": True,
        "outcome_note": "Human operator sent the approved buyer follow-up message.",
    }

    assert payload["audit_notes"] == [
        "follow_up_message_review_completed",
        "human_operated_follow_up_recorded",
        "automated_follow_up_not_performed",
    ]

    assert payload["next_action"] == {
        "action": "review_follow_up_event_record",
        "operator_instruction": (
            "Review the buyer follow-up event record, confirm follow-up "
            "metadata, and preserve the record for commercial tracking."
        ),
        "future_action": "prepare_assessment_scope_call_package",
    }

    assert payload["operator_message"] == (
        "Assessment Factory Lite buyer follow-up event record has been "
        "created for a human-operated follow-up action."
    )


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_pending_human_confirmation():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-002",
                "recorded_at": "2026-07-21T12:05:00+00:00",
                "human_operator_confirmed": False,
                "follow_up_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_human_confirmation"
    assert payload["recommended_action"] == "resolve_buyer_follow_up_event_record_gaps"
    assert "human_operator_confirmation_required" in payload["audit_notes"]
    assert payload["next_action"] == {
        "action": "confirm_human_operator_follow_up",
        "operator_instruction": (
            "Confirm that a human operator reviewed and controlled the "
            "follow-up action before recording completion."
        ),
        "future_action": "record_buyer_follow_up_event",
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_pending_follow_up_completion():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-003",
                "recorded_at": "2026-07-21T12:10:00+00:00",
                "human_operator_confirmed": True,
                "follow_up_completed": False,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_follow_up_completion"
    assert payload["recommended_action"] == "resolve_buyer_follow_up_event_record_gaps"
    assert "follow_up_completion_required" in payload["audit_notes"]
    assert payload["next_action"] == {
        "action": "complete_follow_up_before_recording",
        "operator_instruction": (
            "Complete the human-operated follow-up action before marking "
            "the event as recorded."
        ),
        "future_action": "record_buyer_follow_up_event",
    }


def test_assessment_factory_lite_buyer_follow_up_event_record_endpoint_blocks_invalid_message_and_preserves_route():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
        json={
            "export": export,
            "event_context": {
                "event_id": "buyer-delivery-event-003",
                "recorded_at": "2026-07-17T12:10:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-004",
                "recorded_at": "2026-07-21T12:15:00+00:00",
                "human_operator_confirmed": True,
                "follow_up_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_buyer_follow_up_event_record_gaps"
    assert payload["source_follow_up_message"]["message_status"] == "blocked"
    assert "valid_follow_up_message_required" in payload["audit_notes"]
    assert payload["next_action"] == {
        "action": "resolve_buyer_follow_up_event_record_gaps",
        "operator_instruction": (
            "Resolve follow-up message readiness or human confirmation gaps "
            "before recording buyer follow-up."
        ),
        "future_action": "rerun_buyer_follow_up_event_record",
    }

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-follow-up-event-record" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.1.0",
        "release": "assessment-factory-lite-proposal-export-package",
        "sprint": "5.0",
        "status": "complete",
    }