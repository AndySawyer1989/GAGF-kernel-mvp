from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_coverage_endpoint_returns_summary():
    response = client.get("/sources/coverage")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["total_sources"] == 7
    assert data["enabled_sources"] == 7
    assert data["disabled_sources"] == 0
    assert data["category_count"] >= 5
    assert data["trust_tier_count"] >= 2
    assert data["kernel_role_count"] >= 5


def test_source_coverage_endpoint_includes_health_counts():
    response = client.get("/sources/coverage")

    assert response.status_code == 200

    data = response.json()

    assert data["health_counts"]["available"] == 7
    assert data["health_counts"]["disabled"] == 0
    assert data["health_counts"]["misconfigured"] == 0


def test_source_coverage_endpoint_includes_grouped_views():
    response = client.get("/sources/coverage")

    assert response.status_code == 200

    data = response.json()

    assert "categories" in data
    assert "trust_tiers" in data
    assert "kernel_roles" in data
    assert isinstance(data["categories"], list)
    assert isinstance(data["trust_tiers"], list)
    assert isinstance(data["kernel_roles"], list)


def test_source_coverage_endpoint_reports_no_gaps_for_complete_registry():
    response = client.get("/sources/coverage")

    assert response.status_code == 200

    data = response.json()

    assert data["coverage_gaps"] == []


def test_source_coverage_endpoint_does_not_conflict_with_source_detail_route():
    response = client.get("/sources/coverage")

    assert response.status_code == 200

    data = response.json()

    assert "total_sources" in data
    assert "source" not in data






