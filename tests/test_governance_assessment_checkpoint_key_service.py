from dataclasses import replace

import pytest

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_checkpoint_key_registry import (
    AssessmentCheckpointSigningKeyRegistry,
)
from backend.app.gagf.governance_assessment_checkpoint_key_service import (
    AssessmentCheckpointKeyService,
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
        created_at="2026-07-29T22:00:00+00:00",
    )


def build_service():
    registry = AssessmentCheckpointSigningKeyRegistry()
    service = AssessmentCheckpointKeyService(
        registry=registry
    )
    return registry, service


def test_active_key_signs_checkpoint():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )

    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    assert signed.key_id == "key-001"
    assert len(signed.signature) == 64


def test_signed_checkpoint_verifies_with_active_key():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=signed
    )

    assert result.valid is True
    assert result.reason_code is None


def test_rotation_uses_new_key_for_new_checkpoint():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
    first = service.sign_checkpoint(
        checkpoint=checkpoint(
            checkpoint_id="checkpoint-001"
        )
    )

    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret=b"secret-002",
        make_active=True,
    )
    second = service.sign_checkpoint(
        checkpoint=checkpoint(
            checkpoint_id="checkpoint-002"
        )
    )

    assert first.key_id == "key-001"
    assert second.key_id == "key-002"
    assert first.signature != second.signature


def test_retired_key_still_verifies_old_checkpoint():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
    historical = service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-002",
        secret=b"secret-002",
        make_active=True,
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=historical
    )

    assert result.valid is True
    assert result.key_id == "key-001"


def test_unknown_key_returns_verification_failure():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
    signed = service.sign_checkpoint(
        checkpoint=checkpoint()
    )
    unknown = replace(
        signed,
        key_id="missing-key",
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=unknown
    )

    assert result.valid is False
    assert result.reason_code == (
        "ASSESSMENT_CHECKPOINT_KEY_NOT_FOUND"
    )


def test_modified_checkpoint_returns_invalid_signature():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
        secret=b"secret-001",
        make_active=True,
    )
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


def test_cross_tenant_key_is_not_used_for_verification():
    registry, service = build_service()
    registry.register_key(
        tenant_id="tenant-alpha",
        key_id="shared-key",
        secret=b"alpha-secret",
        make_active=True,
    )
    registry.register_key(
        tenant_id="tenant-beta",
        key_id="shared-key",
        secret=b"beta-secret",
        make_active=True,
    )

    alpha_signed = service.sign_checkpoint(
        checkpoint=checkpoint(
            tenant_id="tenant-alpha"
        )
    )
    tampered = replace(
        alpha_signed,
        checkpoint=replace(
            alpha_signed.checkpoint,
            tenant_id="tenant-beta",
        ),
    )

    result = service.verify_signed_checkpoint(
        signed_checkpoint=tampered
    )

    assert result.valid is False
    assert result.reason_code == (
        "ASSESSMENT_CHECKPOINT_SIGNATURE_INVALID"
    )


def test_missing_active_key_prevents_signing():
    _, service = build_service()

    with pytest.raises(
        KeyError,
        match="active checkpoint signing key",
    ):
        service.sign_checkpoint(
            checkpoint=checkpoint()
        )
