from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def headers(
    *,
    tenant_id: str = "tenant-alpha",
    roles: str = "assessment:read",
) -> dict[str, str]:
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-001",
        "X-Actor-Roles": roles,
    }


def test_main_assessment_api_requires_authentication():
    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code == 401


def test_main_assessment_list_allows_matching_reader():
    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200


def test_main_assessment_list_rejects_cross_tenant_request():
    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_main_assessment_execute_rejects_reader_role():
    response = client.post(
        "/api/v1/governance-assessments/execute",
        json={"tenant_id": "tenant-alpha"},
        headers=headers(roles="assessment:read"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_ROLE_FORBIDDEN"
    )
