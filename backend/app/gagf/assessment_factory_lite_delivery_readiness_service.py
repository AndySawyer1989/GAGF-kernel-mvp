from backend.app.gagf.assessment_factory_lite_buyer_export_polish_service import (
    AssessmentFactoryLiteBuyerExportPolishService,
)
from backend.app.gagf.assessment_factory_lite_delivery_manifest_service import (
    AssessmentFactoryLiteDeliveryManifestService,
)
from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)
from backend.app.gagf.assessment_factory_lite_demo_ui_html_service import (
    AssessmentFactoryLiteDemoUIHTMLService,
)
from backend.app.gagf.assessment_factory_lite_operator_runbook_service import (
    AssessmentFactoryLiteOperatorRunbookService,
)


class AssessmentFactoryLiteDeliveryReadinessService:
    """Evaluate delivery readiness for the Assessment Factory Lite demo package."""

    def __init__(
        self,
        manifest_service: AssessmentFactoryLiteDeliveryManifestService | None = None,
        runbook_service: AssessmentFactoryLiteOperatorRunbookService | None = None,
        sample_rows_service: AssessmentFactoryLiteDemoSampleRowsService | None = None,
        html_service: AssessmentFactoryLiteDemoUIHTMLService | None = None,
        buyer_export_service: AssessmentFactoryLiteBuyerExportPolishService | None = None,
    ):
        self.manifest_service = (
            manifest_service or AssessmentFactoryLiteDeliveryManifestService()
        )
        self.runbook_service = (
            runbook_service or AssessmentFactoryLiteOperatorRunbookService()
        )
        self.sample_rows_service = (
            sample_rows_service or AssessmentFactoryLiteDemoSampleRowsService()
        )
        self.html_service = html_service or AssessmentFactoryLiteDemoUIHTMLService()
        self.buyer_export_service = (
            buyer_export_service or AssessmentFactoryLiteBuyerExportPolishService()
        )

    def evaluate_readiness(self) -> dict:
        manifest = self.manifest_service.build_manifest()
        runbook = self.runbook_service.build_runbook()
        standard_rows = self.sample_rows_service.get_sample_rows("standard")
        invalid_rows = self.sample_rows_service.get_sample_rows("invalid")
        empty_rows = self.sample_rows_service.get_sample_rows("empty")
        html_screen = self.html_service.render_html(sample_scenario="standard")
        buyer_export = self.buyer_export_service.build_polished_export(
            rows=standard_rows["rows"]
        )

        checks = [
            self._manifest_check(manifest),
            self._runbook_check(runbook),
            self._sample_rows_check(standard_rows, invalid_rows, empty_rows),
            self._scenario_menu_check(html_screen),
            self._styled_html_check(html_screen),
            self._buyer_export_check(buyer_export),
            self._demo_boundary_check(manifest, runbook, html_screen, buyer_export),
            self._stop_condition_check(runbook),
        ]

        failed_checks = [check for check in checks if check["status"] != "passed"]
        readiness_status = "ready" if not failed_checks else "not_ready"

        return {
            "status": "ok",
            "readiness_type": "assessment_factory_lite_demo_delivery_readiness",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-styling-export",
            "version": "1.6.0",
            "delivery_stage": "demo_delivery_packaging",
            "readiness_status": readiness_status,
            "is_ready": readiness_status == "ready",
            "checks": checks,
            "passed_check_count": len(checks) - len(failed_checks),
            "failed_check_count": len(failed_checks),
            "failed_checks": failed_checks,
            "delivery_decision": self._delivery_decision(readiness_status),
            "source_artifacts": {
                "manifest_type": manifest.get("manifest_type"),
                "runbook_type": runbook.get("runbook_type"),
                "standard_sample_status": standard_rows.get("status"),
                "html_screen_type": html_screen.get("screen_type"),
                "buyer_export_polish_type": buyer_export.get("polish_type"),
            },
            "demo_boundary": self._demo_boundary(),
            "operator_message": (
                "Assessment Factory Lite delivery readiness evaluation complete."
            ),
            "recommended_action": (
                "proceed_with_demo_delivery"
                if readiness_status == "ready"
                else "repair_demo_delivery_package"
            ),
        }

    def _manifest_check(self, manifest: dict) -> dict:
        required_capabilities = {
            "sample_rows",
            "scenario_menu",
            "dataset_contract_validation",
            "demo_diagnostics",
            "styled_html_screen",
            "buyer_export_polish",
        }
        capabilities = {
            item.get("capability")
            for item in manifest.get("included_capabilities", [])
        }

        passed = (
            manifest.get("status") == "ok"
            and manifest.get("manifest_type")
            == "assessment_factory_lite_demo_delivery_manifest"
            and required_capabilities.issubset(capabilities)
        )

        return self._check_result(
            check="delivery_manifest_ready",
            passed=passed,
            summary="Delivery manifest is available and includes required capabilities.",
            repair_action="repair_delivery_manifest",
        )

    def _runbook_check(self, runbook: dict) -> dict:
        passed = (
            runbook.get("status") == "ok"
            and runbook.get("runbook_type")
            == "assessment_factory_lite_demo_operator_runbook"
            and len(runbook.get("live_demo_sequence", [])) == 7
            and len(runbook.get("pre_demo_checklist", [])) >= 6
        )

        return self._check_result(
            check="operator_runbook_ready",
            passed=passed,
            summary="Operator runbook is available with checklist and live-demo sequence.",
            repair_action="repair_operator_runbook",
        )

    def _sample_rows_check(
        self,
        standard_rows: dict,
        invalid_rows: dict,
        empty_rows: dict,
    ) -> dict:
        passed = (
            standard_rows.get("status") == "ok"
            and standard_rows.get("is_valid_sample") is True
            and standard_rows.get("row_count") == 3
            and invalid_rows.get("status") == "ok"
            and invalid_rows.get("is_valid_sample") is False
            and empty_rows.get("status") == "ok"
            and empty_rows.get("row_count") == 0
        )

        return self._check_result(
            check="sample_scenarios_ready",
            passed=passed,
            summary="Standard, invalid, and empty sample scenarios are available.",
            repair_action="repair_sample_scenarios",
        )

    def _scenario_menu_check(self, html_screen: dict) -> dict:
        scenario_menu = html_screen.get("scenario_menu") or {}
        menu_items = {
            item.get("scenario") for item in scenario_menu.get("menu_items", [])
        }

        passed = (
            scenario_menu.get("menu_type")
            == "assessment_factory_lite_demo_scenario_menu"
            and {"standard", "invalid", "empty"}.issubset(menu_items)
        )

        return self._check_result(
            check="scenario_menu_ready",
            passed=passed,
            summary="Scenario menu is available with standard, invalid, and empty choices.",
            repair_action="repair_scenario_menu",
        )

    def _styled_html_check(self, html_screen: dict) -> dict:
        html = html_screen.get("html", "")

        passed = (
            html_screen.get("status") == "ok"
            and html_screen.get("screen_type")
            == "assessment_factory_lite_demo_ui_html_screen"
            and "Demo Scenario Menu" in html
            and "Sample Data Loader" in html
            and '<style data-style-token-type="assessment_factory_lite_demo_style_tokens">' in html
            and "--afl-brand-orange: #F97316;" in html
        )

        return self._check_result(
            check="styled_html_screen_ready",
            passed=passed,
            summary="Styled HTML screen renders scenario menu, sample loader, and style tokens.",
            repair_action="repair_styled_html_screen",
        )

    def _buyer_export_check(self, buyer_export: dict) -> dict:
        passed = (
            buyer_export.get("status") == "ok"
            and buyer_export.get("polish_type")
            == "assessment_factory_lite_buyer_export_polish"
            and buyer_export.get("recommended_action")
            == "present_polished_buyer_export"
            and buyer_export.get("recommended_intervention", {}).get(
                "intervention_type"
            )
            == "streamline_approval_path"
        )

        return self._check_result(
            check="buyer_export_polish_ready",
            passed=passed,
            summary="Buyer export polish is available for the standard scenario.",
            repair_action="repair_buyer_export_polish",
        )

    def _demo_boundary_check(
        self,
        manifest: dict,
        runbook: dict,
        html_screen: dict,
        buyer_export: dict,
    ) -> dict:
        boundaries = [
            manifest.get("demo_boundary", {}),
            runbook.get("demo_boundary", {}),
            buyer_export.get("trust_and_boundary_note", {}),
        ]

        html = html_screen.get("html", "")

        boundary_payloads_ok = all(
            boundary.get("boundary_type") == "demo_only_sample_data"
            and boundary.get("certification_claims_allowed") is False
            and "real_customer_data" in boundary.get("prohibited_data", [])
            and "regulated_data" in boundary.get("prohibited_data", [])
            and "federal_data" in boundary.get("prohibited_data", [])
            for boundary in boundaries
        )

        passed = boundary_payloads_ok and "Sample-data-only buyer demo path" in html

        return self._check_result(
            check="demo_boundary_ready",
            passed=passed,
            summary="Demo-only data boundary is present across package artifacts.",
            repair_action="repair_demo_boundary_visibility",
        )

    def _stop_condition_check(self, runbook: dict) -> dict:
        stop_conditions = {
            item.get("condition") for item in runbook.get("stop_conditions", [])
        }

        passed = {
            "buyer_requests_real_data_upload",
            "regulated_or_federal_data_is_offered",
            "certification_claim_requested",
            "unsafe_sample_rows_detected",
        }.issubset(stop_conditions)

        return self._check_result(
            check="operator_stop_conditions_ready",
            passed=passed,
            summary="Operator stop conditions are defined for unsafe demo situations.",
            repair_action="repair_operator_stop_conditions",
        )

    def _check_result(
        self,
        check: str,
        passed: bool,
        summary: str,
        repair_action: str,
    ) -> dict:
        return {
            "check": check,
            "status": "passed" if passed else "failed",
            "summary": summary,
            "required": True,
            "repair_action": "none" if passed else repair_action,
        }

    def _delivery_decision(self, readiness_status: str) -> dict:
        if readiness_status == "ready":
            return {
                "decision": "go",
                "summary": (
                    "The Assessment Factory Lite demo delivery package is ready "
                    "for a sample-data-only live walkthrough."
                ),
                "next_action": "proceed_with_demo_delivery",
            }

        return {
            "decision": "no_go",
            "summary": (
                "The Assessment Factory Lite demo delivery package needs repair "
                "before a live walkthrough."
            ),
            "next_action": "repair_demo_delivery_package",
        }

    def _demo_boundary(self) -> dict:
        return {
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