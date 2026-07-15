from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_operator_runbook_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["runbook_type"] == (
        "assessment_factory_lite_demo_operator_runbook"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-styling-export"
    assert payload["version"] == "1.6.0"
    assert payload["runbook_stage"] == "demo_delivery_packaging"
    assert payload["recommended_action"] == "use_operator_runbook_for_demo_delivery"


def test_assessment_factory_lite_operator_runbook_endpoint_returns_summary():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    payload = response.json()
    summary = payload["runbook_summary"]

    assert summary["primary_operator"] == "founder_operator"
    assert summary["delivery_mode"] == "live_walkthrough"
    assert summary["estimated_duration"] == "10_to_20_minutes"
    assert "operational friction" in summary["positioning"]
    assert summary["target_audience"] == [
        "operations_leader",
        "it_manager",
        "workflow_owner",
        "early_buyer",
    ]


def test_assessment_factory_lite_operator_runbook_endpoint_returns_pre_demo_checklist():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    payload = response.json()

    checks = {item["check"]: item for item in payload["pre_demo_checklist"]}

    assert set(checks) == {
        "version_endpoint_ready",
        "delivery_manifest_available",
        "scenario_menu_available",
        "styled_html_screen_available",
        "buyer_export_polish_available",
        "demo_boundary_visible",
    }

    assert checks["version_endpoint_ready"]["expected"] == (
        "1.6.0 assessment-factory-lite-demo-styling-export"
    )
    assert all(item["required"] is True for item in payload["pre_demo_checklist"])


def test_assessment_factory_lite_operator_runbook_endpoint_returns_live_demo_sequence():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    payload = response.json()

    assert [step["step"] for step in payload["live_demo_sequence"]] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
    ]

    assert [step["title"] for step in payload["live_demo_sequence"]] == [
        "Open with the problem",
        "Show the scenario menu",
        "Load the standard demo",
        "Explain the finding",
        "Show buyer export polish",
        "Show boundary protection",
        "Close with next evidence question",
    ]


def test_assessment_factory_lite_operator_runbook_endpoint_returns_scenario_talking_points():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    payload = response.json()
    scenarios = {
        scenario["scenario"]: scenario
        for scenario in payload["scenario_talking_points"]
    }

    assert set(scenarios) == {"standard", "invalid", "empty"}
    assert scenarios["standard"]["label"] == "Approval Delay and Blocked Work"
    assert scenarios["standard"]["expected_message"] == (
        "Approval delays are creating workflow drag."
    )
    assert scenarios["standard"]["recommended_intervention"] == (
        "streamline_approval_path"
    )
    assert scenarios["invalid"]["recommended_intervention"] == (
        "repair_sample_csv_before_demo"
    )
    assert scenarios["empty"]["recommended_intervention"] == "add_demo_rows"


def test_assessment_factory_lite_operator_runbook_endpoint_returns_safety_rules_and_stop_conditions():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    payload = response.json()

    rules = {rule["rule"] for rule in payload["operator_safety_rules"]}
    stop_conditions = {
        condition["condition"] for condition in payload["stop_conditions"]
    }

    assert rules == {
        "use_sample_data_only",
        "avoid_certification_claims",
        "do_not_overstate_automation",
        "preserve_traceability",
        "ask_for_workflow_similarity",
    }

    assert stop_conditions == {
        "buyer_requests_real_data_upload",
        "regulated_or_federal_data_is_offered",
        "certification_claim_requested",
        "unsafe_sample_rows_detected",
    }


def test_assessment_factory_lite_operator_runbook_endpoint_returns_follow_up_and_success_criteria():
    response = client.get(
        "/products/assessment-factory-lite/delivery/runbook"
    )

    payload = response.json()

    follow_ups = {item["follow_up"] for item in payload["buyer_follow_up"]}

    assert follow_ups == {
        "workflow_similarity_question",
        "evidence_source_question",
        "first_intervention_question",
    }

    assert "scenario_menu_is_visible" in payload["success_criteria"]
    assert "standard_demo_renders_successfully" in payload["success_criteria"]
    assert "buyer_export_polish_is_presented" in payload["success_criteria"]
    assert "no_real_customer_data_is_used" in payload["success_criteria"]


def test_assessment_factory_lite_operator_runbook_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/delivery/runbook" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.7.0",
        "release": "assessment-factory-lite-demo-delivery-packaging",
        "sprint": "4.6",
        "status": "complete",
    }
