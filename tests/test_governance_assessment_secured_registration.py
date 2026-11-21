from backend.app.gagf.governance_assessment_auth import AssessmentActorContext
from fastapi import HTTPException
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


async def verify_test_identity(request):
    tenant_id = request.headers.get("X-Tenant-ID")
    actor_id = request.headers.get("X-Actor-ID")
    roles_header = request.headers.get("X-Actor-Roles")

    if not tenant_id or not actor_id or not roles_header:
        raise HTTPException(
            status_code=401,
            detail={"code": "ASSESSMENT_AUTH_REQUIRED"},
        )

    return AssessmentActorContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        roles=tuple(
            role.strip()
            for role in roles_header.split(",")
            if role.strip()
        ),
    )


def configure_test_identity(app):
    app.state.assessment_identity_verifier = verify_test_identity

@pytest.fixture(autouse=True)
def configure_assessment_test_identity():
    previous_verifier = getattr(
        app.state,
        "assessment_identity_verifier",
        None,
    )
    had_previous_verifier = hasattr(
        app.state,
        "assessment_identity_verifier",
    )

    app.state.assessment_identity_verifier = verify_test_identity

    yield

    if had_previous_verifier:
        app.state.assessment_identity_verifier = previous_verifier
    elif hasattr(app.state, "assessment_identity_verifier"):
        delattr(app.state, "assessment_identity_verifier")

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
