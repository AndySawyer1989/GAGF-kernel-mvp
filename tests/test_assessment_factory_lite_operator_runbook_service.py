from backend.app.gagf.assessment_factory_lite_operator_runbook_service import (
    AssessmentFactoryLiteOperatorRunbookService,
)


def service():
    return AssessmentFactoryLiteOperatorRunbookService()


def test_assessment_factory_lite_operator_runbook_builds_contract():
    result = service().build_runbook()

    assert result["status"] == "ok"
    assert result["runbook_type"] == (
        "assessment_factory_lite_demo_operator_runbook"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-styling-export"
    assert result["version"] == "1.6.0"
    assert result["runbook_stage"] == "demo_delivery_packaging"
    assert result["recommended_action"] == "use_operator_runbook_for_demo_delivery"


def test_assessment_factory_lite_operator_runbook_summary():
    result = service().build_runbook()
    summary = result["runbook_summary"]

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


def test_assessment_factory_lite_operator_runbook_pre_demo_checklist():
    result = service().build_runbook()

    checks = {item["check"]: item for item in result["pre_demo_checklist"]}

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

    assert all(item["required"] is True for item in result["pre_demo_checklist"])


def test_assessment_factory_lite_operator_runbook_live_demo_sequence():
    result = service().build_runbook()

    assert [step["step"] for step in result["live_demo_sequence"]] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
    ]

    titles = [step["title"] for step in result["live_demo_sequence"]]

    assert titles == [
        "Open with the problem",
        "Show the scenario menu",
        "Load the standard demo",
        "Explain the finding",
        "Show buyer export polish",
        "Show boundary protection",
        "Close with next evidence question",
    ]


def test_assessment_factory_lite_operator_runbook_scenario_talking_points():
    result = service().build_runbook()
    scenarios = {
        scenario["scenario"]: scenario
        for scenario in result["scenario_talking_points"]
    }

    assert set(scenarios) == {"standard", "invalid", "empty"}
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


def test_assessment_factory_lite_operator_runbook_safety_rules_and_stop_conditions():
    result = service().build_runbook()

    rules = {rule["rule"] for rule in result["operator_safety_rules"]}
    stop_conditions = {
        condition["condition"] for condition in result["stop_conditions"]
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


def test_assessment_factory_lite_operator_runbook_buyer_follow_up_and_success_criteria():
    result = service().build_runbook()

    follow_ups = {item["follow_up"] for item in result["buyer_follow_up"]}

    assert follow_ups == {
        "workflow_similarity_question",
        "evidence_source_question",
        "first_intervention_question",
    }

    assert "scenario_menu_is_visible" in result["success_criteria"]
    assert "standard_demo_renders_successfully" in result["success_criteria"]
    assert "buyer_export_polish_is_presented" in result["success_criteria"]
    assert "no_real_customer_data_is_used" in result["success_criteria"]


def test_assessment_factory_lite_operator_runbook_preserves_demo_boundary():
    result = service().build_runbook()
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
