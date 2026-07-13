from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_category_endpoint_returns_summary():
    response = client.get("/sources/categories")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["category_count"] >= 5
    assert isinstance(data["categories"], list)


def test_source_category_endpoint_includes_identity_category():
    response = client.get("/sources/categories")

    assert response.status_code == 200

    data = response.json()

    categories = {
        category["category"]: category
        for category in data["categories"]
    }

    assert "identity" in categories
    assert categories["identity"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in categories["identity"]["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems


def test_source_category_endpoint_includes_endpoint_security_category():
    response = client.get("/sources/categories")

    assert response.status_code == 200

    data = response.json()

    categories = {
        category["category"]: category
        for category in data["categories"]
    }

    assert "endpoint_security" in categories
    assert categories["endpoint_security"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in categories["endpoint_security"]["sources"]
    }

    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_category_endpoint_does_not_conflict_with_source_detail_route():
    response = client.get("/sources/categories")

    assert response.status_code == 200

    data = response.json()

    assert "categories" in data
    assert "source" not in data



