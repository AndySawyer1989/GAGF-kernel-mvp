import sqlite3

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
    build_assessment_audit_event,
)
from backend.app.gagf.governance_assessment_audit_api import (
    create_governance_assessment_audit_router,
)


def build_client(tmp_path):
    database_path = tmp_path / "audit.sqlite3"
    ledger = AssessmentAuditLedger(database_path)
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger
    )
    app.router.routes.extend(router.routes)

    return TestClient(app), ledger, database_path


def headers(
    *,
    tenant_id: str = "tenant-alpha",
    roles: str = "assessment:admin",
):
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": roles,
    }


def append_event(
    ledger: AssessmentAuditLedger,
    *,
    tenant_id: str = "tenant-alpha",
    request_id: str = "request-001",
):
    return ledger.append(
        build_assessment_audit_event(
            request_id=request_id,
            tenant_id=tenant_id,
            actor_id="actor-001",
            actor_roles=("assessment:read",),
            method="GET",
            route="/api/v1/governance-assessments",
            outcome="allowed",
            status_code=200,
        )
    )


def test_admin_can_verify_valid_audit_chain(tmp_path):
    client, ledger, _ = build_client(tmp_path)
    append_event(ledger, request_id="request-001")
    append_event(ledger, request_id="request-002")

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "tenant-alpha",
        "valid": True,
        "checked_count": 2,
        "failure_index": None,
        "failure_event_id": None,
        "reason_code": None,
    }


def test_empty_tenant_chain_is_valid(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["checked_count"] == 0


def test_missing_authentication_returns_401(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code == 401


def test_reader_cannot_verify_audit_integrity(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(roles="assessment:read"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_AUDIT_ROLE_FORBIDDEN"
    )


def test_cross_tenant_verification_is_denied(tmp_path):
    client, ledger, _ = build_client(tmp_path)
    append_event(ledger, tenant_id="tenant-beta")

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_tampered_event_is_reported(tmp_path):
    client, ledger, database_path = build_client(tmp_path)
    event = append_event(ledger)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE assessment_audit_events
            SET status_code = 403
            WHERE event_id = ?
            """,
            (event.event_id,),
        )
        connection.commit()

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert payload["checked_count"] == 0
    assert payload["failure_index"] == 0
    assert payload["failure_event_id"] == event.event_id
    assert payload["reason_code"] == (
        "AUDIT_EVENT_HASH_MISMATCH"
    )


def test_other_tenant_tampering_does_not_affect_result(
    tmp_path,
):
    client, ledger, database_path = build_client(tmp_path)
    alpha = append_event(
        ledger,
        tenant_id="tenant-alpha",
        request_id="alpha-request",
    )
    beta = append_event(
        ledger,
        tenant_id="tenant-beta",
        request_id="beta-request",
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE assessment_audit_events
            SET status_code = 403
            WHERE event_id = ?
            """,
            (beta.event_id,),
        )
        connection.commit()

    response = client.get(
        "/api/v1/governance-assessments/audit-integrity",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["checked_count"] == 1
    assert alpha.tenant_id == "tenant-alpha"
