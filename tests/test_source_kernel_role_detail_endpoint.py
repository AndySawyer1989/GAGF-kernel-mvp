from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_kernel_role_detail_endpoint_returns_threat_evidence_sources():
    response = client.get("/sources/kernel-roles/threat_evidence")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["kernel_role"] == "threat_evidence"
    assert data["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in data["sources"]
    }

    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_kernel_role_detail_endpoint_returns_identity_evidence_sources():
    response = client.get("/sources/kernel-roles/identity_evidence")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["kernel_role"] == "identity_evidence"
    assert data["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in data["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems


def test_source_kernel_role_detail_endpoint_returns_delivery_evidence_source():
    response = client.get("/sources/kernel-roles/delivery_evidence")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["kernel_role"] == "delivery_evidence"
    assert data["source_count"] == 1
    assert data["sources"][0]["source_system"] == "github"


def test_source_kernel_role_detail_endpoint_returns_failure_for_unknown_kernel_role():
    response = client.get("/sources/kernel-roles/unknown-role")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["error"] == "kernel_role_not_found"
    assert data["kernel_role"] == "unknown-role"
    assert data["source_count"] == 0
    assert data["sources"] == []


def test_source_kernel_role_detail_endpoint_does_not_conflict_with_kernel_role_summary_route():
    response = client.get("/sources/kernel-roles")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "kernel_roles" in data
    assert "source_count" not in data


