from dataclasses import replace

import pytest

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature import (
    ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM,
    compute_checkpoint_signature,
    sign_assessment_audit_checkpoint,
    verify_assessment_audit_checkpoint_signature,
)


SIGNING_SECRET = b"test-checkpoint-signing-secret"


def checkpoint() -> AssessmentAuditCheckpoint:
    return AssessmentAuditCheckpoint(
        checkpoint_id="checkpoint-001",
        tenant_id="tenant-alpha",
        chain_head_hash="a" * 64,
        checked_count=12,
        valid=True,
        reason_code=None,
        created_at="2026-07-29T20:00:00+00:00",
    )


def test_signature_is_deterministic():
    first = compute_checkpoint_signature(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )
    second = compute_checkpoint_signature(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )

    assert first == second
    assert len(first) == 64


def test_signed_checkpoint_verifies():
    signed = sign_assessment_audit_checkpoint(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )

    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=signed,
        secret=SIGNING_SECRET,
    ) is True


def test_modified_checkpoint_fails_verification():
    signed = sign_assessment_audit_checkpoint(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )
    tampered = replace(
        signed,
        checkpoint=replace(
            signed.checkpoint,
            checked_count=13,
        ),
    )

    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=tampered,
        secret=SIGNING_SECRET,
    ) is False


def test_modified_tenant_fails_verification():
    signed = sign_assessment_audit_checkpoint(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )
    tampered = replace(
        signed,
        checkpoint=replace(
            signed.checkpoint,
            tenant_id="tenant-beta",
        ),
    )

    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=tampered,
        secret=SIGNING_SECRET,
    ) is False


def test_wrong_secret_fails_verification():
    signed = sign_assessment_audit_checkpoint(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )

    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=signed,
        secret=b"wrong-secret",
    ) is False


def test_different_key_id_changes_signature():
    first = compute_checkpoint_signature(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )
    second = compute_checkpoint_signature(
        checkpoint=checkpoint(),
        key_id="key-002",
        secret=SIGNING_SECRET,
    )

    assert first != second


def test_empty_key_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="key_id is required",
    ):
        compute_checkpoint_signature(
            checkpoint=checkpoint(),
            key_id="",
            secret=SIGNING_SECRET,
        )


def test_empty_secret_is_rejected():
    with pytest.raises(
        ValueError,
        match="signing secret is required",
    ):
        compute_checkpoint_signature(
            checkpoint=checkpoint(),
            key_id="key-001",
            secret=b"",
        )


def test_unsupported_algorithm_is_rejected():
    with pytest.raises(
        ValueError,
        match="unsupported checkpoint signature algorithm",
    ):
        compute_checkpoint_signature(
            checkpoint=checkpoint(),
            key_id="key-001",
            secret=SIGNING_SECRET,
            signature_algorithm="rsa-sha256",
        )


def test_serialized_output_excludes_secret():
    signed = sign_assessment_audit_checkpoint(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )

    payload = signed.to_dict()

    assert payload["key_id"] == "key-001"
    assert payload["signature_algorithm"] == (
        ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM
    )
    assert "secret" not in payload
    assert SIGNING_SECRET.decode() not in str(payload)


def test_chain_head_is_bound_to_signature():
    signed = sign_assessment_audit_checkpoint(
        checkpoint=checkpoint(),
        key_id="key-001",
        secret=SIGNING_SECRET,
    )
    tampered = replace(
        signed,
        checkpoint=replace(
            signed.checkpoint,
            chain_head_hash="b" * 64,
        ),
    )

    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=tampered,
        secret=SIGNING_SECRET,
    ) is False
