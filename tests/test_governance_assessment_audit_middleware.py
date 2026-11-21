from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_middleware import (
    install_assessment_audit_middleware,
)
from backend.app.gagf.governance_assessment_auth import (
    AssessmentActorContext,
    require_assessment_actor,
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


def build_client(tmp_path, *, configure_verifier=True):
    app = FastAPI()

    if configure_verifier:
        # Test-only verifier. Never configure this in production.
        app.state.assessment_identity_verifier = (
            verify_test_identity
        )
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    install_assessment_audit_middleware(
        app=app,
        ledger=ledger,
    )

    @app.get(
        "/api/v1/governance-assessments",
        dependencies=[Depends(require_assessment_actor)],
    )
    def list_assessments(tenant_id: str):
        return {"tenant_id": tenant_id}

    return TestClient(app), ledger


def headers(
    *,
    tenant_id: str = "tenant-alpha",
    roles: str = "assessment:read",
):
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-001",
        "X-Actor-Roles": roles,
        "X-Request-ID": "request-001",
    }


def test_successful_request_is_audited(tmp_path):
    client, ledger = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == (
        "request-001"
    )

    events = ledger.list_events(
        tenant_id="tenant-alpha"
    )

    assert len(events) == 1
    assert events[0].actor_id == "actor-001"
    assert events[0].outcome == "allowed"
    assert events[0].status_code == 200


def test_missing_authentication_is_audited(tmp_path):
    client, ledger = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Request-ID": "request-002",
        },
    )

    assert response.status_code == 401

    with ledger._connect() as connection:
        event = connection.execute(
            """
            SELECT tenant_id, actor_id, actor_roles_json,
                   outcome, status_code, reason_code
            FROM assessment_audit_events
            WHERE request_id = ?
            """,
            ("request-002",),
        ).fetchone()

    assert event is not None
    assert event["tenant_id"] is None
    assert event["actor_id"] is None
    assert event["actor_roles_json"] == "[]"
    assert event["outcome"] == "denied"
    assert event["status_code"] == 401
    assert event["reason_code"] == (
        "ASSESSMENT_AUTH_REQUIRED"
    )


def test_forged_identity_headers_are_not_audit_attribution(tmp_path):
    client, ledger = build_client(
        tmp_path,
        configure_verifier=False,
    )

    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 503

    with ledger._connect() as connection:
        event = connection.execute(
            """
            SELECT tenant_id, actor_id, actor_roles_json,
                   outcome, status_code
            FROM assessment_audit_events
            WHERE request_id = ?
            """,
            ("request-001",),
        ).fetchone()

    assert event is not None
    assert event["tenant_id"] is None
    assert event["actor_id"] is None
    assert event["actor_roles_json"] == "[]"
    assert event["outcome"] == "denied"
    assert event["status_code"] == 503


def test_cross_tenant_request_is_audited(tmp_path):
    client, ledger = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403

    events = ledger.list_events(
        tenant_id="tenant-alpha"
    )

    assert len(events) == 1
    assert events[0].outcome == "denied"
    assert events[0].status_code == 403


def test_non_assessment_route_is_not_audited(tmp_path):
    app = FastAPI()
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    install_assessment_audit_middleware(
        app=app,
        ledger=ledger,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert ledger.list_events(
        tenant_id="tenant-alpha"
    ) == []


def test_middleware_registration_is_idempotent(tmp_path):
    app = FastAPI()
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    install_assessment_audit_middleware(
        app=app,
        ledger=ledger,
    )
    install_assessment_audit_middleware(
        app=app,
        ledger=ledger,
    )

    assert (
        app.state.governance_assessment_audit_middleware_installed
        is True
    )
    assert app.state.governance_assessment_audit_ledger is ledger
