from backend.app.gagf.assessment_factory_lite_demo_export_service import (
    AssessmentFactoryLiteDemoExportService,
)


class AssessmentFactoryLiteBuyerExportPolishService:
    """Build buyer-facing polished export copy for the Assessment Factory Lite demo."""

    def __init__(
        self,
        export_service: AssessmentFactoryLiteDemoExportService | None = None,
    ):
        self.export_service = export_service or AssessmentFactoryLiteDemoExportService()

    def build_polished_export(
        self,
        export_summary: dict | None = None,
        diagnostics_result: dict | None = None,
        rows: list[dict] | None = None,
    ) -> dict:
        if export_summary is None:
            export_summary = self.export_service.build_export_summary(
                diagnostics_result=diagnostics_result,
                rows=rows,
            )

        if export_summary.get("status") == "rejected":
            return self._rejected_export(export_summary)

        return {
            "status": "ok",
            "polish_type": "assessment_factory_lite_buyer_export_polish",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-usability",
            "version": "1.5.0",
            "buyer_headline": self._buyer_headline(export_summary),
            "buyer_summary": self._buyer_summary(export_summary),
            "key_findings": self._key_findings(export_summary),
            "recommended_intervention": self._recommended_intervention(
                export_summary
            ),
            "next_steps": self._next_steps(export_summary),
            "trust_and_boundary_note": self._trust_and_boundary_note(),
            "source_export_summary": export_summary,
            "operator_message": (
                "Assessment Factory Lite buyer export polish is ready for "
                "demo presentation."
            ),
            "recommended_action": "present_polished_buyer_export",
        }

    def _rejected_export(self, export_summary: dict) -> dict:
        return {
            "status": "rejected",
            "polish_type": "assessment_factory_lite_buyer_export_polish",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-usability",
            "version": "1.5.0",
            "buyer_headline": "Sample data needs repair before buyer presentation.",
            "buyer_summary": (
                "The demo input did not pass the sample-data boundary check. "
                "Repair the sample rows before presenting findings."
            ),
            "key_findings": [
                {
                    "finding_type": "sample_data_boundary_failure",
                    "title": "Unsafe or invalid sample rows detected",
                    "summary": (
                        "The input was rejected before buyer-facing findings "
                        "were generated."
                    ),
                    "severity": "high",
                }
            ],
            "recommended_intervention": {
                "title": "Repair the demo sample data",
                "summary": (
                    "Use synthetic, demo-only rows that match the Assessment "
                    "Factory Lite dataset contract."
                ),
                "action": "repair_sample_csv_before_demo",
            },
            "next_steps": [
                "Replace unsafe rows with synthetic demo rows.",
                "Run dataset contract validation again.",
                "Regenerate the polished buyer export after validation passes.",
            ],
            "trust_and_boundary_note": self._trust_and_boundary_note(),
            "source_export_summary": export_summary,
            "operator_message": (
                "Buyer export polish rejected the unsafe demo input."
            ),
            "recommended_action": "repair_sample_csv_before_demo",
        }

    def _buyer_headline(self, export_summary: dict) -> str:
        findings = export_summary.get("governance_drag_findings", {})
        drag_level = findings.get("drag_level", "unknown")

        if drag_level in {"high", "critical"}:
            return "Operational drag is slowing work in the demo workflow."

        if drag_level == "medium":
            return "The demo workflow shows measurable friction worth addressing."

        if drag_level == "low":
            return "The demo workflow shows limited friction in the current sample."

        return "The demo workflow is ready for review."

    def _buyer_summary(self, export_summary: dict) -> str:
        source_summary = export_summary.get("executive_summary", "")

        if source_summary:
            return (
                f"{source_summary} This polished view translates the demo "
                "diagnostics into buyer-facing findings and next steps."
            )

        return (
            "Assessment Factory Lite analyzed the sample workflow and prepared "
            "buyer-facing findings from the synthetic demo data."
        )

    def _key_findings(self, export_summary: dict) -> list[dict]:
        constraints = export_summary.get("top_constraints", [])
        findings = []

        for index, constraint in enumerate(constraints[:3], start=1):
            findings.append(
                {
                    "finding_type": "top_constraint",
                    "rank": index,
                    "title": self._title_for_constraint(constraint),
                    "summary": self._summary_for_constraint(constraint),
                    "severity": constraint.get("severity", "medium"),
                    "friction_label": constraint.get(
                        "friction_label",
                        constraint.get("constraint_label", "unknown"),
                    ),
                }
            )

        if findings:
            return findings

        return [
            {
                "finding_type": "no_major_constraint",
                "rank": 1,
                "title": "No major sample constraint was detected",
                "summary": (
                    "The current synthetic sample did not surface a major "
                    "constraint requiring immediate action."
                ),
                "severity": "low",
                "friction_label": "none",
            }
        ]

    def _recommended_intervention(self, export_summary: dict) -> dict:
        intervention = export_summary.get("recommended_intervention", {})
        intervention_type = intervention.get("intervention_type", "review_workflow")

        titles = {
            "streamline_approval_path": "Streamline the approval path",
            "repair_sample_csv_before_demo": "Repair the demo sample data",
            "add_demo_rows": "Add synthetic sample rows",
            "review_workflow": "Review the workflow",
        }

        return {
            "intervention_type": intervention_type,
            "title": titles.get(intervention_type, "Review the workflow"),
            "summary": intervention.get(
                "summary",
                "Review the workflow constraint and choose a focused next step.",
            ),
            "buyer_value": self._buyer_value_for_intervention(intervention_type),
            "action": intervention.get("recommended_action", intervention_type),
        }

    def _next_steps(self, export_summary: dict) -> list[str]:
        source_steps = export_summary.get("next_steps", [])

        if source_steps:
            return [
                "Review the top friction point with the workflow owner.",
                "Choose one narrow intervention to test first.",
                "Use the demo output to decide what evidence should be collected next.",
            ]

        return [
            "Review the demo findings with the buyer.",
            "Confirm whether the sample friction resembles the buyer's real workflow.",
            "Define the first evidence collection plan before using production data.",
        ]

    def _trust_and_boundary_note(self) -> dict:
        return {
            "boundary_type": "demo_only_sample_data",
            "summary": (
                "This polished export is generated from synthetic demo data only. "
                "It is not a FedRAMP High, HIPAA, SOC 2, WCAG, or production-readiness claim."
            ),
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

    def _title_for_constraint(self, constraint: dict) -> str:
        label = constraint.get(
            "friction_label",
            constraint.get("constraint_label", "workflow_constraint"),
        )

        titles = {
            "approval_delay": "Approval delays are creating workflow drag",
            "work_blocked": "Blocked work is slowing delivery",
            "dependency_wait": "Dependency waits are creating avoidable delay",
            "handoff_delayed": "Delayed handoffs are increasing cycle time",
            "ownership_gap": "Ownership gaps are creating uncertainty",
            "environment_failure": "Environment failures are disrupting progress",
            "escalation": "Escalations are signaling unresolved friction",
            "none": "No major constraint was detected",
        }

        return titles.get(label, "Workflow constraint requires review")

    def _summary_for_constraint(self, constraint: dict) -> str:
        label = constraint.get(
            "friction_label",
            constraint.get("constraint_label", "workflow_constraint"),
        )
        count = constraint.get("event_count", constraint.get("count", 0))

        return (
            f"The synthetic demo data surfaced {label} as a constraint "
            f"across {count} event(s)."
        )

    def _buyer_value_for_intervention(self, intervention_type: str) -> str:
        values = {
            "streamline_approval_path": (
                "Reduce waiting time and make approval ownership clearer."
            ),
            "repair_sample_csv_before_demo": (
                "Protect trust by keeping unsafe data out of the demo."
            ),
            "add_demo_rows": (
                "Create enough synthetic evidence to demonstrate the workflow."
            ),
            "review_workflow": (
                "Focus attention on the workflow step most likely to create drag."
            ),
        }

        return values.get(
            intervention_type,
            "Turn the diagnostic finding into a focused operational next step.",
        )