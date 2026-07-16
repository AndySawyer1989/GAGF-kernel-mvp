from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_dataset_contract_service import (
    AssessmentFactoryLiteDatasetContractService,
)
from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)
from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_sample_rows_endpoint_returns_default_standard_rows():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["sample_type"] == (
        "assessment_factory_lite_demo_sample_rows"
    )
    assert payload["scenario"] == "standard"
    assert payload["scenario_label"] == "Approval Delay and Blocked Work"
    assert payload["boundary_type"] == "demo_only_sample_data"
    assert payload["is_valid_sample"] is True
    assert payload["row_count"] == 3
    assert payload["recommended_action"] == "load_sample_rows_into_demo"


def test_assessment_factory_lite_demo_sample_rows_endpoint_returns_standard_by_scenario():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/standard"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scenario"] == "standard"
    assert payload["expected_demo_outcome"] == {
        "validation_status": "passed",
        "top_friction_label": "approval_delay",
        "recommended_intervention": "streamline_approval_path",
        "recommended_action": "run_demo_diagnostics",
    }


def test_assessment_factory_lite_demo_sample_rows_endpoint_standard_rows_validate():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/standard"
    )

    payload = response.json()

    validation = AssessmentFactoryLiteDatasetContractService().validate_rows(
        payload["rows"]
    )

    assert validation["is_valid"] is True
    assert validation["error_count"] == 0
    assert validation["accepted_boundary"] == "demo_only_sample_data"


def test_assessment_factory_lite_demo_sample_rows_endpoint_standard_rows_run_diagnostics():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/standard"
    )

    payload = response.json()

    diagnostics = AssessmentFactoryLiteDemoDiagnosticsService().run_diagnostics(
        payload["rows"]
    )

    assert diagnostics["status"] == "ok"
    assert diagnostics["top_friction_points"][0]["friction_label"] == (
        "approval_delay"
    )
    assert diagnostics["recommended_intervention"]["intervention_type"] == (
        "streamline_approval_path"
    )


def test_assessment_factory_lite_demo_sample_rows_endpoint_returns_invalid_scenario():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/invalid"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["scenario"] == "invalid"
    assert payload["scenario_label"] == "Unsafe Data Boundary Example"
    assert payload["boundary_type"] == "demo_only_sample_data"
    assert payload["is_valid_sample"] is False
    assert payload["row_count"] == 1
    assert payload["recommended_action"] == (
        "test_sample_data_boundary_rejection"
    )


def test_assessment_factory_lite_demo_sample_rows_endpoint_invalid_rows_are_rejected():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/invalid"
    )

    payload = response.json()

    validation = AssessmentFactoryLiteDatasetContractService().validate_rows(
        payload["rows"]
    )

    assert validation["is_valid"] is False
    assert validation["accepted_boundary"] == "none"
    assert {
        error["error_type"] for error in validation["errors"]
    } == {
        "invalid_event_type",
        "invalid_severity",
        "real_customer_data_not_allowed",
    }


def test_assessment_factory_lite_demo_sample_rows_endpoint_returns_empty_scenario():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/empty"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "status": "ok",
        "sample_type": "assessment_factory_lite_demo_sample_rows",
        "scenario": "empty",
        "scenario_label": "Empty Demo Starting State",
        "boundary_type": "demo_only_sample_data",
        "is_valid_sample": True,
        "rows": [],
        "row_count": 0,
        "expected_demo_outcome": {
            "validation_status": "passed",
            "top_friction_label": "none",
            "recommended_intervention": "add_demo_rows",
            "recommended_action": "add_synthetic_sample_rows",
        },
        "operator_message": (
            "Empty sample rows are available for initializing the demo "
            "screen before sample data is loaded."
        ),
        "recommended_action": "initialize_empty_demo_screen",
    }


def test_assessment_factory_lite_demo_sample_rows_endpoint_handles_unknown_scenario():
    response = client.get(
        "/products/assessment-factory-lite/demo-samples/rows/does-not-exist"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "not_found"
    assert payload["scenario"] == "does-not-exist"
    assert payload["rows"] == []
    assert payload["row_count"] == 0
    assert "standard" in payload["available_scenarios"]
    assert "invalid" in payload["available_scenarios"]
    assert "empty" in payload["available_scenarios"]
    assert payload["recommended_action"] == "choose_available_sample_scenario"


def test_assessment_factory_lite_demo_sample_rows_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-samples/rows" in actual_routes
    assert (
        "/products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in actual_routes
    )


def test_assessment_factory_lite_demo_sample_rows_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.8.0",
        "release": "assessment-factory-lite-buyer-conversion",
        "sprint": "4.7",
        "status": "complete",
    }




