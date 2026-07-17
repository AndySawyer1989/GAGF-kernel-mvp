from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_ui_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.1.0",
        "release": "assessment-factory-lite-proposal-export-package",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_ui_release_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-profile" in actual_routes
    assert "/products/assessment-factory-lite/dataset-contract" in actual_routes
    assert (
        "/products/assessment-factory-lite/dataset-contract/validate"
        in actual_routes
    )
    assert (
        "/products/assessment-factory-lite/demo-diagnostics/run"
        in actual_routes
    )
    assert (
        "/products/assessment-factory-lite/demo-export/summary"
        in actual_routes
    )
    assert "/products/assessment-factory-lite/demo-ui/view" in actual_routes


def test_assessment_factory_lite_demo_ui_release_view_endpoint_works():
    rows = [
        {
            "event_id": "evt-001",
            "case_id": "case-001",
            "event_type": "approval_delayed",
            "actor": "approver",
            "team": "operations",
            "timestamp": "2026-01-01T13:00:00Z",
            "severity": "high",
            "description": "Synthetic approval delayed.",
            "constraint_label": "approval_delay",
            "duration_minutes": 240,
        }
    ]

    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows},
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


def test_assessment_factory_lite_demo_ui_release_view_has_cards():
    rows = [
        {
            "event_id": "evt-001",
            "case_id": "case-001",
            "event_type": "approval_delayed",
            "actor": "approver",
            "team": "operations",
            "timestamp": "2026-01-01T13:00:00Z",
            "severity": "high",
            "description": "Synthetic approval delayed.",
            "constraint_label": "approval_delay",
            "duration_minutes": 240,
        }
    ]

    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={"rows": rows},
    )

    payload = response.json()
    cards = {card["card_id"]: card for card in payload["cards"]}

    assert "demo_readiness_card" in cards
    assert "sample_data_boundary_card" in cards
    assert "dataset_contract_card" in cards
    assert "dataset_validation_card" in cards
    assert "governance_drag_summary_card" in cards
    assert "top_friction_points_card" in cards
    assert "recommended_intervention_card" in cards
    assert "export_summary_preview_card" in cards
    assert cards["dataset_validation_card"]["status"] == "passed"


def test_assessment_factory_lite_demo_ui_release_preserves_demo_boundary():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/view",
        json={},
    )

    assert response.status_code == 200

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
    assert payload["warnings"][0]["warning_type"] == "demo_only_boundary"
    assert payload["warnings"][1]["warning_type"] == "no_certification_claims"













