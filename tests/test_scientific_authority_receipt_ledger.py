import json
from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_authority_receipt_ledger import (
    AUTHORITY_RECEIPT_LEDGER_ID,
    AUTHORITY_RECEIPT_LEDGER_VERSION,
    AuthorityReceiptConflictError,
    InvalidAuthorityReceiptError,
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


def test_ledger_has_stable_identity():
    assert (
        AUTHORITY_RECEIPT_LEDGER_ID
        == "scientific-authority-receipt-ledger"
    )
    assert AUTHORITY_RECEIPT_LEDGER_VERSION == "0.1.0"


def test_append_persists_valid_receipt(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )
    receipt = build_receipt()

    record = ledger.append(receipt)

    assert record.sequence_number == 1
    assert record.receipt == receipt
    assert ledger.count() == 1


def test_record_is_immutable(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )
    record = ledger.append(build_receipt())

    with pytest.raises(FrozenInstanceError):
        record.sequence_number = 99


def test_get_by_hash_restores_receipt(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )
    receipt = build_receipt()
    ledger.append(receipt)

    restored = ledger.get_by_hash(receipt.receipt_hash)

    assert restored is not None
    assert restored.sequence_number == 1
    assert restored.receipt == receipt
    assert restored.receipt.verify() is True


def test_get_unknown_hash_returns_none(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    assert ledger.get_by_hash("0" * 64) is None


def test_identical_append_is_idempotent(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )
    receipt = build_receipt()

    first = ledger.append(receipt)
    second = ledger.append(receipt)

    assert first.sequence_number == 1
    assert second.sequence_number == 1
    assert ledger.count() == 1


def test_invalid_receipt_is_rejected(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )
    tampered = replace(
        build_receipt(),
        receipt_hash="0" * 64,
    )

    with pytest.raises(
        InvalidAuthorityReceiptError,
        match="failed replay verification",
    ):
        ledger.append(tampered)

    assert ledger.count() == 0


def test_records_are_listed_in_sequence_order(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    first_receipt = build_receipt()
    second_receipt = build_receipt(
        contract=ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
        requested_authority=CalculationAuthority.NON_AUTHORITATIVE,
    )

    ledger.append(second_receipt)
    ledger.append(first_receipt)

    records = ledger.list_records()

    assert [
        record.sequence_number
        for record in records
    ] == [1, 2]
    assert records[0].receipt == second_receipt
    assert records[1].receipt == first_receipt


def test_records_can_be_filtered_by_calculation(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    evidence_receipt = build_receipt()
    normalization_receipt = build_receipt(
        contract=ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
        requested_authority=CalculationAuthority.NON_AUTHORITATIVE,
    )

    ledger.append(evidence_receipt)
    ledger.append(normalization_receipt)

    records = ledger.list_records(
        calculation_id="evidence-confidence"
    )

    assert len(records) == 1
    assert records[0].receipt == evidence_receipt


def test_append_many_returns_records(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    receipts = (
        build_receipt(),
        build_receipt(
            contract=ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
            requested_authority=CalculationAuthority.NON_AUTHORITATIVE,
        ),
    )

    records = ledger.append_many(receipts)

    assert len(records) == 2
    assert ledger.count() == 2


def test_verify_all_accepts_valid_ledger(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    ledger.append(build_receipt())

    assert ledger.verify_all() is True


def test_empty_ledger_verifies_vacuously(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    assert ledger.verify_all() is True


def test_record_serialization_contains_sequence_and_receipt(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )

    record = ledger.append(build_receipt())
    serialized = record.to_dict()

    assert serialized["sequence_number"] == 1
    assert serialized["receipt"]["receipt_hash"] == (
        record.receipt.receipt_hash
    )


def test_conflicting_duplicate_hash_is_rejected(tmp_path):
    ledger = ScientificAuthorityReceiptLedger(
        tmp_path / "authority-receipts.db"
    )
    receipt = build_receipt()
    ledger.append(receipt)

    database_path = tmp_path / "authority-receipts.db"

    import sqlite3

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET receipt_json = ?
            WHERE receipt_hash = ?
            """,
            (
                json.dumps({"tampered": True}),
                receipt.receipt_hash,
            ),
        )

    with pytest.raises(
        AuthorityReceiptConflictError,
        match="different content",
    ):
        ledger.append(receipt)
