from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.contracts.constitutional_sequencer import (
    CandidateStatus,
    CanonicalEvidenceCandidate,
    CommitStatus,
    ConstitutionalCommitRequest,
    ConstitutionalCommitResult,
    ReplayStatus,
    ReplayVerificationResult,
    SequenceReceipt,
    SequencerBatchRequest,
    SequencerBatchResult,
    SequencerBatchStatus,
)


UTC = timezone.utc
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def utc_time(hour: int = 12, minute: int = 0) -> datetime:
    return datetime(2026, 7, 10, hour, minute, tzinfo=UTC)


def make_candidate() -> CanonicalEvidenceCandidate:
    return CanonicalEvidenceCandidate(
        candidate_id=uuid4(),
        tenant_id="tenant-a",
        lifecycle_instance_id="lifecycle-001",
        source_event_id="source-event-001",
        source_identity="github-connector",
        source_sequence=10,
        observed_at=utc_time(12, 0),
        received_at=utc_time(12, 1),
        canonical_payload={
            "event_type": "APPROVAL_REQUIRED",
            "work_item_id": "work-item-001",
        },
        candidate_hash=HASH_A,
        schema_version="constraint-event-1.0",
        canonicalizer_version="canonicalizer-1.0",
        canonicalizer_identity="canonicalizer-worker-01",
        status=CandidateStatus.PREPARED,
        created_at=utc_time(12, 2),
    )


def make_receipt(candidate: CanonicalEvidenceCandidate) -> SequenceReceipt:
    return SequenceReceipt(
        receipt_id=uuid4(),
        candidate_id=candidate.candidate_id,
        candidate_hash=candidate.candidate_hash,
        tenant_id=candidate.tenant_id,
        lifecycle_instance_id=candidate.lifecycle_instance_id,
        partition_key="tenant-a/lifecycle-001",
        assigned_sequence=1,
        batch_id=uuid4(),
        sequencer_epoch=4,
        sequencer_identity="constitutional-sequencer-01",
        ordering_policy_version="OPV-1.0",
        previous_receipt_hash=HASH_B,
        receipt_hash=HASH_C,
        issued_at=utc_time(12, 3),
    )


def test_canonical_evidence_candidate_accepts_valid_contract():
    candidate = make_candidate()

    assert candidate.tenant_id == "tenant-a"
    assert candidate.status == CandidateStatus.PREPARED
    assert candidate.candidate_hash == HASH_A
    assert candidate.observed_at.tzinfo is not None


def test_canonical_evidence_candidate_is_immutable():
    candidate = make_candidate()

    with pytest.raises(ValidationError):
        candidate.status = CandidateStatus.SEQUENCED


def test_candidate_rejects_invalid_sha256_hash():
    with pytest.raises(
        ValidationError,
        match="64-character lowercase hexadecimal SHA-256",
    ):
        CanonicalEvidenceCandidate(
            candidate_id=uuid4(),
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            source_event_id="source-event-001",
            source_identity="github-connector",
            observed_at=utc_time(12, 0),
            received_at=utc_time(12, 1),
            canonical_payload={"event_type": "APPROVAL_REQUIRED"},
            candidate_hash="not-a-valid-hash",
            schema_version="constraint-event-1.0",
            canonicalizer_version="canonicalizer-1.0",
            canonicalizer_identity="canonicalizer-worker-01",
            created_at=utc_time(12, 2),
        )


def test_candidate_rejects_naive_timestamp():
    with pytest.raises(
        ValidationError,
        match="observed_at must be timezone-aware",
    ):
        CanonicalEvidenceCandidate(
            candidate_id=uuid4(),
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            source_event_id="source-event-001",
            source_identity="github-connector",
            observed_at=datetime(2026, 7, 10, 12, 0),
            received_at=utc_time(12, 1),
            canonical_payload={"event_type": "APPROVAL_REQUIRED"},
            candidate_hash=HASH_A,
            schema_version="constraint-event-1.0",
            canonicalizer_version="canonicalizer-1.0",
            canonicalizer_identity="canonicalizer-worker-01",
            created_at=utc_time(12, 2),
        )


def test_candidate_rejects_impossible_timeline():
    with pytest.raises(
        ValidationError,
        match="received_at must not occur before observed_at",
    ):
        CanonicalEvidenceCandidate(
            candidate_id=uuid4(),
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            source_event_id="source-event-001",
            source_identity="github-connector",
            observed_at=utc_time(12, 2),
            received_at=utc_time(12, 1),
            canonical_payload={"event_type": "APPROVAL_REQUIRED"},
            candidate_hash=HASH_A,
            schema_version="constraint-event-1.0",
            canonicalizer_version="canonicalizer-1.0",
            canonicalizer_identity="canonicalizer-worker-01",
            created_at=utc_time(12, 3),
        )


def test_sequence_receipt_accepts_epoch_fenced_contract():
    candidate = make_candidate()
    receipt = make_receipt(candidate)

    assert receipt.candidate_id == candidate.candidate_id
    assert receipt.sequencer_epoch == 4
    assert receipt.ordering_policy_version == "OPV-1.0"
    assert receipt.assigned_sequence == 1


def test_sequence_receipt_rejects_zero_epoch():
    candidate = make_candidate()

    with pytest.raises(ValidationError):
        SequenceReceipt(
            receipt_id=uuid4(),
            candidate_id=candidate.candidate_id,
            candidate_hash=candidate.candidate_hash,
            tenant_id=candidate.tenant_id,
            lifecycle_instance_id=candidate.lifecycle_instance_id,
            partition_key="tenant-a/lifecycle-001",
            assigned_sequence=1,
            batch_id=uuid4(),
            sequencer_epoch=0,
            sequencer_identity="constitutional-sequencer-01",
            ordering_policy_version="OPV-1.0",
            previous_receipt_hash=HASH_B,
            receipt_hash=HASH_C,
            issued_at=utc_time(12, 3),
        )


def test_batch_request_rejects_duplicate_candidate_ids():
    candidate_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="candidate_ids must not contain duplicates",
    ):
        SequencerBatchRequest(
            batch_id=uuid4(),
            partition_key="tenant-a/lifecycle-001",
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            candidate_ids=(candidate_id, candidate_id),
            expected_epoch=4,
            ordering_policy_version="OPV-1.0",
            requested_by="canonicalization-service",
            requested_at=utc_time(12, 4),
        )


def test_ordered_batch_requires_receipts():
    with pytest.raises(
        ValidationError,
        match="ordered or accepted batches must contain sequence receipts",
    ):
        SequencerBatchResult(
            batch_id=uuid4(),
            partition_key="tenant-a/lifecycle-001",
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            sequencer_epoch=4,
            ordering_policy_version="OPV-1.0",
            sequencer_identity="constitutional-sequencer-01",
            receipt_ids=(),
            status=SequencerBatchStatus.ORDERED,
            started_at=utc_time(12, 4),
            completed_at=utc_time(12, 5),
        )


def test_rejected_batch_requires_rejection_code():
    with pytest.raises(
        ValidationError,
        match="rejected batches must contain at least one rejection code",
    ):
        SequencerBatchResult(
            batch_id=uuid4(),
            partition_key="tenant-a/lifecycle-001",
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            sequencer_epoch=4,
            ordering_policy_version="OPV-1.0",
            sequencer_identity="constitutional-sequencer-01",
            status=SequencerBatchStatus.REJECTED,
            started_at=utc_time(12, 4),
            completed_at=utc_time(12, 5),
        )


def test_commit_request_requires_one_receipt_per_candidate():
    with pytest.raises(
        ValidationError,
        match="must have the same number of entries",
    ):
        ConstitutionalCommitRequest(
            commit_request_id=uuid4(),
            batch_id=uuid4(),
            tenant_id="tenant-a",
            lifecycle_instance_id="lifecycle-001",
            partition_key="tenant-a/lifecycle-001",
            candidate_ids=(uuid4(), uuid4()),
            receipt_ids=(uuid4(),),
            sequencer_epoch=4,
            ordering_policy_version="OPV-1.0",
            policy_version="GPL-0.1",
            kernel_version="3.4",
            prior_state_hash=HASH_A,
            submitted_by="constitutional-sequencer-01",
            submitted_at=utc_time(12, 6),
        )


def test_accepted_commit_requires_authoritative_outputs():
    with pytest.raises(
        ValidationError,
        match="accepted commits require",
    ):
        ConstitutionalCommitResult(
            commit_request_id=uuid4(),
            batch_id=uuid4(),
            status=CommitStatus.ACCEPTED,
        )


def test_rejected_commit_cannot_contain_authoritative_outputs():
    with pytest.raises(
        ValidationError,
        match="rejected commits must not contain authoritative outputs",
    ):
        ConstitutionalCommitResult(
            commit_request_id=uuid4(),
            batch_id=uuid4(),
            status=CommitStatus.REJECTED,
            decision_id=uuid4(),
            rejection_codes=("STALE_EPOCH",),
        )


def test_valid_accepted_commit_contract():
    result = ConstitutionalCommitResult(
        commit_request_id=uuid4(),
        batch_id=uuid4(),
        status=CommitStatus.ACCEPTED,
        decision_id=uuid4(),
        ledger_offset=144,
        decision_hash=HASH_D,
        resulting_state_hash=HASH_E,
        committed_at=utc_time(12, 7),
    )

    assert result.status == CommitStatus.ACCEPTED
    assert result.ledger_offset == 144
    assert result.rejection_codes == ()


def test_equal_replay_requires_matching_hashes():
    result = ReplayVerificationResult(
        replay_id=uuid4(),
        batch_id=uuid4(),
        decision_id=uuid4(),
        committed_decision_hash=HASH_D,
        replayed_decision_hash=HASH_D,
        committed_state_hash=HASH_E,
        replayed_state_hash=HASH_E,
        ordering_policy_version="OPV-1.0",
        policy_version="GPL-0.1",
        kernel_version="3.4",
        replay_status=ReplayStatus.EQUAL,
        equality=True,
        replay_started_at=utc_time(12, 8),
        replay_completed_at=utc_time(12, 9),
    )

    assert result.equality is True
    assert result.replay_status == ReplayStatus.EQUAL


def test_equal_replay_rejects_mismatched_hash():
    with pytest.raises(
        ValidationError,
        match="matching decision and state hashes",
    ):
        ReplayVerificationResult(
            replay_id=uuid4(),
            batch_id=uuid4(),
            decision_id=uuid4(),
            committed_decision_hash=HASH_D,
            replayed_decision_hash=HASH_A,
            committed_state_hash=HASH_E,
            replayed_state_hash=HASH_E,
            ordering_policy_version="OPV-1.0",
            policy_version="GPL-0.1",
            kernel_version="3.4",
            replay_status=ReplayStatus.EQUAL,
            equality=True,
            replay_started_at=utc_time(12, 8),
            replay_completed_at=utc_time(12, 9),
        )


def test_divergent_replay_requires_divergence_code():
    with pytest.raises(
        ValidationError,
        match="requires divergence codes",
    ):
        ReplayVerificationResult(
            replay_id=uuid4(),
            batch_id=uuid4(),
            decision_id=uuid4(),
            committed_decision_hash=HASH_D,
            replayed_decision_hash=HASH_A,
            committed_state_hash=HASH_E,
            replayed_state_hash=HASH_B,
            ordering_policy_version="OPV-1.0",
            policy_version="GPL-0.1",
            kernel_version="3.4",
            replay_status=ReplayStatus.DIVERGENT,
            equality=False,
            replay_started_at=utc_time(12, 8),
            replay_completed_at=utc_time(12, 9),
        )

