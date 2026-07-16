from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


def service():
    return AssessmentFactoryLiteFormalProposalMarkdownExportService()


def test_assessment_factory_lite_formal_proposal_markdown_export_builds_contract():
    result = service().export_markdown()

    assert result["status"] == "ok"
    assert result["export_type"] == (
        "assessment_factory_lite_formal_proposal_markdown_export"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-package"
    assert result["version"] == "2.0.0"
    assert result["export_stage"] == "formal_proposal_markdown_export"
    assert result["format"] == "markdown"
    assert result["recommended_action"] == "review_formal_proposal_markdown_export"


def test_assessment_factory_lite_formal_proposal_markdown_export_returns_filename_source_and_sections():
    result = service().export_markdown()

    assert result["filename"] == (
        "assessment-factory-lite-proposal-approval-and-handoff-workflow.md"
    )

    assert result["source_document"] == {
        "document_type": "assessment_factory_lite_formal_proposal_document",
        "document_stage": "formal_proposal_document_draft",
        "release": "assessment-factory-lite-proposal-package",
        "version": "2.0.0",
        "recommended_action": "review_formal_proposal_document",
    }

    assert result["export_sections"] == [
        "proposal_metadata",
        "buyer_summary",
        "problem_statement",
        "assessment_scope",
        "evidence_boundary",
        "deliverables",
        "timeline",
        "commercial_terms",
        "assumptions",
        "approval_requirements",
        "exclusions",
        "operator_notes",
        "next_action",
        "boundary_notice",
    ]


def test_assessment_factory_lite_formal_proposal_markdown_export_contains_title_and_metadata():
    markdown = service().export_markdown()["markdown"]

    assert markdown.startswith(
        "# Formal Assessment Factory Lite Proposal for approval and handoff workflow"
    )
    assert "## Proposal Metadata" in markdown
    assert "- Document type: assessment_factory_lite_formal_proposal_document" in markdown
    assert "- Package: Assessment Factory Lite Demo Package" in markdown
    assert "- Release: assessment-factory-lite-proposal-package" in markdown
    assert "- Version: 2.0.0" in markdown
    assert "- Stage: formal_proposal_document_draft" in markdown


def test_assessment_factory_lite_formal_proposal_markdown_export_contains_buyer_problem_scope_and_evidence():
    markdown = service().export_markdown()["markdown"]

    assert "## Buyer Summary" in markdown
    assert "- Primary buyer: operations_leader" in markdown
    assert "it_manager, workflow_owner, founder_operator" in markdown
    assert "workflow drag" in markdown

    assert "## Problem Statement" in markdown
    assert "- Workflow area: approval and handoff workflow" in markdown
    assert "- Default friction hypothesis: approval_delay" in markdown

    assert "## Assessment Scope" in markdown
    assert "- Scope type: bounded_friction_assessment" in markdown
    assert "- Duration: 3_to_5_business_days" in markdown
    assert "- review_safe_workflow_evidence" in markdown
    assert "- recommend_one_focused_intervention" in markdown

    assert "## Evidence Boundary" in markdown
    assert "- Request type: safe_non_sensitive_workflow_evidence" in markdown
    assert "sanitized_workflow_export" in markdown
    assert "redacted_workflow_export" in markdown
    assert "regulated_health_data" in markdown
    assert "federal_sensitive_data" in markdown
    assert "- Certification claims allowed: False" in markdown
    assert "- Binding price quote allowed: False" in markdown


def test_assessment_factory_lite_formal_proposal_markdown_export_contains_deliverables_and_timeline():
    markdown = service().export_markdown()["markdown"]

    assert "## Deliverables" in markdown
    assert "### assessment_summary" in markdown
    assert "- Format: markdown_or_pdf_ready_summary" in markdown
    assert "workflow_friction_finding" in markdown
    assert "recommended_intervention" in markdown

    assert "### recommended_next_test" in markdown
    assert "- Format: short_action_plan" in markdown
    assert "owner_or_stakeholder" in markdown

    assert "## Timeline" in markdown
    assert "- Estimated duration: 3_to_5_business_days" in markdown
    assert "### intake" in markdown
    assert "### evidence_review" in markdown
    assert "### diagnostic_summary" in markdown
    assert "### recommendation_review" in markdown


def test_assessment_factory_lite_formal_proposal_markdown_export_contains_terms_assumptions_and_approvals():
    markdown = service().export_markdown()["markdown"]

    assert "## Commercial Terms" in markdown
    assert "- Pricing model: fixed_fee_discovery_assessment" in markdown
    assert "- Currency: USD" in markdown
    assert "- Recommended price band: USD 500 - 2500" in markdown
    assert "- Payment terms: operator_to_define" in markdown
    assert "- Proposal expiration: operator_to_define" in markdown
    assert "- Binding quote: False" in markdown
    assert "- Terms status: operator_to_finalize" in markdown

    assert "## Assumptions" in markdown
    assert "- buyer_selects_one_workflow_for_assessment" in markdown
    assert "- buyer_provides_safe_non_sensitive_evidence_only" in markdown
    assert "- final_price_and_terms_are_operator_approved" in markdown

    assert "## Approval Requirements" in markdown
    assert "### evidence_boundary_approval" in markdown
    assert "### commercial_terms_approval" in markdown
    assert "### buyer_scope_acknowledgement" in markdown


def test_assessment_factory_lite_formal_proposal_markdown_export_contains_exclusions_notes_next_action_and_boundary():
    markdown = service().export_markdown()["markdown"]

    assert "## Exclusions" in markdown
    assert "- production_customer_data_processing" in markdown
    assert "- regulated_data_processing" in markdown
    assert "- federal_data_processing" in markdown
    assert "- binding_legal_or_compliance_advice" in markdown
    assert "- binding_price_quote" in markdown
    assert "- binding_sales_contract" in markdown
    assert "- legal_or_compliance_certification" in markdown

    assert "## Operator Notes" in markdown
    assert "### review_scope_before_sending" in markdown
    assert "### review_evidence_boundary_before_sending" in markdown
    assert "### review_terms_before_sending" in markdown

    assert "## Next Action" in markdown
    assert "- Action: review_and_finalize_formal_proposal_document" in markdown
    assert "- Future action: export_formal_proposal_document" in markdown

    assert "## Boundary Notice" in markdown
    assert "not a binding quote, sales contract, invoice" in markdown
    assert "The deterministic GAGF Kernel remains the authoritative decision" in markdown


def test_assessment_factory_lite_formal_proposal_markdown_export_accepts_custom_context():
    result = service().export_markdown(
        buyer_context={
            "primary_buyer": "founder_operator",
            "workflow_area": "security review workflow",
            "duration": "5_to_7_business_days",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    assert result["filename"] == (
        "assessment-factory-lite-proposal-security-review-workflow.md"
    )

    markdown = result["markdown"]

    assert "# Formal Assessment Factory Lite Proposal for security review workflow" in markdown
    assert "- Primary buyer: founder_operator" in markdown
    assert "- Workflow area: security review workflow" in markdown
    assert "- Duration: 5_to_7_business_days" in markdown
    assert "- Recommended price band: USD 1500 - 3500" in markdown