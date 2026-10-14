from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)


GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE = (
    "governance-paid-work-authorization-record"
)
GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION = "0.1.0"
GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION = "1.0.0"


class GovernancePaidWorkAuthorizationRecordError(ValueError):
    """Raised when a PA-001 authorization record is invalid."""


class GovernancePaidWorkAuthorizationRecordIntegrityError(
    GovernancePaidWorkAuthorizationRecordError
):
    """Raised when a PA-001 authorization record fails integrity verification."""


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise GovernancePaidWorkAuthorizationRecordError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernancePaidWorkAuthorizationRecordError(
            f"{field_name} must not be empty"
        )

    return normalized


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _require_sha256(
    value: Any,
    field_name: str,
) -> str:
    normalized = _require_text(
        value,
        field_name,
    )

    if len(normalized) != 64:
        raise GovernancePaidWorkAuthorizationRecordError(
            f"{field_name} must be a 64-character SHA-256 digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise GovernancePaidWorkAuthorizationRecordError(
            f"{field_name} must be hexadecimal"
        ) from exc

    return normalized.lower()


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkAuthorizationRecord:
    authorization_id: str

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    contract_execution_event_id: str

    authorized_by: str
    authorized_at: str

    paid_assessment_authorized: bool

    authorization_hash: str
    record_hash: str

    record_type: str = (
        GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE
    )
    version: str = (
        GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION
    )
    schema_version: str = (
        GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        for field_name in (
            "authorization_id",
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "contract_execution_event_id",
            "authorized_by",
            "authorized_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if self.paid_assessment_authorized is not True:
            raise GovernancePaidWorkAuthorizationRecordError(
                "paid_assessment_authorized must be true"
            )

        object.__setattr__(
            self,
            "authorization_hash",
            _require_sha256(
                self.authorization_hash,
                "authorization_hash",
            ),
        )

        object.__setattr__(
            self,
            "record_hash",
            _require_sha256(
                self.record_hash,
                "record_hash",
            ),
        )

        if (
            self.record_type
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE
        ):
            raise GovernancePaidWorkAuthorizationRecordError(
                "unsupported paid-work authorization record type"
            )

        if (
            self.version
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION
        ):
            raise GovernancePaidWorkAuthorizationRecordError(
                "unsupported paid-work authorization record version"
            )

        if (
            self.schema_version
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION
        ):
            raise GovernancePaidWorkAuthorizationRecordError(
                "unsupported paid-work authorization record schema version"
            )

        expected_hash = self.compute_record_hash()

        if self.record_hash != expected_hash:
            raise GovernancePaidWorkAuthorizationRecordIntegrityError(
                "paid-work authorization record hash mismatch"
            )

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

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "record_type": self.record_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "authorization_id": self.authorization_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "contract_execution_event_id": (
                self.contract_execution_event_id
            ),
            "authorized_by": self.authorized_by,
            "authorized_at": self.authorized_at,
            "paid_assessment_authorized": (
                self.paid_assessment_authorized
            ),
            "authorization_hash": self.authorization_hash,
            "boundaries": {
                "recording_does_not_create_authority": True,
                "record_integrity_is_not_actor_authentication": True,
                "paid_work_authorization_is_not_trial_authorization": True,
                "paid_work_authorization_is_not_execution": True,
                "paid_work_authorization_is_not_delivery": True,
                "paid_work_authorization_is_not_intervention_authority": True,
            },
        }

    def compute_record_hash(self) -> str:
        return _sha256_text(
            _canonical_json(
                self.canonical_payload()
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.canonical_payload(),
            "record_hash": self.record_hash,
        }

    def to_paid_work_authorization(
        self,
    ) -> PaidAssessmentWorkAuthorization:
        return PaidAssessmentWorkAuthorization(
            authorization_id=self.authorization_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
            contract_execution_event_id=(
                self.contract_execution_event_id
            ),
            authorized_by=self.authorized_by,
            authorized_at=self.authorized_at,
            paid_assessment_authorized=True,
        )


def build_paid_work_authorization_record(
    *,
    authorization: PaidAssessmentWorkAuthorization,
) -> GovernancePaidWorkAuthorizationRecord:
    if not isinstance(
        authorization,
        PaidAssessmentWorkAuthorization,
    ):
        raise GovernancePaidWorkAuthorizationRecordError(
            "authorization must be a PaidAssessmentWorkAuthorization"
        )

    if authorization.paid_assessment_authorized is not True:
        raise GovernancePaidWorkAuthorizationRecordError(
            "paid-work authorization is not affirmative"
        )

    provisional = {
        "record_type": (
            GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE
        ),
        "version": (
            GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION
        ),
        "schema_version": (
            GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION
        ),
        "authorization_id": authorization.authorization_id,
        "tenant_id": authorization.tenant_id,
        "client_id": authorization.client_id,
        "engagement_id": authorization.engagement_id,
        "assessment_id": authorization.assessment_id,
        "hierarchy_key": "/".join(
            (
                authorization.tenant_id,
                authorization.client_id,
                authorization.engagement_id,
                authorization.assessment_id,
            )
        ),
        "contract_execution_event_id": (
            authorization.contract_execution_event_id
        ),
        "authorized_by": authorization.authorized_by,
        "authorized_at": authorization.authorized_at,
        "paid_assessment_authorized": True,
        "authorization_hash": authorization.authorization_hash,
        "boundaries": {
            "recording_does_not_create_authority": True,
            "record_integrity_is_not_actor_authentication": True,
            "paid_work_authorization_is_not_trial_authorization": True,
            "paid_work_authorization_is_not_execution": True,
            "paid_work_authorization_is_not_delivery": True,
            "paid_work_authorization_is_not_intervention_authority": True,
        },
    }

    record_hash = _sha256_text(
        _canonical_json(provisional)
    )

    return GovernancePaidWorkAuthorizationRecord(
        authorization_id=authorization.authorization_id,
        tenant_id=authorization.tenant_id,
        client_id=authorization.client_id,
        engagement_id=authorization.engagement_id,
        assessment_id=authorization.assessment_id,
        contract_execution_event_id=(
            authorization.contract_execution_event_id
        ),
        authorized_by=authorization.authorized_by,
        authorized_at=authorization.authorized_at,
        paid_assessment_authorized=True,
        authorization_hash=authorization.authorization_hash,
        record_hash=record_hash,
    )


def paid_work_authorization_record_from_dict(
    payload: Mapping[str, Any],
) -> GovernancePaidWorkAuthorizationRecord:
    if not isinstance(payload, Mapping):
        raise GovernancePaidWorkAuthorizationRecordError(
            "payload must be a mapping"
        )

    try:
        record = GovernancePaidWorkAuthorizationRecord(
            authorization_id=payload["authorization_id"],
            tenant_id=payload["tenant_id"],
            client_id=payload["client_id"],
            engagement_id=payload["engagement_id"],
            assessment_id=payload["assessment_id"],
            contract_execution_event_id=(
                payload["contract_execution_event_id"]
            ),
            authorized_by=payload["authorized_by"],
            authorized_at=payload["authorized_at"],
            paid_assessment_authorized=(
                payload["paid_assessment_authorized"]
            ),
            authorization_hash=payload["authorization_hash"],
            record_hash=payload["record_hash"],
            record_type=payload["record_type"],
            version=payload["version"],
            schema_version=payload["schema_version"],
        )
    except KeyError as exc:
        raise GovernancePaidWorkAuthorizationRecordError(
            f"missing paid-work authorization record field: {exc.args[0]}"
        ) from exc

    expected_boundaries = (
        record.canonical_payload()["boundaries"]
    )

    if payload.get("boundaries") != expected_boundaries:
        raise GovernancePaidWorkAuthorizationRecordIntegrityError(
            "paid-work authorization record boundaries mismatch"
        )

    if payload.get("hierarchy_key") != record.hierarchy_key:
        raise GovernancePaidWorkAuthorizationRecordIntegrityError(
            "paid-work authorization record hierarchy mismatch"
        )

    reconstructed = record.to_paid_work_authorization()

    if (
        reconstructed.authorization_hash
        != record.authorization_hash
    ):
        raise GovernancePaidWorkAuthorizationRecordIntegrityError(
            "paid-work authorization hash mismatch"
        )

    return record


def verify_paid_work_authorization_record(
    record: GovernancePaidWorkAuthorizationRecord,
) -> PaidAssessmentWorkAuthorization:
    if not isinstance(
        record,
        GovernancePaidWorkAuthorizationRecord,
    ):
        raise GovernancePaidWorkAuthorizationRecordError(
            "record must be a GovernancePaidWorkAuthorizationRecord"
        )

    if record.compute_record_hash() != record.record_hash:
        raise GovernancePaidWorkAuthorizationRecordIntegrityError(
            "paid-work authorization record hash mismatch"
        )

    authorization = record.to_paid_work_authorization()

    if authorization.authorization_hash != record.authorization_hash:
        raise GovernancePaidWorkAuthorizationRecordIntegrityError(
            "paid-work authorization hash mismatch"
        )

    return authorization