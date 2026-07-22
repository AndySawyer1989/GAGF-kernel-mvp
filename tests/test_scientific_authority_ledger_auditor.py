import sqlite3
from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_authority_ledger_auditor import (
    AUTHORITY_LEDGER_AUDITOR_ID,
    AUTHORITY_LEDGER_AUDITOR_VERSION,
    ScientificAuthorityLedgerIntegrityAuditor,
)
from backend.app.gagf.scientific_authority_receipt_ledger import (
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_calculation_contract import (
    ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
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


def build_receipt(
    *,
    contract=EVIDENCE_CONFIDENCE_CONTRACT,
    requested_authority=CalculationAuthority.ADVISORY,
):
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=contract,
            requested_authority=requested_authority,
            evidence=complete_evidence(),
        )
    )
    return receipt


def build_ledger(tmp_path):
    database_path = tmp_path / "authority-receipts.db"
    ledger = ScientificAuthorityReceiptLedger(database_path)
    return database_path, ledger


def test_auditor_has_stable_identity():
    assert AUTHORITY_LEDGER_AUDITOR_ID == (
        "scientific-authority-ledger-integrity-auditor"
    )
    assert AUTHORITY_LEDGER_AUDITOR_VERSION == "0.1.0"


def test_valid_empty_ledger_passes_audit(tmp_path):
    database_path, _ = build_ledger(tmp_path)

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is True
    assert result.record_count == 0
    assert result.findings == ()
    assert all(result.checks.values())


def test_valid_populated_ledger_passes_audit(tmp_path):
    database_path, ledger = build_ledger(tmp_path)

    ledger.append(build_receipt())
    ledger.append(
        build_receipt(
            contract=ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
            requested_authority=(
                CalculationAuthority.NON_AUTHORITATIVE
            ),
        )
    )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is True
    assert result.record_count == 2
    assert result.findings == ()


def test_audit_result_is_immutable(tmp_path):
    database_path, _ = build_ledger(tmp_path)

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_audit_serialization_is_stable(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    ledger.append(build_receipt())

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )
    serialized = result.to_dict()

    assert serialized["valid"] is True
    assert serialized["auditor_id"] == (
        "scientific-authority-ledger-integrity-auditor"
    )
    assert serialized["auditor_version"] == "0.1.0"
    assert serialized["record_count"] == 1
    assert serialized["findings"] == []


def test_missing_table_fails_audit(tmp_path):
    database_path = tmp_path / "missing-table.db"

    with sqlite3.connect(database_path):
        pass

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["table_present"] is False
    assert result.findings[0].code == "LEDGER_TABLE_MISSING"


def test_sequence_gap_is_detected(tmp_path):
    database_path, ledger = build_ledger(tmp_path)

    first = ledger.append(build_receipt())
    ledger.append(
        build_receipt(
            contract=ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
            requested_authority=(
                CalculationAuthority.NON_AUTHORITATIVE
            ),
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM scientific_authority_receipts
            WHERE sequence_number = ?
            """,
            (first.sequence_number,),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["sequence_contiguous"] is False
    assert any(
        finding.code == "SEQUENCE_DISCONTINUITY"
        for finding in result.findings
    )


def test_invalid_receipt_json_is_detected(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    record = ledger.append(build_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET receipt_json = ?
            WHERE sequence_number = ?
            """,
            ("not-json", record.sequence_number),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["receipt_json_valid"] is False
    assert any(
        finding.code == "INVALID_RECEIPT_JSON"
        for finding in result.findings
    )


def test_stored_column_mismatch_is_detected(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    record = ledger.append(build_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET policy_version = ?
            WHERE sequence_number = ?
            """,
            ("9.9.9", record.sequence_number),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert (
        result.checks["stored_columns_match_receipts"]
        is False
    )
    assert any(
        finding.code == "STORED_COLUMN_MISMATCH"
        for finding in result.findings
    )


def test_evidence_json_mismatch_is_detected(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    record = ledger.append(build_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET evidence_json = ?
            WHERE sequence_number = ?
            """,
            ('{"tampered":true}', record.sequence_number),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert (
        result.checks["stored_columns_match_receipts"]
        is False
    )


def test_decision_json_mismatch_is_detected(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    record = ledger.append(build_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET decision_json = ?
            WHERE sequence_number = ?
            """,
            ('{"allowed":false}', record.sequence_number),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert (
        result.checks["stored_columns_match_receipts"]
        is False
    )


def test_tampered_receipt_hash_fails_replay(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    record = ledger.append(build_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET receipt_json = json_set(
                receipt_json,
                '$.receipt_hash',
                ?
            )
            WHERE sequence_number = ?
            """,
            ("0" * 64, record.sequence_number),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )

    assert result.valid is False
    assert result.checks["all_receipts_replay_valid"] is False
    assert any(
        finding.code == "REPLAY_VERIFICATION_FAILED"
        for finding in result.findings
    )


def test_finding_serialization_contains_context(tmp_path):
    database_path, ledger = build_ledger(tmp_path)
    record = ledger.append(build_receipt())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET policy_id = ?
            WHERE sequence_number = ?
            """,
            ("tampered-policy", record.sequence_number),
        )

    result = ScientificAuthorityLedgerIntegrityAuditor().audit(
        database_path
    )
    finding = next(
        finding
        for finding in result.findings
        if finding.code == "STORED_COLUMN_MISMATCH"
    )

    serialized = finding.to_dict()

    assert serialized["sequence_number"] == 1
    assert serialized["receipt_hash"] == (
        record.receipt.receipt_hash
    )
    assert "policy_id" in serialized["message"]
