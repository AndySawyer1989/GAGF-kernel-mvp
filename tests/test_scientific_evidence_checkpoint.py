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
    SCIENTIFIC_EVIDENCE_CHECKPOINT_ID,
    SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION,
    SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION,
    ScientificEvidenceCheckpointBuilder,
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


def build_complete_evidence_system(tmp_path):
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

    return authority_database, audit_database


def test_checkpoint_has_stable_identity():
    assert SCIENTIFIC_EVIDENCE_CHECKPOINT_ID == (
        "constitutional-scientific-evidence-checkpoint"
    )
    assert SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION == "0.1.0"
    assert (
        SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_valid_ledgers_produce_valid_checkpoint(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert checkpoint.valid is True
    assert checkpoint.verify() is True
    assert checkpoint.authority_audit["record_count"] == 1
    assert checkpoint.audit_ledger_audit["record_count"] == 1


def test_empty_valid_ledgers_produce_valid_checkpoint(tmp_path):
    authority_database = tmp_path / "authority.db"
    audit_database = tmp_path / "audit.db"

    ScientificAuthorityReceiptLedger(authority_database)
    ScientificAuthorityAuditReceiptLedger(audit_database)

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert checkpoint.valid is True
    assert checkpoint.verify() is True
    assert checkpoint.authority_audit["record_count"] == 0
    assert checkpoint.audit_ledger_audit["record_count"] == 0


def test_authority_ledger_failure_invalidates_checkpoint(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
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

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert checkpoint.valid is False
    assert checkpoint.authority_audit["valid"] is False
    assert checkpoint.audit_ledger_audit["valid"] is True
    assert checkpoint.verify() is True


def test_audit_ledger_failure_invalidates_checkpoint(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    with sqlite3.connect(audit_database) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET auditor_version = ?
            WHERE sequence_number = 1
            """,
            ("9.9.9",),
        )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert checkpoint.valid is False
    assert checkpoint.authority_audit["valid"] is True
    assert checkpoint.audit_ledger_audit["valid"] is False
    assert checkpoint.verify() is True


def test_identical_inputs_produce_identical_checkpoint(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )
    builder = ScientificEvidenceCheckpointBuilder()

    first = builder.build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )
    second = builder.build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert first == second
    assert first.checkpoint_hash == second.checkpoint_hash


def test_different_database_identity_changes_hash(tmp_path):
    first_authority, first_audit = (
        build_complete_evidence_system(
            tmp_path / "first"
        )
    )
    second_authority, second_audit = (
        build_complete_evidence_system(
            tmp_path / "second"
        )
    )

    builder = ScientificEvidenceCheckpointBuilder()

    first = builder.build(
        authority_database_path=first_authority,
        audit_database_path=first_audit,
    )
    second = builder.build(
        authority_database_path=second_authority,
        audit_database_path=second_audit,
    )

    assert (
        first.authority_ledger_identity
        != second.authority_ledger_identity
    )
    assert first.audit_ledger_identity != (
        second.audit_ledger_identity
    )
    assert first.checkpoint_hash != second.checkpoint_hash


def test_changed_ledger_state_changes_checkpoint_hash(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )
    builder = ScientificEvidenceCheckpointBuilder()

    before = builder.build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
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

    after = builder.build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert before.checkpoint_hash != after.checkpoint_hash
    assert before.valid is True
    assert after.valid is False


def test_checkpoint_hash_is_sha256_hex(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    assert len(checkpoint.checkpoint_hash) == 64
    int(checkpoint.checkpoint_hash, 16)


def test_checkpoint_serialization_contains_hash(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )
    serialized = checkpoint.to_dict()

    assert serialized["checkpoint_hash"] == (
        checkpoint.checkpoint_hash
    )
    assert serialized["checkpoint_id"] == (
        "constitutional-scientific-evidence-checkpoint"
    )
    assert serialized["valid"] is True


def test_tampered_validity_fails_verification(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )
    tampered = replace(
        checkpoint,
        valid=False,
    )

    assert tampered.verify() is False


def test_tampered_authority_audit_fails_verification(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    authority_audit = dict(checkpoint.authority_audit)
    authority_audit["record_count"] = 999

    tampered = replace(
        checkpoint,
        authority_audit=authority_audit,
    )

    assert tampered.verify() is False


def test_tampered_audit_ledger_identity_fails_verification(
    tmp_path,
):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    tampered = replace(
        checkpoint,
        audit_ledger_identity="0" * 64,
    )

    assert tampered.verify() is False


def test_checkpoint_is_immutable(tmp_path):
    authority_database, audit_database = (
        build_complete_evidence_system(tmp_path)
    )

    checkpoint = ScientificEvidenceCheckpointBuilder().build(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )

    with pytest.raises(FrozenInstanceError):
        checkpoint.valid = False
