from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.scientific_authority_audit_receipt_ledger import (
    ScientificAuthorityAuditReceiptLedger,
)
from backend.app.gagf.scientific_authority_evidence_pipeline import (
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID,
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION,
    ScientificAuthorityEvidencePipeline,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_authority_receipt_ledger import (
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    ScientificEvidenceCheckpointLedger,
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
            tmp_path
            / "authority"
            / "authority.db"
        ),
        audit_database_path=(
            tmp_path
            / "audit"
            / "audit.db"
        ),
        checkpoint_database_path=(
            tmp_path
            / "checkpoint"
            / "checkpoint.db"
        ),
    )


def test_pipeline_has_stable_identity():
    assert SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID == (
        "constitutional-scientific-authority-evidence-pipeline"
    )
    assert (
        SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION
        == "0.1.0"
    )


def test_allowed_authority_request_completes_pipeline(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert result.decision_allowed is True
    assert result.authority_receipt_sequence == 1
    assert result.audit_receipt_sequence == 1
    assert result.checkpoint_sequence == 1
    assert result.authority_ledger_audit_valid is True
    assert result.checkpoint_valid is True


def test_denied_authority_request_is_still_persisted(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=LEGACY_METRIC_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert result.decision_allowed is False
    assert result.authority_receipt_sequence == 1
    assert result.audit_receipt_sequence == 1
    assert result.checkpoint_sequence == 1
    assert result.checkpoint_valid is True


def test_incomplete_evidence_denial_completes_pipeline(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=incomplete_evidence(),
    )

    assert result.decision_allowed is False
    assert result.authority_ledger_audit_valid is True
    assert result.checkpoint_valid is True


def test_pipeline_creates_parent_directories(tmp_path):
    pipeline = build_pipeline(tmp_path)

    assert pipeline.authority_database_path.parent.is_dir()
    assert pipeline.audit_database_path.parent.is_dir()
    assert pipeline.checkpoint_database_path.parent.is_dir()


def test_pipeline_persists_all_three_evidence_layers(tmp_path):
    pipeline = build_pipeline(tmp_path)

    pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    authority_ledger = ScientificAuthorityReceiptLedger(
        pipeline.authority_database_path
    )
    audit_ledger = ScientificAuthorityAuditReceiptLedger(
        pipeline.audit_database_path
    )
    checkpoint_ledger = ScientificEvidenceCheckpointLedger(
        pipeline.checkpoint_database_path
    )

    assert authority_ledger.count() == 1
    assert audit_ledger.count() == 1
    assert checkpoint_ledger.count() == 1


def test_identical_execution_is_idempotent(tmp_path):
    pipeline = build_pipeline(tmp_path)

    first = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    second = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert first == second
    assert first.authority_receipt_sequence == 1
    assert first.audit_receipt_sequence == 1
    assert first.checkpoint_sequence == 1

    assert pipeline.authority_ledger.count() == 1
    assert pipeline.audit_ledger.count() == 1
    assert pipeline.checkpoint_ledger.count() == 1


def test_distinct_decisions_create_distinct_history(tmp_path):
    pipeline = build_pipeline(tmp_path)

    first = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    second = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.AUTHORITATIVE,
        evidence=complete_evidence(),
    )

    assert (
        first.authority_receipt_hash
        != second.authority_receipt_hash
    )
    assert second.authority_receipt_sequence == 2
    assert second.audit_receipt_sequence == 2
    assert second.checkpoint_sequence == 2

    assert pipeline.authority_ledger.count() == 2
    assert pipeline.audit_ledger.count() == 2
    assert pipeline.checkpoint_ledger.count() == 2


def test_result_contains_stable_contract_identity(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert result.calculation_id == (
        EVIDENCE_CONFIDENCE_CONTRACT.calculation_id
    )
    assert result.calculation_version == (
        EVIDENCE_CONFIDENCE_CONTRACT.calculation_version
    )
    assert result.requested_authority == (
        CalculationAuthority.ADVISORY.value
    )


def test_result_hashes_are_sha256_hex(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    for value in (
        result.authority_receipt_hash,
        result.audit_receipt_hash,
        result.checkpoint_hash,
    ):
        assert len(value) == 64
        int(value, 16)


def test_result_serialization_is_stable(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    serialized = result.to_dict()

    assert serialized["pipeline_id"] == (
        "constitutional-scientific-authority-evidence-pipeline"
    )
    assert serialized["pipeline_version"] == "0.1.0"
    assert serialized["decision_allowed"] is True
    assert serialized["checkpoint_valid"] is True


def test_result_is_immutable(tmp_path):
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    with pytest.raises(FrozenInstanceError):
        result.checkpoint_valid = False

