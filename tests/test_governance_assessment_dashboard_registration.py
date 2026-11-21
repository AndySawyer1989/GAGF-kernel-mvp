from fastapi import FastAPI, HTTPException
from backend.app.gagf.governance_assessment_auth import (
    AssessmentActorContext,
)
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_api_registration import (
    register_governance_assessment_api,
)


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

def headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
    }


def signing_environment():
    return {
        "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID": "tenant-alpha",
        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID": "key-001",
        "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE": (
            "env://GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET"
        ),
        "GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET": (
            "private-signing-secret"
        ),
    }


def test_dashboard_is_registered_in_unsigned_environment(tmp_path):
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment={},
    )

    response = TestClient(app).get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["signing_key_count"] == 0
    assert response.json()["active_signing_key_id"] is None


def test_dashboard_is_registered_with_signing_enabled(tmp_path):
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment=signing_environment(),
    )

    response = TestClient(app).get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["signing_key_count"] == 1
    assert response.json()["active_signing_key_id"] == "key-001"


def test_dashboard_service_is_exposed_on_app_state(tmp_path):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment={},
    )

    assert (
        app.state.governance_assessment_dashboard_service
        is not None
    )


def test_dashboard_registration_remains_idempotent(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"

    first = register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment={},
    )
    second = register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment={},
    )

    assert first is second
