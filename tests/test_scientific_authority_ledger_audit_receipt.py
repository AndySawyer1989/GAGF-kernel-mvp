import sqlite3
from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_authority_ledger_audit_receipt import (
    AUTHORITY_LEDGER_AUDIT_RECEIPT_ID,
    AUTHORITY_LEDGER_AUDIT_RECEIPT_SCHEMA_VERSION,
    AUTHORITY_LEDGER_AUDIT_RECEIPT_VERSION,
    AuthorityLedgerAuditReceipt,
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


def build_valid_audit_result(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)

    database_path = tmp_path / "authority-receipts.db"
    ledger = ScientificAuthorityReceiptLedger(database_path)
    ledger.append(build_authority_receipt())

    return ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )


def build_invalid_audit_result(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)

    database_path = tmp_path / "authority-receipts.db"
    ledger = ScientificAuthorityReceiptLedger(database_path)
    record = ledger.append(build_authority_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET policy_version = ?
            WHERE sequence_number = ?
            """,
            ("9.9.9", record.sequence_number),
        )

    return ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )


def test_audit_receipt_has_stable_identity():
    assert AUTHORITY_LEDGER_AUDIT_RECEIPT_ID == (
        "scientific-authority-ledger-audit-receipt"
    )
    assert AUTHORITY_LEDGER_AUDIT_RECEIPT_VERSION == "0.1.0"
    assert (
        AUTHORITY_LEDGER_AUDIT_RECEIPT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_valid_audit_builds_valid_receipt(tmp_path):
    audit_result = build_valid_audit_result(tmp_path)

    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )

    assert receipt.valid is True
    assert receipt.record_count == 1
    assert receipt.findings == ()
    assert receipt.verify() is True


def test_invalid_audit_builds_verifiable_failure_receipt(tmp_path):
    audit_result = build_invalid_audit_result(tmp_path)

    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )

    assert receipt.valid is False
    assert len(receipt.findings) >= 1
    assert receipt.verify() is True


def test_receipt_preserves_auditor_identity(tmp_path):
    audit_result = build_valid_audit_result(tmp_path)

    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )

    assert receipt.auditor_id == audit_result.auditor_id
    assert receipt.auditor_version == audit_result.auditor_version


def test_receipt_preserves_audit_checks(tmp_path):
    audit_result = build_valid_audit_result(tmp_path)

    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )

    assert receipt.checks == audit_result.checks
    assert receipt.checks is not audit_result.checks


def test_receipt_preserves_structured_findings(tmp_path):
    audit_result = build_invalid_audit_result(tmp_path)

    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )

    assert receipt.findings == tuple(
        finding.to_dict()
        for finding in audit_result.findings
    )


def test_identical_audits_produce_identical_receipts(tmp_path):
    audit_result = build_valid_audit_result(tmp_path)
    builder = ScientificAuthorityLedgerAuditReceiptBuilder()

    first = builder.build(audit_result)
    second = builder.build(audit_result)

    assert first == second
    assert first.receipt_hash == second.receipt_hash


def test_changed_audit_result_changes_receipt_hash(tmp_path):
    valid_result = build_valid_audit_result(
        tmp_path / "valid"
    )
    invalid_result = build_invalid_audit_result(
        tmp_path / "invalid"
    )

    builder = ScientificAuthorityLedgerAuditReceiptBuilder()

    valid_receipt = builder.build(valid_result)
    invalid_receipt = builder.build(invalid_result)

    assert (
        valid_receipt.receipt_hash
        != invalid_receipt.receipt_hash
    )


def test_receipt_hash_is_sha256_hex(tmp_path):
    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(build_valid_audit_result(tmp_path))
    )

    assert len(receipt.receipt_hash) == 64
    int(receipt.receipt_hash, 16)


def test_tampered_validity_fails_verification(tmp_path):
    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(build_valid_audit_result(tmp_path))
    )

    tampered = replace(
        receipt,
        valid=False,
    )

    assert tampered.verify() is False


def test_tampered_checks_fail_verification(tmp_path):
    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(build_valid_audit_result(tmp_path))
    )

    changed_checks = dict(receipt.checks)
    changed_checks["table_present"] = False

    tampered = replace(
        receipt,
        checks=changed_checks,
    )

    assert tampered.verify() is False


def test_receipt_serialization_includes_hash(tmp_path):
    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(build_valid_audit_result(tmp_path))
    )

    serialized = receipt.to_dict()

    assert serialized["receipt_hash"] == receipt.receipt_hash
    assert serialized["receipt_id"] == (
        "scientific-authority-ledger-audit-receipt"
    )
    assert serialized["valid"] is True


def test_receipt_is_immutable(tmp_path):
    receipt = (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(build_valid_audit_result(tmp_path))
    )

    with pytest.raises(FrozenInstanceError):
        receipt.receipt_hash = "changed"


def test_manual_receipt_with_bad_hash_fails_verification():
    receipt = AuthorityLedgerAuditReceipt(
        receipt_schema_version="1.0.0",
        receipt_id=(
            "scientific-authority-ledger-audit-receipt"
        ),
        receipt_version="0.1.0",
        auditor_id=(
            "scientific-authority-ledger-integrity-auditor"
        ),
        auditor_version="0.1.0",
        valid=True,
        record_count=0,
        checks={
            "table_present": True,
            "sequence_contiguous": True,
            "receipt_hashes_unique": True,
            "receipt_json_valid": True,
            "stored_columns_match_receipts": True,
            "all_receipts_replay_valid": True,
        },
        findings=(),
        receipt_hash="0" * 64,
    )

    assert receipt.verify() is False

