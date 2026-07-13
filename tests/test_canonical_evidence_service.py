from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.app.contracts.constitutional_sequencer import (
    CandidateStatus,
    CanonicalEvidenceCandidate,
)
from backend.app.services.canonical_evidence_service import (
    CandidateHashVerificationError,
    CanonicalEvidenceError,
    CanonicalEvidenceService,
    CanonicalPayloadError,
)


UTC = timezone.utc


class ExampleStatus(str, Enum):
    ACTIVE = "active"


def utc_time(
    hour: int = 12,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    return datetime(
        2026,
        7,
        10,
        hour,
        minute,
        second,
        tzinfo=UTC,
    )


def candidate_kwargs() -> dict:
    return {
        "tenant_id": "tenant-a",
        "lifecycle_instance_id": "lifecycle-001",
        "source_event_id": "source-event-001",
        "source_identity": "github-connector",
        "source_sequence": 10,
        "observed_at": utc_time(12, 0),
        "received_at": utc_time(12, 1),
        "canonical_payload": {
            "event_type": "APPROVAL_REQUIRED",
            "work_item_id": "work-item-001",
            "metadata": {
                "review_required": True,
                "priority": 3,
            },
        },
        "schema_version": "constraint-event-1.0",
        "canonicalizer_version": "canonicalizer-1.0",
        "canonicalizer_identity": "canonicalizer-worker-01",
        "created_at": utc_time(12, 2),
    }


def test_create_candidate_returns_prepared_immutable_contract():
    candidate = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )

    assert isinstance(candidate, CanonicalEvidenceCandidate)
    assert candidate.status == CandidateStatus.PREPARED
    assert len(candidate.candidate_hash) == 64

    with pytest.raises(ValidationError):
        candidate.status = CandidateStatus.SEQUENCED


def test_same_inputs_produce_same_candidate_hash():
    first = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )
    second = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )

    assert first.candidate_id != second.candidate_id
    assert first.candidate_hash == second.candidate_hash


def test_dictionary_key_order_does_not_change_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()

    first_args["canonical_payload"] = {
        "event_type": "APPROVAL_REQUIRED",
        "metadata": {
            "priority": 3,
            "review_required": True,
        },
        "work_item_id": "work-item-001",
    }

    second_args["canonical_payload"] = {
        "work_item_id": "work-item-001",
        "metadata": {
            "review_required": True,
            "priority": 3,
        },
        "event_type": "APPROVAL_REQUIRED",
    }

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash == second.candidate_hash


def test_payload_change_changes_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()

    second_args["canonical_payload"] = {
        **second_args["canonical_payload"],
        "event_type": "APPROVAL_DELAYED",
    }

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash != second.candidate_hash


def test_tenant_change_changes_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()
    second_args["tenant_id"] = "tenant-b"

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash != second.candidate_hash


def test_lifecycle_change_changes_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()
    second_args["lifecycle_instance_id"] = "lifecycle-002"

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash != second.candidate_hash


def test_source_sequence_change_changes_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()
    second_args["source_sequence"] = 11

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash != second.candidate_hash


def test_schema_version_change_changes_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()
    second_args["schema_version"] = "constraint-event-1.1"

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash != second.candidate_hash


def test_received_at_does_not_change_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()

    second_args["received_at"] = utc_time(12, 5)
    second_args["created_at"] = utc_time(12, 6)

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash == second.candidate_hash


def test_candidate_id_does_not_change_hash():
    first_args = candidate_kwargs()
    second_args = candidate_kwargs()

    first_args["candidate_id"] = uuid4()
    second_args["candidate_id"] = uuid4()

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.candidate_hash == second.candidate_hash


def test_timezone_offsets_normalize_to_same_hash():
    eastern = timezone(timedelta(hours=-4))

    first_args = candidate_kwargs()
    second_args = candidate_kwargs()

    second_args["observed_at"] = datetime(
        2026,
        7,
        10,
        8,
        0,
        tzinfo=eastern,
    )

    first = CanonicalEvidenceService.create_candidate(**first_args)
    second = CanonicalEvidenceService.create_candidate(**second_args)

    assert first.observed_at == second.observed_at
    assert first.candidate_hash == second.candidate_hash


def test_payload_normalizes_supported_structured_values():
    evidence_uuid = UUID("12345678-1234-5678-1234-567812345678")

    payload = {
        "event_id": evidence_uuid,
        "occurred_at": utc_time(12, 0),
        "event_date": date(2026, 7, 10),
        "score": Decimal("12.500"),
        "status": ExampleStatus.ACTIVE,
        "coordinates": (1, 2, 3),
    }

    normalized = CanonicalEvidenceService.canonicalize_payload(payload)

    assert normalized == {
        "event_id": "12345678-1234-5678-1234-567812345678",
        "occurred_at": "2026-07-10T12:00:00.000000Z",
        "event_date": "2026-07-10",
        "score": "12.500",
        "status": "active",
        "coordinates": [1, 2, 3],
    }


def test_canonical_json_is_compact_and_sorted():
    serialized = CanonicalEvidenceService.canonical_json(
        {
            "z": 3,
            "a": 1,
            "middle": {
                "b": 2,
                "a": 1,
            },
        }
    )

    assert serialized == (
        '{"a":1,"middle":{"a":1,"b":2},"z":3}'
    )


def test_empty_payload_is_rejected():
    args = candidate_kwargs()
    args["canonical_payload"] = {}

    with pytest.raises(
        CanonicalPayloadError,
        match="payload must not be empty",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_non_mapping_payload_is_rejected():
    with pytest.raises(
        CanonicalPayloadError,
        match="payload must be a mapping",
    ):
        CanonicalEvidenceService.canonicalize_payload(
            ["not", "a", "mapping"]
        )


def test_non_string_dictionary_key_is_rejected():
    with pytest.raises(
        CanonicalPayloadError,
        match="non-string dictionary key",
    ):
        CanonicalEvidenceService.canonicalize_payload(
            {
                "event_type": "APPROVAL_REQUIRED",
                7: "invalid-key",
            }
        )


def test_unordered_collection_is_rejected():
    args = candidate_kwargs()
    args["canonical_payload"] = {
        "event_type": "APPROVAL_REQUIRED",
        "unordered_values": {"a", "b"},
    }

    with pytest.raises(
        CanonicalPayloadError,
        match="unordered collection",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_raw_binary_data_is_rejected():
    args = candidate_kwargs()
    args["canonical_payload"] = {
        "event_type": "APPROVAL_REQUIRED",
        "binary": b"unsafe-for-canonical-json",
    }

    with pytest.raises(
        CanonicalPayloadError,
        match="raw binary data",
    ):
        CanonicalEvidenceService.create_candidate(**args)


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_non_finite_float_is_rejected(value):
    args = candidate_kwargs()
    args["canonical_payload"] = {
        "event_type": "APPROVAL_REQUIRED",
        "score": value,
    }

    with pytest.raises(
        CanonicalPayloadError,
        match="non-finite floating-point value",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_naive_observed_at_is_rejected():
    args = candidate_kwargs()
    args["observed_at"] = datetime(2026, 7, 10, 12, 0)

    with pytest.raises(
        CanonicalEvidenceError,
        match="observed_at must be timezone-aware",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_received_at_before_observed_at_is_rejected():
    args = candidate_kwargs()
    args["received_at"] = utc_time(11, 59)

    with pytest.raises(
        CanonicalEvidenceError,
        match="received_at must not occur before observed_at",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_created_at_before_received_at_is_rejected():
    args = candidate_kwargs()
    args["created_at"] = utc_time(12, 0)

    with pytest.raises(
        CanonicalEvidenceError,
        match="created_at must not occur before received_at",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_negative_source_sequence_is_rejected():
    args = candidate_kwargs()
    args["source_sequence"] = -1

    with pytest.raises(
        CanonicalEvidenceError,
        match="source_sequence must be greater than or equal to zero",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_boolean_source_sequence_is_rejected():
    args = candidate_kwargs()
    args["source_sequence"] = True

    with pytest.raises(
        CanonicalEvidenceError,
        match="source_sequence must be an integer or None",
    ):
        CanonicalEvidenceService.create_candidate(**args)


def test_verify_candidate_returns_true_for_valid_candidate():
    candidate = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )

    assert CanonicalEvidenceService.verify_candidate(candidate) is True


def test_verify_candidate_returns_false_for_tampered_hash():
    candidate = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )

    tampered = candidate.model_copy(
        update={"candidate_hash": "f" * 64}
    )

    assert CanonicalEvidenceService.verify_candidate(tampered) is False


def test_assert_candidate_integrity_accepts_valid_candidate():
    candidate = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )

    CanonicalEvidenceService.assert_candidate_integrity(candidate)


def test_assert_candidate_integrity_rejects_tampered_candidate():
    candidate = CanonicalEvidenceService.create_candidate(
        **candidate_kwargs()
    )

    tampered = candidate.model_copy(
        update={"candidate_hash": "f" * 64}
    )

    with pytest.raises(
        CandidateHashVerificationError,
        match="candidate hash verification failed",
    ):
        CanonicalEvidenceService.assert_candidate_integrity(tampered)




