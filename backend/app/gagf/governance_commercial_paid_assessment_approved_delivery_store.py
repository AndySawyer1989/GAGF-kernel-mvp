from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_ID = (
    "governance-commercial-paid-assessment-approved-delivery-store"
)
COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_SCHEMA_VERSION = "1.0.0"

TABLE_NAME = "governance_commercial_paid_assessment_approved_deliveries"


class CommercialPaidAssessmentApprovedDeliveryStoreError(RuntimeError):
    """Raised when approved delivery material cannot be stored safely."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommercialPaidAssessmentApprovedDeliveryStoreError(
            f"{field_name} must be non-empty"
        )
    return value.strip()


def _require_hash(value: Any, field_name: str) -> str:
    normalized = _require_text(value, field_name)
    if len(normalized) != 64 or normalized != normalized.lower():
        raise CommercialPaidAssessmentApprovedDeliveryStoreError(
            f"{field_name} must be a lowercase SHA-256 hex digest"
        )
    try:
        int(normalized, 16)
    except ValueError as exc:
        raise CommercialPaidAssessmentApprovedDeliveryStoreError(
            f"{field_name} must be a lowercase SHA-256 hex digest"
        ) from exc
    return normalized


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentApprovedDeliverySnapshot:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    execution_status_hash: str
    operator_snapshot_hash: str

    approved_delivery_payload: dict[str, Any]
    approved_delivery_payload_hash: str
    snapshot_hash: str

    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_SCHEMA_VERSION
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "store_type": COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_ID,
            "version": COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_VERSION,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "execution_status_hash": self.execution_status_hash,
            "operator_snapshot_hash": self.operator_snapshot_hash,
            "approved_delivery_payload_hash": (
                self.approved_delivery_payload_hash
            ),
            "snapshot_hash": self.snapshot_hash,
            "boundaries": {
                "snapshot_is_internal_only": True,
                "snapshot_is_not_approval_authority": True,
                "snapshot_is_not_delivery_authority": True,
                "snapshot_is_not_client_receipt": True,
                "real_approval_handoff_remains_authoritative": True,
                "pa003_remains_delivery_envelope_authority": True,
            },
        }


class GovernanceCommercialPaidAssessmentApprovedDeliveryStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    hierarchy_key TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,
                    execution_status_hash TEXT NOT NULL,
                    operator_snapshot_hash TEXT NOT NULL,
                    approved_delivery_payload_json TEXT NOT NULL,
                    approved_delivery_payload_hash TEXT NOT NULL,
                    snapshot_hash TEXT NOT NULL,
                    schema_version TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def put(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        execution_status_hash: str,
        operator_snapshot_hash: str,
        approved_delivery_payload: dict[str, Any],
    ) -> CommercialPaidAssessmentApprovedDeliverySnapshot:
        tenant_id = _require_text(tenant_id, "tenant_id")
        client_id = _require_text(client_id, "client_id")
        engagement_id = _require_text(engagement_id, "engagement_id")
        assessment_id = _require_text(assessment_id, "assessment_id")
        execution_status_hash = _require_hash(
            execution_status_hash,
            "execution_status_hash",
        )
        operator_snapshot_hash = _require_hash(
            operator_snapshot_hash,
            "operator_snapshot_hash",
        )

        if not isinstance(approved_delivery_payload, dict):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved_delivery_payload must be an object"
            )

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        if (
            approved_delivery_payload.get("operator_handoff_passed")
            is not True
        ):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery operator handoff must be explicitly true"
            )

        if (
            approved_delivery_payload.get("approved_for_human_delivery")
            is not True
        ):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery payload is not approved_for_human_delivery"
            )

        result = approved_delivery_payload.get("result")

        if not isinstance(result, dict):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery result must be an object"
            )

        if result.get("hierarchy_key") != hierarchy_key:
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery hierarchy does not match requested hierarchy"
            )

        if result.get("handoff_status") != "approved_for_human_delivery":
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery handoff is not approved_for_human_delivery"
            )

        delivery_envelope = result.get("delivery_envelope")

        if not isinstance(delivery_envelope, dict):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery result must contain delivery_envelope"
            )

        if (
            delivery_envelope.get("delivery_status")
            != "approved_for_human_delivery"
        ):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery envelope is not approved_for_human_delivery"
            )

        if delivery_envelope.get("hierarchy_key") != hierarchy_key:
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved delivery envelope hierarchy mismatch"
            )

        payload_json = _canonical_json(approved_delivery_payload)
        payload_hash = _sha256_text(payload_json)

        snapshot_material = {
            "hierarchy_key": hierarchy_key,
            "execution_status_hash": execution_status_hash,
            "operator_snapshot_hash": operator_snapshot_hash,
            "approved_delivery_payload_hash": payload_hash,
            "schema_version": (
                COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_SCHEMA_VERSION
            ),
        }
        snapshot_hash = _sha256_text(
            _canonical_json(snapshot_material)
        )

        snapshot = CommercialPaidAssessmentApprovedDeliverySnapshot(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            execution_status_hash=execution_status_hash,
            operator_snapshot_hash=operator_snapshot_hash,
            approved_delivery_payload=json.loads(payload_json),
            approved_delivery_payload_hash=payload_hash,
            snapshot_hash=snapshot_hash,
        )

        existing = self.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        if existing is not None:
            if existing.snapshot_hash != snapshot.snapshot_hash:
                raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                    "approved-delivery snapshot already exists with different "
                    "governed approval material"
                )
            return existing

        with self._connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_NAME} (
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    execution_status_hash,
                    operator_snapshot_hash,
                    approved_delivery_payload_json,
                    approved_delivery_payload_hash,
                    snapshot_hash,
                    schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    execution_status_hash,
                    operator_snapshot_hash,
                    payload_json,
                    payload_hash,
                    snapshot_hash,
                    COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_STORE_SCHEMA_VERSION,
                ),
            )
            connection.commit()

        return snapshot

    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentApprovedDeliverySnapshot | None:
        hierarchy_key = "/".join(
            (
                _require_text(tenant_id, "tenant_id"),
                _require_text(client_id, "client_id"),
                _require_text(engagement_id, "engagement_id"),
                _require_text(assessment_id, "assessment_id"),
            )
        )

        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT *
                FROM {TABLE_NAME}
                WHERE hierarchy_key = ?
                """,
                (hierarchy_key,),
            ).fetchone()

        if row is None:
            return None

        payload_json = row["approved_delivery_payload_json"]
        payload_hash = _sha256_text(payload_json)

        if payload_hash != row["approved_delivery_payload_hash"]:
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved-delivery payload hash verification failed"
            )

        snapshot_material = {
            "hierarchy_key": hierarchy_key,
            "execution_status_hash": row["execution_status_hash"],
            "operator_snapshot_hash": row["operator_snapshot_hash"],
            "approved_delivery_payload_hash": row[
                "approved_delivery_payload_hash"
            ],
            "schema_version": row["schema_version"],
        }

        if (
            _sha256_text(_canonical_json(snapshot_material))
            != row["snapshot_hash"]
        ):
            raise CommercialPaidAssessmentApprovedDeliveryStoreError(
                "approved-delivery snapshot hash verification failed"
            )

        return CommercialPaidAssessmentApprovedDeliverySnapshot(
            tenant_id=row["tenant_id"],
            client_id=row["client_id"],
            engagement_id=row["engagement_id"],
            assessment_id=row["assessment_id"],
            execution_status_hash=_require_hash(
                row["execution_status_hash"],
                "execution_status_hash",
            ),
            operator_snapshot_hash=_require_hash(
                row["operator_snapshot_hash"],
                "operator_snapshot_hash",
            ),
            approved_delivery_payload=json.loads(payload_json),
            approved_delivery_payload_hash=_require_hash(
                row["approved_delivery_payload_hash"],
                "approved_delivery_payload_hash",
            ),
            snapshot_hash=_require_hash(
                row["snapshot_hash"],
                "snapshot_hash",
            ),
            schema_version=row["schema_version"],
        )
