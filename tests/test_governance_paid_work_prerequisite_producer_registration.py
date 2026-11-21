from __future__ import annotations

from fastapi import FastAPI, HTTPException
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_api_registration import (
    register_governance_assessment_api,
)
from backend.app.gagf.governance_paid_work_prerequisite_persistence_bridge import (
    GovernancePaidWorkPrerequisitePersistenceBridge,
)
from backend.app.gagf.governance_paid_work_prerequisite_producer_service import (
    GovernancePaidWorkPrerequisiteProducerService,
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

def test_registration_adds_prerequisite_producer_routes(tmp_path):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    paths = {
        route.path
        for route in app.router.routes
    }

    assert (
        "/api/v1/governance-paid-work-prerequisites/"
        "authorization-package"
        in paths
    )
    assert (
        "/api/v1/governance-paid-work-prerequisites/"
        "contract-execution-event"
        in paths
    )
    assert (
        "/api/v1/governance-paid-work-prerequisites/"
        "payment-confirmation-event"
        in paths
    )


def test_registration_reuses_same_prerequisite_store(tmp_path):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    bridge = (
        app.state
        .governance_paid_work_prerequisite_persistence_bridge
    )
    producer = (
        app.state
        .governance_paid_work_prerequisite_producer_service
    )
    store = (
        app.state
        .governance_paid_work_prerequisite_store
    )
    resolver = (
        app.state
        .governance_paid_work_prerequisite_resolver
    )

    assert isinstance(
        bridge,
        GovernancePaidWorkPrerequisitePersistenceBridge,
    )
    assert isinstance(
        producer,
        GovernancePaidWorkPrerequisiteProducerService,
    )

    assert bridge.prerequisite_store is store
    assert producer.persistence_bridge is bridge
    assert resolver.prerequisite_store is store


def test_registered_producer_route_requires_actor(tmp_path):
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/governance-paid-work-prerequisites/"
        "authorization-package",
        json={
            "tenant_id": "tenant-alpha",
            "client_id": "client-acme",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
            "evidence": {},
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_AUTH_REQUIRED"
    )


def test_registered_producer_route_requires_admin(tmp_path):
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/governance-paid-work-prerequisites/"
        "authorization-package",
        json={
            "tenant_id": "tenant-alpha",
            "client_id": "client-acme",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
            "evidence": {},
        },
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "operator-001",
            "X-Actor-Roles": "assessment:execute",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_ADMIN_REQUIRED"
    )
