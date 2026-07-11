from backend.app.gagf.architectural_diversity_platform_service import (
    ArchitecturalDiversityPlatformService,
)


class ArchitecturalDiversityDashboardService:
    def __init__(
        self,
        platform_service: ArchitecturalDiversityPlatformService | None = None,
    ):
        self.platform_service = (
            platform_service or ArchitecturalDiversityPlatformService()
        )

    def get_summary(self) -> dict:
        platform_result = self.platform_service.diagnose_platform()

        return self.build_summary(platform_result)

    def build_summary(self, platform_result: dict) -> dict:
        status = platform_result["platform_architecture_status"]
        posture = platform_result["architecture_posture"]
        concentration_risk = platform_result["concentration_risk"]

        return {
            "status": "ok",
            "summary_type": "architectural_diversity_dashboard",
            "platform_architecture_status": status,
            "architecture_posture": posture,
            "concentration_risk": concentration_risk,
            "operator_message": self.get_operator_message(status),
            "recommended_action": self.get_recommended_action(
                platform_architecture_status=status,
                concentration_risk=concentration_risk,
            ),
            "scorecards": self.build_scorecards(platform_result),
            "component_summary": self.build_component_summary(
                platform_result
            ),
            "risk_summary": self.build_risk_summary(platform_result),
        }

    def build_scorecards(self, platform_result: dict) -> list[dict]:
        return [
            {
                "label": "Architectural Diversity Index",
                "metric": "architectural_diversity_index",
                "value": platform_result["architectural_diversity_index"],
                "interpretation": self.interpret_adi(
                    platform_result["architectural_diversity_index"]
                ),
            },
            {
                "label": "Complexity Resilience Ratio",
                "metric": "complexity_resilience_ratio",
                "value": platform_result["complexity_resilience_ratio"],
                "interpretation": self.interpret_crr(
                    platform_result["complexity_resilience_ratio"]
                ),
            },
            {
                "label": "Mononal Risk Score",
                "metric": "mononal_risk_score",
                "value": platform_result["mononal_risk_score"],
                "interpretation": self.interpret_mononal_risk(
                    platform_result["mononal_risk_score"]
                ),
            },
        ]

    def build_component_summary(self, platform_result: dict) -> dict:
        return {
            "component_count": platform_result["component_count"],
            "kernel_component_count": platform_result[
                "kernel_component_count"
            ],
            "source_component_count": platform_result[
                "source_component_count"
            ],
            "dominant_component_type": platform_result[
                "dominant_component_type"
            ],
            "component_type_counts": platform_result[
                "component_type_counts"
            ],
            "subsystem_counts": platform_result["subsystem_counts"],
            "authority_zone_counts": platform_result[
                "authority_zone_counts"
            ],
            "redundancy_group_counts": platform_result[
                "redundancy_group_counts"
            ],
        }

    def build_risk_summary(self, platform_result: dict) -> dict:
        return {
            "architecture_posture": platform_result["architecture_posture"],
            "concentration_risk": platform_result["concentration_risk"],
            "mononal_risk_score": platform_result["mononal_risk_score"],
            "platform_architecture_status": platform_result[
                "platform_architecture_status"
            ],
            "highest_attention_area": self.get_highest_attention_area(
                platform_result
            ),
        }

    def get_operator_message(self, platform_architecture_status: str) -> str:
        messages = {
            "platform_architecture_resilient": (
                "Architecture is currently diverse and resilient."
            ),
            "platform_architecture_balanced": (
                "Architecture is balanced with manageable concentration risk."
            ),
            "platform_architecture_concentrated": (
                "Architecture shows concentration pressure requiring review."
            ),
            "platform_architecture_mononal_risk": (
                "Architecture shows mononal-risk conditions requiring "
                "priority attention."
            ),
            "platform_architecture_review": (
                "Architecture requires review because diagnostic posture is "
                "not yet decisive."
            ),
            "none": "No architecture components are available for diagnosis.",
        }

        return messages.get(
            platform_architecture_status,
            "Architecture status is unknown and requires review.",
        )

    def get_recommended_action(
        self,
        platform_architecture_status: str,
        concentration_risk: str,
    ) -> str:
        if platform_architecture_status == "none":
            return "collect_architecture_components"

        if platform_architecture_status == (
            "platform_architecture_mononal_risk"
        ):
            return "reduce_authority_and_component_concentration"

        if concentration_risk == "critical":
            return "partition_critical_concentration"

        if platform_architecture_status == (
            "platform_architecture_concentrated"
        ):
            return "review_dominant_component_and_redundancy_patterns"

        if platform_architecture_status == "platform_architecture_balanced":
            return "monitor_architecture_concentration"

        if platform_architecture_status == "platform_architecture_resilient":
            return "continue_monitoring"

        return "review_architecture_diagnostics"

    def get_highest_attention_area(self, platform_result: dict) -> str:
        concentration_risk = platform_result["concentration_risk"]
        dominant_component_type = platform_result["dominant_component_type"]
        posture = platform_result["architecture_posture"]

        if concentration_risk in {"critical", "high"}:
            return f"dominant_component_type:{dominant_component_type}"

        if posture == "mononal_architecture_risk":
            return "mononal_architecture_pattern"

        if posture == "concentrated_architecture":
            return "architecture_concentration"

        return "none"

    def interpret_adi(self, score: float) -> str:
        if score >= 0.75:
            return "high_diversity"

        if score >= 0.50:
            return "moderate_diversity"

        if score > 0:
            return "low_diversity"

        return "no_diversity_data"

    def interpret_crr(self, score: float) -> str:
        if score >= 0.70:
            return "high_resilience"

        if score >= 0.50:
            return "moderate_resilience"

        if score > 0:
            return "low_resilience"

        return "no_resilience_data"

    def interpret_mononal_risk(self, score: float) -> str:
        if score >= 0.75:
            return "critical_mononal_risk"

        if score >= 0.50:
            return "high_mononal_risk"

        if score >= 0.25:
            return "moderate_mononal_risk"

        if score > 0:
            return "low_mononal_risk"

        return "no_mononal_risk"