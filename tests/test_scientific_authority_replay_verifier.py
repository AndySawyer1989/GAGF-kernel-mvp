from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AUTHORITY_POLICY_ID,
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_authority_replay_verifier import (
    REPLAY_VERIFIER_ID,
    REPLAY_VERIFIER_VERSION,
    ScientificAuthorityReceiptReplayVerifier,
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


def valid_receipt():
    _, receipt = (
        ScientificAuthorityEscalationGuard()
        .evaluate_with_receipt(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=complete_evidence(),
        )
    )
    return receipt


def test_replay_verifier_has_stable_identity():
    assert (
        REPLAY_VERIFIER_ID
        == "scientific-authority-replay-verifier"
    )
    assert REPLAY_VERIFIER_VERSION == "0.1.0"


def test_valid_receipt_passes_replay_verification():
    result = ScientificAuthorityReceiptReplayVerifier().verify(
        valid_receipt()
    )

    assert result.valid is True
    assert result.errors == ()
    assert all(result.checks.values())


def test_replay_produces_same_receipt_hash():
    receipt = valid_receipt()

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.receipt_hash == receipt.receipt_hash
    assert result.replayed_receipt_hash == receipt.receipt_hash


def test_result_serialization_is_stable():
    result = ScientificAuthorityReceiptReplayVerifier().verify(
        valid_receipt()
    )

    serialized = result.to_dict()

    assert serialized["valid"] is True
    assert serialized["verifier_id"] == (
        "scientific-authority-replay-verifier"
    )
    assert serialized["verifier_version"] == "0.1.0"
    assert serialized["errors"] == []


def test_result_is_immutable():
    result = ScientificAuthorityReceiptReplayVerifier().verify(
        valid_receipt()
    )

    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_tampered_hash_fails_replay_verification():
    receipt = replace(
        valid_receipt(),
        receipt_hash="0" * 64,
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["receipt_hash_valid"] is False
    assert "Receipt hash verification failed." in result.errors


def test_unsupported_schema_fails_verification():
    receipt = replace(
        valid_receipt(),
        receipt_schema_version="99.0.0",
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["receipt_schema_supported"] is False


def test_unsupported_policy_fails_verification():
    receipt = replace(
        valid_receipt(),
        policy_id="unknown-policy",
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["policy_identity_supported"] is False
    assert receipt.policy_id != AUTHORITY_POLICY_ID


def test_unknown_calculation_fails_verification():
    receipt = replace(
        valid_receipt(),
        calculation_id="unknown-calculation",
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["calculation_contract_found"] is False
    assert result.replayed_receipt_hash is None


def test_calculation_version_drift_fails_verification():
    receipt = replace(
        valid_receipt(),
        calculation_version="9.9.9",
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["calculation_version_matches"] is False


def test_authority_drift_fails_verification():
    receipt = replace(
        valid_receipt(),
        current_authority="AUTHORITATIVE",
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["current_authority_matches"] is False


def test_invalid_requested_authority_fails_verification():
    receipt = replace(
        valid_receipt(),
        requested_authority="SUPER_AUTHORITY",
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["requested_authority_valid"] is False
    assert result.replayed_receipt_hash is None


def test_invalid_evidence_schema_fails_verification():
    receipt = replace(
        valid_receipt(),
        evidence={
            "deterministic_replay_verified": True,
        },
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["evidence_valid"] is False
    assert result.replayed_receipt_hash is None


def test_non_boolean_evidence_fails_verification():
    evidence = complete_evidence().to_dict()
    evidence["regression_suite_passed"] = "yes"

    receipt = replace(
        valid_receipt(),
        evidence=evidence,
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["evidence_valid"] is False


def test_changed_decision_fails_replay_verification():
    receipt = valid_receipt()
    changed_decision = dict(receipt.decision)
    changed_decision["allowed"] = False

    receipt = replace(
        receipt,
        decision=changed_decision,
    )

    result = ScientificAuthorityReceiptReplayVerifier().verify(
        receipt
    )

    assert result.valid is False
    assert result.checks["decision_matches_replay"] is False
