from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def valid_rows():
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
            "duration_minutes": 240,
        },
    ]


def test_assessment_factory_lite_dataset_contract_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/dataset-contract"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["contract_type"] == (
        "assessment_factory_lite_demo_dataset_contract"
    )
    assert payload["dataset_name"] == "assessment_factory_lite_sample_csv"
    assert payload["boundary_type"] == "demo_only_sample_data"
    assert payload["recommended_action"] == "build_sample_csv_validator"


def test_assessment_factory_lite_dataset_contract_endpoint_names_required_fields():
    response = client.get(
        "/products/assessment-factory-lite/dataset-contract"
    )

    payload = response.json()

    required_field_names = {
        field["field_name"] for field in payload["required_fields"]
    }

    assert required_field_names == {
        "event_id",
        "case_id",
        "event_type",
        "actor",
        "team",
        "timestamp",
        "severity",
        "description",
    }


def test_assessment_factory_lite_dataset_contract_endpoint_names_allowed_values():
    response = client.get(
        "/products/assessment-factory-lite/dataset-contract"
    )

    payload = response.json()

    assert "approval_requested" in payload["allowed_event_types"]
    assert "approval_delayed" in payload["allowed_event_types"]
    assert "work_blocked" in payload["allowed_event_types"]
    assert "handoff_delayed" in payload["allowed_event_types"]
    assert payload["allowed_severity_values"] == [
        "low",
        "medium",
        "high",
        "critical",
    ]


def test_assessment_factory_lite_dataset_contract_validation_accepts_good_rows():
    response = client.post(
        "/products/assessment-factory-lite/dataset-contract/validate",
        json={"rows": valid_rows()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "status": "ok",
        "validation_type": "assessment_factory_lite_dataset_validation",
        "row_count": 2,
        "is_valid": True,
        "error_count": 0,
        "errors": [],
        "accepted_boundary": "demo_only_sample_data",
        "recommended_action": "run_demo_diagnostics",
    }


def test_assessment_factory_lite_dataset_contract_validation_rejects_invalid_rows():
    rows = [
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
        "/products/assessment-factory-lite/dataset-contract/validate",
        json={"rows": rows},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["is_valid"] is False
    assert payload["error_count"] == 3
    assert payload["accepted_boundary"] == "none"
    assert payload["recommended_action"] == "repair_sample_csv_before_demo"
    assert {
        error["error_type"] for error in payload["errors"]
    } == {
        "invalid_event_type",
        "invalid_severity",
        "real_customer_data_not_allowed",
    }


def test_assessment_factory_lite_dataset_contract_validation_rejects_missing_and_regulated_data():
    rows = [
        {
            "event_id": "evt-004",
            "case_id": "case-003",
            "event_type": "approval_delayed",
            "actor": "approver",
            "team": "operations",
            "timestamp": "2026-01-01T16:00:00Z",
            "severity": "high",
            "contains_regulated_data": True,
            "contains_federal_data": True,
        }
    ]

    response = client.post(
        "/products/assessment-factory-lite/dataset-contract/validate",
        json={"rows": rows},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["is_valid"] is False
    assert payload["error_count"] == 3
    assert {
        error["error_type"] for error in payload["errors"]
    } == {
        "missing_required_fields",
        "regulated_data_not_allowed",
        "federal_data_not_allowed",
    }


def test_assessment_factory_lite_dataset_contract_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/dataset-contract" in actual_routes
    assert (
        "/products/assessment-factory-lite/dataset-contract/validate"
        in actual_routes
    )


def test_assessment_factory_lite_dataset_contract_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.7.0",
        "release": "assessment-factory-lite-demo-delivery-packaging",
        "sprint": "4.6",
        "status": "complete",
    }


def test_assessment_factory_lite_dataset_contract_validation_handles_empty_rows():
    response = client.post(
        "/products/assessment-factory-lite/dataset-contract/validate",
        json={"rows": []},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "status": "ok",
        "validation_type": "assessment_factory_lite_dataset_validation",
        "row_count": 0,
        "is_valid": True,
        "error_count": 0,
        "errors": [],
        "accepted_boundary": "demo_only_sample_data",
        "recommended_action": "run_demo_diagnostics",
    }


def test_assessment_factory_lite_dataset_contract_validation_defaults_missing_rows_to_empty():
    response = client.post(
        "/products/assessment-factory-lite/dataset-contract/validate",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["row_count"] == 0
    assert payload["is_valid"] is True
    assert payload["recommended_action"] == "run_demo_diagnostics"







