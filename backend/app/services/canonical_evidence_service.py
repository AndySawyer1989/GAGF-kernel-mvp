from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from backend.app.contracts.constitutional_sequencer import (
    CandidateStatus,
    CanonicalEvidenceCandidate,
)


class CanonicalEvidenceError(ValueError):
    """
    Base exception for canonical evidence preparation failures.
    """


class CanonicalPayloadError(CanonicalEvidenceError):
    """
    Raised when a payload cannot be represented deterministically.
    """


class CandidateHashVerificationError(CanonicalEvidenceError):
    """
    Raised when a candidate hash does not match its constitutional contents.
    """


class CanonicalEvidenceService:
    """
    Prepares immutable evidence candidates for the Sequencer Security Zone.

    Constitutional boundary:

    This service may:

    - normalize payload values;
    - produce deterministic canonical JSON;
    - calculate candidate hashes;
    - create CanonicalEvidenceCandidate contracts;
    - verify candidate hash integrity.

    This service may not:

    - assign authoritative sequence numbers;
    - establish batch order;
    - issue sequence receipts;
    - select governance policy;
    - commit governance decisions;
    - mutate authoritative state.
    """

    HASH_ALGORITHM = "sha256"
    HASH_CONTRACT_VERSION = "candidate-hash-v1"

    @classmethod
    def canonicalize_payload(cls, payload: Mapping[str, Any]) -> dict[str, Any]:
        """
        Convert a source payload into a deterministic JSON-compatible mapping.

        Dictionary keys are sorted during serialization. Lists retain their
        original order because list order may carry source meaning.
        """
        if not isinstance(payload, Mapping):
            raise CanonicalPayloadError("payload must be a mapping")

        if not payload:
            raise CanonicalPayloadError("payload must not be empty")

        normalized = cls._normalize_value(payload, path="payload")

        if not isinstance(normalized, dict):
            raise CanonicalPayloadError(
                "canonical payload must resolve to a dictionary"
            )

        return normalized

    @classmethod
    def canonical_json(cls, value: Any) -> str:
        """
        Serialize a normalized value using the canonical JSON rules for
        candidate-hash-v1.
        """
        normalized = cls._normalize_value(value, path="value")

        try:
            return json.dumps(
                normalized,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise CanonicalPayloadError(
                f"value cannot be serialized canonically: {exc}"
            ) from exc

    @classmethod
    def calculate_candidate_hash(
        cls,
        *,
        tenant_id: str,
        lifecycle_instance_id: str,
        source_event_id: str,
        source_identity: str,
        source_sequence: int | None,
        observed_at: datetime,
        canonical_payload: Mapping[str, Any],
        schema_version: str,
        canonicalizer_version: str,
        canonicalizer_identity: str,
    ) -> str:
        """
        Calculate the deterministic constitutional hash for an evidence
        candidate.

        received_at, created_at, candidate_id, signature, and candidate status
        are intentionally excluded. They describe processing state rather than
        the source evidence identity.
        """
        normalized_observed_at = cls._normalize_datetime(
            observed_at,
            field_name="observed_at",
        )

        normalized_payload = cls.canonicalize_payload(canonical_payload)

        hash_envelope = {
            "hash_contract_version": cls.HASH_CONTRACT_VERSION,
            "tenant_id": cls._require_text(tenant_id, "tenant_id"),
            "lifecycle_instance_id": cls._require_text(
                lifecycle_instance_id,
                "lifecycle_instance_id",
            ),
            "source_event_id": cls._require_text(
                source_event_id,
                "source_event_id",
            ),
            "source_identity": cls._require_text(
                source_identity,
                "source_identity",
            ),
            "source_sequence": cls._validate_source_sequence(source_sequence),
            "observed_at": cls._datetime_to_canonical_string(
                normalized_observed_at
            ),
            "canonical_payload": normalized_payload,
            "schema_version": cls._require_text(
                schema_version,
                "schema_version",
            ),
            "canonicalizer_version": cls._require_text(
                canonicalizer_version,
                "canonicalizer_version",
            ),
            "canonicalizer_identity": cls._require_text(
                canonicalizer_identity,
                "canonicalizer_identity",
            ),
        }

        encoded = cls.canonical_json(hash_envelope).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def create_candidate(
        cls,
        *,
        tenant_id: str,
        lifecycle_instance_id: str,
        source_event_id: str,
        source_identity: str,
        observed_at: datetime,
        received_at: datetime,
        canonical_payload: Mapping[str, Any],
        schema_version: str,
        canonicalizer_version: str,
        canonicalizer_identity: str,
        source_sequence: int | None = None,
        signature: str | None = None,
        candidate_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> CanonicalEvidenceCandidate:
        """
        Create an immutable PREPARED candidate.

        The resulting candidate has no sequence number, no receipt, and no
        authority to affect governance state.
        """
        normalized_observed_at = cls._normalize_datetime(
            observed_at,
            field_name="observed_at",
        )
        normalized_received_at = cls._normalize_datetime(
            received_at,
            field_name="received_at",
        )

        if created_at is None:
            normalized_created_at = datetime.now(timezone.utc)
        else:
            normalized_created_at = cls._normalize_datetime(
                created_at,
                field_name="created_at",
            )

        if normalized_received_at < normalized_observed_at:
            raise CanonicalEvidenceError(
                "received_at must not occur before observed_at"
            )

        if normalized_created_at < normalized_received_at:
            raise CanonicalEvidenceError(
                "created_at must not occur before received_at"
            )

        normalized_payload = cls.canonicalize_payload(canonical_payload)

        candidate_hash = cls.calculate_candidate_hash(
            tenant_id=tenant_id,
            lifecycle_instance_id=lifecycle_instance_id,
            source_event_id=source_event_id,
            source_identity=source_identity,
            source_sequence=source_sequence,
            observed_at=normalized_observed_at,
            canonical_payload=normalized_payload,
            schema_version=schema_version,
            canonicalizer_version=canonicalizer_version,
            canonicalizer_identity=canonicalizer_identity,
        )

        return CanonicalEvidenceCandidate(
            candidate_id=candidate_id or uuid4(),
            tenant_id=tenant_id,
            lifecycle_instance_id=lifecycle_instance_id,
            source_event_id=source_event_id,
            source_identity=source_identity,
            source_sequence=source_sequence,
            observed_at=normalized_observed_at,
            received_at=normalized_received_at,
            canonical_payload=normalized_payload,
            candidate_hash=candidate_hash,
            schema_version=schema_version,
            canonicalizer_version=canonicalizer_version,
            canonicalizer_identity=canonicalizer_identity,
            signature=signature,
            status=CandidateStatus.PREPARED,
            created_at=normalized_created_at,
        )

    @classmethod
    def verify_candidate(
        cls,
        candidate: CanonicalEvidenceCandidate,
    ) -> bool:
        """
        Return True only when the candidate hash matches the candidate's
        constitutional hash fields.
        """
        expected_hash = cls.calculate_candidate_hash(
            tenant_id=candidate.tenant_id,
            lifecycle_instance_id=candidate.lifecycle_instance_id,
            source_event_id=candidate.source_event_id,
            source_identity=candidate.source_identity,
            source_sequence=candidate.source_sequence,
            observed_at=candidate.observed_at,
            canonical_payload=candidate.canonical_payload,
            schema_version=candidate.schema_version,
            canonicalizer_version=candidate.canonicalizer_version,
            canonicalizer_identity=candidate.canonicalizer_identity,
        )

        return expected_hash == candidate.candidate_hash

    @classmethod
    def assert_candidate_integrity(
        cls,
        candidate: CanonicalEvidenceCandidate,
    ) -> None:
        """
        Raise a constitutional verification exception when a candidate cannot
        be reproduced exactly.
        """
        if not cls.verify_candidate(candidate):
            raise CandidateHashVerificationError(
                "candidate hash verification failed"
            )

    @classmethod
    def _normalize_value(
        cls,
        value: Any,
        *,
        path: str,
    ) -> Any:
        """
        Recursively normalize values into deterministic JSON-compatible forms.
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            if not math.isfinite(value):
                raise CanonicalPayloadError(
                    f"{path} contains a non-finite floating-point value"
                )

            return value

        if isinstance(value, Decimal):
            if not value.is_finite():
                raise CanonicalPayloadError(
                    f"{path} contains a non-finite Decimal value"
                )

            return format(value, "f")

        if isinstance(value, datetime):
            normalized = cls._normalize_datetime(
                value,
                field_name=path,
            )
            return cls._datetime_to_canonical_string(normalized)

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, Enum):
            return cls._normalize_value(value.value, path=path)

        if isinstance(value, Mapping):
            normalized_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise CanonicalPayloadError(
                        f"{path} contains a non-string dictionary key"
                    )

                normalized_mapping[key] = cls._normalize_value(
                    item,
                    path=f"{path}.{key}",
                )

            return normalized_mapping

        if isinstance(value, (list, tuple)):
            return [
                cls._normalize_value(
                    item,
                    path=f"{path}[{index}]",
                )
                for index, item in enumerate(value)
            ]

        if isinstance(value, (set, frozenset)):
            raise CanonicalPayloadError(
                f"{path} contains an unordered collection"
            )

        if isinstance(value, (bytes, bytearray, memoryview)):
            raise CanonicalPayloadError(
                f"{path} contains raw binary data"
            )

        raise CanonicalPayloadError(
            f"{path} contains unsupported value type "
            f"{type(value).__name__}"
        )

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise CanonicalEvidenceError(f"{field_name} must be a string")

        normalized = value.strip()

        if not normalized:
            raise CanonicalEvidenceError(f"{field_name} must not be empty")

        return normalized

    @staticmethod
    def _validate_source_sequence(
        value: int | None,
    ) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, int):
            raise CanonicalEvidenceError(
                "source_sequence must be an integer or None"
            )

        if value < 0:
            raise CanonicalEvidenceError(
                "source_sequence must be greater than or equal to zero"
            )

        return value

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise CanonicalEvidenceError(
                f"{field_name} must be a datetime"
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise CanonicalEvidenceError(
                f"{field_name} must be timezone-aware"
            )

        return value.astimezone(timezone.utc)

    @staticmethod
    def _datetime_to_canonical_string(value: datetime) -> str:
        """
        Produce one stable UTC representation.

        Python emits +00:00 by default. The constitutional representation uses
        Z to make UTC explicit and portable.
        """
        normalized = value.astimezone(timezone.utc)

        return normalized.isoformat(timespec="microseconds").replace(
            "+00:00",
            "Z",
        )