class ArchitectureDriftDetectionService:
    def detect_drift(
        self,
        baseline_result: dict,
        current_result: dict,
    ) -> dict:
        baseline_scores = self.extract_scores(baseline_result)
        current_scores = self.extract_scores(current_result)

        score_drift = self.calculate_score_drift(
            baseline_scores=baseline_scores,
            current_scores=current_scores,
        )

        posture_drift = self.calculate_posture_drift(
            baseline_result=baseline_result,
            current_result=current_result,
        )

        drift_status = self.get_drift_status(
            score_drift=score_drift,
            posture_drift=posture_drift,
        )

        return {
            "status": "ok",
            "drift_type": "architecture_drift",
            "baseline_component_count": baseline_result.get(
                "component_count",
                0,
            ),
            "current_component_count": current_result.get(
                "component_count",
                0,
            ),
            "component_count_delta": (
                current_result.get("component_count", 0)
                - baseline_result.get("component_count", 0)
            ),
            "baseline_scores": baseline_scores,
            "current_scores": current_scores,
            "score_drift": score_drift,
            "posture_drift": posture_drift,
            "drift_status": drift_status,
            "recommended_action": self.get_recommended_action(drift_status),
        }

    def extract_scores(self, result: dict) -> dict:
        return {
            "architectural_diversity_index": result.get(
                "architectural_diversity_index",
                0.0,
            ),
            "complexity_resilience_ratio": result.get(
                "complexity_resilience_ratio",
                0.0,
            ),
            "mononal_risk_score": result.get(
                "mononal_risk_score",
                0.0,
            ),
        }

    def calculate_score_drift(
        self,
        baseline_scores: dict,
        current_scores: dict,
    ) -> dict:
        adi_delta = round(
            current_scores["architectural_diversity_index"]
            - baseline_scores["architectural_diversity_index"],
            4,
        )
        crr_delta = round(
            current_scores["complexity_resilience_ratio"]
            - baseline_scores["complexity_resilience_ratio"],
            4,
        )
        mononal_delta = round(
            current_scores["mononal_risk_score"]
            - baseline_scores["mononal_risk_score"],
            4,
        )

        return {
            "architectural_diversity_index_delta": adi_delta,
            "complexity_resilience_ratio_delta": crr_delta,
            "mononal_risk_score_delta": mononal_delta,
            "diversity_regressed": adi_delta < 0,
            "resilience_regressed": crr_delta < 0,
            "mononal_risk_increased": mononal_delta > 0,
            "severity": self.get_score_drift_severity(
                adi_delta=adi_delta,
                crr_delta=crr_delta,
                mononal_delta=mononal_delta,
            ),
        }

    def calculate_posture_drift(
        self,
        baseline_result: dict,
        current_result: dict,
    ) -> dict:
        baseline_architecture_posture = baseline_result.get(
            "architecture_posture",
            "none",
        )
        current_architecture_posture = current_result.get(
            "architecture_posture",
            "none",
        )
        baseline_concentration_risk = baseline_result.get(
            "concentration_risk",
            "none",
        )
        current_concentration_risk = current_result.get(
            "concentration_risk",
            "none",
        )
        baseline_platform_status = baseline_result.get(
            "platform_architecture_status",
            "none",
        )
        current_platform_status = current_result.get(
            "platform_architecture_status",
            "none",
        )

        return {
            "architecture_posture_changed": (
                baseline_architecture_posture
                != current_architecture_posture
            ),
            "concentration_risk_changed": (
                baseline_concentration_risk
                != current_concentration_risk
            ),
            "platform_architecture_status_changed": (
                baseline_platform_status != current_platform_status
            ),
            "baseline_architecture_posture": baseline_architecture_posture,
            "current_architecture_posture": current_architecture_posture,
            "baseline_concentration_risk": baseline_concentration_risk,
            "current_concentration_risk": current_concentration_risk,
            "baseline_platform_architecture_status": (
                baseline_platform_status
            ),
            "current_platform_architecture_status": current_platform_status,
            "posture_regressed": self.posture_regressed(
                baseline_result=baseline_result,
                current_result=current_result,
            ),
        }

    def get_score_drift_severity(
        self,
        adi_delta: float,
        crr_delta: float,
        mononal_delta: float,
    ) -> str:
        if (
            adi_delta <= -0.25
            or crr_delta <= -0.25
            or mononal_delta >= 0.25
        ):
            return "critical"

        if (
            adi_delta <= -0.15
            or crr_delta <= -0.15
            or mononal_delta >= 0.15
        ):
            return "high"

        if (
            adi_delta <= -0.05
            or crr_delta <= -0.05
            or mononal_delta >= 0.05
        ):
            return "moderate"

        if adi_delta < 0 or crr_delta < 0 or mononal_delta > 0:
            return "low"

        return "none"

    def posture_regressed(
        self,
        baseline_result: dict,
        current_result: dict,
    ) -> bool:
        baseline_rank = self.posture_rank(
            baseline_result.get("platform_architecture_status", "none")
        )
        current_rank = self.posture_rank(
            current_result.get("platform_architecture_status", "none")
        )

        return current_rank > baseline_rank

    def posture_rank(self, platform_architecture_status: str) -> int:
        ranks = {
            "platform_architecture_resilient": 0,
            "platform_architecture_balanced": 1,
            "platform_architecture_review": 2,
            "platform_architecture_concentrated": 3,
            "platform_architecture_mononal_risk": 4,
            "none": 5,
        }

        return ranks.get(platform_architecture_status, 5)

    def get_drift_status(
        self,
        score_drift: dict,
        posture_drift: dict,
    ) -> str:
        if (
            score_drift["severity"] == "critical"
            or posture_drift["current_platform_architecture_status"]
            == "platform_architecture_mononal_risk"
        ):
            return "critical_architecture_drift"

        if (
            score_drift["severity"] == "high"
            or posture_drift["posture_regressed"]
        ):
            return "high_architecture_drift"

        if score_drift["severity"] == "moderate":
            return "moderate_architecture_drift"

        if score_drift["severity"] == "low":
            return "low_architecture_drift"

        return "no_architecture_drift"

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