from backend.app.gagf.assessment_factory_lite_buyer_walkthrough_script_service import (
    AssessmentFactoryLiteBuyerWalkthroughScriptService,
)


def service():
    return AssessmentFactoryLiteBuyerWalkthroughScriptService()


def test_assessment_factory_lite_buyer_walkthrough_script_builds_contract():
    result = service().build_script()

    assert result["status"] == "ok"
    assert result["script_type"] == (
        "assessment_factory_lite_buyer_walkthrough_script"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-delivery-packaging"
    assert result["version"] == "1.7.0"
    assert result["script_stage"] == "buyer_demo_conversion"
    assert result["recommended_action"] == "use_buyer_walkthrough_script"


def test_assessment_factory_lite_buyer_walkthrough_script_summary():
    result = service().build_script()
    summary = result["script_summary"]

    assert summary["primary_operator"] == "founder_operator"
    assert summary["delivery_mode"] == "guided_buyer_walkthrough"
    assert summary["estimated_duration"] == "10_to_20_minutes"
    assert summary["conversion_goal"] == (
        "move_from_demo_interest_to_paid_assessment_conversation"
    )
    assert "where work gets stuck" in summary["positioning"]


def test_assessment_factory_lite_buyer_walkthrough_script_opening_and_problem_frame():
    result = service().build_script()

    opening = result["opening_script"]
    problem = result["problem_frame"]

    assert opening["section"] == "opening"
    assert "sample-data-only demo" in opening["operator_script"]
    assert opening["duration"] == "1_to_2_minutes"

    assert problem["section"] == "problem_frame"
    assert "Most teams feel delays before they can prove them." in problem["operator_script"]
    assert problem["proof_point"] == (
        "sample workflow events become a ranked friction finding"
    )


def test_assessment_factory_lite_buyer_walkthrough_script_scenarios():
    result = service().build_script()
    scenarios = {item["scenario"]: item for item in result["scenario_script"]}

    assert set(scenarios) == {"standard", "invalid", "empty"}

    assert scenarios["standard"]["label"] == "Approval Delay and Blocked Work"
    assert scenarios["standard"]["expected_friction"] == "approval_delay"
    assert "synthetic workflow rows" in scenarios["standard"]["operator_script"]

    assert scenarios["invalid"]["label"] == "Unsafe Data Boundary Test"
    assert scenarios["invalid"]["expected_friction"] == "none"

    assert scenarios["empty"]["label"] == "Empty Demo Starting State"
    assert scenarios["empty"]["expected_friction"] == "none"


def test_assessment_factory_lite_buyer_walkthrough_script_finding_and_intervention():
    result = service().build_script()

    finding = result["finding_script"]
    intervention = result["intervention_script"]

    assert finding["section"] == "finding"
    assert finding["example_finding"] == (
        "Approval delays are creating workflow drag."
    )
    assert finding["evidence_link"] == "synthetic approval and blocked-work events"

    assert intervention["section"] == "intervention"
    assert intervention["recommended_intervention"] == "streamline_approval_path"
    assert intervention["buyer_value"] == (
        "reduce waiting time and make approval ownership clearer"
    )
    assert "does not mean removing accountability" in intervention["operator_script"]


def test_assessment_factory_lite_buyer_walkthrough_script_boundary_and_questions():
    result = service().build_script()

    boundary_script = result["boundary_script"]
    questions = {item["question_type"]: item for item in result["buyer_questions"]}

    assert boundary_script["section"] == "boundary"
    assert "synthetic sample data only" in boundary_script["operator_script"]
    assert "real_customer_data" in boundary_script["prohibited_data"]
    assert "regulated_data" in boundary_script["prohibited_data"]
    assert "federal_data" in boundary_script["prohibited_data"]

    assert set(questions) == {
        "workflow_similarity",
        "evidence_source",
        "first_test",
        "buyer_value",
    }
    assert "team gets stuck" in questions["workflow_similarity"]["question"]
    assert "safe, non-sensitive workflow evidence" in questions["evidence_source"]["question"]


def test_assessment_factory_lite_buyer_walkthrough_script_close_and_objections():
    result = service().build_script()

    close_script = result["close_script"]
    objections = {item["objection"]: item for item in result["objection_responses"]}

    assert close_script["section"] == "close"
    assert close_script["call_to_action"] == "schedule_paid_assessment_conversation"
    assert "small, bounded assessment" in close_script["operator_script"]

    assert set(objections) == {
        "we_do_not_want_to_upload_sensitive_data",
        "we_already_know_where_the_problem_is",
        "this_looks_like_project_management",
        "is_this_production_ready",
    }

    assert "sample-data-only buyer demo" in objections["is_this_production_ready"]["response"]


def test_assessment_factory_lite_buyer_walkthrough_script_success_criteria_and_boundary():
    result = service().build_script()

    assert "buyer_understands_sample_data_only_boundary" in result["success_criteria"]
    assert "buyer_understands_operational_friction_problem" in result["success_criteria"]
    assert "buyer_identifies_workflow_similarity" in result["success_criteria"]
    assert "operator_can_transition_to_assessment_offer" in result["success_criteria"]

    boundary = result["demo_boundary"]

    assert boundary["boundary_type"] == "demo_only_sample_data"
    assert boundary["allowed_data"] == [
        "sample_csv",
        "synthetic_workflow_events",
        "mock_approval_events",
        "mock_delay_events",
    ]
    assert boundary["prohibited_data"] == [
        "real_customer_data",
        "regulated_data",
        "federal_data",
        "production_customer_data",
        "customer_secrets",
        "live_security_telemetry",
    ]
    assert boundary["certification_claims_allowed"] is False