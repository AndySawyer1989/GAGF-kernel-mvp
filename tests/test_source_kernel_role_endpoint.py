from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_kernel_role_endpoint_returns_summary():
    response = client.get("/sources/kernel-roles")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["kernel_role_count"] >= 5
    assert isinstance(data["kernel_roles"], list)


def test_source_kernel_role_endpoint_includes_identity_evidence_sources():
    response = client.get("/sources/kernel-roles")

    assert response.status_code == 200

    data = response.json()

    kernel_roles = {
        kernel_role["kernel_role"]: kernel_role
        for kernel_role in data["kernel_roles"]
    }

    assert "identity_evidence" in kernel_roles
    assert kernel_roles["identity_evidence"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in kernel_roles["identity_evidence"]["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems


def test_source_kernel_role_endpoint_includes_threat_evidence_sources():
    response = client.get("/sources/kernel-roles")

    assert response.status_code == 200

    data = response.json()

    kernel_roles = {
        kernel_role["kernel_role"]: kernel_role
        for kernel_role in data["kernel_roles"]
    }

    assert "threat_evidence" in kernel_roles
    assert kernel_roles["threat_evidence"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in kernel_roles["threat_evidence"]["sources"]
    }

    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_kernel_role_endpoint_includes_single_source_roles():
    response = client.get("/sources/kernel-roles")

    assert response.status_code == 200

    data = response.json()

    kernel_roles = {
        kernel_role["kernel_role"]: kernel_role
        for kernel_role in data["kernel_roles"]
    }

    assert kernel_roles["delivery_evidence"]["source_count"] == 1
    assert kernel_roles["delivery_evidence"]["sources"][0]["source_system"] == "github"

    assert kernel_roles["workflow_evidence"]["source_count"] == 1
    assert kernel_roles["workflow_evidence"]["sources"][0]["source_system"] == "jira"

    assert kernel_roles["incident_evidence"]["source_count"] == 1
    assert kernel_roles["incident_evidence"]["sources"][0]["source_system"] == "servicenow"


def test_source_kernel_role_endpoint_does_not_conflict_with_source_detail_route():
    response = client.get("/sources/kernel-roles")

    assert response.status_code == 200

    data = response.json()

    assert "kernel_roles" in data
    assert "source" not in data


