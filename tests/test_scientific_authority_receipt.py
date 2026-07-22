from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AUTHORITY_POLICY_ID,
    AUTHORITY_POLICY_VERSION,
    AUTHORITY_RECEIPT_SCHEMA_VERSION,
    AuthorityDecisionReceipt,
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
    canonical_json,
    sha256_hex,
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


def test_receipt_schema_has_stable_identity():
    assert AUTHORITY_POLICY_ID == "scientific-authority-escalation"
    assert AUTHORITY_POLICY_VERSION == "0.1.0"
    assert AUTHORITY_RECEIPT_SCHEMA_VERSION == "1.0.0"


def test_canonical_json_is_key_order_independent():
    first = canonical_json({"b": 2, "a": 1})
    second = canonical_json({"a": 1, "b": 2})

    assert first == second
    assert first == '{"a":1,"b":2}'


def test_sha256_hex_is_deterministic():
    first = sha256_hex("authority-decision")
    second = sha256_hex("authority-decision")

    assert first == second
    assert len(first) == 64


def test_evidence_serialization_is_deterministic():
    evidence = complete_evidence()

    assert evidence.to_dict() == {
        "deterministic_replay_verified": True,
        "canonical_input_binding_verified": True,
        "calculation_version_frozen": True,
        "regression_suite_passed": True,
        "validation_report_present": True,
        "constitutional_approval_present": True,
    }


def test_evaluate_with_receipt_returns_matching_decision():
    guard = ScientificAuthorityEscalationGuard()

    decision, receipt = guard.evaluate_with_receipt(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert decision.allowed is True
    assert receipt.decision == decision.to_dict()


def test_receipt_contains_contract_and_policy_identity():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )

    assert receipt.policy_id == "scientific-authority-escalation"
    assert receipt.policy_version == "0.1.0"
    assert receipt.calculation_id == "evidence-confidence"
    assert receipt.calculation_version == "0.1.0-diagnostics"


def test_receipt_hash_is_valid():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )

    assert receipt.verify() is True
    assert len(receipt.receipt_hash) == 64


def test_identical_inputs_produce_identical_receipts():
    guard = ScientificAuthorityEscalationGuard()

    first_decision, first_receipt = guard.evaluate_with_receipt(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    second_decision, second_receipt = guard.evaluate_with_receipt(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert first_decision == second_decision
    assert first_receipt == second_receipt
    assert first_receipt.receipt_hash == second_receipt.receipt_hash


def test_changed_evidence_changes_receipt_hash():
    guard = ScientificAuthorityEscalationGuard()

    _, first_receipt = guard.evaluate_with_receipt(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    changed_evidence = AuthorityEscalationEvidence(
        deterministic_replay_verified=False,
        canonical_input_binding_verified=True,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=True,
    )

    _, second_receipt = guard.evaluate_with_receipt(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=changed_evidence,
    )

    assert first_receipt.receipt_hash != second_receipt.receipt_hash


def test_tampered_receipt_fails_verification():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )

    tampered = replace(
        receipt,
        requested_authority="AUTHORITATIVE",
    )

    assert tampered.verify() is False


def test_receipt_to_dict_includes_hash():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )

    serialized = receipt.to_dict()

    assert serialized["receipt_hash"] == receipt.receipt_hash
    assert serialized["decision"]["allowed"] is True


def test_receipt_is_immutable():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )

    with pytest.raises(FrozenInstanceError):
        receipt.receipt_hash = "changed"


def test_manual_receipt_with_incorrect_hash_is_rejected():
    receipt = AuthorityDecisionReceipt(
        receipt_schema_version="1.0.0",
        policy_id="scientific-authority-escalation",
        policy_version="0.1.0",
        calculation_id="evidence-confidence",
        calculation_version="0.1.0-diagnostics",
        current_authority="NON_AUTHORITATIVE",
        requested_authority="ADVISORY",
        evidence=complete_evidence().to_dict(),
        decision={"allowed": True},
        receipt_hash="0" * 64,
    )

    assert receipt.verify() is False
