from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence
from uuid import UUID, uuid4

from backend.app.contracts.constitutional_sequencer import (
    CandidateStatus,
    CanonicalEvidenceCandidate,
    SequenceReceipt,
    SequencerBatchResult,
    SequencerBatchStatus,
)
from backend.app.services.canonical_evidence_service import (
    CanonicalEvidenceService,
)


GENESIS_RECEIPT_HASH = "0" * 64


class ConstitutionalSequencerError(ValueError):
    """
    Base exception for Sequencer Security Zone failures.
    """


class EmptySequencerBatchError(ConstitutionalSequencerError):
    """
    Raised when no evidence candidates are submitted for sequencing.
    """


class SequencerPartitionMismatchError(ConstitutionalSequencerError):
    """
    Raised when a batch contains candidates from different causal partitions.
    """


class DuplicateCandidateError(ConstitutionalSequencerError):
    """
    Raised when a batch contains duplicate candidate identifiers or hashes.
    """


class CandidateIntegrityError(ConstitutionalSequencerError):
    """
    Raised when a candidate fails constitutional hash verification.
    """


class CandidateStatusError(ConstitutionalSequencerError):
    """
    Raised when a candidate is not eligible to enter the sequencing boundary.
    """


class ReceiptIntegrityError(ConstitutionalSequencerError):
    """
    Raised when a sequence receipt cannot be cryptographically reproduced.
    """


class ReceiptChainError(ConstitutionalSequencerError):
    """
    Raised when sequence continuity or receipt-chain continuity is broken.
    """


class UnsupportedOrderingPolicyError(ConstitutionalSequencerError):
    """
    Raised when the requested ordering policy is unknown.
    """


@dataclass(frozen=True)
class SequencingOutcome:
    """
    Internal service outcome containing the batch result and issued receipts.
    """

    batch_result: SequencerBatchResult
    receipts: tuple[SequenceReceipt, ...]


class ConstitutionalSequencerService:
    """
    Assigns authoritative local order within one causal partition.

    Constitutional boundary:

    This service may:

    - verify prepared evidence candidates;
    - apply a recognized deterministic ordering policy;
    - assign local authoritative sequence numbers;
    - create immutable sequence receipts;
    - cryptographically chain those receipts;
    - return an ordered batch result.

    This service may not:

    - grant or renew sequencer partition leases;
    - determine whether its epoch is currently authoritative;
    - execute governance policy;
    - commit authoritative governance state;
    - mutate the evidence ledger.

    Epoch ownership enforcement is introduced in US-059D.
    """

    RECEIPT_HASH_CONTRACT_VERSION = "sequence-receipt-hash-v1"
    DEFAULT_ORDERING_POLICY_VERSION = "OPV-1.0"
    SUPPORTED_ORDERING_POLICIES = frozenset(
        {
            DEFAULT_ORDERING_POLICY_VERSION,
        }
    )

    @classmethod
    def sequence_candidates(
        cls,
        *,
        candidates: Sequence[CanonicalEvidenceCandidate],
        partition_key: str,
        sequencer_epoch: int,
        sequencer_identity: str,
        ordering_policy_version: str = DEFAULT_ORDERING_POLICY_VERSION,
        starting_sequence: int = 1,
        previous_receipt_hash: str = GENESIS_RECEIPT_HASH,
        batch_id: UUID | None = None,
        issued_at: datetime | None = None,
    ) -> SequencingOutcome:
        """
        Verify, order, and issue one immutable receipt per candidate.

        All candidates must belong to the same tenant and lifecycle partition.
        """
        if not candidates:
            raise EmptySequencerBatchError(
                "sequencer batch must contain at least one candidate"
            )

        cls._validate_partition_key(partition_key)
        cls._validate_epoch(sequencer_epoch)
        cls._validate_sequence(starting_sequence, "starting_sequence")
        cls._validate_identity(sequencer_identity)
        cls._validate_hash(
            previous_receipt_hash,
            "previous_receipt_hash",
        )
        cls._validate_ordering_policy(ordering_policy_version)

        normalized_issued_at = cls._normalize_datetime(
            issued_at or datetime.now(timezone.utc),
            "issued_at",
        )

        candidate_tuple = tuple(candidates)

        cls._validate_candidates(
            candidates=candidate_tuple,
            partition_key=partition_key,
        )

        ordered_candidates = cls.order_candidates(
            candidate_tuple,
            ordering_policy_version=ordering_policy_version,
        )

        resolved_batch_id = batch_id or uuid4()

        receipts: list[SequenceReceipt] = []
        current_previous_hash = previous_receipt_hash

        for offset, candidate in enumerate(ordered_candidates):
            assigned_sequence = starting_sequence + offset

            receipt_hash = cls.calculate_receipt_hash(
                candidate_id=candidate.candidate_id,
                candidate_hash=candidate.candidate_hash,
                tenant_id=candidate.tenant_id,
                lifecycle_instance_id=candidate.lifecycle_instance_id,
                partition_key=partition_key,
                assigned_sequence=assigned_sequence,
                batch_id=resolved_batch_id,
                sequencer_epoch=sequencer_epoch,
                sequencer_identity=sequencer_identity,
                ordering_policy_version=ordering_policy_version,
                previous_receipt_hash=current_previous_hash,
                issued_at=normalized_issued_at,
            )

            receipt = SequenceReceipt(
                receipt_id=uuid4(),
                candidate_id=candidate.candidate_id,
                candidate_hash=candidate.candidate_hash,
                tenant_id=candidate.tenant_id,
                lifecycle_instance_id=candidate.lifecycle_instance_id,
                partition_key=partition_key,
                assigned_sequence=assigned_sequence,
                batch_id=resolved_batch_id,
                sequencer_epoch=sequencer_epoch,
                sequencer_identity=sequencer_identity,
                ordering_policy_version=ordering_policy_version,
                previous_receipt_hash=current_previous_hash,
                receipt_hash=receipt_hash,
                issued_at=normalized_issued_at,
            )

            receipts.append(receipt)
            current_previous_hash = receipt.receipt_hash

        batch_result = SequencerBatchResult(
            batch_id=resolved_batch_id,
            partition_key=partition_key,
            tenant_id=ordered_candidates[0].tenant_id,
            lifecycle_instance_id=ordered_candidates[0].lifecycle_instance_id,
            sequencer_epoch=sequencer_epoch,
            ordering_policy_version=ordering_policy_version,
            sequencer_identity=sequencer_identity,
            receipt_ids=tuple(
                receipt.receipt_id
                for receipt in receipts
            ),
            status=SequencerBatchStatus.ORDERED,
            rejection_codes=(),
            started_at=normalized_issued_at,
            completed_at=normalized_issued_at,
        )

        return SequencingOutcome(
            batch_result=batch_result,
            receipts=tuple(receipts),
        )

    @classmethod
    def order_candidates(
        cls,
        candidates: Iterable[CanonicalEvidenceCandidate],
        *,
        ordering_policy_version: str = DEFAULT_ORDERING_POLICY_VERSION,
    ) -> tuple[CanonicalEvidenceCandidate, ...]:
        """
        Apply the recognized constitutional ordering comparator.

        OPV-1.0 ordering:

        1. source_sequence presence
        2. source_sequence
        3. observed_at
        4. source_event_id
        5. candidate_id

        Candidates with a valid source_sequence are ordered before candidates
        lacking one.
        """
        cls._validate_ordering_policy(ordering_policy_version)

        candidate_tuple = tuple(candidates)

        return tuple(
            sorted(
                candidate_tuple,
                key=cls._ordering_key_v1,
            )
        )

    @classmethod
    def calculate_receipt_hash(
        cls,
        *,
        candidate_id: UUID,
        candidate_hash: str,
        tenant_id: str,
        lifecycle_instance_id: str,
        partition_key: str,
        assigned_sequence: int,
        batch_id: UUID,
        sequencer_epoch: int,
        sequencer_identity: str,
        ordering_policy_version: str,
        previous_receipt_hash: str,
        issued_at: datetime,
    ) -> str:
        """
        Calculate the deterministic cryptographic hash for a sequence receipt.
        """
        cls._validate_hash(candidate_hash, "candidate_hash")
        cls._validate_hash(
            previous_receipt_hash,
            "previous_receipt_hash",
        )
        cls._validate_sequence(
            assigned_sequence,
            "assigned_sequence",
        )
        cls._validate_epoch(sequencer_epoch)
        cls._validate_partition_key(partition_key)
        cls._validate_identity(sequencer_identity)
        cls._validate_ordering_policy(ordering_policy_version)

        normalized_issued_at = cls._normalize_datetime(
            issued_at,
            "issued_at",
        )

        envelope = {
            "receipt_hash_contract_version": (
                cls.RECEIPT_HASH_CONTRACT_VERSION
            ),
            "candidate_id": str(candidate_id),
            "candidate_hash": candidate_hash,
            "tenant_id": tenant_id,
            "lifecycle_instance_id": lifecycle_instance_id,
            "partition_key": partition_key,
            "assigned_sequence": assigned_sequence,
            "batch_id": str(batch_id),
            "sequencer_epoch": sequencer_epoch,
            "sequencer_identity": sequencer_identity,
            "ordering_policy_version": ordering_policy_version,
            "previous_receipt_hash": previous_receipt_hash,
            "issued_at": cls._datetime_to_canonical_string(
                normalized_issued_at
            ),
        }

        serialized = json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    @classmethod
    def verify_receipt(
        cls,
        receipt: SequenceReceipt,
    ) -> bool:
        """
        Return True only if the receipt hash can be reproduced exactly.
        """
        expected_hash = cls.calculate_receipt_hash(
            candidate_id=receipt.candidate_id,
            candidate_hash=receipt.candidate_hash,
            tenant_id=receipt.tenant_id,
            lifecycle_instance_id=receipt.lifecycle_instance_id,
            partition_key=receipt.partition_key,
            assigned_sequence=receipt.assigned_sequence,
            batch_id=receipt.batch_id,
            sequencer_epoch=receipt.sequencer_epoch,
            sequencer_identity=receipt.sequencer_identity,
            ordering_policy_version=receipt.ordering_policy_version,
            previous_receipt_hash=receipt.previous_receipt_hash,
            issued_at=receipt.issued_at,
        )

        return expected_hash == receipt.receipt_hash

    @classmethod
    def assert_receipt_integrity(
        cls,
        receipt: SequenceReceipt,
    ) -> None:
        """
        Raise if a sequence receipt cannot be cryptographically reproduced.
        """
        if not cls.verify_receipt(receipt):
            raise ReceiptIntegrityError(
                "sequence receipt hash verification failed"
            )

    @classmethod
    def verify_receipt_chain(
        cls,
        receipts: Sequence[SequenceReceipt],
        *,
        expected_starting_sequence: int = 1,
        expected_previous_receipt_hash: str = GENESIS_RECEIPT_HASH,
    ) -> bool:
        """
        Verify sequence continuity and cryptographic receipt-chain continuity.
        """
        if not receipts:
            raise ReceiptChainError(
                "receipt chain must contain at least one receipt"
            )

        cls._validate_sequence(
            expected_starting_sequence,
            "expected_starting_sequence",
        )
        cls._validate_hash(
            expected_previous_receipt_hash,
            "expected_previous_receipt_hash",
        )

        first = receipts[0]

        expected_batch_id = first.batch_id
        expected_partition_key = first.partition_key
        expected_tenant_id = first.tenant_id
        expected_lifecycle_instance_id = (
            first.lifecycle_instance_id
        )
        expected_epoch = first.sequencer_epoch
        expected_policy_version = (
            first.ordering_policy_version
        )
        expected_sequencer_identity = (
            first.sequencer_identity
        )

        previous_hash = expected_previous_receipt_hash

        for index, receipt in enumerate(receipts):
            expected_sequence = (
                expected_starting_sequence + index
            )

            if receipt.assigned_sequence != expected_sequence:
                raise ReceiptChainError(
                    "receipt sequence continuity violation"
                )

            if receipt.previous_receipt_hash != previous_hash:
                raise ReceiptChainError(
                    "receipt hash-chain continuity violation"
                )

            if receipt.batch_id != expected_batch_id:
                raise ReceiptChainError(
                    "receipt chain contains multiple batch identifiers"
                )

            if receipt.partition_key != expected_partition_key:
                raise ReceiptChainError(
                    "receipt chain contains multiple partitions"
                )

            if receipt.tenant_id != expected_tenant_id:
                raise ReceiptChainError(
                    "receipt chain contains multiple tenants"
                )

            if (
                receipt.lifecycle_instance_id
                != expected_lifecycle_instance_id
            ):
                raise ReceiptChainError(
                    "receipt chain contains multiple lifecycle instances"
                )

            if receipt.sequencer_epoch != expected_epoch:
                raise ReceiptChainError(
                    "receipt chain contains multiple sequencer epochs"
                )

            if (
                receipt.ordering_policy_version
                != expected_policy_version
            ):
                raise ReceiptChainError(
                    "receipt chain contains multiple ordering policies"
                )

            if (
                receipt.sequencer_identity
                != expected_sequencer_identity
            ):
                raise ReceiptChainError(
                    "receipt chain contains multiple sequencer identities"
                )

            cls.assert_receipt_integrity(receipt)
            previous_hash = receipt.receipt_hash

        return True

    @classmethod
    def assert_candidate_receipt_binding(
        cls,
        *,
        candidate: CanonicalEvidenceCandidate,
        receipt: SequenceReceipt,
    ) -> None:
        """
        Verify that a receipt is bound to the exact candidate submitted.
        """
        if receipt.candidate_id != candidate.candidate_id:
            raise ReceiptIntegrityError(
                "receipt candidate_id does not match candidate"
            )

        if receipt.candidate_hash != candidate.candidate_hash:
            raise ReceiptIntegrityError(
                "receipt candidate_hash does not match candidate"
            )

        if receipt.tenant_id != candidate.tenant_id:
            raise ReceiptIntegrityError(
                "receipt tenant_id does not match candidate"
            )

        if (
            receipt.lifecycle_instance_id
            != candidate.lifecycle_instance_id
        ):
            raise ReceiptIntegrityError(
                "receipt lifecycle_instance_id does not match candidate"
            )

        cls.assert_receipt_integrity(receipt)

    @classmethod
    def _validate_candidates(
        cls,
        *,
        candidates: tuple[CanonicalEvidenceCandidate, ...],
        partition_key: str,
    ) -> None:
        candidate_ids: set[UUID] = set()
        candidate_hashes: set[str] = set()

        first = candidates[0]
        expected_tenant_id = first.tenant_id
        expected_lifecycle_instance_id = (
            first.lifecycle_instance_id
        )
        expected_partition_key = cls.build_partition_key(
            tenant_id=expected_tenant_id,
            lifecycle_instance_id=expected_lifecycle_instance_id,
        )

        if partition_key != expected_partition_key:
            raise SequencerPartitionMismatchError(
                "partition_key does not match candidate tenant and lifecycle"
            )

        for candidate in candidates:
            if candidate.status not in {
                CandidateStatus.PREPARED,
                CandidateStatus.SUBMITTED,
            }:
                raise CandidateStatusError(
                    "candidate must be PREPARED or SUBMITTED before sequencing"
                )

            if candidate.tenant_id != expected_tenant_id:
                raise SequencerPartitionMismatchError(
                    "sequencer batch contains multiple tenants"
                )

            if (
                candidate.lifecycle_instance_id
                != expected_lifecycle_instance_id
            ):
                raise SequencerPartitionMismatchError(
                    "sequencer batch contains multiple lifecycle instances"
                )

            if candidate.candidate_id in candidate_ids:
                raise DuplicateCandidateError(
                    "sequencer batch contains duplicate candidate_id"
                )

            if candidate.candidate_hash in candidate_hashes:
                raise DuplicateCandidateError(
                    "sequencer batch contains duplicate candidate_hash"
                )

            if not CanonicalEvidenceService.verify_candidate(
                candidate
            ):
                raise CandidateIntegrityError(
                    "candidate hash verification failed"
                )

            candidate_ids.add(candidate.candidate_id)
            candidate_hashes.add(candidate.candidate_hash)

    @staticmethod
    def build_partition_key(
        *,
        tenant_id: str,
        lifecycle_instance_id: str,
    ) -> str:
        """
        Construct the canonical local causality partition key.
        """
        if not tenant_id or not tenant_id.strip():
            raise ConstitutionalSequencerError(
                "tenant_id must not be empty"
            )

        if (
            not lifecycle_instance_id
            or not lifecycle_instance_id.strip()
        ):
            raise ConstitutionalSequencerError(
                "lifecycle_instance_id must not be empty"
            )

        return (
            f"{tenant_id.strip()}/"
            f"{lifecycle_instance_id.strip()}"
        )

    @staticmethod
    def _ordering_key_v1(
        candidate: CanonicalEvidenceCandidate,
    ) -> tuple:
        source_sequence_missing = (
            candidate.source_sequence is None
        )

        source_sequence_value = (
            candidate.source_sequence
            if candidate.source_sequence is not None
            else 0
        )

        return (
            source_sequence_missing,
            source_sequence_value,
            candidate.observed_at,
            candidate.source_event_id,
            str(candidate.candidate_id),
        )

    @classmethod
    def _validate_ordering_policy(
        cls,
        ordering_policy_version: str,
    ) -> None:
        if (
            ordering_policy_version
            not in cls.SUPPORTED_ORDERING_POLICIES
        ):
            raise UnsupportedOrderingPolicyError(
                "unsupported ordering policy version: "
                f"{ordering_policy_version}"
            )

    @staticmethod
    def _validate_partition_key(
        partition_key: str,
    ) -> None:
        if (
            not isinstance(partition_key, str)
            or not partition_key.strip()
        ):
            raise ConstitutionalSequencerError(
                "partition_key must not be empty"
            )

    @staticmethod
    def _validate_identity(
        sequencer_identity: str,
    ) -> None:
        if (
            not isinstance(sequencer_identity, str)
            or not sequencer_identity.strip()
        ):
            raise ConstitutionalSequencerError(
                "sequencer_identity must not be empty"
            )

    @staticmethod
    def _validate_epoch(
        sequencer_epoch: int,
    ) -> None:
        if (
            isinstance(sequencer_epoch, bool)
            or not isinstance(sequencer_epoch, int)
        ):
            raise ConstitutionalSequencerError(
                "sequencer_epoch must be an integer"
            )

        if sequencer_epoch < 1:
            raise ConstitutionalSequencerError(
                "sequencer_epoch must be greater than or equal to one"
            )

    @staticmethod
    def _validate_sequence(
        sequence: int,
        field_name: str,
    ) -> None:
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            raise ConstitutionalSequencerError(
                f"{field_name} must be an integer"
            )

        if sequence < 0:
            raise ConstitutionalSequencerError(
                f"{field_name} must be greater than or equal to zero"
            )

    @staticmethod
    def _validate_hash(
        value: str,
        field_name: str,
    ) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(
                character not in "0123456789abcdef"
                for character in value
            )
        ):
            raise ConstitutionalSequencerError(
                f"{field_name} must be a lowercase SHA-256 hash"
            )

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ConstitutionalSequencerError(
                f"{field_name} must be a datetime"
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ConstitutionalSequencerError(
                f"{field_name} must be timezone-aware"
            )

        return value.astimezone(timezone.utc)

    @staticmethod
    def _datetime_to_canonical_string(
        value: datetime,
    ) -> str:
        return value.astimezone(timezone.utc).isoformat(
            timespec="microseconds"
        ).replace(
            "+00:00",
            "Z",
        )