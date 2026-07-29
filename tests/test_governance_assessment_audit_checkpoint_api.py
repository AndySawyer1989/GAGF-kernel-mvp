from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
    build_assessment_audit_event,
)
from backend.app.gagf.governance_assessment_audit_api import (
    create_governance_assessment_audit_router,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
)


def build_client(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=store,
    )
    app.router.routes.extend(router.routes)

    return TestClient(app), ledger, store


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


def append_event(ledger):
    ledger.append(
        build_assessment_audit_event(
            request_id="request-001",
            tenant_id="tenant-alpha",
            actor_id="actor-001",
            actor_roles=("assessment:read",),
            method="GET",
            route="/api/v1/governance-assessments",
            outcome="allowed",
            status_code=200,
        )
    )


def test_admin_can_create_checkpoint(tmp_path):
    client, ledger, store = build_client(tmp_path)
    append_event(ledger)

    response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["tenant_id"] == "tenant-alpha"
    assert payload["valid"] is True
    assert payload["checked_count"] == 1
    assert len(payload["chain_head_hash"]) == 64
    assert len(store.list_checkpoints(
        tenant_id="tenant-alpha"
    )) == 1


def test_admin_can_list_checkpoints(tmp_path):
    client, _, _ = build_client(tmp_path)

    create_response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )
    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["tenant_id"] == "tenant-alpha"


def test_reader_cannot_create_checkpoint(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(roles="assessment:read"),
    )

    assert response.status_code == 403


def test_cross_tenant_checkpoint_creation_is_denied(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_checkpoint_lists_are_tenant_isolated(tmp_path):
    client, ledger, store = build_client(tmp_path)

    client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert len(store.list_checkpoints(
        tenant_id="tenant-alpha"
    )) == 1
    assert store.list_checkpoints(
        tenant_id="tenant-beta"
    ) == []


def test_missing_checkpoint_store_returns_503(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger
    )
    app.router.routes.extend(router.routes)
    client = TestClient(app)

    response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_CHECKPOINT_STORE_UNAVAILABLE"
    )
