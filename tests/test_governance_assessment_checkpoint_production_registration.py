import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_api_registration import (
    AssessmentApiRegistrationError,
    register_governance_assessment_api,
)


def admin_headers():
    return {
        "X-Tenant-ID": "tenant-alpha",
        "X-Actor-ID": "actor-admin",
        "X-Actor-Roles": "assessment:admin",
    }


def signing_environment():
    return {
        "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID": (
            "tenant-alpha"
        ),
        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID": "key-001",
        "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE": (
            "env://GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET"
        ),
        "GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET": (
            "private-signing-secret"
        ),
    }


def test_registration_without_configuration_starts_unsigned(
    tmp_path,
):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment={},
    )

    response = TestClient(app).post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 201
    assert response.json()["signed"] is False
    assert (
        app.state.governance_assessment_checkpoint_key_service
        is None
    )


def test_configured_registration_signs_checkpoint(tmp_path):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment=signing_environment(),
    )

    response = TestClient(app).post(
        "/api/v1/governance-assessments/audit-checkpoints",
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["signed"] is True
    assert payload["key_id"] == "key-001"
    assert payload["checkpoint"]["tenant_id"] == (
        "tenant-alpha"
    )


def test_registration_persists_key_metadata(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment=signing_environment(),
    )

    metadata_path = (
        tmp_path
        / "governance_assessment_checkpoint_keys.sqlite3"
    )

    assert metadata_path.exists()

    with sqlite3.connect(metadata_path) as connection:
        row = connection.execute(
            """
            SELECT tenant_id, key_id, secret_reference, active
            FROM assessment_checkpoint_signing_keys
            """
        ).fetchone()

    assert row == (
        "tenant-alpha",
        "key-001",
        "env://GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET",
        1,
    )


def test_metadata_database_does_not_store_secret(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment=signing_environment(),
    )

    metadata_path = (
        tmp_path
        / "governance_assessment_checkpoint_keys.sqlite3"
    )
    database_bytes = metadata_path.read_bytes()

    assert b"private-signing-secret" not in database_bytes


def test_partial_signing_configuration_rejects_registration(
    tmp_path,
):
    environment = signing_environment()
    del environment[
        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID"
    ]
    app = FastAPI()

    with pytest.raises(
        AssessmentApiRegistrationError,
        match="signing configuration is invalid",
    ):
        register_governance_assessment_api(
            app=app,
            database_path=tmp_path / "assessment.sqlite3",
            environment=environment,
        )


def test_missing_secret_rejects_configured_registration(
    tmp_path,
):
    environment = signing_environment()
    del environment[
        "GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET"
    ]
    app = FastAPI()

    with pytest.raises(
        AssessmentApiRegistrationError,
        match="signing configuration is invalid",
    ):
        register_governance_assessment_api(
            app=app,
            database_path=tmp_path / "assessment.sqlite3",
            environment=environment,
        )


def test_registration_exposes_checkpoint_stores_on_state(
    tmp_path,
):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment={},
    )

    assert (
        app.state.governance_assessment_checkpoint_store
        is not None
    )
    assert (
        app.state.governance_assessment_signed_checkpoint_store
        is not None
    )


def test_configured_registration_is_idempotent(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"
    environment = signing_environment()

    first = register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment=environment,
    )
    second = register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment=environment,
    )

    assert second is first


def test_configured_registration_exposes_key_admin_api(tmp_path):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment=signing_environment(),
    )

    response = TestClient(app).get(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["key_id"] == "key-001"


def test_unsigned_registration_does_not_expose_key_admin_api(
    tmp_path,
):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment={},
    )

    response = TestClient(app).get(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 404


def test_registered_admin_api_can_activate_second_key(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"
    environment = signing_environment()
    environment["GAGF_SECOND_CHECKPOINT_SECRET"] = (
        "second-secret"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment=environment,
    )

    service = (
        app.state.governance_assessment_checkpoint_key_service
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="env://GAGF_SECOND_CHECKPOINT_SECRET",
        make_active=False,
    )

    response = TestClient(app).post(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/key-002/activate"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert response.json()["key_id"] == "key-002"
    assert response.json()["active"] is True


def test_registration_exposes_key_audit_store_on_state(tmp_path):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment=signing_environment(),
    )

    assert (
        app.state.governance_assessment_checkpoint_key_audit_store
        is not None
    )


def test_registered_activation_writes_production_audit_event(
    tmp_path,
):
    app = FastAPI()
    environment = signing_environment()
    environment["GAGF_SECOND_CHECKPOINT_SECRET"] = (
        "second-secret"
    )

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
        environment=environment,
    )

    service = (
        app.state.governance_assessment_checkpoint_key_service
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="env://GAGF_SECOND_CHECKPOINT_SECRET",
        make_active=False,
    )

    client = TestClient(app)
    activation = client.post(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/key-002/activate"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )
    history = client.get(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/audit-events"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert activation.status_code == 200
    assert history.status_code == 200
    assert history.json()["count"] == 1
    event = history.json()["items"][0]
    assert event["actor_id"] == "actor-admin"
    assert event["previous_key_id"] == "key-001"
    assert event["active_key_id"] == "key-002"


def test_key_audit_database_survives_application_restart(tmp_path):
    database_path = tmp_path / "assessment.sqlite3"
    environment = signing_environment()
    environment["GAGF_SECOND_CHECKPOINT_SECRET"] = (
        "second-secret"
    )

    first_app = FastAPI()
    register_governance_assessment_api(
        app=first_app,
        database_path=database_path,
        environment=environment,
    )

    first_service = (
        first_app.state
        .governance_assessment_checkpoint_key_service
    )
    first_service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="env://GAGF_SECOND_CHECKPOINT_SECRET",
        make_active=False,
    )

    activation = TestClient(first_app).post(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/key-002/activate"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )
    assert activation.status_code == 200

    second_app = FastAPI()
    register_governance_assessment_api(
        app=second_app,
        database_path=database_path,
        environment=environment,
    )

    history = TestClient(second_app).get(
        (
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys/audit-events"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=admin_headers(),
    )

    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert history.json()["items"][0]["active_key_id"] == (
        "key-002"
    )


def test_key_audit_database_contains_no_signing_secret(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
        environment=signing_environment(),
    )

    audit_path = (
        tmp_path
        / "governance_assessment_checkpoint_key_audit.sqlite3"
    )

    assert audit_path.exists()
    assert b"private-signing-secret" not in audit_path.read_bytes()
