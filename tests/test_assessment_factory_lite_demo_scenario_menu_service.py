from backend.app.gagf.assessment_factory_lite_demo_scenario_menu_service import (
    AssessmentFactoryLiteDemoScenarioMenuService,
)


def service():
    return AssessmentFactoryLiteDemoScenarioMenuService()


def test_assessment_factory_lite_demo_scenario_menu_builds_contract():
    result = service().build_menu()

    assert result["status"] == "ok"
    assert result["menu_type"] == "assessment_factory_lite_demo_scenario_menu"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-loader"
    assert result["version"] == "1.4.0"
    assert result["default_scenario"] == "standard"
    assert result["recommended_action"] == "render_demo_scenario_menu"


def test_assessment_factory_lite_demo_scenario_menu_has_three_menu_items():
    result = service().build_menu()

    assert [item["scenario"] for item in result["menu_items"]] == [
        "standard",
        "invalid",
        "empty",
    ]


def test_assessment_factory_lite_demo_scenario_menu_standard_item():
    result = service().build_menu()
    items = {item["scenario"]: item for item in result["menu_items"]}

    assert items["standard"] == {
        "scenario": "standard",
        "label": "Approval Delay and Blocked Work",
        "description": (
            "Load valid synthetic workflow rows showing approval delay "
            "and blocked work."
        ),
        "recommended_use": "buyer_demo_default",
        "is_valid_sample": True,
        "row_count": 3,
        "expected_top_friction_label": "approval_delay",
        "expected_intervention": "streamline_approval_path",
        "ui_action": "load_standard_demo_scenario",
        "html_payload": {"sample_scenario": "standard"},
    }


def test_assessment_factory_lite_demo_scenario_menu_invalid_item():
    result = service().build_menu()
    items = {item["scenario"]: item for item in result["menu_items"]}

    assert items["invalid"] == {
        "scenario": "invalid",
        "label": "Unsafe Data Boundary Test",
        "description": (
            "Load intentionally invalid rows to demonstrate boundary "
            "rejection behavior."
        ),
        "recommended_use": "boundary_rejection_demo",
        "is_valid_sample": False,
        "row_count": 1,
        "expected_top_friction_label": "none",
        "expected_intervention": "repair_sample_csv_before_demo",
        "ui_action": "load_invalid_boundary_test_scenario",
        "html_payload": {"sample_scenario": "invalid"},
    }


def test_assessment_factory_lite_demo_scenario_menu_empty_item():
    result = service().build_menu()
    items = {item["scenario"]: item for item in result["menu_items"]}

    assert items["empty"] == {
        "scenario": "empty",
        "label": "Empty Demo Starting State",
        "description": (
            "Initialize the demo screen before sample rows are loaded."
        ),
        "recommended_use": "initial_empty_state",
        "is_valid_sample": True,
        "row_count": 0,
        "expected_top_friction_label": "none",
        "expected_intervention": "add_demo_rows",
        "ui_action": "load_empty_demo_scenario",
        "html_payload": {"sample_scenario": "empty"},
    }


def test_assessment_factory_lite_demo_scenario_menu_aliases():
    result = service().build_menu()

    assert result["aliases"] == {
        "standard": "standard",
        "valid": "standard",
        "approval_delay": "standard",
        "invalid": "invalid",
        "unsafe": "invalid",
        "empty": "empty",
        "blank": "empty",
    }


def test_assessment_factory_lite_demo_scenario_menu_items_are_html_ready():
    result = service().build_menu()

    for item in result["menu_items"]:
        assert set(item) == {
            "scenario",
            "label",
            "description",
            "recommended_use",
            "is_valid_sample",
            "row_count",
            "expected_top_friction_label",
            "expected_intervention",
            "ui_action",
            "html_payload",
        }
        assert "sample_scenario" in item["html_payload"]


