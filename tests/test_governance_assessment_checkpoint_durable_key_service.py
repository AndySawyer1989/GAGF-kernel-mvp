from dataclasses import replace

import pytest

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_checkpoint_durable_key_service import (
    AssessmentCheckpointDurableKeyService,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadata,
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    InMemoryAssessmentCheckpointSecretResolver,
)


def checkpoint(
    *,
    checkpoint_id: str = "checkpoint-001",
    tenant_id: str = "tenant-alpha",
) -> AssessmentAuditCheckpoint:
    return AssessmentAuditCheckpoint(
        checkpoint_id=checkpoint_id,
        tenant_id=tenant_id,
        chain_head_hash="a" * 64,
        checked_count=3,
        valid=True,
        reason_code=None,
        created_at="2026-07-29T23:30:00+00:00",
    )


def build_service(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    resolver = InMemoryAssessmentCheckpointSecretResolver()
    service = AssessmentCheckpointDurableKeyService(
        metadata_store=store,
        secret_resolver=resolver,
    )
    return store, resolver, service


def register_active_key(
    resolver,
    service,
    *,
    key_id: str = "key-001",
    secret: bytes = b"secret-001",
):
    reference = f"secret://tenant-alpha/{key_id}"
    resolver.register_secret(
        secret_reference=reference,
        secret=secret,
    )
    return service.register_key(
        tenant_id="tenant-alpha",
        key_id=key_id,
        secret_reference=reference,
        make_active=True,
    )


def test_durable_active_key_signs_checkpoint(tmp_path):
    _, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)

    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    assert signed.key_id == "key-001"
    assert len(signed.signature) == 64


def test_signed_checkpoint_verifies(tmp_path):
    _, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)
    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=signed
    )

    assert result.valid is True
    assert result.reason_code is None


def test_rotation_retires_previous_metadata(tmp_path):
    store, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)

    resolver.register_secret(
        secret_reference="secret://tenant-alpha/key-002",
        secret=b"secret-002",
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="secret://tenant-alpha/key-002",
        make_active=True,
    )

    first = store.get_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
    )
    second = store.get_active_key(
        tenant_id="tenant-alpha"
    )

    assert first.active is False
    assert first.retired_at is not None
    assert second.key_id == "key-002"
    assert second.active is True


def test_historical_checkpoint_verifies_after_rotation(tmp_path):
    _, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)
    historical = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    resolver.register_secret(
        secret_reference="secret://tenant-alpha/key-002",
        secret=b"secret-002",
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret_reference="secret://tenant-alpha/key-002",
        make_active=True,
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=historical
    )

    assert result.valid is True
    assert result.key_id == "key-001"


def test_service_state_survives_restart(tmp_path):
    store, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)

    restarted_store = (
        AssessmentCheckpointSigningKeyMetadataStore(
            tmp_path / "keys.sqlite3"
        )
    )
    restarted_service = AssessmentCheckpointDurableKeyService(
        metadata_store=restarted_store,
        secret_resolver=resolver,
    )

    signed = restarted_service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    assert signed.key_id == "key-001"


def test_unknown_secret_reference_prevents_registration(tmp_path):
    _, _, service = build_service(tmp_path)

    with pytest.raises(
        KeyError,
        match="signing secret was not found",
    ):
        service.register_key(
            tenant_id="tenant-alpha",
            key_id="key-001",
            secret_reference="secret://missing",
            make_active=True,
        )


def test_missing_historical_secret_returns_failure(tmp_path):
    store, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)
    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    empty_resolver = InMemoryAssessmentCheckpointSecretResolver()
    restarted_service = AssessmentCheckpointDurableKeyService(
        metadata_store=store,
        secret_resolver=empty_resolver,
    )

    result = restarted_service.verify_signed_checkpoint(
        signed_checkpoint=signed
    )

    assert result.valid is False
    assert result.reason_code == (
        "ASSESSMENT_CHECKPOINT_SECRET_NOT_FOUND"
    )


def test_modified_checkpoint_returns_invalid_signature(tmp_path):
    _, resolver, service = build_service(tmp_path)
    register_active_key(resolver, service)
    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )
    tampered = replace(
        signed,
        checkpoint=replace(
            signed.checkpoint,
            checked_count=4,
        ),
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=tampered
    )

    assert result.valid is False
    assert result.reason_code == (
        "ASSESSMENT_CHECKPOINT_SIGNATURE_INVALID"
    )


def test_activate_key_delegates_to_atomic_store_rotation(
    tmp_path,
    monkeypatch,
):
    metadata_store = AssessmentCheckpointSigningKeyMetadataStore(
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
        metadata_store=metadata_store,
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

    calls = []
    original_rotate = metadata_store.rotate_active_key

    def tracked_rotate_active_key(**kwargs):
        calls.append(kwargs)
        return original_rotate(**kwargs)

    monkeypatch.setattr(
        metadata_store,
        "rotate_active_key",
        tracked_rotate_active_key,
    )

    result = service.activate_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
    )

    assert result.key_id == "key-002"
    assert result.active is True
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == "tenant-alpha"
    assert calls[0]["key_id"] == "key-002"
    assert calls[0]["retired_at"]


def test_atomic_service_rotation_retires_previous_key(tmp_path):
    metadata_store = AssessmentCheckpointSigningKeyMetadataStore(
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
        metadata_store=metadata_store,
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

    service.activate_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
    )

    previous = metadata_store.get_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
    )
    active = metadata_store.get_active_key(
        tenant_id="tenant-alpha",
    )

    assert previous.active is False
    assert previous.retired_at is not None
    assert active.key_id == "key-002"
    assert active.retired_at is None


def test_failed_secret_resolution_preserves_active_key(tmp_path):
    metadata_store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    resolver = InMemoryAssessmentCheckpointSecretResolver()
    resolver.register_secret(
        secret_reference="secret://key-001",
        secret=b"secret-001",
    )
    service = AssessmentCheckpointDurableKeyService(
        metadata_store=metadata_store,
        secret_resolver=resolver,
    )
    service.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret_reference="secret://key-001",
        make_active=True,
    )

    metadata_store.insert(
        AssessmentCheckpointSigningKeyMetadata(
            tenant_id="tenant-alpha",
            key_id="key-002",
            secret_reference="secret://missing-key",
            active=False,
            created_at="2026-07-30T23:00:00+00:00",
        )
    )

    with pytest.raises(KeyError):
        service.activate_key(
            tenant_id="tenant-alpha",
            key_id="key-002",
        )

    active = metadata_store.get_active_key(
        tenant_id="tenant-alpha",
    )

    assert active.key_id == "key-001"
    assert active.active is True
    assert active.retired_at is None
