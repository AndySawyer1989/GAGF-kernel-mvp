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
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_registry import (
    AssessmentCheckpointSigningKeyRegistry,
)


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
        secret=b"secret-001",
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

    return TestClient(app), registry, signed_store


def headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
    }


def create_checkpoint(client):
    return client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )


def test_active_registry_key_signs_checkpoint(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = create_checkpoint(client)

    assert response.status_code == 201
    assert response.json()["signed"] is True
    assert response.json()["key_id"] == "key-001"


def test_rotation_signs_new_checkpoint_with_new_key(tmp_path):
    client, registry, _ = build_client(tmp_path)

    first = create_checkpoint(client)
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret=b"secret-002",
        make_active=True,
    )
    second = create_checkpoint(client)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["key_id"] == "key-001"
    assert second.json()["key_id"] == "key-002"


def test_historical_checkpoint_verifies_after_rotation(tmp_path):
    client, registry, _ = build_client(tmp_path)

    create_checkpoint(client)
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret=b"secret-002",
        make_active=True,
    )
    create_checkpoint(client)

    response = client.get(
        (
            "/api/v1/governance-assessments/"
            "audit-checkpoints/signed/verification"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["valid_count"] == 2
    assert payload["invalid_count"] == 0
    assert {
        item["key_id"] for item in payload["items"]
    } == {"key-001", "key-002"}


def test_missing_active_key_returns_503(tmp_path):
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
    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        checkpoint_key_registry=registry,
    )
    app.router.routes.extend(router.routes)

    response = TestClient(app).post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_ACTIVE_SIGNING_KEY_UNAVAILABLE"
    )


def test_verification_endpoint_is_tenant_bound(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments/"
            "audit-checkpoints/signed/verification"
        ),
        params={"tenant_id": "tenant-beta"},
        headers=headers(),
    )

    assert response.status_code == 403


def test_reader_cannot_verify_signed_checkpoints(tmp_path):
    client, _, _ = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments/"
            "audit-checkpoints/signed/verification"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "actor-reader",
            "X-Actor-Roles": "assessment:read",
        },
    )

    assert response.status_code == 403
