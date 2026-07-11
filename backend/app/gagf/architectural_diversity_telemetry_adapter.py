from backend.app.gagf.source_registry import SourceRegistry


class ArchitecturalDiversityTelemetryAdapter:
    default_component_map = {
        "github": {
            "component_type": "connector",
            "subsystem": "delivery",
            "authority_zone": "source_connector",
            "redundancy_group": "delivery_sources",
            "interfaces": ["webhook", "api"],
            "criticality": "medium",
        },
        "jira": {
            "component_type": "connector",
            "subsystem": "workflow",
            "authority_zone": "source_connector",
            "redundancy_group": "workflow_sources",
            "interfaces": ["api", "issue_events"],
            "criticality": "medium",
        },
        "servicenow": {
            "component_type": "connector",
            "subsystem": "operations",
            "authority_zone": "source_connector",
            "redundancy_group": "operations_sources",
            "interfaces": ["api", "incident_events"],
            "criticality": "high",
        },
        "okta": {
            "component_type": "connector",
            "subsystem": "identity",
            "authority_zone": "source_connector",
            "redundancy_group": "identity_sources",
            "interfaces": ["api", "system_log"],
            "criticality": "high",
        },
        "entra": {
            "component_type": "connector",
            "subsystem": "identity",
            "authority_zone": "source_connector",
            "redundancy_group": "identity_sources",
            "interfaces": ["api", "audit_log"],
            "criticality": "high",
        },
        "defender": {
            "component_type": "connector",
            "subsystem": "security",
            "authority_zone": "source_connector",
            "redundancy_group": "security_sources",
            "interfaces": ["api", "alert_stream"],
            "criticality": "critical",
        },
        "sentinelone": {
            "component_type": "connector",
            "subsystem": "security",
            "authority_zone": "source_connector",
            "redundancy_group": "security_sources",
            "interfaces": ["api", "threat_stream"],
            "criticality": "critical",
        },
    }

    kernel_components = [
        {
            "component_id": "gagf-kernel",
            "component_type": "kernel",
            "subsystem": "decision",
            "authority_zone": "kernel",
            "redundancy_group": "kernel-core",
            "dependencies": ["snapshot-ledger", "decision-ledger"],
            "interfaces": ["arbitration", "policy", "decision"],
            "criticality": "critical",
        },
        {
            "component_id": "snapshot-ledger",
            "component_type": "ledger",
            "subsystem": "evidence",
            "authority_zone": "ledger",
            "redundancy_group": "evidence-ledgers",
            "dependencies": [],
            "interfaces": ["snapshot", "diagnostics", "confidence"],
            "criticality": "critical",
        },
        {
            "component_id": "decision-ledger",
            "component_type": "ledger",
            "subsystem": "decision",
            "authority_zone": "ledger",
            "redundancy_group": "decision-ledgers",
            "dependencies": [],
            "interfaces": ["decision", "audit"],
            "criticality": "critical",
        },
        {
            "component_id": "governance-diagnostic-chain",
            "component_type": "worker",
            "subsystem": "diagnostics",
            "authority_zone": "diagnostic",
            "redundancy_group": "diagnostic-workers",
            "dependencies": [
                "governance-signals",
                "friction-signals",
                "governance-debt",
                "intervention-candidates",
            ],
            "interfaces": ["signals", "correlations", "friction", "debt"],
            "criticality": "high",
        },
    ]

    def __init__(self, source_registry: SourceRegistry | None = None):
        self.source_registry = source_registry or SourceRegistry()

    def build_components_from_sources(self) -> dict:
        sources = self.source_registry.list_sources()
        components = self.build_source_components(sources)

        return {
            "status": "ok",
            "source_count": len(sources),
            "component_count": len(components),
            "component_origin": "source_registry",
            "components": components,
        }

    def build_components_from_platform(self) -> dict:
        source_result = self.build_components_from_sources()
        source_components = source_result["components"]
        kernel_components = [dict(component) for component in self.kernel_components]

        components = kernel_components + source_components

        return {
            "status": "ok",
            "source_count": source_result["source_count"],
            "kernel_component_count": len(kernel_components),
            "source_component_count": len(source_components),
            "component_count": len(components),
            "component_origin": "platform_telemetry",
            "components": components,
        }

    def build_source_components(self, sources: list[dict]) -> list[dict]:
        components = []

        for source in sources:
            source_system = self.normalize_string(
                source.get("source_system") or source.get("name") or "unknown"
            )
            mapping = self.default_component_map.get(
                source_system,
                self.default_source_component_mapping(source_system),
            )

            component = {
                "component_id": f"source-{source_system}",
                "component_type": mapping["component_type"],
                "subsystem": mapping["subsystem"],
                "authority_zone": mapping["authority_zone"],
                "redundancy_group": mapping["redundancy_group"],
                "dependencies": self.build_source_dependencies(source),
                "interfaces": list(mapping["interfaces"]),
                "criticality": self.resolve_criticality(
                    source=source,
                    fallback=mapping["criticality"],
                ),
            }

            components.append(component)

        return sorted(
            components,
            key=lambda component: component["component_id"],
        )

    def build_source_dependencies(self, source: dict) -> list[str]:
        dependencies = ["snapshot-ledger"]

        kernel_role = self.normalize_string(
            source.get("kernel_role") or source.get("role") or ""
        )

        if kernel_role in {"security", "identity", "governance"}:
            dependencies.append("gagf-kernel")

        return dependencies

    def default_source_component_mapping(self, source_system: str) -> dict:
        return {
            "component_type": "connector",
            "subsystem": "unknown",
            "authority_zone": "source_connector",
            "redundancy_group": f"{source_system}_sources",
            "interfaces": ["api"],
            "criticality": "unknown",
        }

    def resolve_criticality(self, source: dict, fallback: str) -> str:
        explicit = self.normalize_string(
            source.get("criticality") or source.get("trust_tier") or ""
        )

        if explicit in {"critical", "high", "medium", "low"}:
            return explicit

        trust_tier = self.normalize_string(source.get("trust_tier") or "")

        if trust_tier in {"tier_0", "tier_1", "primary"}:
            return "critical"

        if trust_tier in {"tier_2", "secondary"}:
            return "high"

        if trust_tier in {"tier_3", "supporting"}:
            return "medium"

        return fallback

    def normalize_string(self, value) -> str:
        if value is None:
            return "unknown"

        normalized = str(value).strip().lower().replace(" ", "_")

        if not normalized:
            return "unknown"

        return normalized