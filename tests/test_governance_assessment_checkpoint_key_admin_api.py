from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_checkpoint_durable_key_service import (
    AssessmentCheckpointDurableKeyService,
)
from backend.app.gagf.governance_assessment_checkpoint_key_admin_api import (
    create_assessment_checkpoint_key_admin_router,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    InMemoryAssessmentCheckpointSecretResolver,
)


def headers(
    *,
    tenant_id="tenant-alpha",
    roles="assessment:admin",
):
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": roles,
    }


def build_client(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    resolver = InMemoryAssessmentCheckpointSecretResolver()
    resolver.register_secret(
        secret_reference="secret://key-001",
        secret=b"secret-001",
    )
    resolver.register_secret(
        secret_reference="secret://key-002",
        secret=b"secret-002",
    )

    service = AssessmentCheckpointDurableKeyService(
        metadata_store=store,
        secret_resolver=resolver,
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret_reference="secret://key-001",
        make_active=True,
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="secret://key-002",
        make_active=False,
    )

    app = FastAPI()
    app.include_router(
        create_assessment_checkpoint_key_admin_router(
            metadata_store=store,
            key_service=service,
        )
    )

    return TestClient(app), store


def test_admin_can_list_tenant_keys(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/checkpoint-signing-keys",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_list_response_does_not_include_secret_material(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/checkpoint-signing-keys",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert "secret-001" not in response.text
    assert "secret-002" not in response.text


def test_admin_can_get_active_key(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/active"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["key_id"] == "key-001"


def test_admin_can_activate_registered_key(tmp_path):
    client, store = build_client(tmp_path)

    response = client.post(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/key-002/activate"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["key_id"] == "key-002"
    assert store.get_active_key(
        tenant_id="tenant-alpha"
    ).key_id == "key-002"


def test_non_admin_cannot_manage_keys(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/checkpoint-signing-keys",
        params={"tenant_id": "tenant-alpha"},
        headers=headers(roles="assessment:operator"),
    )

    assert response.status_code == 403


def test_cross_tenant_access_is_rejected(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/api/v1/governance-assessments/checkpoint-signing-keys",
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403


def test_unknown_key_returns_not_found(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/missing/activate"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 404
