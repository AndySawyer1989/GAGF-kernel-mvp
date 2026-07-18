from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_BUYER_DELIVERY_PACKAGE.md")


def test_assessment_factory_lite_buyer_delivery_package_doc_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_buyer_delivery_package_doc_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteBuyerDeliveryPackageService" in content
    assert "POST /products/assessment-factory-lite/buyer-delivery-package" in content
    assert "assessment_factory_lite_buyer_delivery_package" in content
    assert "assessment-factory-lite-proposal-export-package" in content
    assert "2.1.0" in content
    assert "buyer_delivery_package" in content
    assert "review_buyer_delivery_package" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_request_and_response_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "export_package" in content
    assert "export" in content
    assert "document" in content
    assert "proposal" in content
    assert "offer" in content
    assert "buyer_context" in content
    assert "operator_approval" in content

    assert "status" in content
    assert "delivery_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "delivery_stage" in content
    assert "delivery_status" in content
    assert "source_export_package" in content
    assert "buyer_facing_deliverables" in content
    assert "delivery_checklist" in content
    assert "delivery_blockers" in content
    assert "boundary_notices" in content
    assert "send_readiness" in content
    assert "delivery_manifest" in content
    assert "next_action" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_delivery_statuses():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "review_ready" in content
    assert "send_ready" in content
    assert "blocked" in content
    assert "review_buyer_delivery_package" in content
    assert "prepare_buyer_delivery_message" in content
    assert "resolve_buyer_delivery_package_gaps" in content
    assert "Operator approval is still incomplete." in content
    assert "Scope is operator-approved." in content
    assert "The proposal export package is not ready" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_source_package_and_deliverables():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "package_type: assessment_factory_lite_proposal_export_package" in content
    assert "package_stage: proposal_export_package" in content
    assert "package_status: ready" in content
    assert "release: assessment-factory-lite-proposal-package" in content
    assert "version: 2.0.0" in content

    assert "proposal_markdown_export" in content
    assert "proposal_pdf_export_object" in content
    assert "proposal_export_manifest" in content
    assert "format: markdown" in content
    assert "format: pdf" in content
    assert "format: json" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.md" in content
    assert "assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf" in content
    assert "buyer_facing: False" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_operator_approval_and_checklist():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "approval_status: operator_review_required" in content
    assert "scope_approved: False" in content
    assert "evidence_boundary_approved: False" in content
    assert "commercial_terms_approved: False" in content
    assert "buyer_language_approved: False" in content
    assert "Operator must approve scope, evidence boundary, commercial terms" in content

    assert "export_package_ready" in content
    assert "markdown_export_present" in content
    assert "pdf_export_object_ready" in content
    assert "readiness_passed" in content
    assert "scope_approved" in content
    assert "evidence_boundary_approved" in content
    assert "commercial_terms_approved" in content
    assert "buyer_language_approved" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_blockers_send_readiness_and_manifest():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "buyer_language_approved" in content
    assert "commercial_terms_approved" in content
    assert "evidence_boundary_approved" in content
    assert "scope_approved" in content

    assert "send_ready: False" in content
    assert "review_ready: True" in content
    assert "blocked: False" in content
    assert "blocker_count: 4" in content
    assert "requires_operator_approval: True" in content
    assert "Buyer delivery is allowed only when export package is ready" in content

    assert "buyer_delivery_package_manifest" in content
    assert "source_package_type" in content
    assert "source_package_status" in content
    assert "ready_for_pdf: True" in content
    assert "readiness_score: 1.0" in content
    assert "AssessmentFactoryLiteBuyerDeliveryPackageService" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_boundaries_and_next_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "commercial_boundary" in content
    assert "evidence_boundary" in content
    assert "pdf_boundary" in content
    assert "constitutional_boundary" in content

    assert "complete_operator_delivery_approval" in content
    assert "Review deliverables, approve scope, evidence boundary" in content
    assert "prepare_buyer_delivery_message" in content
    assert "generate_buyer_delivery_message" in content
    assert "resolve_buyer_delivery_package_gaps" in content
    assert "rerun_buyer_delivery_package" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_examples_and_relationships():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Full Operator Approval Example" in content
    assert "approval_status: operator_approved" in content
    assert "scope_approved: True" in content
    assert "evidence_boundary_approved: True" in content
    assert "commercial_terms_approved: True" in content
    assert "buyer_language_approved: True" in content
    assert "delivery_status: send_ready" in content
    assert "delivery_blockers: []" in content

    assert "Failed Export Package Example" in content
    assert "Binding quote: False" in content
    assert "Binding quote: True" in content
    assert "commercial_terms_present" in content

    assert "The proposal export package answers:" in content
    assert "The buyer delivery package answers:" in content
    assert "future send workflow" in content
    assert "delivery log" in content


def test_assessment_factory_lite_buyer_delivery_package_doc_names_commercial_compliance_and_constitutional_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The buyer delivery package does not create a binding quote" in content
    assert "operator approves final scope, price, payment terms" in content

    assert (
        "The Assessment Factory Lite Buyer Delivery Package does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG "
        "certified, or production-ready."
    ) in content
    assert "bounded paid-assessment conversation" in content

    assert "does not autonomously approve production launch" in content
    assert "send actions" in content
    assert "The deterministic GAGF Kernel remains the authoritative decision and verification layer." in content
    assert "AI may later explain or adapt buyer delivery language" in content
    assert "AI must not override deterministic delivery checks" in content
