import pytest

from backend.app.gagf.governance_assessment_checkpoint_key_registry import (
    AssessmentCheckpointSigningKeyRegistry,
)


def test_register_and_activate_key():
    registry = AssessmentCheckpointSigningKeyRegistry()

    key = registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )

    assert key.active is True
    assert registry.get_active_key(
        tenant_id="tenant-alpha"
    ) == key


def test_rotation_retires_previous_key():
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret=b"secret-002",
    )

    active = registry.activate_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
    )
    retired = registry.get_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
    )

    assert active.key_id == "key-002"
    assert active.active is True
    assert retired.active is False
    assert retired.retired_at is not None


def test_retired_key_remains_available_for_verification():
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret=b"secret-002",
        make_active=True,
    )

    historical = registry.get_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
    )

    assert historical.secret == b"secret-001"
    assert historical.active is False


def test_tenant_key_registries_are_isolated():
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"alpha-secret",
        make_active=True,
    )
    registry.register_key(
        tenant_id="tenant-beta",
        key_id="key-001",
        secret=b"beta-secret",
        make_active=True,
    )

    assert registry.get_active_key(
        tenant_id="tenant-alpha"
    ).secret == b"alpha-secret"
    assert registry.get_active_key(
        tenant_id="tenant-beta"
    ).secret == b"beta-secret"


def test_metadata_excludes_secret():
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"private-secret",
        make_active=True,
    )

    metadata = registry.list_key_metadata(
        tenant_id="tenant-alpha"
    )

    assert len(metadata) == 1
    assert "secret" not in metadata[0]
    assert "private-secret" not in str(metadata)


def test_duplicate_tenant_key_id_is_rejected():
    registry = AssessmentCheckpointSigningKeyRegistry()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        registry.register_key(
            tenant_id="tenant-alpha",
            key_id="key-001",
            secret=b"replacement-secret",
        )


def test_missing_active_key_is_rejected():
    registry = AssessmentCheckpointSigningKeyRegistry()

    with pytest.raises(
        KeyError,
        match="active checkpoint signing key",
    ):
        registry.get_active_key(
            tenant_id="tenant-alpha"
        )


def test_unknown_key_is_rejected():
    registry = AssessmentCheckpointSigningKeyRegistry()

    with pytest.raises(
        KeyError,
        match="checkpoint signing key was not found",
    ):
        registry.get_key(
            tenant_id="tenant-alpha",
            key_id="missing-key",
        )


@pytest.mark.parametrize(
    ("tenant_id", "key_id", "secret", "message"),
    [
        ("", "key-001", b"secret", "tenant_id is required"),
        ("tenant-alpha", "", b"secret", "key_id is required"),
        (
            "tenant-alpha",
            "key-001",
            b"",
            "signing secret is required",
        ),
    ],
)
def test_invalid_registration_is_rejected(
    tenant_id,
    key_id,
    secret,
    message,
):
    registry = AssessmentCheckpointSigningKeyRegistry()

    with pytest.raises(ValueError, match=message):
        registry.register_key(
            tenant_id=tenant_id,
            key_id=key_id,
            secret=secret,
        )
