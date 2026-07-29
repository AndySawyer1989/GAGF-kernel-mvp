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
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger
    )
    app.router.routes.extend(router.routes)
    return TestClient(app), ledger


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
    ledger,
    *,
    tenant_id: str = "tenant-alpha",
    request_id: str = "request-001",
):
    ledger.append(
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


def test_admin_can_list_tenant_audit_events(tmp_path):
    client, ledger = build_client(tmp_path)
    append_event(ledger)

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-alpha"
    assert payload["count"] == 1
    assert payload["items"][0]["request_id"] == (
        "request-001"
    )


def test_missing_authentication_returns_401(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code == 401


def test_reader_role_cannot_list_audit_events(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(roles="assessment:read"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_AUDIT_ROLE_FORBIDDEN"
    )


def test_cross_tenant_audit_request_is_denied(tmp_path):
    client, ledger = build_client(tmp_path)
    append_event(
        ledger,
        tenant_id="tenant-beta",
    )

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_tenant_results_are_isolated(tmp_path):
    client, ledger = build_client(tmp_path)
    append_event(
        ledger,
        tenant_id="tenant-alpha",
        request_id="alpha-request",
    )
    append_event(
        ledger,
        tenant_id="tenant-beta",
        request_id="beta-request",
    )

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    request_ids = {
        item["request_id"]
        for item in response.json()["items"]
    }
    assert request_ids == {"alpha-request"}


def test_limit_is_applied(tmp_path):
    client, ledger = build_client(tmp_path)

    for index in range(4):
        append_event(
            ledger,
            request_id=f"request-{index}",
        )

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={
            "tenant_id": "tenant-alpha",
            "limit": 2,
        },
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["limit"] == 2


def test_limit_above_maximum_returns_422(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-events",
        params={
            "tenant_id": "tenant-alpha",
            "limit": 501,
        },
        headers=headers(),
    )

    assert response.status_code == 422
