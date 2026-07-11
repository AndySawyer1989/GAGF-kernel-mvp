class ArchitectureDriftDashboardService:
    def build_summary(self, drift_result: dict) -> dict:
        drift_status = drift_result.get("drift_status", "unknown")
        score_drift = drift_result.get("score_drift", {})
        posture_drift = drift_result.get("posture_drift", {})

        return {
            "status": "ok",
            "summary_type": "architecture_drift_dashboard",
            "drift_status": drift_status,
            "drift_severity": score_drift.get("severity", "none"),
            "operator_message": self.get_operator_message(drift_status),
            "recommended_action": drift_result.get(
                "recommended_action",
                self.get_recommended_action(drift_status),
            ),
            "scorecards": self.build_scorecards(score_drift),
            "component_summary": self.build_component_summary(drift_result),
            "posture_summary": self.build_posture_summary(posture_drift),
            "risk_summary": self.build_risk_summary(
                drift_status=drift_status,
                score_drift=score_drift,
                posture_drift=posture_drift,
            ),
        }

    def build_scorecards(self, score_drift: dict) -> list[dict]:
        return [
            {
                "label": "ADI Drift",
                "metric": "architectural_diversity_index_delta",
                "value": score_drift.get(
                    "architectural_diversity_index_delta",
                    0.0,
                ),
                "interpretation": self.interpret_delta(
                    delta=score_drift.get(
                        "architectural_diversity_index_delta",
                        0.0,
                    ),
                    positive_is_good=True,
                ),
            },
            {
                "label": "CRR Drift",
                "metric": "complexity_resilience_ratio_delta",
                "value": score_drift.get(
                    "complexity_resilience_ratio_delta",
                    0.0,
                ),
                "interpretation": self.interpret_delta(
                    delta=score_drift.get(
                        "complexity_resilience_ratio_delta",
                        0.0,
                    ),
                    positive_is_good=True,
                ),
            },
            {
                "label": "Mononal Risk Drift",
                "metric": "mononal_risk_score_delta",
                "value": score_drift.get(
                    "mononal_risk_score_delta",
                    0.0,
                ),
                "interpretation": self.interpret_delta(
                    delta=score_drift.get(
                        "mononal_risk_score_delta",
                        0.0,
                    ),
                    positive_is_good=False,
                ),
            },
        ]

    def build_component_summary(self, drift_result: dict) -> dict:
        return {
            "baseline_component_count": drift_result.get(
                "baseline_component_count",
                0,
            ),
            "current_component_count": drift_result.get(
                "current_component_count",
                0,
            ),
            "component_count_delta": drift_result.get(
                "component_count_delta",
                0,
            ),
        }

    def build_posture_summary(self, posture_drift: dict) -> dict:
        return {
            "architecture_posture_changed": posture_drift.get(
                "architecture_posture_changed",
                False,
            ),
            "concentration_risk_changed": posture_drift.get(
                "concentration_risk_changed",
                False,
            ),
            "platform_architecture_status_changed": posture_drift.get(
                "platform_architecture_status_changed",
                False,
            ),
            "posture_regressed": posture_drift.get(
                "posture_regressed",
                False,
            ),
            "baseline_architecture_posture": posture_drift.get(
                "baseline_architecture_posture",
                "none",
            ),
            "current_architecture_posture": posture_drift.get(
                "current_architecture_posture",
                "none",
            ),
            "baseline_concentration_risk": posture_drift.get(
                "baseline_concentration_risk",
                "none",
            ),
            "current_concentration_risk": posture_drift.get(
                "current_concentration_risk",
                "none",
            ),
            "baseline_platform_architecture_status": posture_drift.get(
                "baseline_platform_architecture_status",
                "none",
            ),
            "current_platform_architecture_status": posture_drift.get(
                "current_platform_architecture_status",
                "none",
            ),
        }

    def build_risk_summary(
        self,
        drift_status: str,
        score_drift: dict,
        posture_drift: dict,
    ) -> dict:
        return {
            "drift_status": drift_status,
            "drift_severity": score_drift.get("severity", "none"),
            "diversity_regressed": score_drift.get(
                "diversity_regressed",
                False,
            ),
            "resilience_regressed": score_drift.get(
                "resilience_regressed",
                False,
            ),
            "mononal_risk_increased": score_drift.get(
                "mononal_risk_increased",
                False,
            ),
            "posture_regressed": posture_drift.get(
                "posture_regressed",
                False,
            ),
            "highest_attention_area": self.get_highest_attention_area(
                drift_status=drift_status,
                score_drift=score_drift,
                posture_drift=posture_drift,
            ),
        }

    def get_highest_attention_area(
        self,
        drift_status: str,
        score_drift: dict,
        posture_drift: dict,
    ) -> str:
        if drift_status == "critical_architecture_drift":
            return "critical_architecture_regression"

        if score_drift.get("mononal_risk_increased", False):
            return "mononal_risk_increase"

        if score_drift.get("diversity_regressed", False):
            return "architectural_diversity_regression"

        if score_drift.get("resilience_regressed", False):
            return "complexity_resilience_regression"

        if posture_drift.get("posture_regressed", False):
            return "platform_posture_regression"

        return "none"

    def get_operator_message(self, drift_status: str) -> str:
        messages = {
            "critical_architecture_drift": (
                "Architecture drift is critical and requires immediate "
                "stabilization."
            ),
            "high_architecture_drift": (
                "Architecture drift is high and requires regression review."
            ),
            "moderate_architecture_drift": (
                "Architecture drift is moderate and should be monitored."
            ),
            "low_architecture_drift": (
                "Architecture drift is low and should be tracked."
            ),
            "no_architecture_drift": (
                "No architecture drift is currently detected."
            ),
        }

        return messages.get(
            drift_status,
            "Architecture drift status is unknown and requires review.",
        )

    def get_recommended_action(self, drift_status: str) -> str:
        actions = {
            "critical_architecture_drift": (
                "stabilize_architecture_and_reduce_mononal_risk"
            ),
            "high_architecture_drift": (
                "review_architecture_regression_sources"
            ),
            "moderate_architecture_drift": (
                "monitor_architecture_diversity_regression"
            ),
            "low_architecture_drift": "track_architecture_drift",
            "no_architecture_drift": "continue_monitoring",
        }

        return actions.get(drift_status, "review_architecture_drift")

    def interpret_delta(
        self,
        delta: float,
        positive_is_good: bool,
    ) -> str:
        if delta == 0:
            return "stable"

        if positive_is_good:
            if delta > 0:
                return "improved"
            return "regressed"

        if delta > 0:
            return "risk_increased"

        return "risk_reduced"