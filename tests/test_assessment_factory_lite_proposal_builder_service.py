from backend.app.gagf.assessment_factory_lite_proposal_builder_service import (
    AssessmentFactoryLiteProposalBuilderService,
)


def service():
    return AssessmentFactoryLiteProposalBuilderService()


def test_assessment_factory_lite_proposal_builder_builds_contract():
    result = service().build_proposal()

    assert result["status"] == "ok"
    assert result["proposal_type"] == (
        "assessment_factory_lite_paid_assessment_proposal"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-commercial-offer"
    assert result["version"] == "1.9.0"
    assert result["proposal_stage"] == "proposal_ready_artifact"
    assert result["recommended_action"] == "review_proposal_ready_artifact"


def test_assessment_factory_lite_proposal_builder_title_buyer_and_problem():
    result = service().build_proposal()

    assert result["proposal_title"] == (
        "Assessment Factory Lite Proposal for approval and handoff workflow"
    )

    assert result["buyer_context"]["primary_buyer"] == "operations_leader"
    assert result["buyer_context"]["secondary_buyers"] == [
        "it_manager",
        "workflow_owner",
        "founder_operator",
    ]
    assert "workflow drag" in result["buyer_context"]["buyer_pain"]

    assert result["problem_statement"]["workflow_area"] == (
        "approval and handoff workflow"
    )
    assert result["problem_statement"]["default_friction_hypothesis"] == (
        "approval_delay"
    )


def test_assessment_factory_lite_proposal_builder_scope_and_evidence_boundary():
    result = service().build_proposal()

    scope = result["proposed_scope"]
    evidence = result["evidence_boundary"]

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


def test_assessment_factory_lite_proposal_builder_deliverables_and_timeline():
    result = service().build_proposal()

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

    assert deliverables["recommended_next_test"]["format"] == "short_action_plan"
    assert "next_test" in deliverables["recommended_next_test"]["sections"]

    timeline = result["timeline"]

    assert timeline["estimated_duration"] == "3_to_5_business_days"
    assert [phase["phase"] for phase in timeline["phases"]] == [
        "intake",
        "evidence_review",
        "diagnostic_summary",
        "recommendation_review",
    ]


def test_assessment_factory_lite_proposal_builder_commercial_terms_and_exclusions():
    result = service().build_proposal()

    terms = result["commercial_terms_placeholder"]

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
    }

    assert "production_customer_data_processing" in result["excluded_scope"]
    assert "regulated_data_processing" in result["excluded_scope"]
    assert "federal_data_processing" in result["excluded_scope"]
    assert "guaranteed_operational_outcomes" in result["excluded_scope"]
    assert "binding_legal_or_compliance_advice" in result["excluded_scope"]


def test_assessment_factory_lite_proposal_builder_assumptions_approvals_and_controls():
    result = service().build_proposal()

    assert result["assumptions"] == [
        "buyer_selects_one_workflow_for_assessment",
        "buyer_provides_safe_non_sensitive_evidence_only",
        "operator_reviews_evidence_boundary_before_analysis",
        "assessment_output_is_reviewed_before_buyer_delivery",
        "final_price_and_terms_are_operator_approved",
    ]

    approvals = {
        item["approval"]: item for item in result["approval_requirements"]
    }

    assert set(approvals) == {
        "evidence_boundary_approval",
        "commercial_terms_approval",
        "buyer_scope_acknowledgement",
    }
    assert all(item["required"] is True for item in approvals.values())

    controls = {
        item["control"]: item for item in result["proposal_risk_controls"]
    }

    assert set(controls) == {
        "non_binding_proposal_until_operator_approval",
        "safe_evidence_boundary_required",
        "excluded_scope_must_be_visible",
        "human_review_before_sending",
    }
    assert all(item["required"] is True for item in controls.values())


def test_assessment_factory_lite_proposal_builder_source_offer_and_next_action():
    result = service().build_proposal()

    assert result["source_offer"] == {
        "offer_type": "assessment_factory_lite_paid_assessment_offer",
        "offer_stage": "paid_assessment_conversion",
        "release": "assessment-factory-lite-buyer-conversion",
        "version": "1.8.0",
        "recommended_action": "present_paid_assessment_offer",
    }

    assert result["next_action"] == {
        "action": "review_and_prepare_proposal",
        "operator_instruction": (
            "Review the proposal-ready artifact, confirm evidence boundary, "
            "approve commercial terms, and decide whether to generate a formal "
            "proposal document."
        ),
        "future_action": "generate_formal_proposal",
    }


def test_assessment_factory_lite_proposal_builder_accepts_custom_context():
    result = service().build_proposal(
        buyer_context={
            "primary_buyer": "founder_operator",
            "workflow_area": "security review workflow",
            "duration": "5_to_7_business_days",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    assert result["proposal_title"] == (
        "Assessment Factory Lite Proposal for security review workflow"
    )
    assert result["buyer_context"]["primary_buyer"] == "founder_operator"
    assert result["problem_statement"]["workflow_area"] == "security review workflow"
    assert result["proposed_scope"]["workflow_area"] == "security review workflow"
    assert result["proposed_scope"]["duration"] == "5_to_7_business_days"
    assert result["commercial_terms_placeholder"]["recommended_price_band"] == {
        "low": 1500,
        "high": 3500,
    }
