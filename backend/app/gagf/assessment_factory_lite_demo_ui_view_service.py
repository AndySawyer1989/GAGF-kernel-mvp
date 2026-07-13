from backend.app.gagf.assessment_factory_lite_dataset_contract_service import (
    AssessmentFactoryLiteDatasetContractService,
)
from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)
from backend.app.gagf.assessment_factory_lite_demo_export_service import (
    AssessmentFactoryLiteDemoExportService,
)
from backend.app.gagf.assessment_factory_lite_demo_profile_service import (
    AssessmentFactoryLiteDemoProfileService,
)


class AssessmentFactoryLiteDemoUIViewService:
    """Build the Operator Workstation UI view contract for the demo package."""

    def __init__(
        self,
        profile_service: AssessmentFactoryLiteDemoProfileService | None = None,
        contract_service: AssessmentFactoryLiteDatasetContractService | None = None,
        diagnostics_service: AssessmentFactoryLiteDemoDiagnosticsService | None = None,
        export_service: AssessmentFactoryLiteDemoExportService | None = None,
    ):
        self.profile_service = (
            profile_service or AssessmentFactoryLiteDemoProfileService()
        )
        self.contract_service = (
            contract_service or AssessmentFactoryLiteDatasetContractService()
        )
        self.diagnostics_service = (
            diagnostics_service or AssessmentFactoryLiteDemoDiagnosticsService()
        )
        self.export_service = export_service or AssessmentFactoryLiteDemoExportService()

    def build_view(
        self,
        checkpoint: dict | None = None,
        rows: list[dict] | None = None,
        diagnostics_result: dict | None = None,
        export_summary: dict | None = None,
    ) -> dict:
        rows = rows or []

        profile = self.profile_service.build_profile(checkpoint or {})
        dataset_contract = self.contract_service.get_contract()

        if diagnostics_result is None:
            diagnostics_result = self.diagnostics_service.run_diagnostics(rows)

        if export_summary is None:
            export_summary = self.export_service.build_export_summary(
                diagnostics_result=diagnostics_result,
                rows=rows,
            )

        return {
            "status": "ok",
            "view_type": "assessment_factory_lite_demo_ui_view",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-package",
            "version": "1.1.0",
            "ui_sections": self._ui_sections(),
            "cards": self._cards(
                profile=profile,
                dataset_contract=dataset_contract,
                diagnostics_result=diagnostics_result,
                export_summary=export_summary,
            ),
            "operator_actions": self._operator_actions(
                diagnostics_result=diagnostics_result,
                export_summary=export_summary,
            ),
            "warnings": self._warnings(),
            "data_boundary": self._data_boundary(),
            "source_payloads": {
                "profile": profile,
                "dataset_contract": dataset_contract,
                "diagnostics_result": diagnostics_result,
                "export_summary": export_summary,
            },
            "operator_message": (
                "Assessment Factory Lite demo UI view is ready for the "
                "Operator Workstation using demo-only synthetic data."
            ),
            "recommended_action": "render_assessment_factory_lite_demo_view",
        }

    def _ui_sections(self) -> list[str]:
        return [
            "demo_readiness",
            "sample_data_boundary",
            "dataset_contract",
            "dataset_validation",
            "governance_drag_summary",
            "top_friction_points",
            "recommended_intervention",
            "export_summary_preview",
            "next_steps",
            "compliance_disclaimer",
        ]

    def _cards(
        self,
        profile: dict,
        dataset_contract: dict,
        diagnostics_result: dict,
        export_summary: dict,
    ) -> list[dict]:
        return [
            self._demo_readiness_card(profile),
            self._sample_data_boundary_card(),
            self._dataset_contract_card(dataset_contract),
            self._dataset_validation_card(diagnostics_result),
            self._governance_drag_card(diagnostics_result),
            self._top_friction_points_card(diagnostics_result),
            self._recommended_intervention_card(export_summary),
            self._export_summary_card(export_summary),
        ]

    def _demo_readiness_card(self, profile: dict) -> dict:
        readiness = profile.get("demo_readiness", {})

        return {
            "card_id": "demo_readiness_card",
            "title": "Demo Readiness",
            "status": "ready" if readiness.get("ready_for_demo_package") else "not_ready",
            "summary": readiness.get("reason", "not_available"),
            "primary_value": readiness.get("decision", "unknown"),
            "action": profile.get("recommended_action"),
        }

    def _sample_data_boundary_card(self) -> dict:
        return {
            "card_id": "sample_data_boundary_card",
            "title": "Sample Data Boundary",
            "status": "enforced",
            "summary": "Demo-only synthetic data is required.",
            "primary_value": "demo_only_sample_data",
            "action": "enforce_sample_data_boundary",
        }

    def _dataset_contract_card(self, dataset_contract: dict) -> dict:
        return {
            "card_id": "dataset_contract_card",
            "title": "Dataset Contract",
            "status": dataset_contract.get("status", "unknown"),
            "summary": "Sample CSV contract is available.",
            "primary_value": dataset_contract.get("dataset_name"),
            "action": "show_dataset_contract",
        }

    def _dataset_validation_card(self, diagnostics_result: dict) -> dict:
        validation = diagnostics_result.get("validation", {})
        is_valid = validation.get("is_valid", False)

        return {
            "card_id": "dataset_validation_card",
            "title": "Dataset Validation",
            "status": "passed" if is_valid else "failed",
            "summary": (
                "Dataset passed validation."
                if is_valid
                else "Dataset must be repaired before diagnostics can run."
            ),
            "primary_value": validation.get("error_count", 0),
            "action": (
                "run_demo_diagnostics"
                if is_valid
                else "repair_sample_csv_before_demo"
            ),
        }

    def _governance_drag_card(self, diagnostics_result: dict) -> dict:
        drag = diagnostics_result.get("governance_drag_summary", {})

        return {
            "card_id": "governance_drag_summary_card",
            "title": "Governance Drag Summary",
            "status": drag.get("drag_level", "none"),
            "summary": "Synthetic workflow drag summary.",
            "primary_value": drag.get("governance_drag_score", 0.0),
            "action": "review_governance_drag_summary",
        }

    def _top_friction_points_card(self, diagnostics_result: dict) -> dict:
        points = diagnostics_result.get("top_friction_points", [])
        top_label = points[0]["friction_label"] if points else "none"

        return {
            "card_id": "top_friction_points_card",
            "title": "Top Friction Points",
            "status": "available" if points else "empty",
            "summary": "Highest priority synthetic friction points.",
            "primary_value": top_label,
            "action": "review_top_friction_points",
        }

    def _recommended_intervention_card(self, export_summary: dict) -> dict:
        intervention = export_summary.get("recommended_intervention", {})

        return {
            "card_id": "recommended_intervention_card",
            "title": "Recommended Intervention",
            "status": intervention.get("priority", "unknown"),
            "summary": intervention.get("reason", "not_available"),
            "primary_value": intervention.get("intervention_type"),
            "action": "review_recommended_intervention",
        }

    def _export_summary_card(self, export_summary: dict) -> dict:
        return {
            "card_id": "export_summary_preview_card",
            "title": "Export Summary Preview",
            "status": export_summary.get("status", "unknown"),
            "summary": export_summary.get("executive_summary"),
            "primary_value": export_summary.get("report_title"),
            "action": export_summary.get("recommended_action"),
        }

    def _operator_actions(
        self,
        diagnostics_result: dict,
        export_summary: dict,
    ) -> list[str]:
        if diagnostics_result.get("status") == "rejected":
            return [
                "repair_sample_csv_before_demo",
                "rerun_dataset_validation",
                "rerun_demo_diagnostics",
            ]

        intervention = export_summary.get("recommended_intervention", {})
        intervention_type = intervention.get("intervention_type")

        if intervention_type == "add_demo_rows":
            return [
                "add_synthetic_sample_rows",
                "rerun_demo_diagnostics",
                "generate_demo_export_summary",
            ]

        return [
            "review_demo_readiness",
            "review_sample_data_boundary",
            "review_governance_drag_summary",
            "review_top_friction_points",
            "review_recommended_intervention",
            "review_demo_export_summary",
        ]

    def _warnings(self) -> list[dict]:
        return [
            {
                "warning_type": "demo_only_boundary",
                "severity": "high",
                "message": (
                    "Use synthetic sample data only. Do not upload real "
                    "customer, regulated, federal, secret, or live telemetry data."
                ),
            },
            {
                "warning_type": "no_certification_claims",
                "severity": "high",
                "message": (
                    "This demo does not certify FedRAMP High, HIPAA compliance, "
                    "SOC 2, production readiness, or customer deployment readiness."
                ),
            },
        ]

    def _data_boundary(self) -> dict:
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