from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_trust_tier_detail_endpoint_returns_security_sources():
    response = client.get("/sources/trust-tiers/security")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["trust_tier"] == "security"
    assert data["source_count"] == 4

    source_systems = {
        source["source_system"]
        for source in data["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_trust_tier_detail_endpoint_returns_operational_sources():
    response = client.get("/sources/trust-tiers/operational")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["trust_tier"] == "operational"
    assert data["source_count"] == 3

    source_systems = {
        source["source_system"]
        for source in data["sources"]
    }

    assert "github" in source_systems
    assert "jira" in source_systems
    assert "servicenow" in source_systems


def test_source_trust_tier_detail_endpoint_returns_failure_for_unknown_trust_tier():
    response = client.get("/sources/trust-tiers/unknown-tier")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["error"] == "trust_tier_not_found"
    assert data["trust_tier"] == "unknown-tier"
    assert data["source_count"] == 0
    assert data["sources"] == []


def test_source_trust_tier_detail_endpoint_does_not_conflict_with_trust_tier_summary_route():
    response = client.get("/sources/trust-tiers")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "trust_tiers" in data
    assert "source_count" not in data



