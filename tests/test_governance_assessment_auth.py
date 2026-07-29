from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_auth import (
    require_assessment_actor,
)


def build_client() -> TestClient:
    app = FastAPI()

    @app.get(
        "/assessments/{tenant_id}",
        dependencies=[Depends(require_assessment_actor)],
    )
    def read_assessment(tenant_id: str):
        return {"tenant_id": tenant_id}

    @app.get(
        "/assessments",
        dependencies=[Depends(require_assessment_actor)],
    )
    def list_assessments(tenant_id: str):
        return {"tenant_id": tenant_id}

    @app.post(
        "/assessments",
        dependencies=[Depends(require_assessment_actor)],
    )
    def create_assessment(payload: dict):
        return payload

    return TestClient(app)


def auth_headers(
    *,
    tenant_id: str = "tenant-alpha",
    roles: str = "assessment:read",
) -> dict[str, str]:
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-001",
        "X-Actor-Roles": roles,
    }


def test_missing_headers_returns_401():
    response = build_client().get(
        "/assessments/tenant-alpha"
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_AUTH_REQUIRED"
    )


def test_reader_can_access_matching_path_tenant():
    response = build_client().get(
        "/assessments/tenant-alpha",
        headers=auth_headers(),
    )

    assert response.status_code == 200


def test_path_tenant_mismatch_returns_403():
    response = build_client().get(
        "/assessments/tenant-beta",
        headers=auth_headers(),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_query_tenant_mismatch_returns_403():
    response = build_client().get(
        "/assessments",
        params={"tenant_id": "tenant-beta"},
        headers=auth_headers(),
    )

    assert response.status_code == 403


def test_body_tenant_mismatch_returns_403():
    response = build_client().post(
        "/assessments",
        json={"tenant_id": "tenant-beta"},
        headers=auth_headers(roles="assessment:execute"),
    )

    assert response.status_code == 403


def test_reader_cannot_execute_assessment():
    response = build_client().post(
        "/assessments",
        json={"tenant_id": "tenant-alpha"},
        headers=auth_headers(roles="assessment:read"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_ROLE_FORBIDDEN"
    )


def test_executor_can_execute_assessment():
    response = build_client().post(
        "/assessments",
        json={"tenant_id": "tenant-alpha"},
        headers=auth_headers(roles="assessment:execute"),
    )

    assert response.status_code == 200


def test_admin_can_read_and_execute():
    client = build_client()
    headers = auth_headers(roles="assessment:admin")

    read_response = client.get(
        "/assessments/tenant-alpha",
        headers=headers,
    )
    execute_response = client.post(
        "/assessments",
        json={"tenant_id": "tenant-alpha"},
        headers=headers,
    )

    assert read_response.status_code == 200
    assert execute_response.status_code == 200


def test_roles_are_case_normalized():
    response = build_client().get(
        "/assessments/tenant-alpha",
        headers=auth_headers(roles="ASSESSMENT:READ"),
    )

    assert response.status_code == 200


def test_comma_separated_roles_are_supported():
    response = build_client().post(
        "/assessments",
        json={"tenant_id": "tenant-alpha"},
        headers=auth_headers(
            roles="assessment:read, assessment:execute"
        ),
    )

    assert response.status_code == 200
