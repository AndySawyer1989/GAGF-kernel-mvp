from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_delivery_readiness_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["readiness_type"] == (
        "assessment_factory_lite_demo_delivery_readiness"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-styling-export"
    assert payload["version"] == "1.6.0"
    assert payload["delivery_stage"] == "demo_delivery_packaging"
    assert payload["recommended_action"] == "proceed_with_demo_delivery"


def test_assessment_factory_lite_delivery_readiness_endpoint_reports_ready():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    payload = response.json()

    assert payload["readiness_status"] == "ready"
    assert payload["is_ready"] is True
    assert payload["passed_check_count"] == 8
    assert payload["failed_check_count"] == 0
    assert payload["failed_checks"] == []


def test_assessment_factory_lite_delivery_readiness_endpoint_returns_checks():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    payload = response.json()

    assert {check["check"] for check in payload["checks"]} == {
        "delivery_manifest_ready",
        "operator_runbook_ready",
        "sample_scenarios_ready",
        "scenario_menu_ready",
        "styled_html_screen_ready",
        "buyer_export_polish_ready",
        "demo_boundary_ready",
        "operator_stop_conditions_ready",
    }

    assert all(check["required"] is True for check in payload["checks"])
    assert all(check["status"] == "passed" for check in payload["checks"])
    assert all(check["repair_action"] == "none" for check in payload["checks"])


def test_assessment_factory_lite_delivery_readiness_endpoint_returns_delivery_decision():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    payload = response.json()

    assert payload["delivery_decision"] == {
        "decision": "go",
        "summary": (
            "The Assessment Factory Lite demo delivery package is ready "
            "for a sample-data-only live walkthrough."
        ),
        "next_action": "proceed_with_demo_delivery",
    }


def test_assessment_factory_lite_delivery_readiness_endpoint_returns_source_artifacts():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    payload = response.json()

    assert payload["source_artifacts"] == {
        "manifest_type": "assessment_factory_lite_demo_delivery_manifest",
        "runbook_type": "assessment_factory_lite_demo_operator_runbook",
        "standard_sample_status": "ok",
        "html_screen_type": "assessment_factory_lite_demo_ui_html_screen",
        "buyer_export_polish_type": "assessment_factory_lite_buyer_export_polish",
    }


def test_assessment_factory_lite_delivery_readiness_endpoint_returns_key_check_summaries():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    payload = response.json()
    checks = {check["check"]: check for check in payload["checks"]}

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


def test_assessment_factory_lite_delivery_readiness_endpoint_preserves_demo_boundary():
    response = client.get(
        "/products/assessment-factory-lite/delivery/readiness"
    )

    payload = response.json()
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


def test_assessment_factory_lite_delivery_readiness_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/delivery/readiness" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }






