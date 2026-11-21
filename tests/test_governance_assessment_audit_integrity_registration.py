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
