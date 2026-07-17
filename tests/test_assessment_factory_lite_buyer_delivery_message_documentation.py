from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_DELIVERY_MESSAGE.md")


def test_assessment_factory_lite_buyer_delivery_message_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_delivery_message_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerDeliveryMessageService" in content
    assert "POST /products/assessment-factory-lite/buyer-delivery-message" in content
    assert "assessment_factory_lite_buyer_delivery_message" in content
    assert "assessment-factory-lite-proposal-export-package" in content
    assert "2.1.0" in content
    assert "buyer_delivery_message_draft" in content
    assert "review_buyer_delivery_message" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "delivery_package" in content
    assert "export_package" in content
    assert "export" in content
    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "operator_approval" in content
    assert "message_context" in content

    assert "status" in content
    assert "message_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "message_stage" in content
    assert "message_status" in content
    assert "delivery_channel" in content
    assert "recipient" in content
    assert "sender" in content
    assert "subject" in content
    assert "message_body" in content
    assert "source_delivery_package" in content
    assert "delivery_summary" in content
    assert "attachments" in content
    assert "operator_review" in content
    assert "send_policy" in content
    assert "next_action" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_message_statuses_and_context():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "draft_ready" in content
    assert "send_ready_draft" in content
    assert "blocked" in content
    assert "review_and_send_buyer_delivery_message" in content
    assert "resolve_buyer_delivery_message_gaps" in content

    assert "recipient_role" in content
    assert "sender_name" in content
    assert "delivery_channel" in content
    assert "operations_leader" in content
    assert "Assessment Factory Lite Operator" in content
    assert "email_draft" in content
    assert "founder_operator" in content
    assert "Andy Sawyer" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_recipient_sender_subject_and_body():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "recipient_type: buyer_role" in content
    assert "email_required: True" in content
    assert "email_status: operator_to_provide" in content
    assert "sender_type: operator" in content
    assert "signature_required: True" in content

    assert (
        "Assessment Factory Lite Proposal Package Ready for Review - "
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf"
    ) in content
    assert "greeting" in content
    assert "proposal package introduction" in content
    assert "Primary proposal artifact" in content
    assert "bounded paid-assessment workflow" in content
    assert "non-binding boundary" in content
    assert "operator signature" in content
    assert "requires operator approval before it can be sent" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_source_summary_and_attachments():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "delivery_type: assessment_factory_lite_buyer_delivery_package" in content
    assert "delivery_stage: buyer_delivery_package" in content
    assert "delivery_status: review_ready" in content
    assert "recommended_action: review_buyer_delivery_package" in content

    assert "send_ready: False" in content
    assert "review_ready: True" in content
    assert "blocked: False" in content
    assert "blocker_count: 4" in content
    assert "buyer_language_approved" in content
    assert "commercial_terms_approved" in content
    assert "evidence_boundary_approved" in content
    assert "scope_approved" in content

    assert "proposal_markdown_export" in content
    assert "proposal_pdf_export_object" in content
    assert "proposal_export_manifest" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in content
    assert "attachment_status: operator_review_required" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_operator_review_and_send_policy():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "approval_status: operator_review_required" in content
    assert "scope_approved: False" in content
    assert "evidence_boundary_approved: False" in content
    assert "commercial_terms_approved: False" in content
    assert "buyer_language_approved: False" in content
    assert "review_required: True" in content

    assert "send_allowed: False" in content
    assert "Operator approval and delivery readiness are required before sending." in content
    assert "automated_send_allowed: False" in content
    assert "requires_human_operator: True" in content
    assert "Automated sending is never allowed by this message service." in content
    assert "Human operator review is always required before delivery." in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_next_actions_and_messages():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "complete_operator_approval_before_sending" in content
    assert "Complete operator approvals before sending this buyer delivery message draft." in content
    assert "review_and_send_buyer_delivery_message" in content
    assert "verify recipient details" in content
    assert "approved human-operated channel" in content
    assert "record_buyer_delivery_event" in content
    assert "resolve_buyer_delivery_message_gaps" in content
    assert "rerun_buyer_delivery_message" in content

    assert "ready for operator review but not approved for sending" in content
    assert "ready for final human review and sending" in content
    assert "blocked because delivery package requirements are not satisfied" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_examples_and_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Full Operator Approval Example" in content
    assert "approval_status: operator_approved" in content
    assert "scope_approved: True" in content
    assert "evidence_boundary_approved: True" in content
    assert "commercial_terms_approved: True" in content
    assert "buyer_language_approved: True" in content
    assert "message_status: send_ready_draft" in content
    assert "send_policy.send_allowed: True" in content

    assert "Failed Delivery Package Example" in content
    assert "Binding quote: False" in content
    assert "Binding quote: True" in content
    assert "commercial_terms_present" in content

    assert "The buyer delivery package answers:" in content
    assert "The buyer delivery message answers:" in content
    assert "future send workflow" in content
    assert "delivery log" in content


def test_assessment_factory_lite_buyer_delivery_message_doc_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The buyer delivery message does not create a binding quote" in content
    assert "operator approves final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Buyer Delivery Message does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG "
        "certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "email delivery" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI may later explain or adapt buyer delivery language" in content
    assert "AI must not override deterministic delivery checks" in content