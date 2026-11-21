from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


PAID_WORK_PREREQUISITE_RECORD_TYPE = (
    "governance-paid-work-prerequisite-record"
)
PAID_WORK_PREREQUISITE_RECORD_VERSION = "0.1.0"
PAID_WORK_PREREQUISITE_SCHEMA_VERSION = "1.0.0"

AUTHORIZATION_PACKAGE_KIND = "authorization_package"
CONTRACT_EXECUTION_EVENT_KIND = "contract_execution_event"
PAYMENT_CONFIRMATION_EVENT_KIND = "payment_confirmation_event"

SUPPORTED_PREREQUISITE_KINDS = frozenset(
    {
        AUTHORIZATION_PACKAGE_KIND,
        CONTRACT_EXECUTION_EVENT_KIND,
        PAYMENT_CONFIRMATION_EVENT_KIND,
    }
)

_EXPECTED = {
    AUTHORIZATION_PACKAGE_KIND: {
        "event_type": (
            "assessment_factory_lite_paid_assessment_authorization_package"
        ),
        "status_field": "package_status",
        "status": "ready_for_paid_assessment_authorization",
        "id_field": "authorization_id",
        "timestamp_field": "prepared_at",
    },
    CONTRACT_EXECUTION_EVENT_KIND: {
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "status_field": "event_status",
        "status": "contract_executed",
        "id_field": "contract_execution_event_id",
        "timestamp_field": "recorded_at",
    },
    PAYMENT_CONFIRMATION_EVENT_KIND: {
        "event_type": (
            "assessment_factory_lite_payment_confirmation_event"
        ),
        "status_field": "event_status",
        "status": "payment_confirmed",
        "id_field": "payment_confirmation_event_id",
        "timestamp_field": "recorded_at",
    },
}


class GovernancePaidWorkPrerequisiteRecordError(ValueError):
    """Raised when a paid-work prerequisite record is invalid."""


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise GovernancePaidWorkPrerequisiteRecordError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernancePaidWorkPrerequisiteRecordError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_sha256(
    value: Any,
    field_name: str,
) -> str:
    normalized = _require_text(
        value,
        field_name,
    )

    if len(normalized) != 64:
        raise GovernancePaidWorkPrerequisiteRecordError(
            f"{field_name} must be a SHA-256 hex digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise GovernancePaidWorkPrerequisiteRecordError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc

    return normalized.lower()


def _canonical_json(
    value: Mapping[str, Any],
) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "artifact payload must be canonical-JSON serializable"
        ) from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _decode_canonical_artifact(
    canonical_artifact_json: str,
) -> dict[str, Any]:
    try:
        decoded = json.loads(
            canonical_artifact_json
        )
    except json.JSONDecodeError as exc:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "canonical_artifact_json is invalid JSON"
        ) from exc

    if not isinstance(decoded, dict):
        raise GovernancePaidWorkPrerequisiteRecordError(
            "canonical_artifact_json must decode to an object"
        )

    recanonicalized = _canonical_json(
        decoded
    )

    if recanonicalized != canonical_artifact_json:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "canonical_artifact_json is not canonical"
        )

    return decoded


def _expected_definition(
    prerequisite_kind: str,
) -> dict[str, str]:
    if prerequisite_kind not in SUPPORTED_PREREQUISITE_KINDS:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "unsupported prerequisite_kind"
        )

    return _EXPECTED[prerequisite_kind]


def _validate_artifact(
    *,
    prerequisite_kind: str,
    artifact: Mapping[str, Any],
) -> tuple[str, str, str, str]:
    expected = _expected_definition(
        prerequisite_kind
    )

    if artifact.get("status") != "ok":
        raise GovernancePaidWorkPrerequisiteRecordError(
            "prerequisite artifact status must be ok"
        )

    event_type = _require_text(
        artifact.get("event_type"),
        "artifact.event_type",
    )

    if event_type != expected["event_type"]:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "prerequisite artifact event_type does not match kind"
        )

    source_status = _require_text(
        artifact.get(
            expected["status_field"]
        ),
        (
            "artifact."
            + expected["status_field"]
        ),
    )

    if source_status != expected["status"]:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "prerequisite artifact is not in its required terminal status"
        )

    artifact_id = _require_text(
        artifact.get(
            expected["id_field"]
        ),
        (
            "artifact."
            + expected["id_field"]
        ),
    )

    source_timestamp = _require_text(
        artifact.get(
            expected["timestamp_field"]
        ),
        (
            "artifact."
            + expected["timestamp_field"]
        ),
    )

    if source_timestamp == "not_recorded":
        raise GovernancePaidWorkPrerequisiteRecordError(
            "prerequisite artifact source timestamp must be recorded"
        )

    return (
        event_type,
        source_status,
        artifact_id,
        source_timestamp,
    )


def _record_boundaries() -> dict[str, bool]:
    return {
        "recording_does_not_create_paid_work_authority": True,
        "package_readiness_is_not_paid_work_authority": True,
        "contract_execution_is_not_paid_work_authority": True,
        "payment_confirmation_is_not_paid_work_authority": True,
        "record_integrity_is_not_actor_authentication": True,
        "record_integrity_is_not_execution_authority": True,
        "record_integrity_is_not_delivery_authority": True,
        "record_integrity_is_not_intervention_authority": True,
    }


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkPrerequisiteRecord:
    prerequisite_kind: str
    artifact_id: str

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    source_event_type: str
    source_status: str
    source_timestamp: str

    artifact_hash: str
    canonical_artifact_json: str
    record_hash: str

    record_type: str = PAID_WORK_PREREQUISITE_RECORD_TYPE
    record_version: str = PAID_WORK_PREREQUISITE_RECORD_VERSION
    schema_version: str = PAID_WORK_PREREQUISITE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text(
            self.prerequisite_kind,
            "prerequisite_kind",
        )
        _expected_definition(
            self.prerequisite_kind
        )

        _require_text(
            self.artifact_id,
            "artifact_id",
        )

        _require_text(
            self.tenant_id,
            "tenant_id",
        )
        _require_text(
            self.client_id,
            "client_id",
        )
        _require_text(
            self.engagement_id,
            "engagement_id",
        )
        _require_text(
            self.assessment_id,
            "assessment_id",
        )

        _require_text(
            self.source_event_type,
            "source_event_type",
        )
        _require_text(
            self.source_status,
            "source_status",
        )
        _require_text(
            self.source_timestamp,
            "source_timestamp",
        )

        _require_sha256(
            self.artifact_hash,
            "artifact_hash",
        )
        _require_text(
            self.canonical_artifact_json,
            "canonical_artifact_json",
        )
        _require_sha256(
            self.record_hash,
            "record_hash",
        )

        if self.record_type != PAID_WORK_PREREQUISITE_RECORD_TYPE:
            raise GovernancePaidWorkPrerequisiteRecordError(
                "record_type does not match"
            )

        if (
            self.record_version
            != PAID_WORK_PREREQUISITE_RECORD_VERSION
        ):
            raise GovernancePaidWorkPrerequisiteRecordError(
                "record_version does not match"
            )

        if (
            self.schema_version
            != PAID_WORK_PREREQUISITE_SCHEMA_VERSION
        ):
            raise GovernancePaidWorkPrerequisiteRecordError(
                "schema_version does not match"
            )

        self.verify()

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    @property
    def artifact(self) -> dict[str, Any]:
        return _decode_canonical_artifact(
            self.canonical_artifact_json
        )

    def canonical_record_payload(
        self,
    ) -> dict[str, Any]:
        return {
            "record_type": self.record_type,
            "record_version": self.record_version,
            "schema_version": self.schema_version,
            "prerequisite_kind": self.prerequisite_kind,
            "artifact_id": self.artifact_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "source_event_type": self.source_event_type,
            "source_status": self.source_status,
            "source_timestamp": self.source_timestamp,
            "artifact_hash": self.artifact_hash,
            "canonical_artifact_json": (
                self.canonical_artifact_json
            ),
            "boundaries": _record_boundaries(),
        }

    def verify(self) -> None:
        artifact = _decode_canonical_artifact(
            self.canonical_artifact_json
        )

        (
            event_type,
            source_status,
            artifact_id,
            source_timestamp,
        ) = _validate_artifact(
            prerequisite_kind=(
                self.prerequisite_kind
            ),
            artifact=artifact,
        )

        if artifact_id != self.artifact_id:
            raise GovernancePaidWorkPrerequisiteRecordError(
                "artifact_id does not match artifact payload"
            )

        if event_type != self.source_event_type:
            raise GovernancePaidWorkPrerequisiteRecordError(
                "source_event_type does not match artifact payload"
            )

        if source_status != self.source_status:
            raise GovernancePaidWorkPrerequisiteRecordError(
                "source_status does not match artifact payload"
            )

        if source_timestamp != self.source_timestamp:
            raise GovernancePaidWorkPrerequisiteRecordError(
                "source_timestamp does not match artifact payload"
            )

        expected_artifact_hash = _sha256_text(
            self.canonical_artifact_json
        )

        if (
            expected_artifact_hash
            != self.artifact_hash
        ):
            raise GovernancePaidWorkPrerequisiteRecordError(
                "artifact_hash does not match artifact payload"
            )

        expected_record_hash = _sha256_text(
            _canonical_json(
                self.canonical_record_payload()
            )
        )

        if expected_record_hash != self.record_hash:
            raise GovernancePaidWorkPrerequisiteRecordError(
                "record_hash does not match record payload"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.canonical_record_payload(),
            "artifact": self.artifact,
            "record_hash": self.record_hash,
        }


def build_paid_work_prerequisite_record(
    *,
    prerequisite_kind: str,
    tenant_id: str,
    client_id: str,
    engagement_id: str,
    assessment_id: str,
    artifact: Mapping[str, Any],
) -> GovernancePaidWorkPrerequisiteRecord:
    prerequisite_kind = _require_text(
        prerequisite_kind,
        "prerequisite_kind",
    )
    _expected_definition(
        prerequisite_kind
    )

    tenant_id = _require_text(
        tenant_id,
        "tenant_id",
    )
    client_id = _require_text(
        client_id,
        "client_id",
    )
    engagement_id = _require_text(
        engagement_id,
        "engagement_id",
    )
    assessment_id = _require_text(
        assessment_id,
        "assessment_id",
    )

    if not isinstance(artifact, Mapping):
        raise GovernancePaidWorkPrerequisiteRecordError(
            "artifact must be a mapping"
        )

    canonical_artifact_json = _canonical_json(
        artifact
    )

    canonical_artifact = _decode_canonical_artifact(
        canonical_artifact_json
    )

    (
        source_event_type,
        source_status,
        artifact_id,
        source_timestamp,
    ) = _validate_artifact(
        prerequisite_kind=prerequisite_kind,
        artifact=canonical_artifact,
    )

    artifact_hash = _sha256_text(
        canonical_artifact_json
    )

    provisional = GovernancePaidWorkPrerequisiteRecord.__new__(
        GovernancePaidWorkPrerequisiteRecord
    )

    object.__setattr__(
        provisional,
        "prerequisite_kind",
        prerequisite_kind,
    )
    object.__setattr__(
        provisional,
        "artifact_id",
        artifact_id,
    )
    object.__setattr__(
        provisional,
        "tenant_id",
        tenant_id,
    )
    object.__setattr__(
        provisional,
        "client_id",
        client_id,
    )
    object.__setattr__(
        provisional,
        "engagement_id",
        engagement_id,
    )
    object.__setattr__(
        provisional,
        "assessment_id",
        assessment_id,
    )
    object.__setattr__(
        provisional,
        "source_event_type",
        source_event_type,
    )
    object.__setattr__(
        provisional,
        "source_status",
        source_status,
    )
    object.__setattr__(
        provisional,
        "source_timestamp",
        source_timestamp,
    )
    object.__setattr__(
        provisional,
        "artifact_hash",
        artifact_hash,
    )
    object.__setattr__(
        provisional,
        "canonical_artifact_json",
        canonical_artifact_json,
    )
    object.__setattr__(
        provisional,
        "record_hash",
        "0" * 64,
    )
    object.__setattr__(
        provisional,
        "record_type",
        PAID_WORK_PREREQUISITE_RECORD_TYPE,
    )
    object.__setattr__(
        provisional,
        "record_version",
        PAID_WORK_PREREQUISITE_RECORD_VERSION,
    )
    object.__setattr__(
        provisional,
        "schema_version",
        PAID_WORK_PREREQUISITE_SCHEMA_VERSION,
    )

    record_hash = _sha256_text(
        _canonical_json(
            provisional.canonical_record_payload()
        )
    )

    return GovernancePaidWorkPrerequisiteRecord(
        prerequisite_kind=prerequisite_kind,
        artifact_id=artifact_id,
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=engagement_id,
        assessment_id=assessment_id,
        source_event_type=source_event_type,
        source_status=source_status,
        source_timestamp=source_timestamp,
        artifact_hash=artifact_hash,
        canonical_artifact_json=canonical_artifact_json,
        record_hash=record_hash,
    )


def paid_work_prerequisite_record_from_dict(
    value: Mapping[str, Any],
) -> GovernancePaidWorkPrerequisiteRecord:
    if not isinstance(value, Mapping):
        raise GovernancePaidWorkPrerequisiteRecordError(
            "record value must be a mapping"
        )

    artifact = value.get("artifact")

    if not isinstance(artifact, Mapping):
        raise GovernancePaidWorkPrerequisiteRecordError(
            "record artifact must be a mapping"
        )

    canonical_artifact_json = _require_text(
        value.get("canonical_artifact_json"),
        "canonical_artifact_json",
    )

    if _canonical_json(artifact) != canonical_artifact_json:
        raise GovernancePaidWorkPrerequisiteRecordError(
            "artifact does not match canonical_artifact_json"
        )

    return GovernancePaidWorkPrerequisiteRecord(
        prerequisite_kind=_require_text(
            value.get("prerequisite_kind"),
            "prerequisite_kind",
        ),
        artifact_id=_require_text(
            value.get("artifact_id"),
            "artifact_id",
        ),
        tenant_id=_require_text(
            value.get("tenant_id"),
            "tenant_id",
        ),
        client_id=_require_text(
            value.get("client_id"),
            "client_id",
        ),
        engagement_id=_require_text(
            value.get("engagement_id"),
            "engagement_id",
        ),
        assessment_id=_require_text(
            value.get("assessment_id"),
            "assessment_id",
        ),
        source_event_type=_require_text(
            value.get("source_event_type"),
            "source_event_type",
        ),
        source_status=_require_text(
            value.get("source_status"),
            "source_status",
        ),
        source_timestamp=_require_text(
            value.get("source_timestamp"),
            "source_timestamp",
        ),
        artifact_hash=_require_sha256(
            value.get("artifact_hash"),
            "artifact_hash",
        ),
        canonical_artifact_json=canonical_artifact_json,
        record_hash=_require_sha256(
            value.get("record_hash"),
            "record_hash",
        ),
        record_type=_require_text(
            value.get("record_type"),
            "record_type",
        ),
        record_version=_require_text(
            value.get("record_version"),
            "record_version",
        ),
        schema_version=_require_text(
            value.get("schema_version"),
            "schema_version",
        ),
    )
