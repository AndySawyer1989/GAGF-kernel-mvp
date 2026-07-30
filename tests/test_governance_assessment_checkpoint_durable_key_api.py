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
from backend.app.gagf.governance_assessment_checkpoint_durable_key_service import (
    AssessmentCheckpointDurableKeyService,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    InMemoryAssessmentCheckpointSecretResolver,
)


def headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
    }


def build_components(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    signed_store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )
    metadata_store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    resolver = InMemoryAssessmentCheckpointSecretResolver()
    resolver.register_secret(
        secret_reference="secret://tenant-alpha/key-001",
        secret=b"secret-001",
    )
    key_service = AssessmentCheckpointDurableKeyService(
        metadata_store=metadata_store,
        secret_resolver=resolver,
    )
    key_service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret_reference="secret://tenant-alpha/key-001",
        make_active=True,
    )

    return (
        ledger,
        checkpoint_store,
        signed_store,
        metadata_store,
        resolver,
        key_service,
    )


def build_client(tmp_path):
    components = build_components(tmp_path)
    (
        ledger,
        checkpoint_store,
        signed_store,
        _,
        _,
        key_service,
    ) = components

    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        durable_checkpoint_key_service=key_service,
    )
    app.router.routes.extend(router.routes)

    return TestClient(app), components


def test_durable_key_service_signs_checkpoint(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["signed"] is True
    assert payload["key_id"] == "key-001"


def test_signed_checkpoint_verifies_through_api(tmp_path):
    client, _ = build_client(tmp_path)

    create_response = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )
    assert create_response.status_code == 201

    response = client.get(
        (
            "/api/v1/governance-assessments/"
            "audit-checkpoints/signed/verification"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["valid_count"] == 1
    assert response.json()["invalid_count"] == 0


def test_signing_survives_service_restart(tmp_path):
    client, components = build_client(tmp_path)
    (
        ledger,
        checkpoint_store,
        signed_store,
        _,
        resolver,
        _,
    ) = components

    restarted_metadata_store = (
        AssessmentCheckpointSigningKeyMetadataStore(
            tmp_path / "keys.sqlite3"
        )
    )
    restarted_key_service = AssessmentCheckpointDurableKeyService(
        metadata_store=restarted_metadata_store,
        secret_resolver=resolver,
    )

    restarted_app = FastAPI()
    restarted_router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        durable_checkpoint_key_service=restarted_key_service,
    )
    restarted_app.router.routes.extend(
        restarted_router.routes
    )

    response = TestClient(restarted_app).post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 201
    assert response.json()["key_id"] == "key-001"


def test_missing_resolved_secret_returns_503(tmp_path):
    (
        ledger,
        checkpoint_store,
        signed_store,
        metadata_store,
        _,
        _,
    ) = build_components(tmp_path)

    empty_resolver = InMemoryAssessmentCheckpointSecretResolver()
    key_service = AssessmentCheckpointDurableKeyService(
        metadata_store=metadata_store,
        secret_resolver=empty_resolver,
    )

    app = FastAPI()
    router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        durable_checkpoint_key_service=key_service,
    )
    app.router.routes.extend(router.routes)

    response = TestClient(app).post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 503


def test_rotation_persists_across_restart(tmp_path):
    client, components = build_client(tmp_path)
    (
        ledger,
        checkpoint_store,
        signed_store,
        metadata_store,
        resolver,
        key_service,
    ) = components

    first = client.post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    resolver.register_secret(
        secret_reference="secret://tenant-alpha/key-002",
        secret=b"secret-002",
    )
    key_service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="secret://tenant-alpha/key-002",
        make_active=True,
    )

    restarted_service = AssessmentCheckpointDurableKeyService(
        metadata_store=(
            AssessmentCheckpointSigningKeyMetadataStore(
                tmp_path / "keys.sqlite3"
            )
        ),
        secret_resolver=resolver,
    )
    restarted_app = FastAPI()
    restarted_router = create_governance_assessment_audit_router(
        ledger=ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        durable_checkpoint_key_service=restarted_service,
    )
    restarted_app.router.routes.extend(
        restarted_router.routes
    )

    second = TestClient(restarted_app).post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["key_id"] == "key-001"
    assert second.json()["key_id"] == "key-002"
