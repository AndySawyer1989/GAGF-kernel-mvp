from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_DELIVERY_EVENT_RECORD.md")


def test_assessment_factory_lite_buyer_delivery_event_record_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerDeliveryEventRecordService" in content
    assert "POST /products/assessment-factory-lite/buyer-delivery-event-record" in content
    assert "assessment_factory_lite_buyer_delivery_event_record" in content
    assert "assessment-factory-lite-proposal-export-package" in content
    assert "2.1.0" in content
    assert "buyer_delivery_event_record" in content
    assert "review_buyer_delivery_event_record" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "message" in content
    assert "delivery_package" in content
    assert "export_package" in content
    assert "export" in content
    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "operator_approval" in content
    assert "message_context" in content
    assert "event_context" in content

    assert "status" in content
    assert "event_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "event_stage" in content
    assert "event_status" in content
    assert "event_id" in content
    assert "recorded_at" in content
    assert "source_message" in content
    assert "delivery_channel" in content
    assert "recipient_status" in content
    assert "attachment_summary" in content
    assert "send_policy_snapshot" in content
    assert "operator_approval_snapshot" in content
    assert "boundary_notices" in content
    assert "delivery_outcome" in content
    assert "audit_notes" in content
    assert "next_action" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_event_statuses():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "recorded" in content
    assert "pending_human_confirmation" in content
    assert "pending_delivery_completion" in content
    assert "blocked" in content
    assert "review_buyer_delivery_event_record" in content
    assert "confirm_human_operator_delivery" in content
    assert "complete_delivery_before_recording" in content
    assert "resolve_buyer_delivery_event_record_gaps" in content
    assert "source buyer delivery message is not send_ready_draft" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_event_identity_source_and_channel():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "buyer-delivery-event-draft-001" in content
    assert "buyer-delivery-event-001" in content
    assert "2026-07-17T12:00:00+00:00" in content

    assert "message_type: assessment_factory_lite_buyer_delivery_message" in content
    assert "message_stage: buyer_delivery_message_draft" in content
    assert "message_status: send_ready_draft" in content
    assert "delivery_channel: email_draft" in content
    assert "recommended_action: review_buyer_delivery_message" in content

    assert "channel: email_draft" in content
    assert "channel_status: operator_recorded" in content
    assert "automated_send_used: False" in content
    assert "human_operated: True" in content
    assert "send_reference: manual-send-log-001" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_recipient_and_attachments():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "recipient_type: buyer_role" in content
    assert "recipient_role: founder_operator" in content
    assert "email_required: True" in content
    assert "email_status: operator_confirmed" in content
    assert "recipient_confirmed: True" in content

    assert "attachment_count: 3" in content
    assert "ready_attachment_count: 3" in content
    assert "buyer_facing_attachment_count: 0" in content
    assert "proposal_markdown_export" in content
    assert "proposal_pdf_export_object" in content
    assert "proposal_export_manifest" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in content
    assert "format:" in content
    assert "markdown" in content
    assert "pdf" in content
    assert "json" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_snapshots_and_outcome():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "send_allowed: True" in content
    assert "send_blocked_reason: empty string" in content
    assert "automated_send_allowed: False" in content
    assert "requires_human_operator: True" in content
    assert "Buyer delivery is allowed only when export package is ready" in content

    assert "approval_status: operator_approved" in content
    assert "scope_approved: True" in content
    assert "evidence_boundary_approved: True" in content
    assert "commercial_terms_approved: True" in content
    assert "buyer_language_approved: True" in content
    assert "delivery_blockers: []" in content
    assert "review_required: False" in content

    assert "delivery_completed: True" in content
    assert "delivery_result: delivered" in content
    assert "human_operator_confirmed: True" in content
    assert "Human operator sent the approved buyer delivery message." in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_audit_notes_and_next_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "operator_review_completed" in content
    assert "human_operated_delivery_recorded" in content
    assert "automated_send_not_performed" in content
    assert "human_operator_confirmation_required" in content
    assert "delivery_completion_required" in content
    assert "send_ready_message_required" in content

    assert "review_delivery_event_record" in content
    assert "prepare_buyer_follow_up_tracker" in content
    assert "confirm_human_operator_delivery" in content
    assert "record_buyer_delivery_event" in content
    assert "complete_delivery_before_recording" in content
    assert "rerun_buyer_delivery_event_record" in content

    assert "created for a human-operated delivery action" in content
    assert "pending human operator confirmation" in content
    assert "pending delivery completion" in content
    assert "blocked because the message is not send-ready" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_examples_and_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Full Recorded Event Example" in content
    assert "message_status: send_ready_draft" in content
    assert "human_operator_confirmed: True" in content
    assert "delivery_completed: True" in content
    assert "delivery_result: delivered" in content

    assert "Pending Human Confirmation Example" in content
    assert "event_status: pending_human_confirmation" in content
    assert "next_action.action: confirm_human_operator_delivery" in content

    assert "Pending Delivery Completion Example" in content
    assert "event_status: pending_delivery_completion" in content
    assert "next_action.action: complete_delivery_before_recording" in content

    assert "Blocked Message Example" in content
    assert "source_message.message_status: blocked" in content

    assert "The buyer delivery message answers:" in content
    assert "The buyer delivery event record answers:" in content
    assert "future buyer follow-up tracker" in content
    assert "future delivery ledger" in content
    assert "immutable chain hash" in content


def test_assessment_factory_lite_buyer_delivery_event_record_doc_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The buyer delivery event record does not create a binding quote" in content
    assert "only captures delivery metadata after a human-operated delivery action" in content

    assert (
        "The Assessment Factory Lite Buyer Delivery Event Record does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG "
        "certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "It does not perform automated sending." in content
    assert "records a human-operated event only after readiness" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI may later explain or summarize delivery events" in content
    assert "AI must not override deterministic delivery checks" in content
