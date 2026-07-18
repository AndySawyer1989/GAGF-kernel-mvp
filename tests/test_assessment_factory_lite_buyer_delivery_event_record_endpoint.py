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


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": RECORDED_EVENT_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_buyer_delivery_event_record"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["event_stage"] == "buyer_delivery_event_record"
    assert payload["event_status"] == "recorded"
    assert payload["event_id"] == "buyer-delivery-event-001"
    assert payload["recorded_at"] == "2026-07-17T12:00:00+00:00"
    assert payload["recommended_action"] == "review_buyer_delivery_event_record"


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_includes_source_message():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": RECORDED_EVENT_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["source_message"] == {
        "message_type": "assessment_factory_lite_buyer_delivery_message",
        "message_stage": "buyer_delivery_message_draft",
        "message_status": "send_ready_draft",
        "delivery_channel": "email_draft",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_delivery_message",
    }


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_includes_delivery_channel_and_recipient_status():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": RECORDED_EVENT_CONTEXT,
            "message_context": {"recipient_role": "founder_operator"},
        },
    )

    payload = response.json()

    assert payload["delivery_channel"] == {
        "channel": "email_draft",
        "channel_status": "operator_recorded",
        "automated_send_used": False,
        "human_operated": True,
        "send_reference": "manual-send-log-001",
    }

    assert payload["recipient_status"] == {
        "recipient_type": "buyer_role",
        "recipient_role": "founder_operator",
        "email_required": True,
        "email_status": "operator_confirmed",
        "recipient_confirmed": True,
    }


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_includes_attachment_summary():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": RECORDED_EVENT_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["attachment_summary"]["attachment_count"] == 3
    assert payload["attachment_summary"]["ready_attachment_count"] == 3
    assert payload["attachment_summary"]["buyer_facing_attachment_count"] == 0

    attachments = {
        item["attachment"]: item
        for item in payload["attachment_summary"]["attachments"]
    }

    assert attachments["proposal_markdown_export"]["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
    )
    assert attachments["proposal_pdf_export_object"]["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    )
    assert attachments["proposal_export_manifest"]["format"] == "json"


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_includes_policy_and_approval_snapshots():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": RECORDED_EVENT_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["send_policy_snapshot"] == {
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

    assert payload["operator_approval_snapshot"] == {
        "approval_status": "operator_approved",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "commercial_terms_approved": True,
        "buyer_language_approved": True,
        "delivery_blockers": [],
        "review_required": False,
    }


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_includes_delivery_outcome_audit_and_next_action():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": RECORDED_EVENT_CONTEXT,
        },
    )

    payload = response.json()

    assert payload["delivery_outcome"] == {
        "delivery_completed": True,
        "delivery_result": "delivered",
        "message_status": "send_ready_draft",
        "send_allowed": True,
        "human_operator_confirmed": True,
        "outcome_note": "Human operator sent the approved buyer delivery message.",
    }

    assert payload["audit_notes"] == [
        "operator_review_completed",
        "human_operated_delivery_recorded",
        "automated_send_not_performed",
    ]

    assert payload["next_action"] == {
        "action": "review_delivery_event_record",
        "operator_instruction": (
            "Review the buyer delivery event record, confirm delivery "
            "metadata, and preserve the record for future follow-up."
        ),
        "future_action": "prepare_buyer_follow_up_tracker",
    }

    assert payload["operator_message"] == (
        "Assessment Factory Lite buyer delivery event record has been "
        "created for a human-operated delivery action."
    )


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_pending_human_confirmation():
    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "operator_approval": APPROVAL,
            "event_context": {
                "event_id": "buyer-delivery-event-002",
                "recorded_at": "2026-07-17T12:05:00+00:00",
                "human_operator_confirmed": False,
                "delivery_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "pending_human_confirmation"
    assert payload["recommended_action"] == "resolve_buyer_delivery_event_record_gaps"
    assert "human_operator_confirmation_required" in payload["audit_notes"]
    assert payload["next_action"] == {
        "action": "confirm_human_operator_delivery",
        "operator_instruction": (
            "Confirm that a human operator reviewed and controlled the "
            "delivery action before recording completion."
        ),
        "future_action": "record_buyer_delivery_event",
    }


def test_assessment_factory_lite_buyer_delivery_event_record_endpoint_blocks_not_send_ready_message_and_preserves_route():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/buyer-delivery-event-record",
        json={
            "export": export,
            "event_context": {
                "event_id": "buyer-delivery-event-003",
                "recorded_at": "2026-07-17T12:10:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_buyer_delivery_event_record_gaps"
    assert payload["source_message"]["message_status"] == "blocked"
    assert payload["delivery_outcome"]["send_allowed"] is False
    assert "send_ready_message_required" in payload["audit_notes"]
    assert payload["next_action"] == {
        "action": "resolve_buyer_delivery_event_record_gaps",
        "operator_instruction": (
            "Resolve message readiness, delivery approval, or send-policy gaps "
            "before recording buyer delivery."
        ),
        "future_action": "rerun_buyer_delivery_event_record",
    }

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-delivery-event-record" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }



