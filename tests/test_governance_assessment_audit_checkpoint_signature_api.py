from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_api import (
    create_governance_assessment_audit_router,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature import (
    verify_assessment_audit_checkpoint_signature,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_registry import (
    AssessmentCheckpointSigningKeyRegistry,
)


SIGNING_SECRET = b"test-signing-secret"


def build_client(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    signed_store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=SIGNING_SECRET,
        make_active=True,
    )

    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        checkpoint_key_registry=registry,
    )
    app.router.routes.extend(router.routes)

    return TestClient(app), signed_store


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


def test_checkpoint_creation_returns_signed_envelope(tmp_path):
    client, signed_store = build_client(tmp_path)

    response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["signed"] is True
    assert payload["key_id"] == "key-001"
    assert len(payload["signature"]) == 64
    assert payload["checkpoint"]["tenant_id"] == (
        "tenant-alpha"
    )

    stored = signed_store.list_signed_checkpoints(
        tenant_id="tenant-alpha"
    )

    assert len(stored) == 1
    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=stored[0],
        secret=SIGNING_SECRET,
    ) is True


def test_admin_can_list_signed_checkpoints(tmp_path):
    client, _ = build_client(tmp_path)

    create_response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )
    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-alpha"
    assert payload["count"] == 1
    assert payload["items"][0]["key_id"] == "key-001"


def test_reader_cannot_list_signed_checkpoints(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(roles="assessment:read"),
    )

    assert response.status_code == 403


def test_cross_tenant_signed_list_is_denied(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403


def test_missing_signed_store_returns_503(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=SIGNING_SECRET,
        make_active=True,
    )

    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        checkpoint_key_registry=registry,
    )
    app.router.routes.extend(router.routes)
    client = TestClient(app)

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_SIGNED_CHECKPOINT_STORE_UNAVAILABLE"
    )
