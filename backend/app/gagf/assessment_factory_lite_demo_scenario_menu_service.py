from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)


class AssessmentFactoryLiteDemoScenarioMenuService:
    """Build a UI-ready scenario menu for the Assessment Factory Lite demo."""

    def __init__(
        self,
        sample_rows_service: AssessmentFactoryLiteDemoSampleRowsService | None = None,
    ):
        self.sample_rows_service = (
            sample_rows_service or AssessmentFactoryLiteDemoSampleRowsService()
        )

    def build_menu(self) -> dict:
        return {
            "status": "ok",
            "menu_type": "assessment_factory_lite_demo_scenario_menu",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-loader",
            "version": "1.4.0",
            "default_scenario": "standard",
            "menu_items": [
                self._standard_item(),
                self._invalid_item(),
                self._empty_item(),
            ],
            "aliases": self._aliases(),
            "operator_message": (
                "Assessment Factory Lite demo scenario menu is ready for "
                "the Operator Workstation."
            ),
            "recommended_action": "render_demo_scenario_menu",
        }

    def _standard_item(self) -> dict:
        sample = self.sample_rows_service.get_sample_rows("standard")

        return {
            "scenario": "standard",
            "label": "Approval Delay and Blocked Work",
            "description": (
                "Load valid synthetic workflow rows showing approval delay "
                "and blocked work."
            ),
            "recommended_use": "buyer_demo_default",
            "is_valid_sample": sample["is_valid_sample"],
            "row_count": sample["row_count"],
            "expected_top_friction_label": sample["expected_demo_outcome"][
                "top_friction_label"
            ],
            "expected_intervention": sample["expected_demo_outcome"][
                "recommended_intervention"
            ],
            "ui_action": "load_standard_demo_scenario",
            "html_payload": {"sample_scenario": "standard"},
        }

    def _invalid_item(self) -> dict:
        sample = self.sample_rows_service.get_sample_rows("invalid")

        return {
            "scenario": "invalid",
            "label": "Unsafe Data Boundary Test",
            "description": (
                "Load intentionally invalid rows to demonstrate boundary "
                "rejection behavior."
            ),
            "recommended_use": "boundary_rejection_demo",
            "is_valid_sample": sample["is_valid_sample"],
            "row_count": sample["row_count"],
            "expected_top_friction_label": sample["expected_demo_outcome"][
                "top_friction_label"
            ],
            "expected_intervention": sample["expected_demo_outcome"][
                "recommended_intervention"
            ],
            "ui_action": "load_invalid_boundary_test_scenario",
            "html_payload": {"sample_scenario": "invalid"},
        }

    def _empty_item(self) -> dict:
        sample = self.sample_rows_service.get_sample_rows("empty")

        return {
            "scenario": "empty",
            "label": "Empty Demo Starting State",
            "description": (
                "Initialize the demo screen before sample rows are loaded."
            ),
            "recommended_use": "initial_empty_state",
            "is_valid_sample": sample["is_valid_sample"],
            "row_count": sample["row_count"],
            "expected_top_friction_label": sample["expected_demo_outcome"][
                "top_friction_label"
            ],
            "expected_intervention": sample["expected_demo_outcome"][
                "recommended_intervention"
            ],
            "ui_action": "load_empty_demo_scenario",
            "html_payload": {"sample_scenario": "empty"},
        }

    def _aliases(self) -> dict:
        return {
            "standard": "standard",
            "valid": "standard",
            "approval_delay": "standard",
            "invalid": "invalid",
            "unsafe": "invalid",
            "empty": "empty",
            "blank": "empty",
        }