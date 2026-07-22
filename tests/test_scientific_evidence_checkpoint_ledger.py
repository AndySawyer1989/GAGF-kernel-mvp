import json
import sqlite3
from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_audit_receipt_ledger import (
    ScientificAuthorityAuditReceiptLedger,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_authority_ledger_audit_receipt import (
    ScientificAuthorityLedgerAuditReceiptBuilder,
)
from backend.app.gagf.scientific_authority_ledger_auditor import (
    ScientificAuthorityLedgerIntegrityAuditor,
)
from backend.app.gagf.scientific_authority_receipt_ledger import (
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_evidence_checkpoint import (
    ScientificEvidenceCheckpointBuilder,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    SCIENTIFIC_EVIDENCE_CHECKPOINT_LEDGER_ID,
    SCIENTIFIC_EVIDENCE_CHECKPOINT_LEDGER_VERSION,
    InvalidScientificEvidenceCheckpointError,
    ScientificEvidenceCheckpointConflictError,
    ScientificEvidenceCheckpointLedger,
)


def complete_evidence() -> AuthorityEscalationEvidence:
    return AuthorityEscalationEvidence(
        deterministic_replay_verified=True,
        canonical_input_binding_verified=True,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=True,
    )


def build_authority_receipt():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )

    return receipt


def build_system(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)

    authority_database = tmp_path / "authority.db"
    audit_database = tmp_path / "audit.db"

    authority_ledger = ScientificAuthorityReceiptLedger(
        authority_database
    )
    authority_ledger.append(build_authority_receipt())

    authority_audit = (
        ScientificAuthorityLedgerIntegrityAuditor()
        .audit(authority_database)
    )
    audit_receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(authority_audit)
    )

    audit_ledger = ScientificAuthorityAuditReceiptLedger(
        audit_database
    )
    audit_ledger.append(audit_receipt)

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    return authority_database, audit_database, checkpoint


def append_checkpoint(
    ledger,
    checkpoint,
    authority_database,
    audit_database,
):
    return ledger.append(
        checkpoint=checkpoint,
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )


def test_checkpoint_ledger_has_stable_identity():
    assert SCIENTIFIC_EVIDENCE_CHECKPOINT_LEDGER_ID == (
        "scientific-evidence-checkpoint-ledger"
    )
    assert (
        SCIENTIFIC_EVIDENCE_CHECKPOINT_LEDGER_VERSION
        == "0.1.0"
    )


def test_append_persists_replay_valid_checkpoint(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    record = append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    assert record.sequence_number == 1
    assert record.checkpoint == checkpoint
    assert ledger.count() == 1


def test_parent_directory_is_created(tmp_path):
    database_path = (
        tmp_path
        / "nested"
        / "checkpoint"
        / "checkpoints.db"
    )

    ledger = ScientificEvidenceCheckpointLedger(
        database_path
    )

    assert database_path.parent.is_dir()
    assert ledger.count() == 0


def test_record_is_immutable(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )
    record = append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    with pytest.raises(FrozenInstanceError):
        record.sequence_number = 10


def test_get_by_hash_restores_checkpoint(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )
    append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    restored = ledger.get_by_hash(
        checkpoint.checkpoint_hash
    )

    assert restored is not None
    assert restored.sequence_number == 1
    assert restored.checkpoint == checkpoint
    assert restored.checkpoint.verify() is True


def test_unknown_hash_returns_none(tmp_path):
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    assert ledger.get_by_hash("0" * 64) is None


def test_identical_append_is_idempotent(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    first = append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )
    second = append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    assert first.sequence_number == 1
    assert second.sequence_number == 1
    assert ledger.count() == 1


def test_tampered_checkpoint_is_rejected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )
    tampered = replace(
        checkpoint,
        checkpoint_hash="0" * 64,
    )

    with pytest.raises(
        InvalidScientificEvidenceCheckpointError,
        match="failed replay verification",
    ):
        append_checkpoint(
            ledger,
            tampered,
            authority_database,
            audit_database,
        )

    assert ledger.count() == 0


def test_stale_checkpoint_is_rejected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    with sqlite3.connect(authority_database) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET policy_version = ?
            WHERE sequence_number = 1
            """,
            ("9.9.9",),
        )

    with pytest.raises(
        InvalidScientificEvidenceCheckpointError,
        match="does not match replay",
    ):
        append_checkpoint(
            ledger,
            checkpoint,
            authority_database,
            audit_database,
        )

    assert ledger.count() == 0


def test_records_are_listed_in_sequence_order(tmp_path):
    first_authority, first_audit, first_checkpoint = (
        build_system(tmp_path / "first")
    )
    second_authority, second_audit, second_checkpoint = (
        build_system(tmp_path / "second")
    )

    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    append_checkpoint(
        ledger,
        first_checkpoint,
        first_authority,
        first_audit,
    )
    append_checkpoint(
        ledger,
        second_checkpoint,
        second_authority,
        second_audit,
    )

    records = ledger.list_records()

    assert [
        record.sequence_number
        for record in records
    ] == [1, 2]
    assert records[0].checkpoint == first_checkpoint
    assert records[1].checkpoint == second_checkpoint


def test_records_can_be_filtered_by_validity(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    assert len(ledger.list_records(valid=True)) == 1
    assert len(ledger.list_records(valid=False)) == 0
    assert ledger.count(valid=True) == 1
    assert ledger.count(valid=False) == 0


def test_append_many_returns_records(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    records = ledger.append_many(
        checkpoints=(checkpoint, checkpoint),
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert len(records) == 2
    assert records[0].sequence_number == 1
    assert records[1].sequence_number == 1
    assert ledger.count() == 1


def test_verify_all_hashes_accepts_valid_records(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    assert ledger.verify_all_hashes() is True


def test_empty_ledger_verifies_vacuously(tmp_path):
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    assert ledger.verify_all_hashes() is True


def test_record_serialization_contains_checkpoint(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    ledger = ScientificEvidenceCheckpointLedger(
        tmp_path / "checkpoints.db"
    )

    record = append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )
    serialized = record.to_dict()

    assert serialized["sequence_number"] == 1
    assert serialized["checkpoint"]["checkpoint_hash"] == (
        checkpoint.checkpoint_hash
    )


def test_conflicting_duplicate_hash_is_rejected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "source")
    )
    database_path = tmp_path / "checkpoints.db"
    ledger = ScientificEvidenceCheckpointLedger(
        database_path
    )

    append_checkpoint(
        ledger,
        checkpoint,
        authority_database,
        audit_database,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_evidence_checkpoints
            SET checkpoint_json = ?
            WHERE checkpoint_hash = ?
            """,
            (
                json.dumps({"tampered": True}),
                checkpoint.checkpoint_hash,
            ),
        )

    with pytest.raises(
        ScientificEvidenceCheckpointConflictError,
        match="different content",
    ):
        append_checkpoint(
            ledger,
            checkpoint,
            authority_database,
            audit_database,
        )
