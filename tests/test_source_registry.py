from backend.app.gagf.source_registry import SourceRegistry


def test_source_registry_lists_supported_sources():
    registry = SourceRegistry()

    sources = registry.list_sources()
    source_systems = {source["source_system"] for source in sources}

    assert "github" in source_systems
    assert "jira" in source_systems
    assert "servicenow" in source_systems
    assert "okta" in source_systems
    assert "entra" in source_systems
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_registry_includes_defender_metadata():
    registry = SourceRegistry()

    defender = registry.get_source("defender")

    assert defender is not None
    assert defender["source_system"] == "defender"
    assert defender["display_name"] == "Microsoft Defender"
    assert defender["category"] == "endpoint_security"
    assert defender["ingestion_endpoint"] == "/ingest/defender"
    assert defender["trust_tier"] == "security"
    assert defender["kernel_role"] == "threat_evidence"
    assert defender["enabled"] is True


def test_source_registry_includes_sentinelone_metadata():
    registry = SourceRegistry()

    sentinelone = registry.get_source("sentinelone")

    assert sentinelone is not None
    assert sentinelone["source_system"] == "sentinelone"
    assert sentinelone["display_name"] == "SentinelOne"
    assert sentinelone["category"] == "endpoint_security"
    assert sentinelone["ingestion_endpoint"] == "/ingest/sentinelone"
    assert sentinelone["trust_tier"] == "security"
    assert sentinelone["kernel_role"] == "threat_evidence"
    assert sentinelone["enabled"] is True


def test_source_registry_returns_none_for_unknown_source():
    registry = SourceRegistry()

    unknown = registry.get_source("unknown-source")

    assert unknown is None



