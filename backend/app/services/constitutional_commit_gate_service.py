from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence
from uuid import UUID, uuid4

from backend.app.contracts.constitutional_sequencer import (
    CanonicalEvidenceCandidate,
    CommitStatus,
    ConstitutionalCommitRequest,
    ConstitutionalCommitResult,
    SequenceReceipt,
)
from backend.app.services.canonical_evidence_service import (
    CanonicalEvidenceService,
)
from backend.app.services.constitutional_sequencer_service import (
    ConstitutionalSequencerService,
    ReceiptChainError,
)
from backend.app.services.sequencer_partition_lease_service import (
    SequencerPartitionLeaseService,
)


GENESIS_STATE_HASH = "0" * 64


class ConstitutionalCommitGateError(ValueError):
    """
    Base exception for Constitutional Commit Gate failures.
    """


class CommitBatchEmptyError(ConstitutionalCommitGateError):
    """
    Raised when a commit contains no candidates or receipts.
    """


class CommitBatchCardinalityError(ConstitutionalCommitGateError):
    """
    Raised when candidate and receipt counts do not match.
    """


class CommitBatchBindingError(ConstitutionalCommitGateError):
    """
    Raised when candidates, receipts, or the request are not bound together.
    """


class CommitPartitionMismatchError(ConstitutionalCommitGateError):
    """
    Raised when a commit crosses tenant, lifecycle, or partition boundaries.
    """


class CommitEpochMismatchError(ConstitutionalCommitGateError):
    """
    Raised when the receipt epoch differs from the authorized commit epoch.
    """


class CommitPolicyMismatchError(ConstitutionalCommitGateError):
    """
    Raised when policy or ordering-policy versions conflict.
    """


class CommitCandidateIntegrityError(ConstitutionalCommitGateError):
    """
    Raised when candidate integrity verification fails.
    """


class CommitReceiptIntegrityError(ConstitutionalCommitGateError):
    """
    Raised when receipt or receipt-chain verification fails.
    """


class PreviousStateHashMismatchError(ConstitutionalCommitGateError):
    """
    Raised when the caller presents a stale or incorrect prior state.
    """


class DuplicateCommitBatchError(ConstitutionalCommitGateError):
    """
    Raised when an already-committed batch is submitted again.
    """


class DuplicateDecisionHashError(ConstitutionalCommitGateError):
    """
    Raised when an already-committed deterministic decision is submitted again.
    """


class UnsupportedCommitContractError(ConstitutionalCommitGateError):
    """
    Raised when the requested commit contract is unsupported.
    """


@dataclass(frozen=True)
class GovernanceStateTransition:
    """
    Immutable constitutional state transition.
    """

    partition_key: str
    prior_state_hash: str
    resulting_state_hash: str
    policy_version: str
    kernel_version: str
    ordering_policy_version: str
    candidate_hashes: tuple[str, ...]
    receipt_hashes: tuple[str, ...]


@dataclass(frozen=True)
class ConstitutionalCommitRecord:
    """
    Immutable authoritative record produced by a successful Commit Gate action.
    """

    commit_request_id: UUID
    batch_id: UUID
    decision_id: UUID

    tenant_id: str
    lifecycle_instance_id: str
    partition_key: str

    candidate_ids: tuple[UUID, ...]
    receipt_ids: tuple[UUID, ...]

    sequencer_epoch: int
    ordering_policy_version: str
    policy_version: str
    kernel_version: str
    commit_contract_version: str

    prior_state_hash: str
    resulting_state_hash: str
    decision_hash: str

    ledger_offset: int
    committed_at: datetime


class InMemoryConstitutionalCommitRepository:
    """
    In-memory atomic commit repository for the MVP.

    All validation occurs before repository mutation. The repository then
    performs duplicate checks and applies the complete commit in one method.
    """

    def __init__(self) -> None:
        self._records_by_batch: dict[
            UUID,
            ConstitutionalCommitRecord,
        ] = {}

        self._records_by_decision_hash: dict[
            str,
            ConstitutionalCommitRecord,
        ] = {}

        self._current_state_by_partition: dict[str, str] = {}
        self._records_by_partition: dict[
            str,
            list[ConstitutionalCommitRecord],
        ] = {}

        self._next_ledger_offset = 0

    def get_by_batch_id(
        self,
        batch_id: UUID,
    ) -> ConstitutionalCommitRecord | None:
        return self._records_by_batch.get(batch_id)

    def get_by_decision_hash(
        self,
        decision_hash: str,
    ) -> ConstitutionalCommitRecord | None:
        return self._records_by_decision_hash.get(decision_hash)

    def get_current_state_hash(
        self,
        partition_key: str,
    ) -> str:
        return self._current_state_by_partition.get(
            partition_key,
            GENESIS_STATE_HASH,
        )

    def list_partition_records(
        self,
        partition_key: str,
    ) -> tuple[ConstitutionalCommitRecord, ...]:
        return tuple(
            self._records_by_partition.get(partition_key, [])
        )

    def next_ledger_offset(self) -> int:
        return self._next_ledger_offset

    def commit(
        self,
        record: ConstitutionalCommitRecord,
    ) -> ConstitutionalCommitRecord:
        """
        Apply one complete authoritative commit atomically.

        No repository mutation occurs before all duplicate and state-continuity
        checks pass.
        """
        if record.batch_id in self._records_by_batch:
            raise DuplicateCommitBatchError(
                "batch has already been committed"
            )

        if record.decision_hash in self._records_by_decision_hash:
            raise DuplicateDecisionHashError(
                "decision hash has already been committed"
            )

        current_state = self.get_current_state_hash(
            record.partition_key
        )

        if current_state != record.prior_state_hash:
            raise PreviousStateHashMismatchError(
                "repository state changed before commit"
            )

        if record.ledger_offset != self._next_ledger_offset:
            raise ConstitutionalCommitGateError(
                "ledger offset does not match repository next offset"
            )

        self._records_by_batch[record.batch_id] = record
        self._records_by_decision_hash[
            record.decision_hash
        ] = record

        self._current_state_by_partition[
            record.partition_key
        ] = record.resulting_state_hash

        partition_records = self._records_by_partition.setdefault(
            record.partition_key,
            [],
        )
        partition_records.append(record)

        self._next_ledger_offset += 1

        return record


class ConstitutionalCommitGateService:
    """
    Converts valid, ordered, authorized evidence into authoritative state.

    Constitutional boundary:

    The Commit Gate may:

    - verify candidates and sequence receipts;
    - verify receipt-chain continuity;
    - validate active lease authority;
    - enforce prior-state continuity;
    - calculate deterministic state and decision hashes;
    - atomically persist an authoritative commit.

    The Commit Gate may not:

    - canonicalize raw source evidence;
    - assign sequence numbers;
    - issue sequence receipts;
    - acquire or transfer partition leases;
    - modify previous commit records.
    """

    COMMIT_CONTRACT_VERSION = "constitutional-commit-v1"
    SUPPORTED_COMMIT_CONTRACTS = frozenset(
        {
            COMMIT_CONTRACT_VERSION,
        }
    )

    def __init__(
        self,
        *,
        lease_service: SequencerPartitionLeaseService,
        repository: InMemoryConstitutionalCommitRepository | None = None,
    ) -> None:
        self.lease_service = lease_service
        self.repository = (
            repository
            or InMemoryConstitutionalCommitRepository()
        )

    def commit_batch(
        self,
        *,
        request: ConstitutionalCommitRequest,
        candidates: Sequence[CanonicalEvidenceCandidate],
        receipts: Sequence[SequenceReceipt],
        committed_at: datetime,
        commit_contract_version: str = COMMIT_CONTRACT_VERSION,
        decision_id: UUID | None = None,
    ) -> ConstitutionalCommitResult:
        """
        Validate and atomically commit one ordered evidence batch.
        """
        normalized_committed_at = self._normalize_datetime(
            committed_at,
            "committed_at",
        )

        self._validate_commit_contract(
            commit_contract_version
        )

        if (
            self.repository.get_by_batch_id(
                request.batch_id
            )
            is not None
        ):
            raise DuplicateCommitBatchError(
                "batch has already been committed"
            )

        candidate_tuple = tuple(candidates)
        receipt_tuple = tuple(receipts)

        self._validate_non_empty(
            candidates=candidate_tuple,
            receipts=receipt_tuple,
        )

        self._validate_cardinality(
            request=request,
            candidates=candidate_tuple,
            receipts=receipt_tuple,
        )

        self._validate_request_scope(
            request=request,
            candidates=candidate_tuple,
            receipts=receipt_tuple,
        )

        self._validate_candidate_integrity(candidate_tuple)

        self._validate_candidate_receipt_bindings(
            request=request,
            candidates=candidate_tuple,
            receipts=receipt_tuple,
        )

        self._validate_receipt_authority(
            request=request,
            receipts=receipt_tuple,
        )

        self._validate_receipt_integrity(receipt_tuple)

        self.lease_service.assert_authorized(
            partition_key=request.partition_key,
            owner_identity=request.submitted_by,
            epoch=request.sequencer_epoch,
            at=normalized_committed_at,
        )

        current_state_hash = (
            self.repository.get_current_state_hash(
                request.partition_key
            )
        )

        if request.prior_state_hash != current_state_hash:
            raise PreviousStateHashMismatchError(
                "prior_state_hash does not match current partition state"
            )

        ordered_candidates = self._order_candidates_by_receipts(
            candidates=candidate_tuple,
            receipts=receipt_tuple,
        )

        ordered_receipts = tuple(
            sorted(
                receipt_tuple,
                key=lambda receipt: receipt.assigned_sequence,
            )
        )

        resulting_state_hash = self.calculate_resulting_state_hash(
            partition_key=request.partition_key,
            prior_state_hash=request.prior_state_hash,
            candidate_hashes=tuple(
                candidate.candidate_hash
                for candidate in ordered_candidates
            ),
            receipt_hashes=tuple(
                receipt.receipt_hash
                for receipt in ordered_receipts
            ),
            ordering_policy_version=(
                request.ordering_policy_version
            ),
            policy_version=request.policy_version,
            kernel_version=request.kernel_version,
            commit_contract_version=commit_contract_version,
        )

        decision_hash = self.calculate_decision_hash(
            commit_request_id=request.commit_request_id,
            batch_id=request.batch_id,
            partition_key=request.partition_key,
            sequencer_epoch=request.sequencer_epoch,
            prior_state_hash=request.prior_state_hash,
            resulting_state_hash=resulting_state_hash,
            candidate_hashes=tuple(
                candidate.candidate_hash
                for candidate in ordered_candidates
            ),
            receipt_hashes=tuple(
                receipt.receipt_hash
                for receipt in ordered_receipts
            ),
            ordering_policy_version=(
                request.ordering_policy_version
            ),
            policy_version=request.policy_version,
            kernel_version=request.kernel_version,
            commit_contract_version=commit_contract_version,
        )

        resolved_decision_id = decision_id or uuid4()
        ledger_offset = self.repository.next_ledger_offset()

        record = ConstitutionalCommitRecord(
            commit_request_id=request.commit_request_id,
            batch_id=request.batch_id,
            decision_id=resolved_decision_id,
            tenant_id=request.tenant_id,
            lifecycle_instance_id=(
                request.lifecycle_instance_id
            ),
            partition_key=request.partition_key,
            candidate_ids=tuple(
                candidate.candidate_id
                for candidate in ordered_candidates
            ),
            receipt_ids=tuple(
                receipt.receipt_id
                for receipt in ordered_receipts
            ),
            sequencer_epoch=request.sequencer_epoch,
            ordering_policy_version=(
                request.ordering_policy_version
            ),
            policy_version=request.policy_version,
            kernel_version=request.kernel_version,
            commit_contract_version=commit_contract_version,
            prior_state_hash=request.prior_state_hash,
            resulting_state_hash=resulting_state_hash,
            decision_hash=decision_hash,
            ledger_offset=ledger_offset,
            committed_at=normalized_committed_at,
        )

        committed_record = self.repository.commit(record)

        return ConstitutionalCommitResult(
            commit_request_id=(
                committed_record.commit_request_id
            ),
            batch_id=committed_record.batch_id,
            status=CommitStatus.ACCEPTED,
            decision_id=committed_record.decision_id,
            ledger_offset=committed_record.ledger_offset,
            decision_hash=committed_record.decision_hash,
            resulting_state_hash=(
                committed_record.resulting_state_hash
            ),
            rejection_codes=(),
            committed_at=committed_record.committed_at,
        )

    @classmethod
    def calculate_resulting_state_hash(
        cls,
        *,
        partition_key: str,
        prior_state_hash: str,
        candidate_hashes: tuple[str, ...],
        receipt_hashes: tuple[str, ...],
        ordering_policy_version: str,
        policy_version: str,
        kernel_version: str,
        commit_contract_version: str = COMMIT_CONTRACT_VERSION,
    ) -> str:
        """
        Calculate the deterministic state produced by an accepted batch.
        """
        cls._validate_sha256(
            prior_state_hash,
            "prior_state_hash",
        )

        if not candidate_hashes:
            raise CommitBatchEmptyError(
                "candidate_hashes must not be empty"
            )

        if len(candidate_hashes) != len(receipt_hashes):
            raise CommitBatchCardinalityError(
                "candidate and receipt hash counts must match"
            )

        for candidate_hash in candidate_hashes:
            cls._validate_sha256(
                candidate_hash,
                "candidate_hash",
            )

        for receipt_hash in receipt_hashes:
            cls._validate_sha256(
                receipt_hash,
                "receipt_hash",
            )

        envelope = {
            "commit_contract_version": (
                commit_contract_version
            ),
            "partition_key": partition_key,
            "prior_state_hash": prior_state_hash,
            "candidate_hashes": list(candidate_hashes),
            "receipt_hashes": list(receipt_hashes),
            "ordering_policy_version": (
                ordering_policy_version
            ),
            "policy_version": policy_version,
            "kernel_version": kernel_version,
        }

        return cls._hash_envelope(envelope)

    @classmethod
    def calculate_decision_hash(
        cls,
        *,
        commit_request_id: UUID,
        batch_id: UUID,
        partition_key: str,
        sequencer_epoch: int,
        prior_state_hash: str,
        resulting_state_hash: str,
        candidate_hashes: tuple[str, ...],
        receipt_hashes: tuple[str, ...],
        ordering_policy_version: str,
        policy_version: str,
        kernel_version: str,
        commit_contract_version: str = COMMIT_CONTRACT_VERSION,
    ) -> str:
        """
        Calculate the deterministic constitutional decision hash.
        """
        cls._validate_sha256(
            prior_state_hash,
            "prior_state_hash",
        )
        cls._validate_sha256(
            resulting_state_hash,
            "resulting_state_hash",
        )

        envelope = {
            "commit_contract_version": (
                commit_contract_version
            ),
            "commit_request_id": str(commit_request_id),
            "batch_id": str(batch_id),
            "partition_key": partition_key,
            "sequencer_epoch": sequencer_epoch,
            "prior_state_hash": prior_state_hash,
            "resulting_state_hash": resulting_state_hash,
            "candidate_hashes": list(candidate_hashes),
            "receipt_hashes": list(receipt_hashes),
            "ordering_policy_version": (
                ordering_policy_version
            ),
            "policy_version": policy_version,
            "kernel_version": kernel_version,
        }

        return cls._hash_envelope(envelope)
    @staticmethod
    def _validate_candidate_integrity(
        candidates: tuple[CanonicalEvidenceCandidate, ...],
    ) -> None:
        for candidate in candidates:
            if not CanonicalEvidenceService.verify_candidate(
                candidate
            ):
                raise CommitCandidateIntegrityError(
                    "candidate hash verification failed"
                )

    @staticmethod
    def _validate_non_empty(
        *,
        candidates: tuple[CanonicalEvidenceCandidate, ...],
        receipts: tuple[SequenceReceipt, ...],
    ) -> None:
        if not candidates:
            raise CommitBatchEmptyError(
                "commit batch must contain candidates"
            )

        if not receipts:
            raise CommitBatchEmptyError(
                "commit batch must contain receipts"
            )

    @staticmethod
    def _validate_cardinality(
        *,
        request: ConstitutionalCommitRequest,
        candidates: tuple[CanonicalEvidenceCandidate, ...],
        receipts: tuple[SequenceReceipt, ...],
    ) -> None:
        if len(candidates) != len(receipts):
            raise CommitBatchCardinalityError(
                "candidate and receipt counts must match"
            )

        if len(request.candidate_ids) != len(candidates):
            raise CommitBatchCardinalityError(
                "request candidate count does not match supplied candidates"
            )

        if len(request.receipt_ids) != len(receipts):
            raise CommitBatchCardinalityError(
                "request receipt count does not match supplied receipts"
            )

    @staticmethod
    def _validate_request_scope(
        *,
        request: ConstitutionalCommitRequest,
        candidates: tuple[CanonicalEvidenceCandidate, ...],
        receipts: tuple[SequenceReceipt, ...],
    ) -> None:
        for candidate in candidates:
            if candidate.tenant_id != request.tenant_id:
                raise CommitPartitionMismatchError(
                    "candidate tenant does not match commit request"
                )

            if (
                candidate.lifecycle_instance_id
                != request.lifecycle_instance_id
            ):
                raise CommitPartitionMismatchError(
                    "candidate lifecycle does not match commit request"
                )

        for receipt in receipts:
            if receipt.batch_id != request.batch_id:
                raise CommitBatchBindingError(
                    "receipt batch_id does not match commit request"
                )

            if receipt.tenant_id != request.tenant_id:
                raise CommitPartitionMismatchError(
                    "receipt tenant does not match commit request"
                )

            if (
                receipt.lifecycle_instance_id
                != request.lifecycle_instance_id
            ):
                raise CommitPartitionMismatchError(
                    "receipt lifecycle does not match commit request"
                )

            if receipt.partition_key != request.partition_key:
                raise CommitPartitionMismatchError(
                    "receipt partition does not match commit request"
                )

    @staticmethod
    def _validate_receipt_integrity(
        receipts: tuple[SequenceReceipt, ...],
    ) -> None:
        ordered_receipts = tuple(
            sorted(
                receipts,
                key=lambda receipt: receipt.assigned_sequence,
            )
        )

        try:
            ConstitutionalSequencerService.verify_receipt_chain(
                ordered_receipts,
                expected_starting_sequence=(
                    ordered_receipts[0].assigned_sequence
                ),
                expected_previous_receipt_hash=(
                    ordered_receipts[0].previous_receipt_hash
                ),
            )

            for receipt in ordered_receipts:
                if not ConstitutionalSequencerService.verify_receipt(
                    receipt
                ):
                    raise CommitReceiptIntegrityError(
                        "sequence receipt hash verification failed"
                    )

        except CommitReceiptIntegrityError:
            raise

        except ValueError as exc:
            raise CommitReceiptIntegrityError(
                str(exc)
            ) from exc

    @staticmethod
    def _validate_candidate_receipt_bindings(
        *,
        request: ConstitutionalCommitRequest,
        candidates: tuple[CanonicalEvidenceCandidate, ...],
        receipts: tuple[SequenceReceipt, ...],
    ) -> None:
        candidates_by_id = {
            candidate.candidate_id: candidate
            for candidate in candidates
        }

        receipts_by_id = {
            receipt.receipt_id: receipt
            for receipt in receipts
        }

        if set(request.candidate_ids) != set(candidates_by_id):
            raise CommitBatchBindingError(
                "request candidate_ids do not match supplied candidates"
            )

        if set(request.receipt_ids) != set(receipts_by_id):
            raise CommitBatchBindingError(
                "request receipt_ids do not match supplied receipts"
            )

        receipt_candidate_ids = {
            receipt.candidate_id
            for receipt in receipts
        }

        if receipt_candidate_ids != set(candidates_by_id):
            raise CommitBatchBindingError(
                "receipt candidate bindings do not match supplied candidates"
            )

        for receipt in receipts:
            candidate = candidates_by_id.get(
                receipt.candidate_id
            )

            if candidate is None:
                raise CommitBatchBindingError(
                    "receipt references an unknown candidate"
                )

            if receipt.candidate_id != candidate.candidate_id:
                raise CommitBatchBindingError(
                    "receipt candidate_id does not match candidate"
                )

            if receipt.candidate_hash != candidate.candidate_hash:
                raise CommitBatchBindingError(
                    "receipt candidate_hash does not match candidate"
                )

            if receipt.tenant_id != candidate.tenant_id:
                raise CommitBatchBindingError(
                    "receipt tenant_id does not match candidate"
                )

            if (
                receipt.lifecycle_instance_id
                != candidate.lifecycle_instance_id
            ):
                raise CommitBatchBindingError(
                    "receipt lifecycle_instance_id does not match candidate"
                )

    @staticmethod
    def _validate_receipt_authority(
        *,
        request: ConstitutionalCommitRequest,
        receipts: tuple[SequenceReceipt, ...],
    ) -> None:
        for receipt in receipts:
            if receipt.sequencer_epoch != request.sequencer_epoch:
                raise CommitEpochMismatchError(
                    "receipt epoch does not match commit request"
                )

            if (
                receipt.sequencer_identity
                != request.submitted_by
            ):
                raise CommitBatchBindingError(
                    "receipt sequencer identity does not match submitter"
                )

            if (
                receipt.ordering_policy_version
                != request.ordering_policy_version
            ):
                raise CommitPolicyMismatchError(
                    "receipt ordering policy does not match commit request"
                )

    @staticmethod
    def _order_candidates_by_receipts(
        *,
        candidates: tuple[CanonicalEvidenceCandidate, ...],
        receipts: tuple[SequenceReceipt, ...],
    ) -> tuple[CanonicalEvidenceCandidate, ...]:
        candidates_by_id = {
            candidate.candidate_id: candidate
            for candidate in candidates
        }

        ordered_receipts = sorted(
            receipts,
            key=lambda receipt: receipt.assigned_sequence,
        )

        return tuple(
            candidates_by_id[receipt.candidate_id]
            for receipt in ordered_receipts
        )

    @classmethod
    def _validate_commit_contract(
        cls,
        commit_contract_version: str,
    ) -> None:
        if (
            commit_contract_version
            not in cls.SUPPORTED_COMMIT_CONTRACTS
        ):
            raise UnsupportedCommitContractError(
                "unsupported commit contract version"
            )

    @staticmethod
    def _hash_envelope(
        envelope: Mapping[str, object],
    ) -> str:
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

    @staticmethod
    def _validate_sha256(
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
            raise ConstitutionalCommitGateError(
                f"{field_name} must be a lowercase SHA-256 hash"
            )

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ConstitutionalCommitGateError(
                f"{field_name} must be a datetime"
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ConstitutionalCommitGateError(
                f"{field_name} must be timezone-aware"
            )

        return value.astimezone(timezone.utc)


