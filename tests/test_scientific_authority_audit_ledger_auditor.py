import sqlite3
from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.scientific_authority_audit_ledger_auditor import (
    AUTHORITY_AUDIT_LEDGER_AUDITOR_ID,
    AUTHORITY_AUDIT_LEDGER_AUDITOR_VERSION,
    ScientificAuthorityAuditLedgerIntegrityAuditor,
)
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


def build_audit_receipt(tmp_path, *, valid: bool = True):
    tmp_path.mkdir(parents=True, exist_ok=True)

    authority_database = tmp_path / "authority.db"
    authority_ledger = ScientificAuthorityReceiptLedger(
        authority_database
    )
    authority_record = authority_ledger.append(
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
                ("9.9.9", authority_record.sequence_number),
            )

    audit_result = (
        ScientificAuthorityLedgerIntegrityAuditor()
        .audit(authority_database)
    )

    return (
        ScientificAuthorityLedgerAuditReceiptBuilder()
        .build(audit_result)
    )


def build_audit_ledger(tmp_path):
    database_path = tmp_path / "audit-receipts.db"
    ledger = ScientificAuthorityAuditReceiptLedger(
        database_path
    )
    return database_path, ledger


def test_auditor_has_stable_identity():
    assert AUTHORITY_AUDIT_LEDGER_AUDITOR_ID == (
        "scientific-authority-audit-ledger-integrity-auditor"
    )
    assert AUTHORITY_AUDIT_LEDGER_AUDITOR_VERSION == "0.1.0"


def test_valid_empty_ledger_passes_audit(tmp_path):
    database_path, _ = build_audit_ledger(tmp_path)

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is True
    assert result.record_count == 0
    assert result.findings == ()
    assert all(result.checks.values())


def test_valid_populated_ledger_passes_audit(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)

    ledger.append(
        build_audit_receipt(
            tmp_path / "valid-source",
            valid=True,
        )
    )
    ledger.append(
        build_audit_receipt(
            tmp_path / "invalid-source",
            valid=False,
        )
    )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is True
    assert result.record_count == 2
    assert result.findings == ()


def test_result_is_immutable(tmp_path):
    database_path, _ = build_audit_ledger(tmp_path)

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_result_serialization_is_stable(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )
    serialized = result.to_dict()

    assert serialized["valid"] is True
    assert serialized["auditor_id"] == (
        "scientific-authority-audit-ledger-integrity-auditor"
    )
    assert serialized["auditor_version"] == "0.1.0"
    assert serialized["record_count"] == 1
    assert serialized["findings"] == []


def test_missing_table_fails_audit(tmp_path):
    database_path = tmp_path / "missing-table.db"

    with sqlite3.connect(database_path):
        pass

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["table_present"] is False
    assert result.findings[0].code == (
        "AUDIT_LEDGER_TABLE_MISSING"
    )


def test_sequence_gap_is_detected(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)

    first = ledger.append(
        build_audit_receipt(
            tmp_path / "first",
            valid=True,
        )
    )
    ledger.append(
        build_audit_receipt(
            tmp_path / "second",
            valid=False,
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM scientific_authority_audit_receipts
            WHERE sequence_number = ?
            """,
            (first.sequence_number,),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["sequence_contiguous"] is False
    assert any(
        finding.code == "SEQUENCE_DISCONTINUITY"
        for finding in result.findings
    )


def test_invalid_receipt_json_is_detected(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET receipt_json = ?
            WHERE sequence_number = ?
            """,
            ("not-json", record.sequence_number),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["receipt_json_valid"] is False
    assert any(
        finding.code == "INVALID_AUDIT_RECEIPT_JSON"
        for finding in result.findings
    )


def test_stored_column_mismatch_is_detected(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET auditor_version = ?
            WHERE sequence_number = ?
            """,
            ("9.9.9", record.sequence_number),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert (
        result.checks["stored_columns_match_receipts"]
        is False
    )
    assert any(
        finding.code == "STORED_AUDIT_COLUMN_MISMATCH"
        for finding in result.findings
    )


def test_checks_json_mismatch_is_detected(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET checks_json = ?
            WHERE sequence_number = ?
            """,
            ('{"tampered":true}', record.sequence_number),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert (
        result.checks["stored_columns_match_receipts"]
        is False
    )


def test_findings_json_mismatch_is_detected(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=False,
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET findings_json = ?
            WHERE sequence_number = ?
            """,
            ('{"findings":[]}', record.sequence_number),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert (
        result.checks["stored_columns_match_receipts"]
        is False
    )


def test_tampered_receipt_hash_is_detected(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT receipt_json
            FROM scientific_authority_audit_receipts
            WHERE sequence_number = ?
            """,
            (record.sequence_number,),
        ).fetchone()

        import json

        receipt_data = json.loads(row[0])
        receipt_data["receipt_hash"] = "0" * 64

        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET receipt_json = ?
            WHERE sequence_number = ?
            """,
            (
                json.dumps(receipt_data),
                record.sequence_number,
            ),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["all_receipt_hashes_valid"] is False
    assert any(
        finding.code == "AUDIT_RECEIPT_HASH_INVALID"
        for finding in result.findings
    )


def test_finding_serialization_contains_context(tmp_path):
    database_path, ledger = build_audit_ledger(tmp_path)
    record = ledger.append(
        build_audit_receipt(
            tmp_path / "source",
            valid=True,
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_audit_receipts
            SET receipt_id = ?
            WHERE sequence_number = ?
            """,
            ("tampered-receipt-id", record.sequence_number),
        )

    result = ScientificAuthorityAuditLedgerIntegrityAuditor().audit(
        database_path
    )

    finding = next(
        finding
        for finding in result.findings
        if finding.code == "STORED_AUDIT_COLUMN_MISMATCH"
    )

    serialized = finding.to_dict()

    assert serialized["sequence_number"] == 1
    assert serialized["receipt_hash"] == (
        record.receipt.receipt_hash
    )
    assert "receipt_id" in serialized["message"]
