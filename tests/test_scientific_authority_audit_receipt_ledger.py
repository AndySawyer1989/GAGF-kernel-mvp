import json
import sqlite3
from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_audit_receipt_ledger import (
    AUTHORITY_AUDIT_RECEIPT_LEDGER_ID,
    AUTHORITY_AUDIT_RECEIPT_LEDGER_VERSION,
    AuthorityAuditReceiptConflictError,
    InvalidAuthorityAuditReceiptError,
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


def build_audit_receipt(
    tmp_path,
    *,
    valid: bool,
):
    tmp_path.mkdir(parents=True, exist_ok=True)

    authority_database = tmp_path / "authority.db"
    authority_ledger = ScientificAuthorityReceiptLedger(
        authority_database
    )
    record = authority_ledger.append(
        build_authority_receipt()
    )

    if not valid:
        with sqlite3.connect(authority_database) as connection:
            connection.execute(
                """
                UPDATE scientific_authority_receipts
                SET policy_version = ?
                WHERE sequence_number = ?
                """,
                ("9.9.9", record.sequence_number),
            )

    audit_result = (
        ScientificAuthorityLedgerIntegrityAuditor()
        .audit(authority_database)
    )

    return (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )


def test_audit_receipt_ledger_has_stable_identity():
    assert AUTHORITY_AUDIT_RECEIPT_LEDGER_ID == (
        "scientific-authority-audit-receipt-ledger"
    )
    assert AUTHORITY_AUDIT_RECEIPT_LEDGER_VERSION == "0.1.0"


def test_append_persists_valid_audit_receipt(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )
    receipt = build_audit_receipt(
        tmp_path / "source",
        valid=True,
    )

    record = ledger.append(receipt)

    assert record.sequence_number == 1
    assert record.receipt == receipt
    assert ledger.count() == 1


def test_parent_directory_is_created(tmp_path):
    database_path = (
        tmp_path
        / "nested"
        / "audit"
        / "audit-receipts.db"
    )

    ledger = ScientificAuthorityAuditReceiptLedger(
        database_path
    )

    assert database_path.parent.is_dir()
    assert ledger.count() == 0


def test_record_is_immutable(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    with pytest.raises(FrozenInstanceError):
        record.sequence_number = 10


def test_get_by_hash_restores_receipt(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )
    receipt = build_audit_receipt(
        tmp_path / "source",
        valid=True,
    )
    ledger.append(receipt)

    restored = ledger.get_by_hash(receipt.receipt_hash)

    assert restored is not None
    assert restored.sequence_number == 1
    assert restored.receipt == receipt
    assert restored.receipt.verify() is True


def test_unknown_hash_returns_none(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    assert ledger.get_by_hash("0" * 64) is None


def test_identical_append_is_idempotent(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )
    receipt = build_audit_receipt(
        tmp_path / "source",
        valid=True,
    )

    first = ledger.append(receipt)
    second = ledger.append(receipt)

    assert first.sequence_number == 1
    assert second.sequence_number == 1
    assert ledger.count() == 1


def test_invalid_hash_receipt_is_rejected(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )
    receipt = build_audit_receipt(
        tmp_path / "source",
        valid=True,
    )
    tampered = replace(
        receipt,
        receipt_hash="0" * 64,
    )

    with pytest.raises(
        InvalidAuthorityAuditReceiptError,
        match="failed hash verification",
    ):
        ledger.append(tampered)

    assert ledger.count() == 0


def test_valid_and_invalid_audits_are_both_persisted(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    valid_receipt = build_audit_receipt(
        tmp_path / "valid-source",
        valid=True,
    )
    invalid_receipt = build_audit_receipt(
        tmp_path / "invalid-source",
        valid=False,
    )

    ledger.append(valid_receipt)
    ledger.append(invalid_receipt)

    assert ledger.count() == 2
    assert ledger.count(valid=True) == 1
    assert ledger.count(valid=False) == 1


def test_records_can_be_filtered_by_validity(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    valid_receipt = build_audit_receipt(
        tmp_path / "valid-source",
        valid=True,
    )
    invalid_receipt = build_audit_receipt(
        tmp_path / "invalid-source",
        valid=False,
    )

    ledger.append(valid_receipt)
    ledger.append(invalid_receipt)

    valid_records = ledger.list_records(valid=True)
    invalid_records = ledger.list_records(valid=False)

    assert len(valid_records) == 1
    assert valid_records[0].receipt.valid is True

    assert len(invalid_records) == 1
    assert invalid_records[0].receipt.valid is False


def test_records_are_listed_in_sequence_order(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    first_receipt = build_audit_receipt(
        tmp_path / "first",
        valid=True,
    )
    second_receipt = build_audit_receipt(
        tmp_path / "second",
        valid=False,
    )

    ledger.append(first_receipt)
    ledger.append(second_receipt)

    records = ledger.list_records()

    assert [
        record.sequence_number
        for record in records
    ] == [1, 2]
    assert records[0].receipt == first_receipt
    assert records[1].receipt == second_receipt


def test_append_many_returns_records(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    receipts = (
        build_audit_receipt(
            tmp_path / "first",
            valid=True,
        ),
        build_audit_receipt(
            tmp_path / "second",
            valid=False,
        ),
    )

    records = ledger.append_many(receipts)

    assert len(records) == 2
    assert ledger.count() == 2


def test_verify_all_accepts_valid_receipt_hashes(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=False,
        )
    )

    assert ledger.verify_all() is True


def test_empty_ledger_verifies_vacuously(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    assert ledger.verify_all() is True


def test_record_serialization_contains_receipt(tmp_path):
    ledger = ScientificAuthorityAuditReceiptLedger(
        tmp_path / "audit-receipts.db"
    )

    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )
    serialized = record.to_dict()

    assert serialized["sequence_number"] == 1
    assert serialized["receipt"]["receipt_hash"] == (
        record.receipt.receipt_hash
    )


def test_conflicting_duplicate_hash_is_rejected(tmp_path):
    database_path = tmp_path / "audit-receipts.db"
    ledger = ScientificAuthorityAuditReceiptLedger(
        database_path
    )
    receipt = build_audit_receipt(
        tmp_path / "source",
        valid=True,
    )
    ledger.append(receipt)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET receipt_json = ?
            WHERE receipt_hash = ?
            """,
            (
                json.dumps({"tampered": True}),
                receipt.receipt_hash,
            ),
        )

    with pytest.raises(
        AuthorityAuditReceiptConflictError,
        match="different content",
    ):
        ledger.append(receipt)
