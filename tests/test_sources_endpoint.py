from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_sources_endpoint_returns_registered_sources():
    response = client.get("/sources")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "sources" in data
    assert isinstance(data["sources"], list)

    source_systems = {source["source_system"] for source in data["sources"]}

    assert "defender" in source_systems
    assert "sentinelone" in source_systems
    assert "okta" in source_systems
    assert "entra" in source_systems


def test_sources_endpoint_includes_required_metadata_fields():
    response = client.get("/sources")

    assert response.status_code == 200

    data = response.json()

    for source in data["sources"]:
        assert "source_system" in source
        assert "display_name" in source
        assert "category" in source
        assert "ingestion_endpoint" in source
        assert "trust_tier" in source
        assert "kernel_role" in source
        assert "enabled" in source
