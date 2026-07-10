from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Sequence
from uuid import UUID

from backend.app.contracts.constitutional_sequencer import (
    CanonicalEvidenceCandidate,
)
from backend.app.services.constitutional_sequencer_service import (
    GENESIS_RECEIPT_HASH,
    ConstitutionalSequencerService,
    SequencingOutcome,
)


class PartitionLeaseError(ValueError):
    """Base exception for partition lease and epoch-fencing failures."""


class PartitionLeaseConflictError(PartitionLeaseError):
    """Raised when an active partition lease is already owned."""


class PartitionLeaseNotFoundError(PartitionLeaseError):
    """Raised when a requested partition lease does not exist."""


class PartitionLeaseExpiredError(PartitionLeaseError):
    """Raised when an operation references an expired lease."""


class PartitionLeaseOwnerMismatchError(PartitionLeaseError):
    """Raised when the caller is not the active partition owner."""


class StaleSequencerEpochError(PartitionLeaseError):
    """Raised when a sequencer attempts to act under an obsolete epoch."""


class PartitionLeaseReleasedError(PartitionLeaseError):
    """Raised when a released lease is presented as active authority."""


class InvalidLeaseDurationError(PartitionLeaseError):
    """Raised when a lease duration is invalid."""


class PartitionLeaseStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"


@dataclass(frozen=True)
class SequencerPartitionLease:
    """
    Operational proof of temporary sequencer ownership.

    This record controls authority but is not itself a committed governance
    decision.
    """

    partition_key: str
    owner_identity: str
    epoch: int
    acquired_at: datetime
    expires_at: datetime
    status: PartitionLeaseStatus


class InMemoryPartitionLeaseRepository:
    """
    Deterministic in-memory repository used by the MVP and unit tests.

    A persistent repository can replace this implementation later without
    changing the service contract.
    """

    def __init__(self) -> None:
        self._leases: dict[str, SequencerPartitionLease] = {}
        self._highest_epochs: dict[str, int] = {}

    def get(
        self,
        partition_key: str,
    ) -> SequencerPartitionLease | None:
        return self._leases.get(partition_key)

    def save(
        self,
        lease: SequencerPartitionLease,
    ) -> SequencerPartitionLease:
        self._leases[lease.partition_key] = lease

        current_highest = self._highest_epochs.get(
            lease.partition_key,
            0,
        )

        if lease.epoch > current_highest:
            self._highest_epochs[lease.partition_key] = lease.epoch

        return lease

    def highest_epoch(
        self,
        partition_key: str,
    ) -> int:
        return self._highest_epochs.get(partition_key, 0)

    def clear(self) -> None:
        self._leases.clear()
        self._highest_epochs.clear()


class SequencerPartitionLeaseService:
    """
    Enforces exclusive, epoch-fenced ownership of sequencer partitions.

    A sequencer may issue sequence receipts only when:

    - it owns the active partition lease;
    - its epoch equals the partition's current epoch;
    - the lease has not expired;
    - the lease has not been released.
    """

    def __init__(
        self,
        repository: InMemoryPartitionLeaseRepository | None = None,
    ) -> None:
        self.repository = (
            repository or InMemoryPartitionLeaseRepository()
        )

    def acquire_lease(
        self,
        *,
        partition_key: str,
        owner_identity: str,
        acquired_at: datetime,
        lease_duration_seconds: int,
    ) -> SequencerPartitionLease:
        normalized_now = self._normalize_datetime(
            acquired_at,
            "acquired_at",
        )

        self._validate_partition_key(partition_key)
        self._validate_identity(owner_identity)

        duration = self._validate_duration(
            lease_duration_seconds
        )

        existing = self.repository.get(partition_key)

        if existing is not None:
            effective_existing = self._effective_lease(
                existing,
                normalized_now,
            )

            if effective_existing.status == PartitionLeaseStatus.ACTIVE:
                raise PartitionLeaseConflictError(
                    "partition already has an active lease"
                )

        next_epoch = (
            self.repository.highest_epoch(partition_key) + 1
        )

        lease = SequencerPartitionLease(
            partition_key=partition_key,
            owner_identity=owner_identity,
            epoch=next_epoch,
            acquired_at=normalized_now,
            expires_at=normalized_now + duration,
            status=PartitionLeaseStatus.ACTIVE,
        )

        return self.repository.save(lease)

    def renew_lease(
        self,
        *,
        partition_key: str,
        owner_identity: str,
        epoch: int,
        renewed_at: datetime,
        lease_duration_seconds: int,
    ) -> SequencerPartitionLease:
        normalized_now = self._normalize_datetime(
            renewed_at,
            "renewed_at",
        )

        duration = self._validate_duration(
            lease_duration_seconds
        )

        current = self._require_current_lease(partition_key)

        self._assert_lease_authority(
            lease=current,
            owner_identity=owner_identity,
            epoch=epoch,
            at=normalized_now,
        )

        renewed = replace(
            current,
            expires_at=normalized_now + duration,
            status=PartitionLeaseStatus.ACTIVE,
        )

        return self.repository.save(renewed)

    def release_lease(
        self,
        *,
        partition_key: str,
        owner_identity: str,
        epoch: int,
        released_at: datetime,
    ) -> SequencerPartitionLease:
        normalized_now = self._normalize_datetime(
            released_at,
            "released_at",
        )

        current = self._require_current_lease(partition_key)

        self._assert_lease_authority(
            lease=current,
            owner_identity=owner_identity,
            epoch=epoch,
            at=normalized_now,
        )

        released = replace(
            current,
            expires_at=normalized_now,
            status=PartitionLeaseStatus.RELEASED,
        )

        return self.repository.save(released)

    def transfer_lease(
        self,
        *,
        partition_key: str,
        current_owner_identity: str,
        current_epoch: int,
        new_owner_identity: str,
        transferred_at: datetime,
        lease_duration_seconds: int,
    ) -> SequencerPartitionLease:
        normalized_now = self._normalize_datetime(
            transferred_at,
            "transferred_at",
        )

        duration = self._validate_duration(
            lease_duration_seconds
        )

        self._validate_identity(new_owner_identity)

        if new_owner_identity == current_owner_identity:
            raise PartitionLeaseError(
                "lease transfer requires a different owner identity"
            )

        current = self._require_current_lease(partition_key)

        self._assert_lease_authority(
            lease=current,
            owner_identity=current_owner_identity,
            epoch=current_epoch,
            at=normalized_now,
        )

        next_epoch = (
            self.repository.highest_epoch(partition_key) + 1
        )

        transferred = SequencerPartitionLease(
            partition_key=partition_key,
            owner_identity=new_owner_identity,
            epoch=next_epoch,
            acquired_at=normalized_now,
            expires_at=normalized_now + duration,
            status=PartitionLeaseStatus.ACTIVE,
        )

        return self.repository.save(transferred)

    def get_effective_lease(
        self,
        *,
        partition_key: str,
        at: datetime,
    ) -> SequencerPartitionLease:
        normalized_at = self._normalize_datetime(at, "at")

        lease = self._require_current_lease(partition_key)

        effective = self._effective_lease(
            lease,
            normalized_at,
        )

        if effective != lease:
            self.repository.save(effective)

        return effective

    def assert_authorized(
        self,
        *,
        partition_key: str,
        owner_identity: str,
        epoch: int,
        at: datetime,
    ) -> SequencerPartitionLease:
        normalized_at = self._normalize_datetime(at, "at")

        current = self._require_current_lease(partition_key)

        self._assert_lease_authority(
            lease=current,
            owner_identity=owner_identity,
            epoch=epoch,
            at=normalized_at,
        )

        return current

    def sequence_candidates(
        self,
        *,
        candidates: Sequence[CanonicalEvidenceCandidate],
        partition_key: str,
        sequencer_epoch: int,
        sequencer_identity: str,
        authorized_at: datetime,
        ordering_policy_version: str = "OPV-1.0",
        starting_sequence: int = 1,
        previous_receipt_hash: str = GENESIS_RECEIPT_HASH,
        batch_id: UUID | None = None,
        issued_at: datetime | None = None,
    ) -> SequencingOutcome:
        """
        Issue sequence receipts only after validating partition authority.

        batch_id may be supplied so deterministic tests, replays, and upstream
        batch coordinators can bind sequencing to a stable batch identity.
        """
        normalized_authorized_at = self._normalize_datetime(
            authorized_at,
            "authorized_at",
        )

        self.assert_authorized(
            partition_key=partition_key,
            owner_identity=sequencer_identity,
            epoch=sequencer_epoch,
            at=normalized_authorized_at,
        )

        resolved_issued_at = (
            self._normalize_datetime(
                issued_at,
                "issued_at",
            )
            if issued_at is not None
            else normalized_authorized_at
        )

        return ConstitutionalSequencerService.sequence_candidates(
            candidates=candidates,
            partition_key=partition_key,
            sequencer_epoch=sequencer_epoch,
            sequencer_identity=sequencer_identity,
            ordering_policy_version=ordering_policy_version,
            starting_sequence=starting_sequence,
            previous_receipt_hash=previous_receipt_hash,
            batch_id=batch_id,
            issued_at=resolved_issued_at,
        )

    def _assert_lease_authority(
        self,
        *,
        lease: SequencerPartitionLease,
        owner_identity: str,
        epoch: int,
        at: datetime,
    ) -> None:
        self._validate_identity(owner_identity)
        self._validate_epoch(epoch)

        effective = self._effective_lease(
            lease,
            at,
        )

        if effective.status == PartitionLeaseStatus.RELEASED:
            raise PartitionLeaseReleasedError(
                "partition lease has been released"
            )

        if effective.status == PartitionLeaseStatus.EXPIRED:
            if effective != lease:
                self.repository.save(effective)

            raise PartitionLeaseExpiredError(
                "partition lease has expired"
            )

        if epoch != effective.epoch:
            raise StaleSequencerEpochError(
                "sequencer epoch does not match active partition epoch"
            )

        if owner_identity != effective.owner_identity:
            raise PartitionLeaseOwnerMismatchError(
                "sequencer identity does not own the active partition lease"
            )

    def _require_current_lease(
        self,
        partition_key: str,
    ) -> SequencerPartitionLease:
        self._validate_partition_key(partition_key)

        lease = self.repository.get(partition_key)

        if lease is None:
            raise PartitionLeaseNotFoundError(
                "partition lease does not exist"
            )

        return lease

    @staticmethod
    def _effective_lease(
        lease: SequencerPartitionLease,
        at: datetime,
    ) -> SequencerPartitionLease:
        if lease.status != PartitionLeaseStatus.ACTIVE:
            return lease

        if at >= lease.expires_at:
            return replace(
                lease,
                status=PartitionLeaseStatus.EXPIRED,
            )

        return lease

    @staticmethod
    def _validate_partition_key(
        partition_key: str,
    ) -> None:
        if (
            not isinstance(partition_key, str)
            or not partition_key.strip()
        ):
            raise PartitionLeaseError(
                "partition_key must not be empty"
            )

    @staticmethod
    def _validate_identity(
        owner_identity: str,
    ) -> None:
        if (
            not isinstance(owner_identity, str)
            or not owner_identity.strip()
        ):
            raise PartitionLeaseError(
                "owner identity must not be empty"
            )

    @staticmethod
    def _validate_epoch(
        epoch: int,
    ) -> None:
        if isinstance(epoch, bool) or not isinstance(epoch, int):
            raise PartitionLeaseError(
                "epoch must be an integer"
            )

        if epoch < 1:
            raise PartitionLeaseError(
                "epoch must be greater than or equal to one"
            )

    @staticmethod
    def _validate_duration(
        lease_duration_seconds: int,
    ) -> timedelta:
        if (
            isinstance(lease_duration_seconds, bool)
            or not isinstance(lease_duration_seconds, int)
        ):
            raise InvalidLeaseDurationError(
                "lease_duration_seconds must be an integer"
            )

        if lease_duration_seconds < 1:
            raise InvalidLeaseDurationError(
                "lease_duration_seconds must be greater than zero"
            )

        return timedelta(seconds=lease_duration_seconds)

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise PartitionLeaseError(
                f"{field_name} must be a datetime"
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise PartitionLeaseError(
                f"{field_name} must be timezone-aware"
            )

        return value.astimezone(timezone.utc)