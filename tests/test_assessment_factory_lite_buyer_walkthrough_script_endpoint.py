from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["script_type"] == (
        "assessment_factory_lite_buyer_walkthrough_script"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-delivery-packaging"
    assert payload["version"] == "1.7.0"
    assert payload["script_stage"] == "buyer_demo_conversion"
    assert payload["recommended_action"] == "use_buyer_walkthrough_script"


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_summary():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    payload = response.json()
    summary = payload["script_summary"]

    assert summary["primary_operator"] == "founder_operator"
    assert summary["delivery_mode"] == "guided_buyer_walkthrough"
    assert summary["estimated_duration"] == "10_to_20_minutes"
    assert summary["conversion_goal"] == (
        "move_from_demo_interest_to_paid_assessment_conversation"
    )
    assert "where work gets stuck" in summary["positioning"]


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_opening_and_problem_frame():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    payload = response.json()

    opening = payload["opening_script"]
    problem = payload["problem_frame"]

    assert opening["section"] == "opening"
    assert "sample-data-only demo" in opening["operator_script"]
    assert opening["duration"] == "1_to_2_minutes"

    assert problem["section"] == "problem_frame"
    assert "Most teams feel delays before they can prove them." in problem["operator_script"]
    assert problem["proof_point"] == (
        "sample workflow events become a ranked friction finding"
    )


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_scenarios():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    payload = response.json()
    scenarios = {item["scenario"]: item for item in payload["scenario_script"]}

    assert set(scenarios) == {"standard", "invalid", "empty"}

    assert scenarios["standard"]["label"] == "Approval Delay and Blocked Work"
    assert scenarios["standard"]["expected_friction"] == "approval_delay"
    assert "synthetic workflow rows" in scenarios["standard"]["operator_script"]

    assert scenarios["invalid"]["label"] == "Unsafe Data Boundary Test"
    assert scenarios["invalid"]["expected_friction"] == "none"

    assert scenarios["empty"]["label"] == "Empty Demo Starting State"
    assert scenarios["empty"]["expected_friction"] == "none"


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_finding_and_intervention():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    payload = response.json()

    finding = payload["finding_script"]
    intervention = payload["intervention_script"]

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


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_boundary_questions_and_close():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    payload = response.json()

    boundary_script = payload["boundary_script"]
    questions = {item["question_type"]: item for item in payload["buyer_questions"]}
    close_script = payload["close_script"]

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

    assert close_script["section"] == "close"
    assert close_script["call_to_action"] == "schedule_paid_assessment_conversation"
    assert "small, bounded assessment" in close_script["operator_script"]


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_returns_objections_success_and_boundary():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/script"
    )

    payload = response.json()

    objections = {item["objection"]: item for item in payload["objection_responses"]}

    assert set(objections) == {
        "we_do_not_want_to_upload_sensitive_data",
        "we_already_know_where_the_problem_is",
        "this_looks_like_project_management",
        "is_this_production_ready",
    }

    assert "sample-data-only buyer demo" in objections["is_this_production_ready"]["response"]

    assert "buyer_understands_sample_data_only_boundary" in payload["success_criteria"]
    assert "buyer_understands_operational_friction_problem" in payload["success_criteria"]
    assert "buyer_identifies_workflow_similarity" in payload["success_criteria"]
    assert "operator_can_transition_to_assessment_offer" in payload["success_criteria"]

    boundary = payload["demo_boundary"]

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


def test_assessment_factory_lite_buyer_walkthrough_script_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-walkthrough/script" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }




