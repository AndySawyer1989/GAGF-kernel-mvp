from backend.app.gagf.architectural_diversity_telemetry_adapter import (
    ArchitecturalDiversityTelemetryAdapter,
)


class FakeSourceRegistry:
    def __init__(self, sources):
        self.sources = sources

    def list_sources(self):
        return self.sources


def test_architectural_diversity_telemetry_adapter_builds_empty_source_result():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry([])
    )

    result = adapter.build_components_from_sources()

    assert result == {
        "status": "ok",
        "source_count": 0,
        "component_count": 0,
        "component_origin": "source_registry",
        "components": [],
    }


def test_architectural_diversity_telemetry_adapter_maps_known_sources():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(
            [
                {
                    "source_system": "github",
                    "kernel_role": "delivery",
                    "trust_tier": "tier_3",
                },
                {
                    "source_system": "defender",
                    "kernel_role": "security",
                    "trust_tier": "tier_0",
                },
            ]
        )
    )

    result = adapter.build_components_from_sources()

    assert result["status"] == "ok"
    assert result["source_count"] == 2
    assert result["component_count"] == 2
    assert result["component_origin"] == "source_registry"

    assert result["components"] == [
        {
            "component_id": "source-defender",
            "component_type": "connector",
            "subsystem": "security",
            "authority_zone": "source_connector",
            "redundancy_group": "security_sources",
            "dependencies": ["snapshot-ledger", "gagf-kernel"],
            "interfaces": ["api", "alert_stream"],
            "criticality": "critical",
        },
        {
            "component_id": "source-github",
            "component_type": "connector",
            "subsystem": "delivery",
            "authority_zone": "source_connector",
            "redundancy_group": "delivery_sources",
            "dependencies": ["snapshot-ledger"],
            "interfaces": ["webhook", "api"],
            "criticality": "medium",
        },
    ]


def test_architectural_diversity_telemetry_adapter_maps_identity_sources():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(
            [
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
            ]
        )
    )

    result = adapter.build_components_from_sources()

    assert result["components"] == [
        {
            "component_id": "source-entra",
            "component_type": "connector",
            "subsystem": "identity",
            "authority_zone": "source_connector",
            "redundancy_group": "identity_sources",
            "dependencies": ["snapshot-ledger", "gagf-kernel"],
            "interfaces": ["api", "audit_log"],
            "criticality": "critical",
        },
        {
            "component_id": "source-okta",
            "component_type": "connector",
            "subsystem": "identity",
            "authority_zone": "source_connector",
            "redundancy_group": "identity_sources",
            "dependencies": ["snapshot-ledger", "gagf-kernel"],
            "interfaces": ["api", "system_log"],
            "criticality": "critical",
        },
    ]


def test_architectural_diversity_telemetry_adapter_maps_unknown_source():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(
            [
                {
                    "source_system": "custom_tool",
                    "kernel_role": "custom",
                    "trust_tier": "supporting",
                }
            ]
        )
    )

    result = adapter.build_components_from_sources()

    assert result["components"] == [
        {
            "component_id": "source-custom_tool",
            "component_type": "connector",
            "subsystem": "unknown",
            "authority_zone": "source_connector",
            "redundancy_group": "custom_tool_sources",
            "dependencies": ["snapshot-ledger"],
            "interfaces": ["api"],
            "criticality": "medium",
        }
    ]


def test_architectural_diversity_telemetry_adapter_builds_platform_components():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(
            [
                {
                    "source_system": "jira",
                    "kernel_role": "workflow",
                    "trust_tier": "tier_3",
                },
                {
                    "source_system": "sentinelone",
                    "kernel_role": "security",
                    "trust_tier": "tier_0",
                },
            ]
        )
    )

    result = adapter.build_components_from_platform()

    assert result["status"] == "ok"
    assert result["source_count"] == 2
    assert result["kernel_component_count"] == 4
    assert result["source_component_count"] == 2
    assert result["component_count"] == 6
    assert result["component_origin"] == "platform_telemetry"

    component_ids = [
        component["component_id"]
        for component in result["components"]
    ]

    assert component_ids == [
        "gagf-kernel",
        "snapshot-ledger",
        "decision-ledger",
        "governance-diagnostic-chain",
        "source-jira",
        "source-sentinelone",
    ]


def test_architectural_diversity_telemetry_adapter_resolves_explicit_criticality():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(
            [
                {
                    "source_system": "github",
                    "kernel_role": "delivery",
                    "trust_tier": "tier_3",
                    "criticality": "high",
                }
            ]
        )
    )

    result = adapter.build_components_from_sources()

    assert result["components"][0]["criticality"] == "high"


def test_architectural_diversity_telemetry_adapter_normalizes_source_aliases():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry(
            [
                {
                    "name": "Custom Source",
                    "role": "Security",
                    "trust_tier": "tier_2",
                }
            ]
        )
    )

    result = adapter.build_components_from_sources()

    assert result["components"][0]["component_id"] == "source-custom_source"
    assert result["components"][0]["dependencies"] == [
        "snapshot-ledger",
        "gagf-kernel",
    ]
    assert result["components"][0]["criticality"] == "high"


def test_architectural_diversity_telemetry_adapter_normalizes_strings():
    adapter = ArchitecturalDiversityTelemetryAdapter(
        source_registry=FakeSourceRegistry([])
    )

    assert adapter.normalize_string("Kernel Zone") == "kernel_zone"
    assert adapter.normalize_string("") == "unknown"
    assert adapter.normalize_string(None) == "unknown"




