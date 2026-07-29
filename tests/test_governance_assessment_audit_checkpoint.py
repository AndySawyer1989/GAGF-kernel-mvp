import sqlite3

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
    build_assessment_audit_event,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
    create_assessment_audit_checkpoint,
)
from backend.app.gagf.governance_assessment_audit_integrity import (
    ASSESSMENT_AUDIT_GENESIS_HASH,
)


def append_event(
    ledger: AssessmentAuditLedger,
    *,
    tenant_id: str = "tenant-alpha",
    request_id: str = "request-001",
):
    return ledger.append(
        build_assessment_audit_event(
            request_id=request_id,
            tenant_id=tenant_id,
            actor_id="actor-001",
            actor_roles=("assessment:read",),
            method="GET",
            route="/api/v1/governance-assessments",
            outcome="allowed",
            status_code=200,
        )
    )


def test_empty_chain_checkpoint_uses_genesis_hash(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    checkpoint = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    )

    assert checkpoint.valid is True
    assert checkpoint.checked_count == 0
    assert checkpoint.chain_head_hash == (
        ASSESSMENT_AUDIT_GENESIS_HASH
    )


def test_checkpoint_captures_current_chain_head(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    append_event(ledger, request_id="request-001")
    latest = append_event(
        ledger,
        request_id="request-002",
    )

    checkpoint = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    )

    assert checkpoint.valid is True
    assert checkpoint.checked_count == 2
    assert checkpoint.chain_head_hash == latest.event_hash


def test_checkpoint_store_persists_checkpoint(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    append_event(ledger)

    checkpoint = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    )
    store.append(checkpoint)

    assert store.list_checkpoints(
        tenant_id="tenant-alpha"
    ) == [checkpoint]


def test_checkpoint_lists_are_tenant_isolated(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    append_event(ledger, tenant_id="tenant-alpha")
    append_event(ledger, tenant_id="tenant-beta")

    alpha = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    )
    beta = create_assessment_audit_checkpoint(
        tenant_id="tenant-beta",
        ledger=ledger,
    )
    store.append(alpha)
    store.append(beta)

    assert store.list_checkpoints(
        tenant_id="tenant-alpha"
    ) == [alpha]
    assert store.list_checkpoints(
        tenant_id="tenant-beta"
    ) == [beta]


def test_tampered_chain_creates_invalid_checkpoint(tmp_path):
    database_path = tmp_path / "audit.sqlite3"
    ledger = AssessmentAuditLedger(database_path)
    event = append_event(ledger)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE assessment_audit_events
            SET status_code = 403
            WHERE event_id = ?
            """,
            (event.event_id,),
        )
        connection.commit()

    checkpoint = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    )

    assert checkpoint.valid is False
    assert checkpoint.reason_code == (
        "AUDIT_EVENT_HASH_MISMATCH"
    )


def test_duplicate_checkpoint_is_rejected(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoint.sqlite3"
    )
    checkpoint = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    )

    store.append(checkpoint)

    try:
        store.append(checkpoint)
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "duplicate checkpoint was accepted"
        )


def test_checkpoint_to_dict_is_serializable(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    payload = create_assessment_audit_checkpoint(
        tenant_id="tenant-alpha",
        ledger=ledger,
    ).to_dict()

    assert payload["tenant_id"] == "tenant-alpha"
    assert payload["valid"] is True
    assert isinstance(payload["checkpoint_id"], str)
