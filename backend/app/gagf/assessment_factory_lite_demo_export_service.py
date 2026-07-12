from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)


class AssessmentFactoryLiteDemoExportService:
    """Convert Assessment Factory Lite diagnostics into an export summary."""

    def __init__(
        self,
        diagnostics_service: AssessmentFactoryLiteDemoDiagnosticsService | None = None,
    ):
        self.diagnostics_service = (
            diagnostics_service or AssessmentFactoryLiteDemoDiagnosticsService()
        )

    def build_export_summary(
        self,
        diagnostics_result: dict | None = None,
        rows: list[dict] | None = None,
    ) -> dict:
        if diagnostics_result is None:
            diagnostics_result = self.diagnostics_service.run_diagnostics(
                rows or []
            )

        if diagnostics_result.get("status") == "rejected":
            return self._rejected_export(diagnostics_result)

        drag_summary = diagnostics_result.get("governance_drag_summary", {})
        friction_points = diagnostics_result.get("top_friction_points", [])
        intervention = diagnostics_result.get("recommended_intervention", {})

        return {
            "status": "ok",
            "export_type": "assessment_factory_lite_demo_export_summary",
            "package_name": "Assessment Factory Lite Demo Package",
            "source_diagnostic_type": diagnostics_result.get(
                "diagnostic_type"
            ),
            "row_count": diagnostics_result.get("row_count", 0),
            "report_title": "Assessment Factory Lite Demo Summary",
            "executive_summary": self._executive_summary(drag_summary),
            "sample_data_boundary": self._sample_data_boundary(),
            "governance_drag_findings": self._governance_drag_findings(
                drag_summary
            ),
            "top_constraints": self._top_constraints(friction_points),
            "recommended_intervention": self._recommended_intervention(
                intervention
            ),
            "next_steps": self._next_steps(intervention),
            "compliance_disclaimer": self._compliance_disclaimer(),
            "export_metadata": self._export_metadata(diagnostics_result),
            "operator_message": (
                "Assessment Factory Lite demo export summary is ready for "
                "review using synthetic sample data only."
            ),
            "recommended_action": "review_demo_export_summary",
        }

    def _rejected_export(self, diagnostics_result: dict) -> dict:
        return {
            "status": "rejected",
            "export_type": "assessment_factory_lite_demo_export_summary",
            "package_name": "Assessment Factory Lite Demo Package",
            "source_diagnostic_type": diagnostics_result.get(
                "diagnostic_type"
            ),
            "row_count": diagnostics_result.get("row_count", 0),
            "report_title": "Assessment Factory Lite Demo Summary",
            "executive_summary": (
                "Demo export could not be generated because the sample "
                "dataset failed validation."
            ),
            "sample_data_boundary": self._sample_data_boundary(),
            "governance_drag_findings": {
                "available": False,
                "reason": "dataset_validation_failed",
            },
            "top_constraints": [],
            "recommended_intervention": {
                "intervention_type": "repair_sample_csv_before_demo",
                "priority": "required",
                "reason": "dataset_validation_failed",
            },
            "next_steps": [
                "repair_sample_csv_before_demo",
                "rerun_dataset_validation",
                "rerun_demo_diagnostics",
            ],
            "compliance_disclaimer": self._compliance_disclaimer(),
            "export_metadata": {
                "is_export_ready": False,
                "source_status": "rejected",
                "validation_status": "failed",
                "demo_only": True,
            },
            "operator_message": (
                "Demo export summary cannot be generated until the sample "
                "CSV passes the demo-only dataset contract."
            ),
            "recommended_action": "repair_sample_csv_before_demo",
        }

    def _executive_summary(self, drag_summary: dict) -> str:
        total_events = drag_summary.get("total_events", 0)
        drag_events = drag_summary.get("drag_event_count", 0)
        drag_level = drag_summary.get("drag_level", "none")
        delay = drag_summary.get("total_delay_minutes", 0)

        if total_events == 0:
            return (
                "No synthetic demo rows were analyzed. Add sample workflow "
                "events to generate an Assessment Factory Lite demo summary."
            )

        return (
            f"Assessment Factory Lite analyzed {total_events} synthetic "
            f"workflow events and found {drag_events} governance drag "
            f"events. The demo drag level is {drag_level}, with {delay} "
            f"synthetic delay minutes observed."
        )

    def _sample_data_boundary(self) -> dict:
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

    def _governance_drag_findings(self, drag_summary: dict) -> dict:
        return {
            "available": True,
            "total_events": drag_summary.get("total_events", 0),
            "drag_event_count": drag_summary.get("drag_event_count", 0),
            "critical_or_high_event_count": drag_summary.get(
                "critical_or_high_event_count", 0
            ),
            "total_delay_minutes": drag_summary.get(
                "total_delay_minutes", 0
            ),
            "governance_drag_score": drag_summary.get(
                "governance_drag_score", 0.0
            ),
            "drag_level": drag_summary.get("drag_level", "none"),
        }

    def _top_constraints(self, friction_points: list[dict]) -> list[dict]:
        constraints = []

        for index, point in enumerate(friction_points, start=1):
            constraints.append(
                {
                    "rank": index,
                    "constraint_label": point.get("friction_label"),
                    "event_count": point.get("event_count", 0),
                    "case_count": point.get("case_count", 0),
                    "total_delay_minutes": point.get(
                        "total_delay_minutes", 0
                    ),
                    "priority_score": point.get("priority_score", 0),
                }
            )

        return constraints

    def _recommended_intervention(self, intervention: dict) -> dict:
        return {
            "intervention_type": intervention.get(
                "intervention_type", "continue_monitoring"
            ),
            "priority": intervention.get("priority", "low"),
            "target_friction_label": intervention.get(
                "target_friction_label"
            ),
            "reason": intervention.get("reason", "not_provided"),
        }

    def _next_steps(self, intervention: dict) -> list[str]:
        intervention_type = intervention.get("intervention_type")

        if intervention_type == "add_demo_rows":
            return [
                "add_synthetic_sample_rows",
                "rerun_demo_diagnostics",
                "generate_demo_export_summary",
            ]

        if intervention_type == "repair_sample_csv_before_demo":
            return [
                "repair_sample_csv_before_demo",
                "rerun_dataset_validation",
                "rerun_demo_diagnostics",
            ]

        return [
            "review_governance_drag_summary",
            "review_top_constraints",
            "review_recommended_intervention",
            "prepare_buyer_demo_walkthrough",
        ]

    def _compliance_disclaimer(self) -> str:
        return (
            "This Assessment Factory Lite demo export is based only on "
            "synthetic sample data. It does not certify FedRAMP High, HIPAA "
            "compliance, SOC 2, production readiness, or customer deployment "
            "readiness."
        )

    def _export_metadata(self, diagnostics_result: dict) -> dict:
        validation = diagnostics_result.get("validation", {})

        return {
            "is_export_ready": True,
            "source_status": diagnostics_result.get("status"),
            "validation_status": (
                "passed" if validation.get("is_valid") else "unknown"
            ),
            "demo_only": True,
            "report_sections": [
                "executive_summary",
                "sample_data_boundary",
                "governance_drag_findings",
                "top_constraints",
                "recommended_intervention",
                "next_steps",
                "compliance_disclaimer",
            ],
        }