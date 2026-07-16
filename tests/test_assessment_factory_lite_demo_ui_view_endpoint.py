from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def rows():
    return [
        {
            "event_id": "evt-001",
            "case_id": "case-001",
            "event_type": "approval_requested",
            "actor": "requester",
            "team": "operations",
            "timestamp": "2026-01-01T09:00:00Z",
            "severity": "medium",
            "description": "Synthetic approval request submitted.",
            "constraint_label": "approval_required",
            "duration_minutes": 0,
        },
        {
            "event_id": "evt-002",
            "case_id": "case-001",
            "event_type": "approval_delayed",
            "actor": "approver",
            "team": "operations",
            "timestamp": "2026-01-01T13:00:00Z",
            "severity": "high",
            "description": "Synthetic approval delayed.",
            "constraint_label": "approval_delay",
            "duration_minutes": 240,
        },
    ]


def test_assessment_factory_lite_demo_ui_view_endpoint_builds_view():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["view_type"] == "assessment_factory_lite_demo_ui_view"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-package"
    assert payload["version"] == "1.1.0"
    assert payload["recommended_action"] == (
        "render_assessment_factory_lite_demo_view"
    )


def test_assessment_factory_lite_demo_ui_view_endpoint_returns_sections():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows()},
    )

    payload = response.json()

    assert payload["ui_sections"] == [
        "demo_readiness",
        "sample_data_boundary",
        "dataset_contract",
        "dataset_validation",
        "governance_drag_summary",
        "top_friction_points",
        "recommended_intervention",
        "export_summary_preview",
        "next_steps",
        "compliance_disclaimer",
    ]


def test_assessment_factory_lite_demo_ui_view_endpoint_returns_cards():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows()},
    )

    payload = response.json()
    cards = {card["card_id"]: card for card in payload["cards"]}

    assert set(cards) == {
        "demo_readiness_card",
        "sample_data_boundary_card",
        "dataset_contract_card",
        "dataset_validation_card",
        "governance_drag_summary_card",
        "top_friction_points_card",
        "recommended_intervention_card",
        "export_summary_preview_card",
    }
    assert cards["dataset_validation_card"]["status"] == "passed"
    assert cards["top_friction_points_card"]["primary_value"] == (
        "approval_delay"
    )
    assert cards["recommended_intervention_card"]["primary_value"] == (
        "streamline_approval_path"
    )


def test_assessment_factory_lite_demo_ui_view_endpoint_preserves_data_boundary():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows()},
    )

    payload = response.json()

    assert payload["data_boundary"] == {
        "boundary_type": "demo_only_sample_data",
        "allowed_data": [
            "sample_csv",
            "synthetic_workflow_events",
            "mock_approval_events",
            "mock_delay_events",
        ],
        "prohibited_data": [
            "real_customer_data",
            "regulated_data",
            "federal_data",
            "production_customer_data",
            "customer_secrets",
            "live_security_telemetry",
        ],
        "certification_claims_allowed": False,
    }


def test_assessment_factory_lite_demo_ui_view_endpoint_preserves_source_payloads():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows()},
    )

    payload = response.json()

    assert set(payload["source_payloads"]) == {
        "profile",
        "dataset_contract",
        "diagnostics_result",
        "export_summary",
    }
    assert payload["source_payloads"]["dataset_contract"]["contract_type"] == (
        "assessment_factory_lite_demo_dataset_contract"
    )
    assert payload["source_payloads"]["diagnostics_result"]["status"] == "ok"
    assert payload["source_payloads"]["export_summary"]["status"] == "ok"


def test_assessment_factory_lite_demo_ui_view_endpoint_rejects_invalid_rows():
    bad_rows = [
        {
            "event_id": "evt-003",
            "case_id": "case-002",
            "event_type": "real_customer_incident",
            "actor": "operator",
            "team": "security",
            "timestamp": "2026-01-01T15:00:00Z",
            "severity": "urgent",
            "description": "Invalid event.",
            "contains_real_customer_data": True,
        }
    ]

    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": bad_rows},
    )

    assert response.status_code == 200

    payload = response.json()
    cards = {card["card_id"]: card for card in payload["cards"]}

    assert cards["dataset_validation_card"]["status"] == "failed"
    assert payload["operator_actions"] == [
        "repair_sample_csv_before_demo",
        "rerun_dataset_validation",
        "rerun_demo_diagnostics",
    ]


def test_assessment_factory_lite_demo_ui_view_endpoint_handles_empty_payload():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["source_payloads"]["diagnostics_result"]["row_count"] == 0
    assert payload["operator_actions"] == [
        "add_synthetic_sample_rows",
        "rerun_demo_diagnostics",
        "generate_demo_export_summary",
    ]


def test_assessment_factory_lite_demo_ui_view_endpoint_includes_warnings():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows()},
    )

    payload = response.json()

    assert payload["warnings"] == [
        {
            "warning_type": "demo_only_boundary",
            "severity": "high",
            "message": (
                "Use synthetic sample data only. Do not upload real "
                "customer, regulated, federal, secret, or live telemetry data."
            ),
        },
        {
            "warning_type": "no_certification_claims",
            "severity": "high",
            "message": (
                "This demo does not certify FedRAMP High, HIPAA compliance, "
                "SOC 2, production readiness, or customer deployment readiness."
            ),
        },
    ]


def test_assessment_factory_lite_demo_ui_view_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-ui/view" in actual_routes


def test_assessment_factory_lite_demo_ui_view_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.9.0",
        "release": "assessment-factory-lite-commercial-offer",
        "sprint": "4.8",
        "status": "complete",
    }











