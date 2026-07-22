import sqlite3
from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authority_evidence_pipeline import (
    ScientificAuthorityEvidencePipeline,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_pipeline_execution_receipt import (
    ScientificPipelineExecutionReceiptBuilder,
)
from backend.app.gagf.scientific_pipeline_execution_replay_verifier import (
    SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_ID,
    SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_VERSION,
    ScientificPipelineExecutionReplayVerifier,
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


def build_system(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)

    authority_database = tmp_path / "authority.db"
    audit_database = tmp_path / "audit.db"
    checkpoint_database = tmp_path / "checkpoint.db"

    pipeline = ScientificAuthorityEvidencePipeline(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
        checkpoint_database_path=checkpoint_database,
    )
    evidence = complete_evidence()

    pipeline_result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
    )

    receipt = ScientificPipelineExecutionReceiptBuilder().build(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
        pipeline_result=pipeline_result,
    )

    return (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    )


def verify(
    receipt,
    authority_database,
    audit_database,
    checkpoint_database,
):
    return ScientificPipelineExecutionReplayVerifier().verify(
        receipt=receipt,
        authority_database_path=authority_database,
        audit_database_path=audit_database,
        checkpoint_database_path=checkpoint_database,
    )


def test_verifier_has_stable_identity():
    assert SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_ID == (
        "scientific-pipeline-execution-replay-verifier"
    )
    assert (
        SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_VERSION
        == "0.1.0"
    )


def test_complete_execution_passes_replay(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is True
    assert result.errors == ()
    assert all(result.checks.values())


def test_result_is_immutable(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_result_serialization_is_stable(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )
    serialized = result.to_dict()

    assert serialized["valid"] is True
    assert serialized["verifier_id"] == (
        "scientific-pipeline-execution-replay-verifier"
    )
    assert serialized["verifier_version"] == "0.1.0"
    assert serialized["errors"] == []


def test_tampered_execution_receipt_hash_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        receipt_hash="0" * 64,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["execution_receipt_hash_valid"]
        is False
    )


def test_unsupported_receipt_schema_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        receipt_schema_version="9.9.9",
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks[
            "execution_receipt_schema_supported"
        ]
        is False
    )


def test_unsupported_receipt_identity_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        receipt_id="unsupported-receipt",
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks[
            "execution_receipt_identity_supported"
        ]
        is False
    )


def test_unknown_contract_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        calculation_id="unknown-calculation",
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["calculation_contract_present"]
        is False
    )


def test_missing_authority_receipt_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    with sqlite3.connect(authority_database) as connection:
        connection.execute(
            """
            DELETE FROM scientific_authority_receipts
            WHERE receipt_hash = ?
            """,
            (receipt.authority_receipt_hash,),
        )

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["authority_receipt_present"]
        is False
    )


def test_authority_sequence_mismatch_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        authority_receipt_sequence=999,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks[
            "authority_receipt_sequence_matches"
        ]
        is False
    )


def test_decision_mismatch_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        decision_allowed=not receipt.decision_allowed,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["authority_decision_matches"]
        is False
    )


def test_evidence_mismatch_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    changed_evidence = dict(receipt.evidence)
    changed_evidence[
        "constitutional_approval_present"
    ] = False

    tampered = replace(
        receipt,
        evidence=changed_evidence,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["authority_evidence_matches"]
        is False
    )


def test_missing_audit_receipt_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    with sqlite3.connect(audit_database) as connection:
        connection.execute(
            """
            DELETE FROM scientific_authority_audit_receipts
            WHERE receipt_hash = ?
            """,
            (receipt.audit_receipt_hash,),
        )

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert result.checks["audit_receipt_present"] is False


def test_missing_checkpoint_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    with sqlite3.connect(checkpoint_database) as connection:
        connection.execute(
            """
            DELETE FROM scientific_evidence_checkpoints
            WHERE checkpoint_hash = ?
            """,
            (receipt.checkpoint_hash,),
        )

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert result.checks["checkpoint_present"] is False


def test_authority_ledger_change_invalidates_replay(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    with sqlite3.connect(authority_database) as connection:
        connection.execute(
            """
            UPDATE scientific_authority_receipts
            SET policy_version = ?
            WHERE receipt_hash = ?
            """,
            (
                "9.9.9",
                receipt.authority_receipt_hash,
            ),
        )

    result = verify(
        receipt,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["authority_ledger_audit_matches"]
        is False
        or result.checks[
            "audit_receipt_matches_current_audit"
        ]
        is False
        or result.checks["checkpoint_replay_valid"]
        is False
    )


def test_checkpoint_sequence_mismatch_is_detected(tmp_path):
    (
        authority_database,
        audit_database,
        checkpoint_database,
        receipt,
    ) = build_system(tmp_path)

    tampered = replace(
        receipt,
        checkpoint_sequence=999,
    )

    result = verify(
        tampered,
        authority_database,
        audit_database,
        checkpoint_database,
    )

    assert result.valid is False
    assert (
        result.checks["checkpoint_sequence_matches"]
        is False
    )
