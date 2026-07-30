import sqlite3

import pytest

from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadata,
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    InMemoryAssessmentCheckpointSecretResolver,
)


def metadata(
    *,
    tenant_id: str = "tenant-alpha",
    key_id: str = "key-001",
    secret_reference: str = "secret://tenant-alpha/key-001",
    active: bool = True,
) -> AssessmentCheckpointSigningKeyMetadata:
    return AssessmentCheckpointSigningKeyMetadata(
        tenant_id=tenant_id,
        key_id=key_id,
        secret_reference=secret_reference,
        active=active,
        created_at="2026-07-29T23:00:00+00:00",
    )


def test_store_persists_key_metadata(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    value = metadata()

    store.insert(value)

    assert store.get_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
    ) == value


def test_active_key_can_be_retrieved(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    value = metadata()
    store.insert(value)

    assert store.get_active_key(
        tenant_id="tenant-alpha"
    ) == value


def test_key_metadata_is_tenant_isolated(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    alpha = metadata()
    beta = metadata(
        tenant_id="tenant-beta",
        secret_reference="secret://tenant-beta/key-001",
    )
    store.insert(alpha)
    store.insert(beta)

    assert store.list_keys(
        tenant_id="tenant-alpha"
    ) == [alpha]
    assert store.list_keys(
        tenant_id="tenant-beta"
    ) == [beta]


def test_only_one_active_key_is_allowed_per_tenant(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    store.insert(metadata())

    with pytest.raises(sqlite3.IntegrityError):
        store.insert(
            metadata(
                key_id="key-002",
                secret_reference=(
                    "secret://tenant-alpha/key-002"
                ),
            )
        )


def test_retired_key_is_not_returned_as_active(tmp_path):
    store = AssessmentCheckpointSigningKeyMetadataStore(
        tmp_path / "keys.sqlite3"
    )
    store.insert(metadata(active=False))

    with pytest.raises(
        KeyError,
        match="active checkpoint signing key metadata",
    ):
        store.get_active_key(
            tenant_id="tenant-alpha"
        )


def test_metadata_contains_reference_not_secret():
    payload = metadata().to_dict()

    assert payload["secret_reference"] == (
        "secret://tenant-alpha/key-001"
    )
    assert "secret" not in {
        key for key in payload if key != "secret_reference"
    }


def test_secret_resolver_returns_registered_secret():
    resolver = InMemoryAssessmentCheckpointSecretResolver()
    resolver.register_secret(
        secret_reference="secret://tenant-alpha/key-001",
        secret=b"private-secret",
    )

    assert resolver.resolve_secret(
        secret_reference="secret://tenant-alpha/key-001"
    ) == b"private-secret"


def test_secret_resolver_rejects_unknown_reference():
    resolver = InMemoryAssessmentCheckpointSecretResolver()

    with pytest.raises(
        KeyError,
        match="signing secret was not found",
    ):
        resolver.resolve_secret(
            secret_reference="secret://missing"
        )


def test_duplicate_secret_reference_is_rejected():
    resolver = InMemoryAssessmentCheckpointSecretResolver()
    resolver.register_secret(
        secret_reference="secret://key-001",
        secret=b"secret-001",
    )

    with pytest.raises(ValueError, match="already exists"):
        resolver.register_secret(
            secret_reference="secret://key-001",
            secret=b"replacement-secret",
        )
