from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_health_endpoint_returns_summary():
    response = client.get("/sources/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["sources_checked"] >= 7
    assert data["healthy_sources"] >= 7
    assert data["unhealthy_sources"] == 0
    assert isinstance(data["sources"], list)


def test_source_health_endpoint_includes_defender_and_sentinelone():
    response = client.get("/sources/health")

    assert response.status_code == 200

    data = response.json()

    sources_by_system = {
        source["source_system"]: source for source in data["sources"]
    }

    assert sources_by_system["defender"]["health"] == "available"
    assert sources_by_system["sentinelone"]["health"] == "available"
    assert sources_by_system["defender"]["ingestion_endpoint"] == "/ingest/defender"
    assert sources_by_system["sentinelone"]["ingestion_endpoint"] == "/ingest/sentinelone"


def test_source_health_endpoint_does_not_conflict_with_source_detail_route():
    response = client.get("/sources/health")

    assert response.status_code == 200

    data = response.json()

    assert "sources_checked" in data
    assert "source" not in data

