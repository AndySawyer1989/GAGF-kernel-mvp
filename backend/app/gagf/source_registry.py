from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class SourceDefinition:
    source_system: str
    display_name: str
    category: str
    ingestion_endpoint: str
    trust_tier: str
    kernel_role: str
    enabled: bool = True


class SourceRegistry:
    def __init__(self):
        self.sources = {
            "github": SourceDefinition(
                source_system="github",
                display_name="GitHub",
                category="devops",
                ingestion_endpoint="/ingest/github",
                trust_tier="operational",
                kernel_role="delivery_evidence",
            ),
            "jira": SourceDefinition(
                source_system="jira",
                display_name="Jira",
                category="work_management",
                ingestion_endpoint="/ingest/jira",
                trust_tier="operational",
                kernel_role="workflow_evidence",
            ),
            "servicenow": SourceDefinition(
                source_system="servicenow",
                display_name="ServiceNow",
                category="it_service_management",
                ingestion_endpoint="/ingest/servicenow",
                trust_tier="operational",
                kernel_role="incident_evidence",
            ),
            "okta": SourceDefinition(
                source_system="okta",
                display_name="Okta",
                category="identity",
                ingestion_endpoint="/ingest/okta",
                trust_tier="security",
                kernel_role="identity_evidence",
            ),
            "entra": SourceDefinition(
                source_system="entra",
                display_name="Microsoft Entra ID",
                category="identity",
                ingestion_endpoint="/ingest/entra",
                trust_tier="security",
                kernel_role="identity_evidence",
            ),
            "defender": SourceDefinition(
                source_system="defender",
                display_name="Microsoft Defender",
                category="endpoint_security",
                ingestion_endpoint="/ingest/defender",
                trust_tier="security",
                kernel_role="threat_evidence",
            ),
            "sentinelone": SourceDefinition(
                source_system="sentinelone",
                display_name="SentinelOne",
                category="endpoint_security",
                ingestion_endpoint="/ingest/sentinelone",
                trust_tier="security",
                kernel_role="threat_evidence",
            ),
        }

    def list_sources(self) -> list[dict]:
        return [asdict(source) for source in self.sources.values()]

    def get_source(self, source_system: str) -> dict | None:
        source = self.sources.get(source_system)

        if source is None:
            return None

        return asdict(source)

    def list_enabled_sources(self) -> list[dict]:
        return [
            asdict(source)
            for source in self.sources.values()
            if source.enabled is True
        ]