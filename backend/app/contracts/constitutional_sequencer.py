from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,254}$")
VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _require_utc(value: datetime, field_name: str) -> datetime:
    """
    Require timezone-aware UTC timestamps.

    Constitutional records must never depend on local machine timezone
    interpretation.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")

    normalized = value.astimezone(timezone.utc)

    if normalized.utcoffset() != timezone.utc.utcoffset(normalized):
        raise ValueError(f"{field_name} must resolve to UTC")

    return normalized


def _validate_sha256(value: str, field_name: str) -> str:
    """
    Validate a lowercase, hexadecimal SHA-256 digest.
    """
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name} must be a 64-character lowercase hexadecimal SHA-256 hash"
        )

    return value


def _validate_identifier(value: str, field_name: str) -> str:
    """
    Validate identifiers used at constitutional trust boundaries.
    """
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name} contains unsupported characters or has an invalid length"
        )

    return value


def _validate_version(value: str, field_name: str) -> str:
    """
    Validate version identifiers such as OPV-1.0 or canonicalizer-1.0.
    """
    if not VERSION_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} is not a valid version identifier")

    return value


class FrozenContract(BaseModel):
    """
    Base class for immutable constitutional interface contracts.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class CandidateStatus(str, Enum):
    PREPARED = "PREPARED"
    SUBMITTED = "SUBMITTED"
    SEQUENCED = "SEQUENCED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class SequencerBatchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ORDERED = "ORDERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CommitStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ReplayStatus(str, Enum):
    EQUAL = "EQUAL"
    DIVERGENT = "DIVERGENT"
    INCOMPLETE = "INCOMPLETE"


class CanonicalEvidenceCandidate(FrozenContract):
    """
    Evidence prepared by the Canonicalization Zone.

    This contract does not grant authoritative order and does not represent a
    committed governance fact. It is a candidate submitted for sequencing.
    """

    candidate_id: UUID
    tenant_id: str
    lifecycle_instance_id: str
    source_event_id: str
    source_identity: str

    source_sequence: int | None = Field(default=None, ge=0)
    observed_at: datetime
    received_at: datetime

    canonical_payload: dict[str, Any]

    candidate_hash: str
    schema_version: str
    canonicalizer_version: str
    canonicalizer_identity: str

    signature: str | None = None
    status: CandidateStatus = CandidateStatus.PREPARED
    created_at: datetime

    @field_validator(
        "tenant_id",
        "lifecycle_instance_id",
        "source_event_id",
        "source_identity",
        "canonicalizer_identity",
    )
    @classmethod
    def validate_identifiers(cls, value: str, info) -> str:
        return _validate_identifier(value, info.field_name)

    @field_validator("schema_version", "canonicalizer_version")
    @classmethod
    def validate_versions(cls, value: str, info) -> str:
        return _validate_version(value, info.field_name)

    @field_validator("candidate_hash")
    @classmethod
    def validate_candidate_hash(cls, value: str) -> str:
        return _validate_sha256(value, "candidate_hash")

    @field_validator("observed_at", "received_at", "created_at")
    @classmethod
    def validate_timestamps(cls, value: datetime, info) -> datetime:
        return _require_utc(value, info.field_name)

    @field_validator("canonical_payload")
    @classmethod
    def canonical_payload_must_not_be_empty(
        cls,
        value: dict[str, Any],
    ) -> dict[str, Any]:
        if not value:
            raise ValueError("canonical_payload must not be empty")

        return value

    @model_validator(mode="after")
    def validate_candidate_timeline(self) -> CanonicalEvidenceCandidate:
        if self.received_at < self.observed_at:
            raise ValueError("received_at must not occur before observed_at")

        if self.created_at < self.received_at:
            raise ValueError("created_at must not occur before received_at")

        return self


class SequenceReceipt(FrozenContract):
    """
    Immutable proof that an authorized sequencer assigned authoritative order
    under a specific partition epoch and ordering-policy version.
    """

    receipt_id: UUID
    candidate_id: UUID
    candidate_hash: str

    tenant_id: str
    lifecycle_instance_id: str
    partition_key: str

    assigned_sequence: int = Field(ge=0)
    batch_id: UUID

    sequencer_epoch: int = Field(ge=1)
    sequencer_identity: str
    ordering_policy_version: str

    previous_receipt_hash: str
    receipt_hash: str

    issued_at: datetime

    @field_validator(
        "tenant_id",
        "lifecycle_instance_id",
        "partition_key",
        "sequencer_identity",
    )
    @classmethod
    def validate_identifiers(cls, value: str, info) -> str:
        return _validate_identifier(value, info.field_name)

    @field_validator("ordering_policy_version")
    @classmethod
    def validate_ordering_policy_version(cls, value: str) -> str:
        return _validate_version(value, "ordering_policy_version")

    @field_validator(
        "candidate_hash",
        "previous_receipt_hash",
        "receipt_hash",
    )
    @classmethod
    def validate_hashes(cls, value: str, info) -> str:
        return _validate_sha256(value, info.field_name)

    @field_validator("issued_at")
    @classmethod
    def validate_issued_at(cls, value: datetime) -> datetime:
        return _require_utc(value, "issued_at")


class SequencerBatchRequest(FrozenContract):
    """
    Request submitted to the Sequencer Security Zone.

    Candidate ordering inside this request is not authoritative. The sequencer
    must independently apply the recognized ordering policy.
    """

    batch_id: UUID
    partition_key: str
    tenant_id: str
    lifecycle_instance_id: str

    candidate_ids: tuple[UUID, ...] = Field(min_length=1)
    expected_epoch: int = Field(ge=1)
    ordering_policy_version: str

    requested_by: str
    requested_at: datetime

    @field_validator(
        "partition_key",
        "tenant_id",
        "lifecycle_instance_id",
        "requested_by",
    )
    @classmethod
    def validate_identifiers(cls, value: str, info) -> str:
        return _validate_identifier(value, info.field_name)

    @field_validator("ordering_policy_version")
    @classmethod
    def validate_ordering_policy_version(cls, value: str) -> str:
        return _validate_version(value, "ordering_policy_version")

    @field_validator("requested_at")
    @classmethod
    def validate_requested_at(cls, value: datetime) -> datetime:
        return _require_utc(value, "requested_at")

    @field_validator("candidate_ids")
    @classmethod
    def candidate_ids_must_be_unique(
        cls,
        value: tuple[UUID, ...],
    ) -> tuple[UUID, ...]:
        if len(value) != len(set(value)):
            raise ValueError("candidate_ids must not contain duplicates")

        return value


class SequencerBatchResult(FrozenContract):
    """
    Result emitted by the Sequencer Security Zone.
    """

    batch_id: UUID
    partition_key: str
    tenant_id: str
    lifecycle_instance_id: str

    sequencer_epoch: int = Field(ge=1)
    ordering_policy_version: str
    sequencer_identity: str

    receipt_ids: tuple[UUID, ...] = Field(default_factory=tuple)
    status: SequencerBatchStatus

    rejection_codes: tuple[str, ...] = Field(default_factory=tuple)

    started_at: datetime
    completed_at: datetime

    @field_validator(
        "partition_key",
        "tenant_id",
        "lifecycle_instance_id",
        "sequencer_identity",
    )
    @classmethod
    def validate_identifiers(cls, value: str, info) -> str:
        return _validate_identifier(value, info.field_name)

    @field_validator("ordering_policy_version")
    @classmethod
    def validate_ordering_policy_version(cls, value: str) -> str:
        return _validate_version(value, "ordering_policy_version")

    @field_validator("started_at", "completed_at")
    @classmethod
    def validate_timestamps(cls, value: datetime, info) -> datetime:
        return _require_utc(value, info.field_name)

    @model_validator(mode="after")
    def validate_result(self) -> SequencerBatchResult:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not occur before started_at")

        if len(self.receipt_ids) != len(set(self.receipt_ids)):
            raise ValueError("receipt_ids must not contain duplicates")

        if self.status in {
            SequencerBatchStatus.ORDERED,
            SequencerBatchStatus.ACCEPTED,
        }:
            if not self.receipt_ids:
                raise ValueError(
                    "ordered or accepted batches must contain sequence receipts"
                )

            if self.rejection_codes:
                raise ValueError(
                    "ordered or accepted batches must not contain rejection codes"
                )

        if self.status == SequencerBatchStatus.REJECTED:
            if not self.rejection_codes:
                raise ValueError(
                    "rejected batches must contain at least one rejection code"
                )

            if self.receipt_ids:
                raise ValueError(
                    "rejected batches must not contain sequence receipts"
                )

        return self


class ConstitutionalCommitRequest(FrozenContract):
    """
    Request submitted to the Constitutional Commit Gate.

    The Commit Gate must verify all referenced artifacts before authoritative
    governance state is created.
    """

    commit_request_id: UUID
    batch_id: UUID

    tenant_id: str
    lifecycle_instance_id: str
    partition_key: str

    candidate_ids: tuple[UUID, ...] = Field(min_length=1)
    receipt_ids: tuple[UUID, ...] = Field(min_length=1)

    sequencer_epoch: int = Field(ge=1)
    ordering_policy_version: str
    policy_version: str
    kernel_version: str

    prior_state_hash: str

    submitted_by: str
    submitted_at: datetime

    @field_validator(
        "tenant_id",
        "lifecycle_instance_id",
        "partition_key",
        "submitted_by",
    )
    @classmethod
    def validate_identifiers(cls, value: str, info) -> str:
        return _validate_identifier(value, info.field_name)

    @field_validator(
        "ordering_policy_version",
        "policy_version",
        "kernel_version",
    )
    @classmethod
    def validate_versions(cls, value: str, info) -> str:
        return _validate_version(value, info.field_name)

    @field_validator("prior_state_hash")
    @classmethod
    def validate_prior_state_hash(cls, value: str) -> str:
        return _validate_sha256(value, "prior_state_hash")

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_at(cls, value: datetime) -> datetime:
        return _require_utc(value, "submitted_at")

    @model_validator(mode="after")
    def validate_commit_request(self) -> ConstitutionalCommitRequest:
        if len(self.candidate_ids) != len(set(self.candidate_ids)):
            raise ValueError("candidate_ids must not contain duplicates")

        if len(self.receipt_ids) != len(set(self.receipt_ids)):
            raise ValueError("receipt_ids must not contain duplicates")

        if len(self.candidate_ids) != len(self.receipt_ids):
            raise ValueError(
                "candidate_ids and receipt_ids must have the same number of entries"
            )

        return self


class ConstitutionalCommitResult(FrozenContract):
    """
    Result emitted by the Constitutional Commit Gate.
    """

    commit_request_id: UUID
    batch_id: UUID

    status: CommitStatus

    decision_id: UUID | None = None
    ledger_offset: int | None = Field(default=None, ge=0)

    decision_hash: str | None = None
    resulting_state_hash: str | None = None

    rejection_codes: tuple[str, ...] = Field(default_factory=tuple)

    committed_at: datetime | None = None

    @field_validator("decision_hash", "resulting_state_hash")
    @classmethod
    def validate_optional_hashes(cls, value: str | None, info) -> str | None:
        if value is None:
            return None

        return _validate_sha256(value, info.field_name)

    @field_validator("committed_at")
    @classmethod
    def validate_committed_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        return _require_utc(value, "committed_at")

    @model_validator(mode="after")
    def validate_commit_result(self) -> ConstitutionalCommitResult:
        if self.status == CommitStatus.ACCEPTED:
            required_values = {
                "decision_id": self.decision_id,
                "ledger_offset": self.ledger_offset,
                "decision_hash": self.decision_hash,
                "resulting_state_hash": self.resulting_state_hash,
                "committed_at": self.committed_at,
            }

            missing = [
                field_name
                for field_name, field_value in required_values.items()
                if field_value is None
            ]

            if missing:
                raise ValueError(
                    "accepted commits require: " + ", ".join(sorted(missing))
                )

            if self.rejection_codes:
                raise ValueError(
                    "accepted commits must not contain rejection codes"
                )

        if self.status == CommitStatus.REJECTED:
            if not self.rejection_codes:
                raise ValueError(
                    "rejected commits must contain at least one rejection code"
                )

            forbidden_values = {
                "decision_id": self.decision_id,
                "ledger_offset": self.ledger_offset,
                "decision_hash": self.decision_hash,
                "resulting_state_hash": self.resulting_state_hash,
                "committed_at": self.committed_at,
            }

            present = [
                field_name
                for field_name, field_value in forbidden_values.items()
                if field_value is not None
            ]

            if present:
                raise ValueError(
                    "rejected commits must not contain authoritative outputs: "
                    + ", ".join(sorted(present))
                )

        return self


class ReplayVerificationResult(FrozenContract):
    """
    Deterministic replay comparison for a committed batch.
    """

    replay_id: UUID
    batch_id: UUID
    decision_id: UUID

    committed_decision_hash: str
    replayed_decision_hash: str | None

    committed_state_hash: str
    replayed_state_hash: str | None

    ordering_policy_version: str
    policy_version: str
    kernel_version: str

    replay_status: ReplayStatus
    equality: bool

    divergence_codes: tuple[str, ...] = Field(default_factory=tuple)

    replay_started_at: datetime
    replay_completed_at: datetime

    @field_validator(
        "committed_decision_hash",
        "replayed_decision_hash",
        "committed_state_hash",
        "replayed_state_hash",
    )
    @classmethod
    def validate_hashes(cls, value: str | None, info) -> str | None:
        if value is None:
            return None

        return _validate_sha256(value, info.field_name)

    @field_validator(
        "ordering_policy_version",
        "policy_version",
        "kernel_version",
    )
    @classmethod
    def validate_versions(cls, value: str, info) -> str:
        return _validate_version(value, info.field_name)

    @field_validator("replay_started_at", "replay_completed_at")
    @classmethod
    def validate_timestamps(cls, value: datetime, info) -> datetime:
        return _require_utc(value, info.field_name)

    @model_validator(mode="after")
    def validate_replay_result(self) -> ReplayVerificationResult:
        if self.replay_completed_at < self.replay_started_at:
            raise ValueError(
                "replay_completed_at must not occur before replay_started_at"
            )

        hashes_are_equal = (
            self.replayed_decision_hash is not None
            and self.replayed_state_hash is not None
            and self.committed_decision_hash == self.replayed_decision_hash
            and self.committed_state_hash == self.replayed_state_hash
        )

        if self.replay_status == ReplayStatus.EQUAL:
            if not self.equality:
                raise ValueError("EQUAL replay status requires equality=True")

            if not hashes_are_equal:
                raise ValueError(
                    "EQUAL replay status requires matching decision and state hashes"
                )

            if self.divergence_codes:
                raise ValueError(
                    "EQUAL replay status must not contain divergence codes"
                )

        if self.replay_status == ReplayStatus.DIVERGENT:
            if self.equality:
                raise ValueError(
                    "DIVERGENT replay status requires equality=False"
                )

            if not self.divergence_codes:
                raise ValueError(
                    "DIVERGENT replay status requires divergence codes"
                )

            if hashes_are_equal:
                raise ValueError(
                    "DIVERGENT replay status cannot contain fully equal hashes"
                )

        if self.replay_status == ReplayStatus.INCOMPLETE:
            if self.equality:
                raise ValueError(
                    "INCOMPLETE replay status requires equality=False"
                )

            if (
                self.replayed_decision_hash is not None
                and self.replayed_state_hash is not None
            ):
                raise ValueError(
                    "INCOMPLETE replay status requires at least one missing replay hash"
                )

        return self