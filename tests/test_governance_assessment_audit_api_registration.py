from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def admin_headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
    }


def test_main_application_registers_audit_endpoint():
    paths = {route.path for route in app.routes}

    assert (
        "/api/v1/governance-assessments/audit-events"
        in paths
    )


def test_main_audit_endpoint_fails_closed_without_verifier():
    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_IDENTITY_VERIFIER_UNAVAILABLE"
    )

def test_main_audit_endpoint_rejects_forged_identity_headers():
    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_IDENTITY_VERIFIER_UNAVAILABLE"
    )
