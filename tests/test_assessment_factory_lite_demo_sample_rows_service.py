from backend.app.gagf.assessment_factory_lite_dataset_contract_service import (
    AssessmentFactoryLiteDatasetContractService,
)
from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)
from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)


def service():
    return AssessmentFactoryLiteDemoSampleRowsService()


def test_assessment_factory_lite_demo_sample_rows_returns_standard_scenario():
    result = service().get_sample_rows("standard")

    assert result["status"] == "ok"
    assert result["sample_type"] == (
        "assessment_factory_lite_demo_sample_rows"
    )
    assert result["scenario"] == "standard"
    assert result["scenario_label"] == "Approval Delay and Blocked Work"
    assert result["boundary_type"] == "demo_only_sample_data"
    assert result["is_valid_sample"] is True
    assert result["row_count"] == 3
    assert result["recommended_action"] == "load_sample_rows_into_demo"


def test_assessment_factory_lite_demo_sample_rows_standard_rows_validate():
    result = service().get_sample_rows("standard")

    validation = AssessmentFactoryLiteDatasetContractService().validate_rows(
        result["rows"]
    )

    assert validation["is_valid"] is True
    assert validation["error_count"] == 0
    assert validation["accepted_boundary"] == "demo_only_sample_data"


def test_assessment_factory_lite_demo_sample_rows_standard_rows_run_diagnostics():
    result = service().get_sample_rows("standard")

    diagnostics = AssessmentFactoryLiteDemoDiagnosticsService().run_diagnostics(
        result["rows"]
    )

    assert diagnostics["status"] == "ok"
    assert diagnostics["top_friction_points"][0]["friction_label"] == (
        "approval_delay"
    )
    assert diagnostics["recommended_intervention"]["intervention_type"] == (
        "streamline_approval_path"
    )


def test_assessment_factory_lite_demo_sample_rows_returns_invalid_scenario():
    result = service().get_sample_rows("invalid")

    assert result["status"] == "ok"
    assert result["scenario"] == "invalid"
    assert result["scenario_label"] == "Unsafe Data Boundary Example"
    assert result["is_valid_sample"] is False
    assert result["row_count"] == 1
    assert result["recommended_action"] == (
        "test_sample_data_boundary_rejection"
    )


def test_assessment_factory_lite_demo_sample_rows_invalid_rows_are_rejected():
    result = service().get_sample_rows("invalid")

    validation = AssessmentFactoryLiteDatasetContractService().validate_rows(
        result["rows"]
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


def test_assessment_factory_lite_demo_sample_rows_returns_empty_scenario():
    result = service().get_sample_rows("empty")

    assert result == {
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


def test_assessment_factory_lite_demo_sample_rows_handles_unknown_scenario():
    result = service().get_sample_rows("does-not-exist")

    assert result["status"] == "not_found"
    assert result["sample_type"] == (
        "assessment_factory_lite_demo_sample_rows"
    )
    assert result["scenario"] == "does-not-exist"
    assert result["rows"] == []
    assert result["row_count"] == 0
    assert "standard" in result["available_scenarios"]
    assert "invalid" in result["available_scenarios"]
    assert "empty" in result["available_scenarios"]
    assert result["recommended_action"] == "choose_available_sample_scenario"