from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_category_detail_endpoint_returns_endpoint_security_sources():
    response = client.get("/sources/categories/endpoint_security")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["category"] == "endpoint_security"
    assert data["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in data["sources"]
    }

    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_category_detail_endpoint_returns_identity_sources():
    response = client.get("/sources/categories/identity")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["category"] == "identity"
    assert data["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in data["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems


def test_source_category_detail_endpoint_returns_devops_sources():
    response = client.get("/sources/categories/devops")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["category"] == "devops"
    assert data["source_count"] == 1
    assert data["sources"][0]["source_system"] == "github"


def test_source_category_detail_endpoint_returns_failure_for_unknown_category():
    response = client.get("/sources/categories/unknown-category")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["error"] == "category_not_found"
    assert data["category"] == "unknown-category"
    assert data["source_count"] == 0
    assert data["sources"] == []


def test_source_category_detail_endpoint_does_not_conflict_with_category_summary_route():
    response = client.get("/sources/categories")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "categories" in data
    assert "source_count" not in data