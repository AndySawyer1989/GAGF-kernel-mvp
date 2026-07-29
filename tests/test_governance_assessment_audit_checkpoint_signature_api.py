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
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        checkpoint_signing_key_id="key-001",
        checkpoint_signing_secret=SIGNING_SECRET,
    )
    app.router.routes.extend(router.routes)

    return TestClient(app), signed_store


def headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
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

    client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["key_id"] == (
        "key-001"
    )


def test_reader_cannot_list_signed_checkpoints(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-alpha"},
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "actor-reader",
            "X-Actor-Roles": "assessment:read",
        },
    )

    assert response.status_code == 403


def test_cross_tenant_signed_list_is_denied(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-beta"},
        headers=headers(),
    )

    assert response.status_code == 403


def test_missing_signed_store_returns_503(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    app.router.routes.extend(router.routes)
    client = TestClient(app)

    response = client.get(
        "/api/v1/governance-assessments/audit-checkpoints/signed",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 503
