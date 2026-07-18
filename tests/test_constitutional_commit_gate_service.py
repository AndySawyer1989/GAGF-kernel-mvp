from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from backend.app.contracts.constitutional_sequencer import (
    ConstitutionalCommitRequest,
)
from backend.app.services.canonical_evidence_service import (
    CanonicalEvidenceService,
)
from backend.app.services.constitutional_commit_gate_service import (
    GENESIS_STATE_HASH,
    CommitBatchBindingError,
    CommitBatchCardinalityError,
    CommitBatchEmptyError,
    CommitCandidateIntegrityError,
    CommitEpochMismatchError,
    CommitPartitionMismatchError,
    CommitPolicyMismatchError,
    CommitReceiptIntegrityError,
    ConstitutionalCommitGateError,
    ConstitutionalCommitGateService,
    DuplicateCommitBatchError,
    InMemoryConstitutionalCommitRepository,
    PreviousStateHashMismatchError,
    UnsupportedCommitContractError,
)
from backend.app.services.sequencer_partition_lease_service import (
    PartitionLeaseOwnerMismatchError,
    SequencerPartitionLeaseService,
    StaleSequencerEpochError,
)


UTC = timezone.utc
PARTITION = "tenant-a/lifecycle-001"
SEQUENCER = "sequencer-a"

BATCH_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)
REQUEST_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)
DECISION_ID = UUID(
    "33333333-3333-3333-3333-333333333333"
)


def at(
    minute: int,
    second: int = 0,
) -> datetime:
    return datetime(
        2026,
        7,
        10,
        18,
        minute,
        second,
        tzinfo=UTC,
    )


def make_candidate(
    *,
    event_number: int,
    tenant_id: str = "tenant-a",
    lifecycle_instance_id: str = "lifecycle-001",
):
    return CanonicalEvidenceService.create_candidate(
        candidate_id=UUID(
            f"00000000-0000-0000-0000-{event_number:012d}"
        ),
        tenant_id=tenant_id,
        lifecycle_instance_id=lifecycle_instance_id,
        source_event_id=f"event-{event_number:03d}",
        source_identity="github-connector",
        source_sequence=event_number,
        observed_at=at(event_number),
        received_at=at(event_number, 10),
        canonical_payload={
            "event_type": "APPROVAL_REQUIRED",
            "event_number": event_number,
        },
        schema_version="constraint-event-1.0",
        canonicalizer_version="canonicalizer-1.0",
        canonicalizer_identity="canonicalizer-worker-01",
        created_at=at(event_number, 20),
    )


def setup_commit_pipeline(
    *,
    candidate_count: int = 2,
):
    lease_service = SequencerPartitionLeaseService()

    lease = lease_service.acquire_lease(
        partition_key=PARTITION,
        owner_identity=SEQUENCER,
        acquired_at=at(0),
        lease_duration_seconds=1200,
    )

    candidates = tuple(
        make_candidate(event_number=index)
        for index in range(1, candidate_count + 1)
    )

    sequencing_outcome = lease_service.sequence_candidates(
        candidates=candidates,
        partition_key=PARTITION,
        sequencer_epoch=lease.epoch,
        sequencer_identity=SEQUENCER,
        authorized_at=at(5),
        issued_at=at(5),
        batch_id=BATCH_ID,
    )

    receipts = sequencing_outcome.receipts

    request = ConstitutionalCommitRequest(
        commit_request_id=REQUEST_ID,
        batch_id=sequencing_outcome.batch_result.batch_id,
        tenant_id="tenant-a",
        lifecycle_instance_id="lifecycle-001",
        partition_key=PARTITION,
        candidate_ids=tuple(
            candidate.candidate_id
            for candidate in candidates
        ),
        receipt_ids=tuple(
            receipt.receipt_id
            for receipt in receipts
        ),
        sequencer_epoch=lease.epoch,
        ordering_policy_version="OPV-1.0",
        policy_version="GPL-0.1",
        kernel_version="3.4",
        prior_state_hash=GENESIS_STATE_HASH,
        submitted_by=SEQUENCER,
        submitted_at=at(6),
    )

    repository = InMemoryConstitutionalCommitRepository()

    service = ConstitutionalCommitGateService(
        lease_service=lease_service,
        repository=repository,
    )

    return {
        "lease_service": lease_service,
        "lease": lease,
        "candidates": candidates,
        "receipts": receipts,
        "request": request,
        "repository": repository,
        "service": service,
    }


def commit_pipeline(pipeline):
    return pipeline["service"].commit_batch(
        request=pipeline["request"],
        candidates=pipeline["candidates"],
        receipts=pipeline["receipts"],
        committed_at=at(7),
        decision_id=DECISION_ID,
    )


def test_valid_batch_commits_successfully():
    pipeline = setup_commit_pipeline()

    result = commit_pipeline(pipeline)

    assert result.status.value == "ACCEPTED"
    assert result.decision_id == DECISION_ID
    assert result.ledger_offset == 0
    assert len(result.decision_hash) == 64
    assert len(result.resulting_state_hash) == 64


def test_commit_updates_partition_state():
    pipeline = setup_commit_pipeline()

    result = commit_pipeline(pipeline)

    current_state = (
        pipeline["repository"].get_current_state_hash(
            PARTITION
        )
    )

    assert current_state == result.resulting_state_hash


def test_commit_creates_immutable_repository_record():
    pipeline = setup_commit_pipeline()

    result = commit_pipeline(pipeline)

    record = pipeline["repository"].get_by_batch_id(
        result.batch_id
    )

    assert record is not None
    assert record.decision_id == DECISION_ID
    assert record.decision_hash == result.decision_hash
    assert record.resulting_state_hash == (
        result.resulting_state_hash
    )


def test_first_commit_receives_ledger_offset_zero():
    pipeline = setup_commit_pipeline()

    result = commit_pipeline(pipeline)

    assert result.ledger_offset == 0
    assert pipeline["repository"].next_ledger_offset() == 1


def test_same_inputs_produce_same_state_hash():
    first = setup_commit_pipeline()
    second = setup_commit_pipeline()

    first_result = commit_pipeline(first)
    second_result = commit_pipeline(second)

    assert (
        first_result.resulting_state_hash
        == second_result.resulting_state_hash
    )


def test_same_inputs_produce_same_decision_hash():
    first = setup_commit_pipeline()
    second = setup_commit_pipeline()

    first_result = commit_pipeline(first)
    second_result = commit_pipeline(second)

    assert (
        first_result.decision_hash
        == second_result.decision_hash
    )


def test_decision_id_does_not_change_decision_hash():
    first = setup_commit_pipeline()
    second = setup_commit_pipeline()

    first_result = first["service"].commit_batch(
        request=first["request"],
        candidates=first["candidates"],
        receipts=first["receipts"],
        committed_at=at(7),
        decision_id=uuid4(),
    )

    second_result = second["service"].commit_batch(
        request=second["request"],
        candidates=second["candidates"],
        receipts=second["receipts"],
        committed_at=at(7),
        decision_id=uuid4(),
    )

    assert first_result.decision_id != second_result.decision_id
    assert first_result.decision_hash == second_result.decision_hash


def test_committed_at_does_not_change_decision_hash():
    first = setup_commit_pipeline()
    second = setup_commit_pipeline()

    first_result = first["service"].commit_batch(
        request=first["request"],
        candidates=first["candidates"],
        receipts=first["receipts"],
        committed_at=at(7),
    )

    second_result = second["service"].commit_batch(
        request=second["request"],
        candidates=second["candidates"],
        receipts=second["receipts"],
        committed_at=at(8),
    )

    assert first_result.decision_hash == second_result.decision_hash


def test_candidate_change_changes_resulting_state_hash():
    first = setup_commit_pipeline(candidate_count=1)
    second = setup_commit_pipeline(candidate_count=2)

    first_result = commit_pipeline(first)
    second_result = commit_pipeline(second)

    assert (
        first_result.resulting_state_hash
        != second_result.resulting_state_hash
    )


def test_policy_version_changes_state_hash():
    first = setup_commit_pipeline()
    second = setup_commit_pipeline()

    second["request"] = second["request"].model_copy(
        update={
            "policy_version": "GPL-0.2",
        }
    )

    first_result = commit_pipeline(first)
    second_result = commit_pipeline(second)

    assert (
        first_result.resulting_state_hash
        != second_result.resulting_state_hash
    )


def test_empty_candidate_batch_is_rejected():
    pipeline = setup_commit_pipeline()

    with pytest.raises(
        CommitBatchEmptyError,
        match="contain candidates",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=(),
            receipts=pipeline["receipts"],
            committed_at=at(7),
        )


def test_empty_receipt_batch_is_rejected():
    pipeline = setup_commit_pipeline()

    with pytest.raises(
        CommitBatchEmptyError,
        match="contain receipts",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=(),
            committed_at=at(7),
        )


def test_candidate_receipt_count_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    with pytest.raises(
        CommitBatchCardinalityError,
        match="counts must match",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=pipeline["receipts"][:1],
            committed_at=at(7),
        )


def test_request_candidate_count_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    pipeline["request"] = pipeline["request"].model_copy(
        update={
            "candidate_ids": (
                pipeline["candidates"][0].candidate_id,
            ),
        }
    )

    with pytest.raises(
        CommitBatchCardinalityError,
        match="request candidate count",
    ):
        commit_pipeline(pipeline)


def test_request_receipt_count_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    pipeline["request"] = pipeline["request"].model_copy(
        update={
            "receipt_ids": (
                pipeline["receipts"][0].receipt_id,
            ),
        }
    )

    with pytest.raises(
        CommitBatchCardinalityError,
        match="request receipt count",
    ):
        commit_pipeline(pipeline)


def test_wrong_candidate_ids_are_rejected():
    pipeline = setup_commit_pipeline()

    pipeline["request"] = pipeline["request"].model_copy(
        update={
            "candidate_ids": (
                uuid4(),
                pipeline["candidates"][1].candidate_id,
            ),
        }
    )

    with pytest.raises(
        CommitBatchBindingError,
        match="candidate_ids do not match",
    ):
        commit_pipeline(pipeline)


def test_wrong_receipt_ids_are_rejected():
    pipeline = setup_commit_pipeline()

    pipeline["request"] = pipeline["request"].model_copy(
        update={
            "receipt_ids": (
                uuid4(),
                pipeline["receipts"][1].receipt_id,
            ),
        }
    )

    with pytest.raises(
        CommitBatchBindingError,
        match="receipt_ids do not match",
    ):
        commit_pipeline(pipeline)


def test_wrong_receipt_batch_id_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[0] = tampered_receipts[0].model_copy(
        update={
            "batch_id": uuid4(),
        }
    )

    with pytest.raises(
        CommitBatchBindingError,
        match="batch_id",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_cross_tenant_candidate_is_rejected():
    pipeline = setup_commit_pipeline()

    cross_tenant = make_candidate(
        event_number=2,
        tenant_id="tenant-b",
    )

    with pytest.raises(
        CommitPartitionMismatchError,
        match="candidate tenant",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=(
                pipeline["candidates"][0],
                cross_tenant,
            ),
            receipts=pipeline["receipts"],
            committed_at=at(7),
        )


def test_tampered_candidate_hash_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_candidates = list(pipeline["candidates"])
    tampered_candidates[0] = tampered_candidates[0].model_copy(
        update={
            "candidate_hash": "f" * 64,
        }
    )

    with pytest.raises(
        CommitCandidateIntegrityError,
        match="candidate hash verification failed",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=tampered_candidates,
            receipts=pipeline["receipts"],
            committed_at=at(7),
        )


def test_tampered_receipt_hash_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[0] = tampered_receipts[0].model_copy(
        update={
            "receipt_hash": "f" * 64,
        }
    )

    with pytest.raises(CommitReceiptIntegrityError):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_broken_receipt_chain_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[1] = tampered_receipts[1].model_copy(
        update={
            "previous_receipt_hash": "e" * 64,
        }
    )

    with pytest.raises(
        CommitReceiptIntegrityError,
        match="continuity",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_receipt_candidate_binding_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[0] = tampered_receipts[0].model_copy(
        update={
            "candidate_id": uuid4(),
        }
    )

    with pytest.raises(
        CommitBatchBindingError,
        match="candidate bindings",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_receipt_epoch_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[0] = tampered_receipts[0].model_copy(
        update={
            "sequencer_epoch": 99,
        }
    )

    with pytest.raises(
        CommitEpochMismatchError,
        match="epoch",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_receipt_identity_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[0] = tampered_receipts[0].model_copy(
        update={
            "sequencer_identity": "sequencer-b",
        }
    )

    with pytest.raises(
        CommitBatchBindingError,
        match="sequencer identity",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_receipt_ordering_policy_mismatch_is_rejected():
    pipeline = setup_commit_pipeline()

    tampered_receipts = list(pipeline["receipts"])
    tampered_receipts[0] = tampered_receipts[0].model_copy(
        update={
            "ordering_policy_version": "OPV-9.9",
        }
    )

    with pytest.raises(
        CommitPolicyMismatchError,
        match="ordering policy",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=tampered_receipts,
            committed_at=at(7),
        )


def test_stale_epoch_cannot_commit():
    pipeline = setup_commit_pipeline()

    pipeline["lease_service"].transfer_lease(
        partition_key=PARTITION,
        current_owner_identity=SEQUENCER,
        current_epoch=pipeline["lease"].epoch,
        new_owner_identity="sequencer-b",
        transferred_at=at(6, 30),
        lease_duration_seconds=300,
    )

    with pytest.raises(StaleSequencerEpochError):
        commit_pipeline(pipeline)


def test_wrong_owner_cannot_commit():
    pipeline = setup_commit_pipeline()

    pipeline["request"] = pipeline["request"].model_copy(
        update={
            "submitted_by": "sequencer-b",
        }
    )

    with pytest.raises(
        CommitBatchBindingError,
        match="sequencer identity",
    ):
        commit_pipeline(pipeline)


def test_wrong_prior_state_hash_is_rejected():
    pipeline = setup_commit_pipeline()

    pipeline["request"] = pipeline["request"].model_copy(
        update={
            "prior_state_hash": "a" * 64,
        }
    )

    with pytest.raises(
        PreviousStateHashMismatchError,
        match="current partition state",
    ):
        commit_pipeline(pipeline)


def test_duplicate_batch_is_rejected():
    pipeline = setup_commit_pipeline()

    commit_pipeline(pipeline)

    with pytest.raises(
        DuplicateCommitBatchError,
        match="already been committed",
    ):
        commit_pipeline(pipeline)


def test_unsupported_commit_contract_is_rejected():
    pipeline = setup_commit_pipeline()

    with pytest.raises(
        UnsupportedCommitContractError,
        match="unsupported commit contract",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=pipeline["receipts"],
            committed_at=at(7),
            commit_contract_version="constitutional-commit-v99",
        )


def test_naive_commit_timestamp_is_rejected():
    pipeline = setup_commit_pipeline()

    with pytest.raises(
        ConstitutionalCommitGateError,
        match="timezone-aware",
    ):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=pipeline["candidates"],
            receipts=pipeline["receipts"],
            committed_at=datetime(
                2026,
                7,
                10,
                18,
                7,
            ),
        )


def test_partition_history_contains_committed_record():
    pipeline = setup_commit_pipeline()

    result = commit_pipeline(pipeline)

    history = pipeline[
        "repository"
    ].list_partition_records(PARTITION)

    assert len(history) == 1
    assert history[0].decision_hash == result.decision_hash


def test_failed_commit_does_not_mutate_repository():
    pipeline = setup_commit_pipeline()

    tampered_candidates = list(pipeline["candidates"])
    tampered_candidates[0] = tampered_candidates[0].model_copy(
        update={
            "candidate_hash": "f" * 64,
        }
    )

    with pytest.raises(CommitCandidateIntegrityError):
        pipeline["service"].commit_batch(
            request=pipeline["request"],
            candidates=tampered_candidates,
            receipts=pipeline["receipts"],
            committed_at=at(7),
        )

    assert (
        pipeline["repository"].next_ledger_offset()
        == 0
    )
    assert (
        pipeline["repository"].list_partition_records(
            PARTITION
        )
        == ()
    )
    assert (
        pipeline["repository"].get_current_state_hash(
            PARTITION
        )
        == GENESIS_STATE_HASH
    )


def test_second_valid_commit_uses_previous_state():
    pipeline = setup_commit_pipeline(candidate_count=1)

    first_result = commit_pipeline(pipeline)

    second_candidate = make_candidate(event_number=9)

    second_outcome = pipeline[
        "lease_service"
    ].sequence_candidates(
        candidates=[second_candidate],
        partition_key=PARTITION,
        sequencer_epoch=pipeline["lease"].epoch,
        sequencer_identity=SEQUENCER,
        authorized_at=at(8),
        issued_at=at(8),
        starting_sequence=2,
        previous_receipt_hash=(
            pipeline["receipts"][-1].receipt_hash
        ),
    )

    second_request = ConstitutionalCommitRequest(
        commit_request_id=uuid4(),
        batch_id=second_outcome.batch_result.batch_id,
        tenant_id="tenant-a",
        lifecycle_instance_id="lifecycle-001",
        partition_key=PARTITION,
        candidate_ids=(second_candidate.candidate_id,),
        receipt_ids=(
            second_outcome.receipts[0].receipt_id,
        ),
        sequencer_epoch=pipeline["lease"].epoch,
        ordering_policy_version="OPV-1.0",
        policy_version="GPL-0.1",
        kernel_version="3.4",
        prior_state_hash=first_result.resulting_state_hash,
        submitted_by=SEQUENCER,
        submitted_at=at(9),
    )

    second_result = pipeline["service"].commit_batch(
        request=second_request,
        candidates=[second_candidate],
        receipts=second_outcome.receipts,
        committed_at=at(10),
    )

    assert second_result.ledger_offset == 1
    assert (
        second_result.resulting_state_hash
        != first_result.resulting_state_hash
    )
    assert (
        pipeline["repository"].get_current_state_hash(
            PARTITION
        )
        == second_result.resulting_state_hash
    )


def test_second_commit_with_stale_prior_state_is_rejected():
    pipeline = setup_commit_pipeline(candidate_count=1)

    commit_pipeline(pipeline)

    second_candidate = make_candidate(event_number=9)

    second_outcome = pipeline[
        "lease_service"
    ].sequence_candidates(
        candidates=[second_candidate],
        partition_key=PARTITION,
        sequencer_epoch=pipeline["lease"].epoch,
        sequencer_identity=SEQUENCER,
        authorized_at=at(8),
        issued_at=at(8),
        starting_sequence=2,
        previous_receipt_hash=(
            pipeline["receipts"][-1].receipt_hash
        ),
    )

    stale_request = ConstitutionalCommitRequest(
        commit_request_id=uuid4(),
        batch_id=second_outcome.batch_result.batch_id,
        tenant_id="tenant-a",
        lifecycle_instance_id="lifecycle-001",
        partition_key=PARTITION,
        candidate_ids=(second_candidate.candidate_id,),
        receipt_ids=(
            second_outcome.receipts[0].receipt_id,
        ),
        sequencer_epoch=pipeline["lease"].epoch,
        ordering_policy_version="OPV-1.0",
        policy_version="GPL-0.1",
        kernel_version="3.4",
        prior_state_hash=GENESIS_STATE_HASH,
        submitted_by=SEQUENCER,
        submitted_at=at(9),
    )

    with pytest.raises(
        PreviousStateHashMismatchError,
        match="current partition state",
    ):
        pipeline["service"].commit_batch(
            request=stale_request,
            candidates=[second_candidate],
            receipts=second_outcome.receipts,
            committed_at=at(10),
        )






