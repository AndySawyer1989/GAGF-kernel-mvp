from backend.app.gagf.assessment_factory_lite_offer_builder_service import (
    AssessmentFactoryLiteOfferBuilderService,
)


def service():
    return AssessmentFactoryLiteOfferBuilderService()


def test_assessment_factory_lite_offer_builder_builds_contract():
    result = service().build_offer()

    assert result["status"] == "ok"
    assert result["offer_type"] == "assessment_factory_lite_paid_assessment_offer"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-buyer-conversion"
    assert result["version"] == "1.8.0"
    assert result["offer_stage"] == "paid_assessment_conversion"
    assert result["recommended_action"] == "present_paid_assessment_offer"


def test_assessment_factory_lite_offer_builder_target_buyer_and_problem_statement():
    result = service().build_offer()

    assert result["target_buyer"]["primary_buyer"] == "operations_leader"
    assert result["target_buyer"]["secondary_buyers"] == [
        "it_manager",
        "workflow_owner",
        "founder_operator",
    ]
    assert "workflow drag" in result["target_buyer"]["buyer_pain"]

    assert result["problem_statement"]["workflow_area"] == (
        "approval and handoff workflow"
    )
    assert result["problem_statement"]["default_friction_hypothesis"] == (
        "approval_delay"
    )
    assert "highest-friction constraint" in result["problem_statement"]["statement"]


def test_assessment_factory_lite_offer_builder_safe_evidence_request():
    result = service().build_offer()
    evidence = result["safe_evidence_request"]

    assert evidence["request_type"] == "safe_non_sensitive_workflow_evidence"
    assert evidence["requested_sources"] == [
        "sanitized_workflow_export",
        "approval_timestamps",
        "handoff_log",
        "blocked_work_items",
    ]
    assert "sanitized_csv" in evidence["allowed_format"]
    assert "redacted_export" in evidence["allowed_format"]
    assert "regulated_health_data" in evidence["prohibited_data"]
    assert "federal_sensitive_data" in evidence["prohibited_data"]
    assert "credentials" in evidence["prohibited_data"]


def test_assessment_factory_lite_offer_builder_scope_and_exclusions():
    result = service().build_offer()

    scope = result["assessment_scope"]

    assert scope["scope_type"] == "bounded_friction_assessment"
    assert scope["duration"] == "3_to_5_business_days"
    assert "review_safe_workflow_evidence" in scope["included_work"]
    assert "identify_top_friction_point" in scope["included_work"]
    assert "recommend_one_focused_intervention" in scope["included_work"]

    assert "production_customer_data_processing" in result["excluded_scope"]
    assert "regulated_data_processing" in result["excluded_scope"]
    assert "federal_data_processing" in result["excluded_scope"]
    assert "guaranteed_operational_outcomes" in result["excluded_scope"]
    assert "binding_legal_or_compliance_advice" in result["excluded_scope"]


def test_assessment_factory_lite_offer_builder_deliverable_and_price_band():
    result = service().build_offer()

    deliverable = result["deliverable"]
    price = result["recommended_price_band"]

    assert deliverable["deliverable_type"] == (
        "assessment_factory_lite_buyer_summary"
    )
    assert deliverable["format"] == "markdown_or_pdf_ready_summary"
    assert "executive_summary" in deliverable["sections"]
    assert "workflow_friction_finding" in deliverable["sections"]
    assert "recommended_intervention" in deliverable["sections"]

    assert price == {
        "currency": "USD",
        "low": 500,
        "high": 2500,
        "pricing_model": "fixed_fee_discovery_assessment",
        "pricing_note": (
            "Final pricing is operator-approved and should not be treated as "
            "an automated binding quote."
        ),
    }


def test_assessment_factory_lite_offer_builder_commitment_questions_and_risk_controls():
    result = service().build_offer()

    assert result["buyer_commitment"]["commitment_type"] == (
        "small_bounded_assessment"
    )
    assert "one_workflow_to_assess" in result["buyer_commitment"]["buyer_provides"]
    assert "safe_non_sensitive_evidence" in result["buyer_commitment"]["buyer_provides"]

    questions = {
        item["question_type"]: item for item in result["qualification_questions"]
    }

    assert set(questions) == {
        "workflow_similarity",
        "evidence_source",
        "first_test",
        "buyer_value",
    }
    assert all(item["used_for_offer"] is True for item in questions.values())

    controls = {item["control"]: item for item in result["risk_controls"]}

    assert set(controls) == {
        "sample_or_redacted_data_only",
        "operator_price_approval",
        "excluded_scope_visibility",
        "human_review_before_delivery",
    }
    assert all(item["required"] is True for item in controls.values())


def test_assessment_factory_lite_offer_builder_next_action_and_source_script():
    result = service().build_offer()

    assert result["next_action"]["action"] == "schedule_paid_assessment_conversation"
    assert "small bounded assessment" in result["next_action"]["recommended_message"]
    assert "approve final price" in result["next_action"]["operator_instruction"]

    assert result["source_script"] == {
        "script_type": "assessment_factory_lite_buyer_walkthrough_script",
        "script_stage": "buyer_demo_conversion",
        "recommended_action": "use_buyer_walkthrough_script",
    }


def test_assessment_factory_lite_offer_builder_custom_context_and_boundary():
    result = service().build_offer(
        buyer_context={
            "primary_buyer": "founder_operator",
            "workflow_area": "security review workflow",
            "duration": "5_to_7_business_days",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    assert result["target_buyer"]["primary_buyer"] == "founder_operator"
    assert result["problem_statement"]["workflow_area"] == "security review workflow"
    assert result["assessment_scope"]["workflow_area"] == "security review workflow"
    assert result["assessment_scope"]["duration"] == "5_to_7_business_days"
    assert result["recommended_price_band"]["low"] == 1500
    assert result["recommended_price_band"]["high"] == 3500

    boundary = result["demo_boundary"]

    assert boundary["boundary_type"] == "demo_and_assessment_intake_boundary"
    assert "sanitized_csv" in boundary["allowed_data"]
    assert "redacted_workflow_export" in boundary["allowed_data"]
    assert "regulated_health_data" in boundary["prohibited_data"]
    assert "federal_sensitive_data" in boundary["prohibited_data"]
    assert boundary["certification_claims_allowed"] is False
    assert boundary["binding_price_quote_allowed"] is False