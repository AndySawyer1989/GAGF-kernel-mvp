from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.canonical_evidence_service import (
    CanonicalEvidenceService,
)
from backend.app.services.sequencer_partition_lease_service import (
    InvalidLeaseDurationError,
    PartitionLeaseConflictError,
    PartitionLeaseError,
    PartitionLeaseExpiredError,
    PartitionLeaseNotFoundError,
    PartitionLeaseOwnerMismatchError,
    PartitionLeaseReleasedError,
    PartitionLeaseStatus,
    SequencerPartitionLeaseService,
    StaleSequencerEpochError,
)


UTC = timezone.utc
PARTITION = "tenant-a/lifecycle-001"
OWNER_A = "sequencer-a"
OWNER_B = "sequencer-b"


def at(minute: int) -> datetime:
    return datetime(
        2026,
        7,
        10,
        18,
        minute,
        tzinfo=UTC,
    )


def make_service() -> SequencerPartitionLeaseService:
    return SequencerPartitionLeaseService()


def acquire(
    service: SequencerPartitionLeaseService,
    *,
    owner: str = OWNER_A,
    minute: int = 0,
    duration: int = 60,
):
    return service.acquire_lease(
        partition_key=PARTITION,
        owner_identity=owner,
        acquired_at=at(minute),
        lease_duration_seconds=duration,
    )


def make_candidate():
    return CanonicalEvidenceService.create_candidate(
        tenant_id="tenant-a",
        lifecycle_instance_id="lifecycle-001",
        source_event_id="event-001",
        source_identity="github-connector",
        source_sequence=1,
        observed_at=at(0),
        received_at=at(1),
        canonical_payload={
            "event_type": "APPROVAL_REQUIRED",
        },
        schema_version="constraint-event-1.0",
        canonicalizer_version="canonicalizer-1.0",
        canonicalizer_identity="canonicalizer-worker-01",
        created_at=at(2),
    )


def test_first_acquisition_receives_epoch_one():
    service = make_service()

    lease = acquire(service)

    assert lease.epoch == 1
    assert lease.owner_identity == OWNER_A
    assert lease.status == PartitionLeaseStatus.ACTIVE


def test_acquisition_sets_expiration():
    service = make_service()

    lease = acquire(service, duration=90)

    assert lease.expires_at == at(0) + timedelta(seconds=90)


def test_active_partition_cannot_be_acquired_twice():
    service = make_service()
    acquire(service)

    with pytest.raises(
        PartitionLeaseConflictError,
        match="active lease",
    ):
        acquire(service, owner=OWNER_B)


def test_same_owner_cannot_reacquire_active_lease():
    service = make_service()
    acquire(service)

    with pytest.raises(PartitionLeaseConflictError):
        acquire(service, owner=OWNER_A)


def test_expired_partition_can_be_reacquired():
    service = make_service()
    first = acquire(service, duration=30)

    second = service.acquire_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_B,
        acquired_at=at(1),
        lease_duration_seconds=60,
    )

    assert first.epoch == 1
    assert second.epoch == 2
    assert second.owner_identity == OWNER_B


def test_reacquisition_by_same_owner_gets_new_epoch():
    service = make_service()
    first = acquire(service, duration=30)

    second = service.acquire_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_A,
        acquired_at=at(1),
        lease_duration_seconds=60,
    )

    assert second.epoch == first.epoch + 1


def test_renewal_preserves_epoch():
    service = make_service()
    lease = acquire(service)

    renewed = service.renew_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_A,
        epoch=lease.epoch,
        renewed_at=at(0) + timedelta(seconds=30),
        lease_duration_seconds=120,
    )

    assert renewed.epoch == lease.epoch
    assert renewed.expires_at == (
        at(0) + timedelta(seconds=150)
    )


def test_wrong_owner_cannot_renew():
    service = make_service()
    lease = acquire(service)

    with pytest.raises(
        PartitionLeaseOwnerMismatchError,
        match="does not own",
    ):
        service.renew_lease(
            partition_key=PARTITION,
            owner_identity=OWNER_B,
            epoch=lease.epoch,
            renewed_at=at(0) + timedelta(seconds=20),
            lease_duration_seconds=60,
        )


def test_stale_epoch_cannot_renew():
    service = make_service()
    lease = acquire(service)

    with pytest.raises(
        StaleSequencerEpochError,
        match="does not match",
    ):
        service.renew_lease(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            epoch=lease.epoch + 1,
            renewed_at=at(0) + timedelta(seconds=20),
            lease_duration_seconds=60,
        )


def test_expired_lease_cannot_be_renewed():
    service = make_service()
    lease = acquire(service, duration=10)

    with pytest.raises(
        PartitionLeaseExpiredError,
        match="expired",
    ):
        service.renew_lease(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            epoch=lease.epoch,
            renewed_at=at(1),
            lease_duration_seconds=60,
        )


def test_owner_can_release_active_lease():
    service = make_service()
    lease = acquire(service)

    released = service.release_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_A,
        epoch=lease.epoch,
        released_at=at(0) + timedelta(seconds=20),
    )

    assert released.status == PartitionLeaseStatus.RELEASED


def test_released_lease_cannot_authorize():
    service = make_service()
    lease = acquire(service)

    service.release_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_A,
        epoch=lease.epoch,
        released_at=at(0) + timedelta(seconds=20),
    )

    with pytest.raises(
        PartitionLeaseReleasedError,
        match="released",
    ):
        service.assert_authorized(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            epoch=lease.epoch,
            at=at(0) + timedelta(seconds=30),
        )


def test_released_partition_can_be_reacquired_with_new_epoch():
    service = make_service()
    first = acquire(service)

    service.release_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_A,
        epoch=first.epoch,
        released_at=at(0) + timedelta(seconds=20),
    )

    second = service.acquire_lease(
        partition_key=PARTITION,
        owner_identity=OWNER_B,
        acquired_at=at(0) + timedelta(seconds=30),
        lease_duration_seconds=60,
    )

    assert second.epoch == first.epoch + 1


def test_transfer_creates_new_epoch():
    service = make_service()
    first = acquire(service)

    transferred = service.transfer_lease(
        partition_key=PARTITION,
        current_owner_identity=OWNER_A,
        current_epoch=first.epoch,
        new_owner_identity=OWNER_B,
        transferred_at=at(0) + timedelta(seconds=20),
        lease_duration_seconds=60,
    )

    assert transferred.owner_identity == OWNER_B
    assert transferred.epoch == first.epoch + 1


def test_previous_owner_is_fenced_after_transfer():
    service = make_service()
    first = acquire(service)

    transferred = service.transfer_lease(
        partition_key=PARTITION,
        current_owner_identity=OWNER_A,
        current_epoch=first.epoch,
        new_owner_identity=OWNER_B,
        transferred_at=at(0) + timedelta(seconds=20),
        lease_duration_seconds=60,
    )

    with pytest.raises(StaleSequencerEpochError):
        service.assert_authorized(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            epoch=first.epoch,
            at=at(0) + timedelta(seconds=30),
        )

    assert transferred.epoch == 2


def test_transfer_requires_different_owner():
    service = make_service()
    lease = acquire(service)

    with pytest.raises(
        PartitionLeaseError,
        match="different owner",
    ):
        service.transfer_lease(
            partition_key=PARTITION,
            current_owner_identity=OWNER_A,
            current_epoch=lease.epoch,
            new_owner_identity=OWNER_A,
            transferred_at=at(0) + timedelta(seconds=20),
            lease_duration_seconds=60,
        )


def test_authorized_owner_passes_validation():
    service = make_service()
    lease = acquire(service)

    result = service.assert_authorized(
        partition_key=PARTITION,
        owner_identity=OWNER_A,
        epoch=lease.epoch,
        at=at(0) + timedelta(seconds=20),
    )

    assert result == lease


def test_wrong_owner_is_rejected():
    service = make_service()
    lease = acquire(service)

    with pytest.raises(
        PartitionLeaseOwnerMismatchError,
        match="does not own",
    ):
        service.assert_authorized(
            partition_key=PARTITION,
            owner_identity=OWNER_B,
            epoch=lease.epoch,
            at=at(0) + timedelta(seconds=20),
        )


def test_stale_epoch_is_rejected():
    service = make_service()
    lease = acquire(service)

    with pytest.raises(StaleSequencerEpochError):
        service.assert_authorized(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            epoch=lease.epoch + 1,
            at=at(0) + timedelta(seconds=20),
        )


def test_expiration_boundary_is_exclusive():
    service = make_service()
    lease = acquire(service, duration=60)

    with pytest.raises(PartitionLeaseExpiredError):
        service.assert_authorized(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            epoch=lease.epoch,
            at=lease.expires_at,
        )


def test_effective_lease_marks_expired_status():
    service = make_service()
    acquire(service, duration=10)

    effective = service.get_effective_lease(
        partition_key=PARTITION,
        at=at(1),
    )

    assert effective.status == PartitionLeaseStatus.EXPIRED


def test_missing_partition_is_rejected():
    service = make_service()

    with pytest.raises(PartitionLeaseNotFoundError):
        service.assert_authorized(
            partition_key="tenant-x/lifecycle-x",
            owner_identity=OWNER_A,
            epoch=1,
            at=at(0),
        )


def test_invalid_duration_is_rejected():
    service = make_service()

    with pytest.raises(
        InvalidLeaseDurationError,
        match="greater than zero",
    ):
        acquire(service, duration=0)


def test_naive_timestamp_is_rejected():
    service = make_service()

    with pytest.raises(
        PartitionLeaseError,
        match="timezone-aware",
    ):
        service.acquire_lease(
            partition_key=PARTITION,
            owner_identity=OWNER_A,
            acquired_at=datetime(2026, 7, 10, 18, 0),
            lease_duration_seconds=60,
        )


def test_authorized_sequencer_can_issue_receipt():
    service = make_service()
    lease = acquire(service)
    candidate = make_candidate()

    outcome = service.sequence_candidates(
        candidates=[candidate],
        partition_key=PARTITION,
        sequencer_epoch=lease.epoch,
        sequencer_identity=OWNER_A,
        authorized_at=at(0) + timedelta(seconds=20),
        issued_at=at(0) + timedelta(seconds=20),
    )

    assert len(outcome.receipts) == 1
    assert outcome.receipts[0].sequencer_epoch == lease.epoch
    assert outcome.receipts[0].sequencer_identity == OWNER_A


def test_stale_sequencer_cannot_issue_receipt_after_transfer():
    service = make_service()
    first = acquire(service)

    service.transfer_lease(
        partition_key=PARTITION,
        current_owner_identity=OWNER_A,
        current_epoch=first.epoch,
        new_owner_identity=OWNER_B,
        transferred_at=at(0) + timedelta(seconds=20),
        lease_duration_seconds=60,
    )

    with pytest.raises(StaleSequencerEpochError):
        service.sequence_candidates(
            candidates=[make_candidate()],
            partition_key=PARTITION,
            sequencer_epoch=first.epoch,
            sequencer_identity=OWNER_A,
            authorized_at=at(0) + timedelta(seconds=30),
        )



