from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from backend.app.contracts.constitutional_sequencer import (
    CandidateStatus,
)
from backend.app.services.canonical_evidence_service import (
    CanonicalEvidenceService,
)
from backend.app.services.constitutional_sequencer_service import (
    GENESIS_RECEIPT_HASH,
    CandidateIntegrityError,
    CandidateStatusError,
    ConstitutionalSequencerError,
    ConstitutionalSequencerService,
    DuplicateCandidateError,
    EmptySequencerBatchError,
    ReceiptChainError,
    ReceiptIntegrityError,
    SequencerPartitionMismatchError,
    UnsupportedOrderingPolicyError,
)


UTC = timezone.utc
ISSUED_AT = datetime(
    2026,
    7,
    10,
    18,
    0,
    tzinfo=UTC,
)


def make_candidate(
    *,
    candidate_id: UUID | None = None,
    tenant_id: str = "tenant-a",
    lifecycle_instance_id: str = "lifecycle-001",
    source_event_id: str = "event-001",
    source_sequence: int | None = 1,
    observed_minute: int = 0,
    event_type: str = "APPROVAL_REQUIRED",
):
    return CanonicalEvidenceService.create_candidate(
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        lifecycle_instance_id=lifecycle_instance_id,
        source_event_id=source_event_id,
        source_identity="github-connector",
        source_sequence=source_sequence,
        observed_at=datetime(
            2026,
            7,
            10,
            17,
            observed_minute,
            tzinfo=UTC,
        ),
        received_at=datetime(
            2026,
            7,
            10,
            17,
            observed_minute + 1,
            tzinfo=UTC,
        ),
        canonical_payload={
            "event_type": event_type,
            "source_event_id": source_event_id,
        },
        schema_version="constraint-event-1.0",
        canonicalizer_version="canonicalizer-1.0",
        canonicalizer_identity="canonicalizer-worker-01",
        created_at=datetime(
            2026,
            7,
            10,
            17,
            observed_minute + 2,
            tzinfo=UTC,
        ),
    )


def sequence(
    candidates,
    *,
    starting_sequence: int = 1,
    previous_receipt_hash: str = GENESIS_RECEIPT_HASH,
):
    return ConstitutionalSequencerService.sequence_candidates(
        candidates=candidates,
        partition_key="tenant-a/lifecycle-001",
        sequencer_epoch=3,
        sequencer_identity="sequencer-01",
        ordering_policy_version="OPV-1.0",
        starting_sequence=starting_sequence,
        previous_receipt_hash=previous_receipt_hash,
        batch_id=UUID(
            "11111111-1111-1111-1111-111111111111"
        ),
        issued_at=ISSUED_AT,
    )


def test_build_partition_key():
    result = ConstitutionalSequencerService.build_partition_key(
        tenant_id="tenant-a",
        lifecycle_instance_id="lifecycle-001",
    )

    assert result == "tenant-a/lifecycle-001"


def test_empty_batch_is_rejected():
    with pytest.raises(
        EmptySequencerBatchError,
        match="at least one candidate",
    ):
        sequence([])


def test_single_candidate_receives_sequence_receipt():
    candidate = make_candidate()

    outcome = sequence([candidate])

    assert len(outcome.receipts) == 1
    assert outcome.receipts[0].candidate_id == candidate.candidate_id
    assert outcome.receipts[0].assigned_sequence == 1
    assert (
        outcome.receipts[0].previous_receipt_hash
        == GENESIS_RECEIPT_HASH
    )


def test_batch_result_is_ordered():
    candidate = make_candidate()

    outcome = sequence([candidate])

    assert outcome.batch_result.status.value == "ORDERED"
    assert outcome.batch_result.receipt_ids == (
        outcome.receipts[0].receipt_id,
    )


def test_candidates_are_ordered_by_source_sequence():
    late = make_candidate(
        source_event_id="event-003",
        source_sequence=3,
        observed_minute=0,
    )
    early = make_candidate(
        source_event_id="event-001",
        source_sequence=1,
        observed_minute=4,
    )
    middle = make_candidate(
        source_event_id="event-002",
        source_sequence=2,
        observed_minute=2,
    )

    outcome = sequence([late, early, middle])

    assert [
        receipt.candidate_id
        for receipt in outcome.receipts
    ] == [
        early.candidate_id,
        middle.candidate_id,
        late.candidate_id,
    ]


def test_missing_source_sequence_is_ordered_after_present_sequence():
    missing = make_candidate(
        source_event_id="event-missing",
        source_sequence=None,
        observed_minute=0,
    )
    sequenced = make_candidate(
        source_event_id="event-sequenced",
        source_sequence=4,
        observed_minute=5,
    )

    outcome = sequence([missing, sequenced])

    assert outcome.receipts[0].candidate_id == sequenced.candidate_id
    assert outcome.receipts[1].candidate_id == missing.candidate_id


def test_equal_source_sequence_uses_observed_at():
    later = make_candidate(
        source_event_id="event-later",
        source_sequence=5,
        observed_minute=5,
    )
    earlier = make_candidate(
        source_event_id="event-earlier",
        source_sequence=5,
        observed_minute=1,
    )

    outcome = sequence([later, earlier])

    assert outcome.receipts[0].candidate_id == earlier.candidate_id
    assert outcome.receipts[1].candidate_id == later.candidate_id


def test_equal_sequence_and_time_use_source_event_id():
    candidate_b = make_candidate(
        candidate_id=UUID(
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        ),
        source_event_id="event-b",
        source_sequence=7,
        observed_minute=1,
    )
    candidate_a = make_candidate(
        candidate_id=UUID(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        ),
        source_event_id="event-a",
        source_sequence=7,
        observed_minute=1,
    )

    outcome = sequence([candidate_b, candidate_a])

    assert outcome.receipts[0].candidate_id == candidate_a.candidate_id
    assert outcome.receipts[1].candidate_id == candidate_b.candidate_id


def test_receipts_receive_contiguous_sequences():
    candidates = [
        make_candidate(
            source_event_id=f"event-{index}",
            source_sequence=index,
            observed_minute=index,
        )
        for index in range(1, 4)
    ]

    outcome = sequence(
        candidates,
        starting_sequence=20,
    )

    assert [
        receipt.assigned_sequence
        for receipt in outcome.receipts
    ] == [20, 21, 22]


def test_receipts_form_hash_chain():
    candidates = [
        make_candidate(
            source_event_id=f"event-{index}",
            source_sequence=index,
            observed_minute=index,
        )
        for index in range(1, 4)
    ]

    outcome = sequence(candidates)

    assert (
        outcome.receipts[1].previous_receipt_hash
        == outcome.receipts[0].receipt_hash
    )
    assert (
        outcome.receipts[2].previous_receipt_hash
        == outcome.receipts[1].receipt_hash
    )


def test_same_inputs_produce_same_receipt_hashes():
    candidates = [
        make_candidate(
            candidate_id=UUID(
                f"00000000-0000-0000-0000-{index:012d}"
            ),
            source_event_id=f"event-{index}",
            source_sequence=index,
            observed_minute=index,
        )
        for index in range(1, 4)
    ]

    first = sequence(candidates)
    second = sequence(candidates)

    assert [
        receipt.receipt_hash
        for receipt in first.receipts
    ] == [
        receipt.receipt_hash
        for receipt in second.receipts
    ]


def test_duplicate_candidate_id_is_rejected():
    candidate = make_candidate()

    with pytest.raises(
        DuplicateCandidateError,
        match="duplicate candidate_id",
    ):
        sequence([candidate, candidate])


def test_duplicate_candidate_hash_is_rejected():
    candidate = make_candidate()

    duplicate_hash_candidate = candidate.model_copy(
        update={
            "candidate_id": uuid4(),
        }
    )

    with pytest.raises(
        DuplicateCandidateError,
        match="duplicate candidate_hash",
    ):
        sequence(
            [
                candidate,
                duplicate_hash_candidate,
            ]
        )


def test_cross_tenant_batch_is_rejected():
    tenant_a = make_candidate()
    tenant_b = make_candidate(
        tenant_id="tenant-b",
        source_event_id="event-002",
    )

    with pytest.raises(
        SequencerPartitionMismatchError,
        match="multiple tenants",
    ):
        sequence([tenant_a, tenant_b])


def test_cross_lifecycle_batch_is_rejected():
    lifecycle_a = make_candidate()
    lifecycle_b = make_candidate(
        lifecycle_instance_id="lifecycle-002",
        source_event_id="event-002",
    )

    with pytest.raises(
        SequencerPartitionMismatchError,
        match="multiple lifecycle instances",
    ):
        sequence([lifecycle_a, lifecycle_b])


def test_incorrect_partition_key_is_rejected():
    candidate = make_candidate()

    with pytest.raises(
        SequencerPartitionMismatchError,
        match="partition_key does not match",
    ):
        ConstitutionalSequencerService.sequence_candidates(
            candidates=[candidate],
            partition_key="tenant-a/wrong-lifecycle",
            sequencer_epoch=3,
            sequencer_identity="sequencer-01",
            issued_at=ISSUED_AT,
        )


def test_tampered_candidate_hash_is_rejected():
    candidate = make_candidate()

    tampered = candidate.model_copy(
        update={
            "candidate_hash": "f" * 64,
        }
    )

    with pytest.raises(
        CandidateIntegrityError,
        match="candidate hash verification failed",
    ):
        sequence([tampered])


def test_sequenced_candidate_status_is_rejected():
    candidate = make_candidate().model_copy(
        update={
            "status": CandidateStatus.SEQUENCED,
        }
    )

    with pytest.raises(
        CandidateStatusError,
        match="PREPARED or SUBMITTED",
    ):
        sequence([candidate])


def test_unsupported_ordering_policy_is_rejected():
    candidate = make_candidate()

    with pytest.raises(
        UnsupportedOrderingPolicyError,
        match="unsupported ordering policy",
    ):
        ConstitutionalSequencerService.sequence_candidates(
            candidates=[candidate],
            partition_key="tenant-a/lifecycle-001",
            sequencer_epoch=3,
            sequencer_identity="sequencer-01",
            ordering_policy_version="OPV-99.0",
            issued_at=ISSUED_AT,
        )


def test_zero_epoch_is_rejected():
    candidate = make_candidate()

    with pytest.raises(
        ConstitutionalSequencerError,
        match="greater than or equal to one",
    ):
        ConstitutionalSequencerService.sequence_candidates(
            candidates=[candidate],
            partition_key="tenant-a/lifecycle-001",
            sequencer_epoch=0,
            sequencer_identity="sequencer-01",
            issued_at=ISSUED_AT,
        )


def test_verify_receipt_accepts_valid_receipt():
    candidate = make_candidate()
    outcome = sequence([candidate])

    assert (
        ConstitutionalSequencerService.verify_receipt(
            outcome.receipts[0]
        )
        is True
    )


def test_verify_receipt_rejects_tampered_receipt_hash():
    candidate = make_candidate()
    receipt = sequence([candidate]).receipts[0]

    tampered = receipt.model_copy(
        update={
            "receipt_hash": "f" * 64,
        }
    )

    assert (
        ConstitutionalSequencerService.verify_receipt(
            tampered
        )
        is False
    )


def test_assert_receipt_integrity_raises_for_tampering():
    candidate = make_candidate()
    receipt = sequence([candidate]).receipts[0]

    tampered = receipt.model_copy(
        update={
            "receipt_hash": "f" * 64,
        }
    )

    with pytest.raises(
        ReceiptIntegrityError,
        match="hash verification failed",
    ):
        ConstitutionalSequencerService.assert_receipt_integrity(
            tampered
        )


def test_valid_receipt_chain_passes():
    candidates = [
        make_candidate(
            source_event_id=f"event-{index}",
            source_sequence=index,
            observed_minute=index,
        )
        for index in range(1, 4)
    ]

    receipts = sequence(candidates).receipts

    assert (
        ConstitutionalSequencerService.verify_receipt_chain(
            receipts
        )
        is True
    )


def test_broken_sequence_continuity_is_rejected():
    candidates = [
        make_candidate(
            source_event_id=f"event-{index}",
            source_sequence=index,
            observed_minute=index,
        )
        for index in range(1, 3)
    ]

    receipts = list(sequence(candidates).receipts)

    receipts[1] = receipts[1].model_copy(
        update={
            "assigned_sequence": 9,
        }
    )

    with pytest.raises(
        ReceiptChainError,
        match="sequence continuity violation",
    ):
        ConstitutionalSequencerService.verify_receipt_chain(
            receipts
        )


def test_broken_hash_chain_is_rejected():
    candidates = [
        make_candidate(
            source_event_id=f"event-{index}",
            source_sequence=index,
            observed_minute=index,
        )
        for index in range(1, 3)
    ]

    receipts = list(sequence(candidates).receipts)

    receipts[1] = receipts[1].model_copy(
        update={
            "previous_receipt_hash": "f" * 64,
        }
    )

    with pytest.raises(
        ReceiptChainError,
        match="hash-chain continuity violation",
    ):
        ConstitutionalSequencerService.verify_receipt_chain(
            receipts
        )


def test_candidate_receipt_binding_passes():
    candidate = make_candidate()
    receipt = sequence([candidate]).receipts[0]

    ConstitutionalSequencerService.assert_candidate_receipt_binding(
        candidate=candidate,
        receipt=receipt,
    )


def test_candidate_receipt_binding_rejects_wrong_candidate():
    first = make_candidate()
    second = make_candidate(
        source_event_id="event-002",
        source_sequence=2,
        observed_minute=2,
    )

    receipt = sequence([first]).receipts[0]

    with pytest.raises(
        ReceiptIntegrityError,
        match="candidate_id does not match",
    ):
        ConstitutionalSequencerService.assert_candidate_receipt_binding(
            candidate=second,
            receipt=receipt,
        )



