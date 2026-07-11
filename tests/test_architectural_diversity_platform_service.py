from backend.app.gagf.architectural_diversity_platform_service import (
    ArchitecturalDiversityPlatformService,
)
from backend.app.gagf.architectural_diversity_telemetry_adapter import (
    ArchitecturalDiversityTelemetryAdapter,
)


class FakeSourceRegistry:
    def __init__(self, sources):
        self.sources = sources

    def list_sources(self):
        return self.sources


def build_service_with_sources(sources):
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(sources)
    )

    return ArchitecturalDiversityPlatformService(
        telemetry_adapter=adapter,
    )


def test_architectural_diversity_platform_service_diagnoses_kernel_only_platform():
    result = build_service_with_sources([]).diagnose_platform()

    assert result["status"] == "ok"
    assert result["component_origin"] == "platform_telemetry"
    assert result["source_count"] == 0
    assert result["kernel_component_count"] == 4
    assert result["source_component_count"] == 0
    assert result["component_count"] == 4

    assert result["architectural_diversity_index"] == 0.8125
    assert result["complexity_resilience_ratio"] == 0.8875
    assert result["mononal_risk_score"] == 0.1875
    assert result["architecture_posture"] == "adaptive_diverse_architecture"
    assert result["concentration_risk"] == "low"
    assert result["platform_architecture_status"] == (
        "platform_architecture_resilient"
    )
    assert result["dominant_component_type"] == "ledger"


def test_architectural_diversity_platform_service_diagnoses_full_known_platform():
    result = build_service_with_sources(
        [
            {
                "source_system": "github",
                "kernel_role": "delivery",
                "trust_tier": "tier_3",
            },
            {
                "source_system": "jira",
                "kernel_role": "workflow",
                "trust_tier": "tier_3",
            },
            {
                "source_system": "okta",
                "kernel_role": "identity",
                "trust_tier": "tier_1",
            },
            {
                "source_system": "entra",
                "kernel_role": "identity",
                "trust_tier": "tier_1",
            },
            {
                "source_system": "defender",
                "kernel_role": "security",
                "trust_tier": "tier_0",
            },
            {
                "source_system": "sentinelone",
                "kernel_role": "security",
                "trust_tier": "tier_0",
            },
            {
                "source_system": "servicenow",
                "kernel_role": "operations",
                "trust_tier": "tier_2",
            },
        ]
    ).diagnose_platform()

    assert result["status"] == "ok"
    assert result["source_count"] == 7
    assert result["kernel_component_count"] == 4
    assert result["source_component_count"] == 7
    assert result["component_count"] == 11

    assert result["architectural_diversity_index"] == 0.5682
    assert result["complexity_resilience_ratio"] == 0.6637
    assert result["mononal_risk_score"] == 0.4318
    assert result["architecture_posture"] == "mixed_resilience_architecture"
    assert result["concentration_risk"] == "moderate"
    assert result["platform_architecture_status"] == (
        "platform_architecture_balanced"
    )
    assert result["dominant_component_type"] == "connector"

    assert result["component_type_counts"] == {
        "kernel": 1,
        "ledger": 2,
        "worker": 1,
        "connector": 7,
    }

    assert result["subsystem_counts"] == {
        "decision": 2,
        "evidence": 1,
        "diagnostics": 1,
        "delivery": 1,
        "security": 2,
        "identity": 2,
        "workflow": 1,
        "operations": 1,
    }


def test_architectural_diversity_platform_service_preserves_components():
    result = build_service_with_sources(
        [
            {
                "source_system": "defender",
                "kernel_role": "security",
                "trust_tier": "tier_0",
            }
        ]
    ).diagnose_platform()

    component_ids = [
        component["component_id"]
        for component in result["components"]
    ]

    assert component_ids == [
        "gagf-kernel",
        "snapshot-ledger",
        "decision-ledger",
        "governance-diagnostic-chain",
        "source-defender",
    ]

    assert len(result["component_diagnostics"]) == 5


def test_architectural_diversity_platform_service_marks_resilient_status():
    service = ArchitecturalDiversityPlatformService()

    assert service.get_platform_architecture_status(
        architecture_posture="adaptive_diverse_architecture",
        concentration_risk="low",
    ) == "platform_architecture_resilient"

    assert service.get_platform_architecture_status(
        architecture_posture="adaptive_diverse_architecture",
        concentration_risk="none",
    ) == "platform_architecture_resilient"


def test_architectural_diversity_platform_service_marks_balanced_status():
    service = ArchitecturalDiversityPlatformService()

    assert service.get_platform_architecture_status(
        architecture_posture="mixed_resilience_architecture",
        concentration_risk="moderate",
    ) == "platform_architecture_balanced"

    assert service.get_platform_architecture_status(
        architecture_posture="mixed_resilience_architecture",
        concentration_risk="low",
    ) == "platform_architecture_balanced"


def test_architectural_diversity_platform_service_marks_concentrated_status():
    service = ArchitecturalDiversityPlatformService()

    assert service.get_platform_architecture_status(
        architecture_posture="concentrated_architecture",
        concentration_risk="moderate",
    ) == "platform_architecture_concentrated"

    assert service.get_platform_architecture_status(
        architecture_posture="mixed_resilience_architecture",
        concentration_risk="high",
    ) == "platform_architecture_concentrated"


def test_architectural_diversity_platform_service_marks_mononal_risk_status():
    service = ArchitecturalDiversityPlatformService()

    assert service.get_platform_architecture_status(
        architecture_posture="mononal_architecture_risk",
        concentration_risk="high",
    ) == "platform_architecture_mononal_risk"

    assert service.get_platform_architecture_status(
        architecture_posture="concentrated_architecture",
        concentration_risk="critical",
    ) == "platform_architecture_mononal_risk"
