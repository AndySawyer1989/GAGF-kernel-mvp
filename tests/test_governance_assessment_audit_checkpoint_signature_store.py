import sqlite3

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature import (
    sign_assessment_audit_checkpoint,
    verify_assessment_audit_checkpoint_signature,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)


SIGNING_SECRET = b"test-signing-secret"


def signed_checkpoint(
    *,
    tenant_id: str = "tenant-alpha",
    checkpoint_id: str = "checkpoint-001",
):
    checkpoint = AssessmentAuditCheckpoint(
        checkpoint_id=checkpoint_id,
        tenant_id=tenant_id,
        chain_head_hash="a" * 64,
        checked_count=3,
        valid=True,
        reason_code=None,
        created_at="2026-07-29T21:00:00+00:00",
    )

    return sign_assessment_audit_checkpoint(
        checkpoint=checkpoint,
        key_id="key-001",
        secret=SIGNING_SECRET,
    )


def test_store_persists_signed_checkpoint(tmp_path):
    store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )
    signed = signed_checkpoint()

    store.append(signed)

    stored = store.list_signed_checkpoints(
        tenant_id="tenant-alpha"
    )

    assert stored == [signed]


def test_persisted_signature_still_verifies(tmp_path):
    store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )
    store.append(signed_checkpoint())

    stored = store.list_signed_checkpoints(
        tenant_id="tenant-alpha"
    )[0]

    assert verify_assessment_audit_checkpoint_signature(
        signed_checkpoint=stored,
        secret=SIGNING_SECRET,
    ) is True


def test_signed_checkpoint_lists_are_tenant_isolated(tmp_path):
    store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )
    alpha = signed_checkpoint(
        tenant_id="tenant-alpha",
        checkpoint_id="checkpoint-alpha",
    )
    beta = signed_checkpoint(
        tenant_id="tenant-beta",
        checkpoint_id="checkpoint-beta",
    )

    store.append(alpha)
    store.append(beta)

    assert store.list_signed_checkpoints(
        tenant_id="tenant-alpha"
    ) == [alpha]
    assert store.list_signed_checkpoints(
        tenant_id="tenant-beta"
    ) == [beta]


def test_duplicate_checkpoint_is_rejected(tmp_path):
    store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )
    signed = signed_checkpoint()
    store.append(signed)

    try:
        store.append(signed)
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "duplicate signed checkpoint was accepted"
        )


def test_list_limit_is_applied(tmp_path):
    store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )

    for index in range(4):
        store.append(
            signed_checkpoint(
                checkpoint_id=f"checkpoint-{index}",
            )
        )

    stored = store.list_signed_checkpoints(
        tenant_id="tenant-alpha",
        limit=2,
    )

    assert len(stored) == 2
