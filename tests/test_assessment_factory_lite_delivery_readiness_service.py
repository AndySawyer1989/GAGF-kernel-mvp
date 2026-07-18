from backend.app.gagf.assessment_factory_lite_delivery_readiness_service import (
    AssessmentFactoryLiteDeliveryReadinessService,
)


def service():
    return AssessmentFactoryLiteDeliveryReadinessService()


def test_assessment_factory_lite_delivery_readiness_builds_contract():
    result = service().evaluate_readiness()

    assert result["status"] == "ok"
    assert result["readiness_type"] == (
        "assessment_factory_lite_demo_delivery_readiness"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-styling-export"
    assert result["version"] == "1.6.0"
    assert result["delivery_stage"] == "demo_delivery_packaging"
    assert result["recommended_action"] == "proceed_with_demo_delivery"


def test_assessment_factory_lite_delivery_readiness_is_ready():
    result = service().evaluate_readiness()

    assert result["readiness_status"] == "ready"
    assert result["is_ready"] is True
    assert result["passed_check_count"] == 8
    assert result["failed_check_count"] == 0
    assert result["failed_checks"] == []


def test_assessment_factory_lite_delivery_readiness_checks_are_all_required_and_passed():
    result = service().evaluate_readiness()

    assert {check["check"] for check in result["checks"]} == {
        "delivery_manifest_ready",
        "operator_runbook_ready",
        "sample_scenarios_ready",
        "scenario_menu_ready",
        "styled_html_screen_ready",
        "buyer_export_polish_ready",
        "demo_boundary_ready",
        "operator_stop_conditions_ready",
    }

    assert all(check["required"] is True for check in result["checks"])
    assert all(check["status"] == "passed" for check in result["checks"])
    assert all(check["repair_action"] == "none" for check in result["checks"])


def test_assessment_factory_lite_delivery_readiness_delivery_decision():
    result = service().evaluate_readiness()

    assert result["delivery_decision"] == {
        "decision": "go",
        "summary": (
            "The Assessment Factory Lite demo delivery package is ready "
            "for a sample-data-only live walkthrough."
        ),
        "next_action": "proceed_with_demo_delivery",
    }


def test_assessment_factory_lite_delivery_readiness_source_artifacts():
    result = service().evaluate_readiness()

    assert result["source_artifacts"] == {
        "manifest_type": "assessment_factory_lite_demo_delivery_manifest",
        "runbook_type": "assessment_factory_lite_demo_operator_runbook",
        "standard_sample_status": "ok",
        "html_screen_type": "assessment_factory_lite_demo_ui_html_screen",
        "buyer_export_polish_type": "assessment_factory_lite_buyer_export_polish",
    }


def test_assessment_factory_lite_delivery_readiness_key_check_summaries():
    result = service().evaluate_readiness()
    checks = {check["check"]: check for check in result["checks"]}

    assert checks["delivery_manifest_ready"]["summary"] == (
        "Delivery manifest is available and includes required capabilities."
    )
    assert checks["operator_runbook_ready"]["summary"] == (
        "Operator runbook is available with checklist and live-demo sequence."
    )
    assert checks["styled_html_screen_ready"]["summary"] == (
        "Styled HTML screen renders scenario menu, sample loader, and style tokens."
    )
    assert checks["buyer_export_polish_ready"]["summary"] == (
        "Buyer export polish is available for the standard scenario."
    )


def test_assessment_factory_lite_delivery_readiness_preserves_demo_boundary():
    result = service().evaluate_readiness()
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


def test_assessment_factory_lite_delivery_readiness_response_keys():
    result = service().evaluate_readiness()

    assert set(result) == {
        "status",
        "readiness_type",
        "package_name",
        "release",
        "version",
        "delivery_stage",
        "readiness_status",
        "is_ready",
        "checks",
        "passed_check_count",
        "failed_check_count",
        "failed_checks",
        "delivery_decision",
        "source_artifacts",
        "demo_boundary",
        "operator_message",
        "recommended_action",
    }
