from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_screen_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.5.0",
        "release": "assessment-factory-lite-demo-usability",
        "sprint": "4.4",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_screen_release_routes_exist():
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
    assert "/products/assessment-factory-lite/demo-ui/html" in actual_routes


def test_assessment_factory_lite_demo_screen_release_html_endpoint_works():
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
        "/products/assessment-factory-lite/demo-ui/html",
        json={"rows": rows},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["screen_type"] == (
        "assessment_factory_lite_demo_ui_html_screen"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-ui"
    assert payload["version"] == "1.2.0"
    assert payload["recommended_action"] == (
        "display_assessment_factory_lite_demo_screen"
    )


def test_assessment_factory_lite_demo_screen_release_html_contains_core_screen_parts():
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
        "/products/assessment-factory-lite/demo-ui/html",
        json={"rows": rows},
    )

    html = response.json()["html"]

    assert "<!doctype html>" in html
    assert 'data-screen="assessment-factory-lite-demo-ui-html-screen"' in html
    assert "FIP/GAGF Operator Workstation" in html
    assert "Assessment Factory Lite Demo" in html
    assert "Demo Safety Warnings" in html
    assert "Operator Demo Cards" in html
    assert "Buyer-Facing Export Preview" in html
    assert "Operator Actions" in html


def test_assessment_factory_lite_demo_screen_release_preserves_demo_boundary():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()
    html = payload["html"]

    assert payload["ui_view"]["data_boundary"] == {
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
    assert "Use synthetic sample data only" in html
    assert "does not certify FedRAMP High" in html





