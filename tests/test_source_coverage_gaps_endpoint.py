from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_coverage_gaps_endpoint_returns_gap_summary():
    response = client.get("/sources/coverage/gaps")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["gap_count"] == 0
    assert data["gaps"] == []


def test_source_coverage_gaps_endpoint_does_not_return_full_coverage_payload():
    response = client.get("/sources/coverage/gaps")

    assert response.status_code == 200

    data = response.json()

    assert "gap_count" in data
    assert "gaps" in data
    assert "total_sources" not in data
    assert "categories" not in data
    assert "trust_tiers" not in data
    assert "kernel_roles" not in data


def test_source_coverage_gaps_endpoint_does_not_conflict_with_coverage_summary_route():
    response = client.get("/sources/coverage")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "total_sources" in data
    assert "coverage_gaps" in data

