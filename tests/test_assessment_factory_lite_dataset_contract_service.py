from backend.app.gagf.assessment_factory_lite_dataset_contract_service import (
    AssessmentFactoryLiteDatasetContractService,
)


def service():
    return AssessmentFactoryLiteDatasetContractService()


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


def test_assessment_factory_lite_dataset_contract_builds_contract():
    contract = service().get_contract()

    assert contract["status"] == "ok"
    assert contract["contract_type"] == (
        "assessment_factory_lite_demo_dataset_contract"
    )
    assert contract["dataset_name"] == "assessment_factory_lite_sample_csv"
    assert contract["boundary_type"] == "demo_only_sample_data"
    assert contract["recommended_action"] == "build_sample_csv_validator"


def test_assessment_factory_lite_dataset_contract_names_required_fields():
    contract = service().get_contract()

    required_field_names = {
        field["field_name"] for field in contract["required_fields"]
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


def test_assessment_factory_lite_dataset_contract_names_allowed_values():
    contract = service().get_contract()

    assert "approval_requested" in contract["allowed_event_types"]
    assert "approval_delayed" in contract["allowed_event_types"]
    assert "work_blocked" in contract["allowed_event_types"]
    assert "handoff_delayed" in contract["allowed_event_types"]
    assert contract["allowed_severity_values"] == [
        "low",
        "medium",
        "high",
        "critical",
    ]


def test_assessment_factory_lite_dataset_contract_preserves_demo_boundary():
    contract = service().get_contract()

    assert "real_customer_data_is_not_allowed" in contract["validation_rules"]
    assert "regulated_data_is_not_allowed" in contract["validation_rules"]
    assert "federal_data_is_not_allowed" in contract["validation_rules"]
    assert "production_customer_data" in contract["excluded_scope"]
    assert "live_security_telemetry" in contract["excluded_scope"]
    assert "fedramp_or_hipaa_certification_claims" in (
        contract["excluded_scope"]
    )


def test_assessment_factory_lite_dataset_contract_validates_good_rows():
    result = service().validate_rows(valid_rows())

    assert result == {
        "status": "ok",
        "validation_type": "assessment_factory_lite_dataset_validation",
        "row_count": 2,
        "is_valid": True,
        "error_count": 0,
        "errors": [],
        "accepted_boundary": "demo_only_sample_data",
        "recommended_action": "run_demo_diagnostics",
    }


def test_assessment_factory_lite_dataset_contract_rejects_invalid_rows():
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

    result = service().validate_rows(rows)

    assert result["is_valid"] is False
    assert result["error_count"] == 3
    assert result["accepted_boundary"] == "none"
    assert result["recommended_action"] == "repair_sample_csv_before_demo"
    assert {
        error["error_type"] for error in result["errors"]
    } == {
        "invalid_event_type",
        "invalid_severity",
        "real_customer_data_not_allowed",
    }


def test_assessment_factory_lite_dataset_contract_rejects_missing_and_regulated_data():
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

    result = service().validate_rows(rows)

    assert result["is_valid"] is False
    assert result["error_count"] == 3
    assert {
        error["error_type"] for error in result["errors"]
    } == {
        "missing_required_fields",
        "regulated_data_not_allowed",
        "federal_data_not_allowed",
    }




