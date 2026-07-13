from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_package_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.3.0",
        "release": "assessment-factory-lite-demo-screen",
        "sprint": "4.2",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_package_release_routes_exist():
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


def test_assessment_factory_lite_demo_package_release_has_dataset_contract():
    response = client.get(
        "/products/assessment-factory-lite/dataset-contract"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["contract_type"] == (
        "assessment_factory_lite_demo_dataset_contract"
    )
    assert payload["boundary_type"] == "demo_only_sample_data"


def test_assessment_factory_lite_demo_package_release_has_demo_diagnostics():
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
        "/products/assessment-factory-lite/demo-diagnostics/run",
        json={"rows": rows},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["diagnostic_type"] == (
        "assessment_factory_lite_demo_diagnostics"
    )
    assert payload["recommended_action"] == "export_demo_summary"


def test_assessment_factory_lite_demo_package_release_has_export_summary():
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
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": rows},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["export_type"] == (
        "assessment_factory_lite_demo_export_summary"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["recommended_action"] == "review_demo_export_summary"


