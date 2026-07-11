from collections import Counter, defaultdict

from backend.app.gagf.assessment_factory_lite_dataset_contract_service import (
    AssessmentFactoryLiteDatasetContractService,
)


class AssessmentFactoryLiteDemoDiagnosticsService:
    """Run demo diagnostics over validated Assessment Factory Lite rows."""

    def __init__(
        self,
        contract_service: AssessmentFactoryLiteDatasetContractService | None = None,
    ):
        self.contract_service = (
            contract_service or AssessmentFactoryLiteDatasetContractService()
        )

    def run_diagnostics(self, rows: list[dict]) -> dict:
        validation = self.contract_service.validate_rows(rows)

        if validation["is_valid"] is False:
            return {
                "status": "rejected",
                "diagnostic_type": "assessment_factory_lite_demo_diagnostics",
                "row_count": validation["row_count"],
                "validation": validation,
                "governance_drag_summary": self._empty_drag_summary(),
                "top_friction_points": [],
                "recommended_intervention": {
                    "intervention_type": "repair_sample_csv_before_demo",
                    "priority": "required",
                    "reason": "dataset_validation_failed",
                },
                "export_ready_summary": {
                    "is_export_ready": False,
                    "reason": "dataset_validation_failed",
                },
                "operator_message": (
                    "Demo diagnostics cannot run until the sample CSV passes "
                    "the demo-only dataset contract."
                ),
                "recommended_action": "repair_sample_csv_before_demo",
            }

        drag_summary = self._governance_drag_summary(rows)
        friction_points = self._top_friction_points(rows)
        intervention = self._recommended_intervention(
            drag_summary=drag_summary,
            friction_points=friction_points,
        )

        return {
            "status": "ok",
            "diagnostic_type": "assessment_factory_lite_demo_diagnostics",
            "row_count": len(rows),
            "validation": validation,
            "governance_drag_summary": drag_summary,
            "top_friction_points": friction_points,
            "recommended_intervention": intervention,
            "export_ready_summary": self._export_ready_summary(
                drag_summary=drag_summary,
                friction_points=friction_points,
                intervention=intervention,
            ),
            "operator_message": (
                "Assessment Factory Lite demo diagnostics completed using "
                "demo-only synthetic workflow events."
            ),
            "recommended_action": "export_demo_summary",
        }

    def _governance_drag_summary(self, rows: list[dict]) -> dict:
        event_counts = Counter(row.get("event_type") for row in rows)
        severity_counts = Counter(row.get("severity") for row in rows)

        total_delay_minutes = sum(
            self._safe_number(row.get("duration_minutes")) for row in rows
        )

        drag_events = [
            row
            for row in rows
            if row.get("event_type")
            in {
                "approval_delayed",
                "work_blocked",
                "dependency_wait",
                "handoff_delayed",
                "ownership_gap",
                "environment_failure",
                "escalation",
            }
        ]

        critical_or_high_events = [
            row
            for row in rows
            if row.get("severity") in {"high", "critical"}
        ]

        drag_score = self._drag_score(
            row_count=len(rows),
            drag_event_count=len(drag_events),
            critical_or_high_count=len(critical_or_high_events),
            total_delay_minutes=total_delay_minutes,
        )

        return {
            "total_events": len(rows),
            "drag_event_count": len(drag_events),
            "critical_or_high_event_count": len(critical_or_high_events),
            "total_delay_minutes": total_delay_minutes,
            "event_type_counts": dict(event_counts),
            "severity_counts": dict(severity_counts),
            "governance_drag_score": drag_score,
            "drag_level": self._drag_level(drag_score),
        }

    def _top_friction_points(self, rows: list[dict]) -> list[dict]:
        grouped = defaultdict(
            lambda: {
                "event_count": 0,
                "total_delay_minutes": 0,
                "high_or_critical_count": 0,
                "cases": set(),
            }
        )

        for row in rows:
            label = row.get("constraint_label") or row.get("event_type")
            item = grouped[label]
            item["event_count"] += 1
            item["total_delay_minutes"] += self._safe_number(
                row.get("duration_minutes")
            )
            item["cases"].add(row.get("case_id"))

            if row.get("severity") in {"high", "critical"}:
                item["high_or_critical_count"] += 1

        friction_points = []

        for label, values in grouped.items():
            friction_points.append(
                {
                    "friction_label": label,
                    "event_count": values["event_count"],
                    "case_count": len(values["cases"]),
                    "total_delay_minutes": values["total_delay_minutes"],
                    "high_or_critical_count": values[
                        "high_or_critical_count"
                    ],
                    "priority_score": self._priority_score(values),
                }
            )

        return sorted(
            friction_points,
            key=lambda point: (
                point["priority_score"],
                point["total_delay_minutes"],
                point["event_count"],
            ),
            reverse=True,
        )[:5]

    def _recommended_intervention(
        self,
        drag_summary: dict,
        friction_points: list[dict],
    ) -> dict:
        if drag_summary["total_events"] == 0:
            return {
                "intervention_type": "add_demo_rows",
                "priority": "required",
                "reason": "no_demo_rows_available",
            }

        if not friction_points:
            return {
                "intervention_type": "continue_monitoring",
                "priority": "low",
                "reason": "no_friction_points_detected",
            }

        top_point = friction_points[0]
        label = top_point["friction_label"]

        if "approval" in label:
            return {
                "intervention_type": "streamline_approval_path",
                "priority": self._intervention_priority(drag_summary),
                "target_friction_label": label,
                "reason": "approval_friction_detected",
            }

        if label in {"work_blocked", "dependency_wait", "handoff_delayed"}:
            return {
                "intervention_type": "clarify_ownership_and_handoffs",
                "priority": self._intervention_priority(drag_summary),
                "target_friction_label": label,
                "reason": "handoff_or_dependency_friction_detected",
            }

        if label in {"environment_failure", "escalation"}:
            return {
                "intervention_type": "stabilize_operational_path",
                "priority": self._intervention_priority(drag_summary),
                "target_friction_label": label,
                "reason": "operational_instability_detected",
            }

        return {
            "intervention_type": "review_top_constraint",
            "priority": self._intervention_priority(drag_summary),
            "target_friction_label": label,
            "reason": "top_friction_point_detected",
        }

    def _export_ready_summary(
        self,
        drag_summary: dict,
        friction_points: list[dict],
        intervention: dict,
    ) -> dict:
        return {
            "is_export_ready": True,
            "report_sections": [
                "executive_summary",
                "sample_data_boundary",
                "governance_drag_findings",
                "top_constraints",
                "recommended_intervention",
                "next_steps",
                "compliance_disclaimer",
            ],
            "executive_summary": (
                f"Demo analyzed {drag_summary['total_events']} synthetic "
                f"events and found {drag_summary['drag_event_count']} "
                f"governance drag events."
            ),
            "top_friction_label": (
                friction_points[0]["friction_label"]
                if friction_points
                else "none"
            ),
            "recommended_intervention_type": intervention[
                "intervention_type"
            ],
            "compliance_disclaimer": (
                "Demo output is based only on synthetic sample data and does "
                "not certify FedRAMP High, HIPAA compliance, SOC 2, or "
                "production readiness."
            ),
        }

    def _drag_score(
        self,
        row_count: int,
        drag_event_count: int,
        critical_or_high_count: int,
        total_delay_minutes: int | float,
    ) -> float:
        if row_count <= 0:
            return 0.0

        drag_ratio = drag_event_count / row_count
        severity_ratio = critical_or_high_count / row_count
        delay_factor = min(total_delay_minutes / 480, 1.0)

        return round(
            (drag_ratio * 0.50)
            + (severity_ratio * 0.30)
            + (delay_factor * 0.20),
            4,
        )

    def _priority_score(self, values: dict) -> float:
        return round(
            values["event_count"]
            + (values["high_or_critical_count"] * 2)
            + min(values["total_delay_minutes"] / 60, 5),
            4,
        )

    def _intervention_priority(self, drag_summary: dict) -> str:
        drag_score = drag_summary.get("governance_drag_score", 0.0)

        if drag_score >= 0.75:
            return "critical"

        if drag_score >= 0.50:
            return "high"

        if drag_score >= 0.25:
            return "medium"

        return "low"

    def _drag_level(self, drag_score: float) -> str:
        if drag_score >= 0.75:
            return "critical"

        if drag_score >= 0.50:
            return "high"

        if drag_score >= 0.25:
            return "moderate"

        if drag_score > 0:
            return "low"

        return "none"

    def _safe_number(self, value) -> int | float:
        if value is None:
            return 0

        if isinstance(value, (int, float)):
            return value

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0

    def _empty_drag_summary(self) -> dict:
        return {
            "total_events": 0,
            "drag_event_count": 0,
            "critical_or_high_event_count": 0,
            "total_delay_minutes": 0,
            "event_type_counts": {},
            "severity_counts": {},
            "governance_drag_score": 0.0,
            "drag_level": "none",
        }