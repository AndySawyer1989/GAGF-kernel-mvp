from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def admin_headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
    }


def test_main_application_registers_integrity_endpoint():
    paths = {route.path for route in app.routes}

    assert (
        "/api/v1/governance-assessments/audit-integrity"
        in paths
    )


def test_main_integrity_endpoint_requires_authentication():
    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code == 401


def test_main_integrity_endpoint_allows_admin():
    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-alpha"
    assert isinstance(payload["valid"], bool)
    assert isinstance(payload["checked_count"], int)
