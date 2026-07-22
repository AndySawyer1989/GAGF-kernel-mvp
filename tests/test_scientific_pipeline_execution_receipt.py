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
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_pipeline_execution_receipt import (
    SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID,
    SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION,
    SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION,
    ScientificPipelineExecutionReceiptBuilder,
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


def incomplete_evidence() -> AuthorityEscalationEvidence:
    return AuthorityEscalationEvidence(
        deterministic_replay_verified=False,
        canonical_input_binding_verified=False,
        calculation_version_frozen=False,
        regression_suite_passed=False,
        validation_report_present=False,
        constitutional_approval_present=False,
    )


def build_pipeline(tmp_path):
    return ScientificAuthorityEvidencePipeline(
        authority_database_path=(
            tmp_path / "authority.db"
        ),
        audit_database_path=(
            tmp_path / "audit.db"
        ),
        checkpoint_database_path=(
            tmp_path / "checkpoint.db"
        ),
    )


def execute_and_build(
    tmp_path,
    *,
    contract=EVIDENCE_CONFIDENCE_CONTRACT,
    requested_authority=CalculationAuthority.ADVISORY,
    evidence=None,
):
    if evidence is None:
        evidence = complete_evidence()

    pipeline = build_pipeline(tmp_path)

    pipeline_result = pipeline.execute(
        contract=contract,
        requested_authority=requested_authority,
        evidence=evidence,
    )

    receipt = ScientificPipelineExecutionReceiptBuilder().build(
        contract=contract,
        requested_authority=requested_authority,
        evidence=evidence,
        pipeline_result=pipeline_result,
    )

    return pipeline_result, receipt


def test_execution_receipt_has_stable_identity():
    assert SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID == (
        "constitutional-scientific-pipeline-execution-receipt"
    )
    assert (
        SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION
        == "0.1.0"
    )
    assert (
        SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_allowed_execution_builds_valid_receipt(tmp_path):
    pipeline_result, receipt = execute_and_build(tmp_path)

    assert receipt.decision_allowed is True
    assert receipt.checkpoint_valid is True
    assert receipt.verify() is True
    assert receipt.authority_receipt_hash == (
        pipeline_result.authority_receipt_hash
    )
    assert receipt.audit_receipt_hash == (
        pipeline_result.audit_receipt_hash
    )
    assert receipt.checkpoint_hash == (
        pipeline_result.checkpoint_hash
    )


def test_denied_execution_builds_valid_receipt(tmp_path):
    _, receipt = execute_and_build(
        tmp_path,
        contract=LEGACY_METRIC_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
    )

    assert receipt.decision_allowed is False
    assert receipt.checkpoint_valid is True
    assert receipt.verify() is True


def test_incomplete_evidence_is_bound_to_receipt(tmp_path):
    _, receipt = execute_and_build(
        tmp_path,
        evidence=incomplete_evidence(),
    )

    assert receipt.decision_allowed is False
    assert receipt.evidence == {
        "deterministic_replay_verified": False,
        "canonical_input_binding_verified": False,
        "calculation_version_frozen": False,
        "regression_suite_passed": False,
        "validation_report_present": False,
        "constitutional_approval_present": False,
    }
    assert receipt.verify() is True


def test_complete_evidence_is_bound_to_receipt(tmp_path):
    _, receipt = execute_and_build(tmp_path)

    assert all(receipt.evidence.values())
    assert receipt.verify() is True


def test_receipt_preserves_all_sequence_numbers(tmp_path):
    pipeline_result, receipt = execute_and_build(tmp_path)

    assert receipt.authority_receipt_sequence == (
        pipeline_result.authority_receipt_sequence
    )
    assert receipt.audit_receipt_sequence == (
        pipeline_result.audit_receipt_sequence
    )
    assert receipt.checkpoint_sequence == (
        pipeline_result.checkpoint_sequence
    )


def test_identical_execution_inputs_produce_identical_receipts(
    tmp_path,
):
    pipeline = build_pipeline(tmp_path)
    evidence = complete_evidence()

    first_result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
    )
    second_result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
    )

    builder = ScientificPipelineExecutionReceiptBuilder()

    first_receipt = builder.build(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
        pipeline_result=first_result,
    )
    second_receipt = builder.build(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
        pipeline_result=second_result,
    )

    assert first_receipt == second_receipt
    assert (
        first_receipt.receipt_hash
        == second_receipt.receipt_hash
    )


def test_different_authority_request_changes_receipt_hash(
    tmp_path,
):
    _, advisory_receipt = execute_and_build(
        tmp_path / "advisory",
        requested_authority=CalculationAuthority.ADVISORY,
    )
    _, authoritative_receipt = execute_and_build(
        tmp_path / "authoritative",
        requested_authority=(
            CalculationAuthority.AUTHORITATIVE
        ),
    )

    assert (
        advisory_receipt.receipt_hash
        != authoritative_receipt.receipt_hash
    )


def test_different_evidence_changes_receipt_hash(tmp_path):
    _, complete_receipt = execute_and_build(
        tmp_path / "complete",
        evidence=complete_evidence(),
    )
    _, incomplete_receipt = execute_and_build(
        tmp_path / "incomplete",
        evidence=incomplete_evidence(),
    )

    assert (
        complete_receipt.receipt_hash
        != incomplete_receipt.receipt_hash
    )


def test_receipt_hash_is_sha256_hex(tmp_path):
    _, receipt = execute_and_build(tmp_path)

    assert len(receipt.receipt_hash) == 64
    int(receipt.receipt_hash, 16)


def test_receipt_serialization_contains_execution_proof(
    tmp_path,
):
    _, receipt = execute_and_build(tmp_path)

    serialized = receipt.to_dict()

    assert serialized["receipt_hash"] == receipt.receipt_hash
    assert serialized["receipt_id"] == (
        "constitutional-scientific-pipeline-execution-receipt"
    )
    assert serialized["authority_receipt_hash"] == (
        receipt.authority_receipt_hash
    )
    assert serialized["audit_receipt_hash"] == (
        receipt.audit_receipt_hash
    )
    assert serialized["checkpoint_hash"] == (
        receipt.checkpoint_hash
    )


def test_tampered_decision_fails_verification(tmp_path):
    _, receipt = execute_and_build(tmp_path)

    tampered = replace(
        receipt,
        decision_allowed=False,
    )

    assert tampered.verify() is False


def test_tampered_evidence_fails_verification(tmp_path):
    _, receipt = execute_and_build(tmp_path)

    changed_evidence = dict(receipt.evidence)
    changed_evidence[
        "constitutional_approval_present"
    ] = False

    tampered = replace(
        receipt,
        evidence=changed_evidence,
    )

    assert tampered.verify() is False


def test_tampered_checkpoint_hash_fails_verification(tmp_path):
    _, receipt = execute_and_build(tmp_path)

    tampered = replace(
        receipt,
        checkpoint_hash="0" * 64,
    )

    assert tampered.verify() is False


def test_receipt_is_immutable(tmp_path):
    _, receipt = execute_and_build(tmp_path)

    with pytest.raises(FrozenInstanceError):
        receipt.receipt_hash = "changed"


def test_contract_identity_mismatch_is_rejected(tmp_path):
    pipeline = build_pipeline(tmp_path)
    evidence = complete_evidence()

    pipeline_result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
    )

    with pytest.raises(
        ValueError,
        match="calculation identity",
    ):
        ScientificPipelineExecutionReceiptBuilder().build(
            contract=LEGACY_METRIC_CONFIDENCE_CONTRACT,
            requested_authority=CalculationAuthority.ADVISORY,
            evidence=evidence,
            pipeline_result=pipeline_result,
        )


def test_requested_authority_mismatch_is_rejected(tmp_path):
    pipeline = build_pipeline(tmp_path)
    evidence = complete_evidence()

    pipeline_result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
    )

    with pytest.raises(
        ValueError,
        match="requested authority",
    ):
        ScientificPipelineExecutionReceiptBuilder().build(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=(
                CalculationAuthority.AUTHORITATIVE
            ),
            evidence=evidence,
            pipeline_result=pipeline_result,
        )
