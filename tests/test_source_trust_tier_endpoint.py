from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_trust_tier_endpoint_returns_summary():
    response = client.get("/sources/trust-tiers")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["trust_tier_count"] >= 2
    assert isinstance(data["trust_tiers"], list)


def test_source_trust_tier_endpoint_includes_security_sources():
    response = client.get("/sources/trust-tiers")

    assert response.status_code == 200

    data = response.json()

    trust_tiers = {
        trust_tier["trust_tier"]: trust_tier
        for trust_tier in data["trust_tiers"]
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


def test_source_trust_tier_endpoint_includes_operational_sources():
    response = client.get("/sources/trust-tiers")

    assert response.status_code == 200

    data = response.json()

    trust_tiers = {
        trust_tier["trust_tier"]: trust_tier
        for trust_tier in data["trust_tiers"]
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


def test_source_trust_tier_endpoint_does_not_conflict_with_source_detail_route():
    response = client.get("/sources/trust-tiers")

    assert response.status_code == 200

    data = response.json()

    assert "trust_tiers" in data
    assert "source" not in data





