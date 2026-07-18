from backend.app.gagf.assessment_factory_lite_formal_proposal_document_service import (
    AssessmentFactoryLiteFormalProposalDocumentService,
)


def service():
    return AssessmentFactoryLiteFormalProposalDocumentService()


def test_assessment_factory_lite_formal_proposal_document_builds_contract():
    result = service().build_document()

    assert result["status"] == "ok"
    assert result["document_type"] == (
        "assessment_factory_lite_formal_proposal_document"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-proposal-package"
    assert result["version"] == "2.0.0"
    assert result["document_stage"] == "formal_proposal_document_draft"
    assert result["recommended_action"] == "review_formal_proposal_document"


def test_assessment_factory_lite_formal_proposal_document_title_and_buyer_summary():
    result = service().build_document()

    assert result["document_title"] == (
        "Formal Assessment Factory Lite Proposal for approval and handoff workflow"
    )

    summary = result["buyer_summary"]

    assert summary["primary_buyer"] == "operations_leader"
    assert summary["secondary_buyers"] == [
        "it_manager",
        "workflow_owner",
        "founder_operator",
    ]
    assert "workflow drag" in summary["buyer_pain"]
    assert "approval and handoff workflow" in summary["summary"]


def test_assessment_factory_lite_formal_proposal_document_problem_scope_and_evidence():
    result = service().build_document()

    problem = result["problem_statement"]
    scope = result["assessment_scope"]
    evidence = result["evidence_boundary"]

    assert problem["workflow_area"] == "approval and handoff workflow"
    assert problem["default_friction_hypothesis"] == "approval_delay"

    assert scope["scope_type"] == "bounded_friction_assessment"
    assert scope["duration"] == "3_to_5_business_days"
    assert "review_safe_workflow_evidence" in scope["included_work"]
    assert "recommend_one_focused_intervention" in scope["included_work"]
    assert "one bounded workflow assessment" in scope["scope_boundary"]

    assert evidence["request_type"] == "safe_non_sensitive_workflow_evidence"
    assert "sanitized_workflow_export" in evidence["requested_sources"]
    assert "sanitized_csv" in evidence["allowed_format"]
    assert "redacted_workflow_export" in evidence["allowed_data"]
    assert "regulated_health_data" in evidence["prohibited_data"]
    assert "federal_sensitive_data" in evidence["prohibited_data"]
    assert evidence["certification_claims_allowed"] is False
    assert evidence["binding_price_quote_allowed"] is False


def test_assessment_factory_lite_formal_proposal_document_deliverables_and_timeline():
    result = service().build_document()

    deliverables = {item["deliverable"]: item for item in result["deliverables"]}

    assert set(deliverables) == {
        "assessment_summary",
        "recommended_next_test",
    }

    assert deliverables["assessment_summary"]["format"] == (
        "markdown_or_pdf_ready_summary"
    )
    assert "workflow_friction_finding" in deliverables["assessment_summary"]["sections"]
    assert "recommended_intervention" in deliverables["assessment_summary"]["sections"]

    timeline = result["timeline"]

    assert timeline["estimated_duration"] == "3_to_5_business_days"
    assert [phase["phase"] for phase in timeline["phases"]] == [
        "intake",
        "evidence_review",
        "diagnostic_summary",
        "recommendation_review",
    ]


def test_assessment_factory_lite_formal_proposal_document_terms_assumptions_and_approvals():
    result = service().build_document()

    terms = result["commercial_terms"]

    assert terms == {
        "pricing_model": "fixed_fee_discovery_assessment",
        "currency": "USD",
        "recommended_price_band": {
            "low": 500,
            "high": 2500,
        },
        "payment_terms": "operator_to_define",
        "proposal_expiration": "operator_to_define",
        "pricing_note": (
            "Final pricing is operator-approved and should not be treated as "
            "an automated binding quote."
        ),
        "binding_quote": False,
        "terms_status": "operator_to_finalize",
    }

    assert "buyer_selects_one_workflow_for_assessment" in result["assumptions"]
    assert "buyer_provides_safe_non_sensitive_evidence_only" in result["assumptions"]
    assert "final_price_and_terms_are_operator_approved" in result["assumptions"]

    approvals = {
        item["approval"]: item for item in result["approval_requirements"]
    }

    assert set(approvals) == {
        "evidence_boundary_approval",
        "commercial_terms_approval",
        "buyer_scope_acknowledgement",
    }


def test_assessment_factory_lite_formal_proposal_document_exclusions_and_operator_notes():
    result = service().build_document()

    assert "production_customer_data_processing" in result["exclusions"]
    assert "regulated_data_processing" in result["exclusions"]
    assert "federal_data_processing" in result["exclusions"]
    assert "guaranteed_operational_outcomes" in result["exclusions"]
    assert "binding_legal_or_compliance_advice" in result["exclusions"]
    assert "binding_price_quote" in result["exclusions"]
    assert "binding_sales_contract" in result["exclusions"]
    assert "production_service_commitment" in result["exclusions"]
    assert "legal_or_compliance_certification" in result["exclusions"]

    notes = {item["note"]: item for item in result["operator_notes"]}

    assert set(notes) == {
        "review_scope_before_sending",
        "review_evidence_boundary_before_sending",
        "review_terms_before_sending",
    }
    assert all(item["required"] is True for item in notes.values())


def test_assessment_factory_lite_formal_proposal_document_source_sections_and_next_action():
    result = service().build_document()

    assert result["source_proposal"] == {
        "proposal_type": "assessment_factory_lite_paid_assessment_proposal",
        "proposal_stage": "proposal_ready_artifact",
        "release": "assessment-factory-lite-commercial-offer",
        "version": "1.9.0",
        "recommended_action": "review_proposal_ready_artifact",
    }

    assert result["document_sections"] == [
        "document_title",
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
    ]

    assert result["next_action"] == {
        "action": "review_and_finalize_formal_proposal_document",
        "operator_instruction": (
            "Review the formal proposal document draft, finalize commercial "
            "terms, confirm evidence boundaries, and decide whether to export "
            "a buyer-facing document."
        ),
        "future_action": "export_formal_proposal_document",
    }


def test_assessment_factory_lite_formal_proposal_document_accepts_custom_context():
    result = service().build_document(
        buyer_context={
            "primary_buyer": "founder_operator",
            "workflow_area": "security review workflow",
            "duration": "5_to_7_business_days",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    assert result["document_title"] == (
        "Formal Assessment Factory Lite Proposal for security review workflow"
    )
    assert result["buyer_summary"]["primary_buyer"] == "founder_operator"
    assert result["problem_statement"]["workflow_area"] == "security review workflow"
    assert result["assessment_scope"]["workflow_area"] == "security review workflow"
    assert result["assessment_scope"]["duration"] == "5_to_7_business_days"
    assert result["commercial_terms"]["recommended_price_band"] == {
        "low": 1500,
        "high": 3500,
    }
