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
from backend.app.gagf.scientific_evidence_checkpoint_replay_verifier import (
    SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_ID,
    SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_VERSION,
    ScientificEvidenceCheckpointReplayVerifier,
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


def verify(
    checkpoint,
    authority_database,
    audit_database,
):
    return ScientificEvidenceCheckpointReplayVerifier().verify(
        checkpoint=checkpoint,
        authority_database_path=authority_database,
        audit_database_path=audit_database,
    )


def test_verifier_has_stable_identity():
    assert SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_ID == (
        "scientific-evidence-checkpoint-replay-verifier"
    )
    assert (
        SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_VERSION
        == "0.1.0"
    )


def test_unchanged_ledgers_pass_replay(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )

    result = verify(
        checkpoint,
        authority_database,
        audit_database,
    )

    assert result.valid is True
    assert result.errors == ()
    assert all(result.checks.values())
    assert result.original_checkpoint_hash == (
        result.replayed_checkpoint_hash
    )


def test_result_is_immutable(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )

    result = verify(
        checkpoint,
        authority_database,
        audit_database,
    )

    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_result_serialization_is_stable(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )

    result = verify(
        checkpoint,
        authority_database,
        audit_database,
    )
    serialized = result.to_dict()

    assert serialized["valid"] is True
    assert serialized["verifier_id"] == (
        "scientific-evidence-checkpoint-replay-verifier"
    )
    assert serialized["verifier_version"] == "0.1.0"
    assert serialized["errors"] == []


def test_tampered_checkpoint_hash_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )
    tampered = replace(
        checkpoint,
        checkpoint_hash="0" * 64,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert result.checks["checkpoint_hash_valid"] is False
    assert (
        result.checks["checkpoint_hash_matches_replay"]
        is False
    )


def test_unsupported_schema_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )
    tampered = replace(
        checkpoint,
        checkpoint_schema_version="9.9.9",
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["checkpoint_schema_supported"]
        is False
    )


def test_unsupported_identity_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )
    tampered = replace(
        checkpoint,
        checkpoint_id="different-checkpoint",
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["checkpoint_identity_supported"]
        is False
    )


def test_unsupported_version_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )
    tampered = replace(
        checkpoint,
        checkpoint_version="9.9.9",
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["checkpoint_version_supported"]
        is False
    )


def test_authority_ledger_change_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
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

    result = verify(
        checkpoint,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["authority_audit_matches_replay"]
        is False
    )
    assert (
        result.checks["checkpoint_validity_matches_replay"]
        is False
    )
    assert (
        result.checks["checkpoint_hash_matches_replay"]
        is False
    )


def test_audit_ledger_change_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
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

    result = verify(
        checkpoint,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["audit_ledger_audit_matches_replay"]
        is False
    )
    assert (
        result.checks["checkpoint_validity_matches_replay"]
        is False
    )
    assert (
        result.checks["checkpoint_hash_matches_replay"]
        is False
    )


def test_different_authority_database_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "original")
    )
    other_authority, _, _ = build_system(
        tmp_path / "other"
    )

    result = verify(
        checkpoint,
        other_authority,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["authority_ledger_identity_matches"]
        is False
    )


def test_different_audit_database_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path / "original")
    )
    _, other_audit, _ = build_system(
        tmp_path / "other"
    )

    result = verify(
        checkpoint,
        authority_database,
        other_audit,
    )

    assert result.valid is False
    assert (
        result.checks["audit_ledger_identity_matches"]
        is False
    )


def test_tampered_authority_audit_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )

    changed_audit = dict(checkpoint.authority_audit)
    changed_audit["record_count"] = 999

    tampered = replace(
        checkpoint,
        authority_audit=changed_audit,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["checkpoint_hash_valid"]
        is False
    )
    assert (
        result.checks["authority_audit_matches_replay"]
        is False
    )


def test_tampered_audit_ledger_audit_is_detected(tmp_path):
    authority_database, audit_database, checkpoint = (
        build_system(tmp_path)
    )

    changed_audit = dict(checkpoint.audit_ledger_audit)
    changed_audit["record_count"] = 999

    tampered = replace(
        checkpoint,
        audit_ledger_audit=changed_audit,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
    )

    assert result.valid is False
    assert (
        result.checks["checkpoint_hash_valid"]
        is False
    )
    assert (
        result.checks["audit_ledger_audit_matches_replay"]
        is False
    )
