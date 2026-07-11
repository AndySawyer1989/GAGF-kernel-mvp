from backend.app.gagf.architectural_diversity_diagnostic_service import (
    ArchitecturalDiversityDiagnosticService,
)
from backend.app.gagf.architectural_diversity_telemetry_adapter import (
    ArchitecturalDiversityTelemetryAdapter,
)


class ArchitecturalDiversityPlatformService:
    def __init__(
        self,
        telemetry_adapter: ArchitecturalDiversityTelemetryAdapter | None = None,
        diagnostic_service: ArchitecturalDiversityDiagnosticService | None = None,
    ):
        self.telemetry_adapter = (
            telemetry_adapter or ArchitecturalDiversityTelemetryAdapter()
        )
        self.diagnostic_service = (
            diagnostic_service or ArchitecturalDiversityDiagnosticService()
        )

    def diagnose_platform(self) -> dict:
        telemetry_result = self.telemetry_adapter.build_components_from_platform()
        diagnostic_result = self.diagnostic_service.diagnose_components(
            telemetry_result["components"]
        )

        return self.build_platform_result(
            telemetry_result=telemetry_result,
            diagnostic_result=diagnostic_result,
        )

    def build_platform_result(
        self,
        telemetry_result: dict,
        diagnostic_result: dict,
    ) -> dict:
        architecture_posture = diagnostic_result["architecture_posture"]
        concentration_risk = diagnostic_result["concentration_risk"]

        return {
            "status": "ok",
            "component_origin": telemetry_result["component_origin"],
            "source_count": telemetry_result["source_count"],
            "kernel_component_count": telemetry_result[
                "kernel_component_count"
            ],
            "source_component_count": telemetry_result[
                "source_component_count"
            ],
            "component_count": telemetry_result["component_count"],
            "architectural_diversity_index": diagnostic_result[
                "architectural_diversity_index"
            ],
            "complexity_resilience_ratio": diagnostic_result[
                "complexity_resilience_ratio"
            ],
            "mononal_risk_score": diagnostic_result["mononal_risk_score"],
            "architecture_posture": architecture_posture,
            "concentration_risk": concentration_risk,
            "platform_architecture_status": (
                self.get_platform_architecture_status(
                    architecture_posture=architecture_posture,
                    concentration_risk=concentration_risk,
                )
            ),
            "dominant_component_type": diagnostic_result[
                "dominant_component_type"
            ],
            "component_type_counts": diagnostic_result[
                "component_type_counts"
            ],
            "subsystem_counts": diagnostic_result["subsystem_counts"],
            "authority_zone_counts": diagnostic_result[
                "authority_zone_counts"
            ],
            "redundancy_group_counts": diagnostic_result[
                "redundancy_group_counts"
            ],
            "diversity_breakdown": diagnostic_result[
                "diversity_breakdown"
            ],
            "component_diagnostics": diagnostic_result[
                "component_diagnostics"
            ],
            "components": telemetry_result["components"],
        }

    def get_platform_architecture_status(
        self,
        architecture_posture: str,
        concentration_risk: str,
    ) -> str:
        if architecture_posture == "none":
            return "none"

        if (
            architecture_posture == "mononal_architecture_risk"
            or concentration_risk == "critical"
        ):
            return "platform_architecture_mononal_risk"

        if (
            architecture_posture == "concentrated_architecture"
            or concentration_risk == "high"
        ):
            return "platform_architecture_concentrated"

        if (
            architecture_posture == "adaptive_diverse_architecture"
            and concentration_risk in {"none", "low"}
        ):
            return "platform_architecture_resilient"

        if (
            architecture_posture == "mixed_resilience_architecture"
            and concentration_risk in {"low", "moderate"}
        ):
            return "platform_architecture_balanced"

        return "platform_architecture_review"