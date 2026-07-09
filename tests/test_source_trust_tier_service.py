from backend.app.gagf.source_trust_tier_service import SourceTrustTierService


def test_source_trust_tier_service_returns_summary():
    summary = SourceTrustTierService().get_trust_tier_summary()

    assert summary["status"] == "ok"
    assert summary["trust_tier_count"] >= 2
    assert isinstance(summary["trust_tiers"], list)


def test_source_trust_tier_service_groups_security_sources():
    summary = SourceTrustTierService().get_trust_tier_summary()

    trust_tiers = {
        trust_tier["trust_tier"]: trust_tier
        for trust_tier in summary["trust_tiers"]
    }

    assert "security" in trust_tiers
    assert trust_tiers["security"]["source_count"] == 4

    source_systems = {
        source["source_system"]
        for source in trust_tiers["security"]["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_trust_tier_service_groups_operational_sources():
    summary = SourceTrustTierService().get_trust_tier_summary()

    trust_tiers = {
        trust_tier["trust_tier"]: trust_tier
        for trust_tier in summary["trust_tiers"]
    }

    assert "operational" in trust_tiers
    assert trust_tiers["operational"]["source_count"] == 3

    source_systems = {
        source["source_system"]
        for source in trust_tiers["operational"]["sources"]
    }

    assert "github" in source_systems
    assert "jira" in source_systems
    assert "servicenow" in source_systems


def test_source_trust_tier_service_gets_sources_for_trust_tier():
    service = SourceTrustTierService()

    sources = service.get_sources_for_trust_tier("security")
    source_systems = {source["source_system"] for source in sources}

    assert len(sources) == 4
    assert "okta" in source_systems
    assert "entra" in source_systems
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_trust_tier_service_returns_empty_list_for_unknown_trust_tier():
    service = SourceTrustTierService()

    sources = service.get_sources_for_trust_tier("unknown-tier")

    assert sources == []