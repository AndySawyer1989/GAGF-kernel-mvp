from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_ID = (
    "governance-commercial-paid-assessment-operator-result-store"
)
COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_SCHEMA_VERSION = "1.0.0"

TABLE_NAME = "governance_commercial_paid_assessment_operator_results"


class CommercialPaidAssessmentOperatorResultStoreError(RuntimeError):
    """Raised when a durable PA015 operator-result snapshot is invalid."""


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
        raise CommercialPaidAssessmentOperatorResultStoreError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _require_hash(value: Any, field_name: str) -> str:
    normalized = _require_text(value, field_name)
    if len(normalized) != 64 or normalized != normalized.lower():
        raise CommercialPaidAssessmentOperatorResultStoreError(
            f"{field_name} must be a lowercase SHA-256 hex digest"
        )
    try:
        int(normalized, 16)
    except ValueError as exc:
        raise CommercialPaidAssessmentOperatorResultStoreError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc
    return normalized


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentOperatorResultSnapshot:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    execution_status_hash: str
    execution_input_binding_hash: str
    assessment_execution_request_hash: str
    operator_result: dict[str, Any]
    operator_result_hash: str
    snapshot_hash: str
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_SCHEMA_VERSION
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
            "store_type": COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_ID,
            "version": COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_VERSION,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "execution_status_hash": self.execution_status_hash,
            "execution_input_binding_hash": self.execution_input_binding_hash,
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "operator_result": self.operator_result,
            "operator_result_hash": self.operator_result_hash,
            "snapshot_hash": self.snapshot_hash,
            "boundaries": {
                "snapshot_is_internal_only": True,
                "snapshot_is_not_execution_authority": True,
                "snapshot_is_not_recovery_authority": True,
                "snapshot_is_not_delivery_readiness": True,
                "snapshot_is_not_delivery_approval": True,
                "snapshot_is_not_delivery": True,
                "pa015_remains_execution_recovery_authority": True,
            },
        }


class GovernanceCommercialPaidAssessmentOperatorResultStore:
    """
    Persist the exact successful PA015 operator/recovery result for later
    restart-safe delivery-readiness verification.

    This store is internal only. It does not execute, recover, approve,
    deliver, or expose the operator payload to the browser.
    """

    def __init__(self, *, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
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
                    execution_input_binding_hash TEXT NOT NULL,
                    assessment_execution_request_hash TEXT NOT NULL,
                    operator_result_json TEXT NOT NULL,
                    operator_result_hash TEXT NOT NULL,
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
        execution_input_binding_hash: str,
        assessment_execution_request_hash: str,
        operator_result: dict[str, Any],
    ) -> CommercialPaidAssessmentOperatorResultSnapshot:
        tenant_id = _require_text(tenant_id, "tenant_id")
        client_id = _require_text(client_id, "client_id")
        engagement_id = _require_text(engagement_id, "engagement_id")
        assessment_id = _require_text(assessment_id, "assessment_id")

        execution_status_hash = _require_hash(
            execution_status_hash,
            "execution_status_hash",
        )
        execution_input_binding_hash = _require_hash(
            execution_input_binding_hash,
            "execution_input_binding_hash",
        )
        assessment_execution_request_hash = _require_hash(
            assessment_execution_request_hash,
            "assessment_execution_request_hash",
        )

        if not isinstance(operator_result, dict):
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator_result must be an object"
            )

        if operator_result.get("operator_run_passed") is not True:
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator_result must represent a successful PA015 operator run"
            )

        recovery = operator_result.get("result")
        if not isinstance(recovery, dict):
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator_result.result must be an object"
            )

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        if recovery.get("hierarchy_key") != hierarchy_key:
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator result hierarchy does not match requested hierarchy"
            )

        operator_result_json = _canonical_json(operator_result)
        operator_result_hash = _sha256_text(operator_result_json)

        snapshot_material = {
            "hierarchy_key": hierarchy_key,
            "execution_status_hash": execution_status_hash,
            "execution_input_binding_hash": execution_input_binding_hash,
            "assessment_execution_request_hash": (
                assessment_execution_request_hash
            ),
            "operator_result_hash": operator_result_hash,
            "schema_version": (
                COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_SCHEMA_VERSION
            ),
        }
        snapshot_hash = _sha256_text(_canonical_json(snapshot_material))

        snapshot = CommercialPaidAssessmentOperatorResultSnapshot(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            execution_status_hash=execution_status_hash,
            execution_input_binding_hash=execution_input_binding_hash,
            assessment_execution_request_hash=(
                assessment_execution_request_hash
            ),
            operator_result=json.loads(operator_result_json),
            operator_result_hash=operator_result_hash,
            snapshot_hash=snapshot_hash,
        )

        existing = self.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )
        if existing is not None:
            if existing.snapshot_hash == snapshot.snapshot_hash:
                return existing

            self._validate_same_governed_attempt(
                existing=existing,
                replacement=snapshot,
            )

            with self._connect() as connection:
                connection.execute(
                    f"""
                    UPDATE {TABLE_NAME}
                    SET execution_status_hash = ?,
                        operator_result_json = ?,
                        operator_result_hash = ?,
                        snapshot_hash = ?,
                        schema_version = ?
                    WHERE hierarchy_key = ?
                    """,
                    (
                        execution_status_hash,
                        operator_result_json,
                        operator_result_hash,
                        snapshot_hash,
                        COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_SCHEMA_VERSION,
                        hierarchy_key,
                    ),
                )
                connection.commit()

            return snapshot

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
                    execution_input_binding_hash,
                    assessment_execution_request_hash,
                    operator_result_json,
                    operator_result_hash,
                    snapshot_hash,
                    schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    execution_status_hash,
                    execution_input_binding_hash,
                    assessment_execution_request_hash,
                    operator_result_json,
                    operator_result_hash,
                    snapshot_hash,
                    COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_STORE_SCHEMA_VERSION,
                ),
            )
            connection.commit()

        return snapshot

    @staticmethod
    def _validate_same_governed_attempt(
        *,
        existing: CommercialPaidAssessmentOperatorResultSnapshot,
        replacement: CommercialPaidAssessmentOperatorResultSnapshot,
    ) -> None:
        if (
            existing.execution_input_binding_hash
            != replacement.execution_input_binding_hash
        ):
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator-result snapshot cannot replace a different "
                "execution-input binding"
            )

        if (
            existing.assessment_execution_request_hash
            != replacement.assessment_execution_request_hash
        ):
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator-result snapshot cannot replace a different "
                "assessment execution request"
            )

        existing_result = existing.operator_result.get("result")
        replacement_result = replacement.operator_result.get("result")

        if not isinstance(existing_result, dict) or not isinstance(
            replacement_result,
            dict,
        ):
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator-result snapshot governed attempt is unavailable"
            )

        for field_name in (
            "attempt_hash",
            "record_hash",
            "hierarchy_key",
        ):
            if existing_result.get(
                field_name
            ) != replacement_result.get(
                field_name
            ):
                raise CommercialPaidAssessmentOperatorResultStoreError(
                    "operator-result snapshot cannot replace a different "
                    f"governed PA015 {field_name}"
                )

    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentOperatorResultSnapshot | None:
        values = (
            _require_text(tenant_id, "tenant_id"),
            _require_text(client_id, "client_id"),
            _require_text(engagement_id, "engagement_id"),
            _require_text(assessment_id, "assessment_id"),
        )
        hierarchy_key = "/".join(values)

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

        operator_result_json = row["operator_result_json"]
        operator_result = json.loads(operator_result_json)

        operator_result_hash = _sha256_text(
            _canonical_json(operator_result)
        )
        if operator_result_hash != row["operator_result_hash"]:
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator-result payload hash verification failed"
            )

        snapshot_material = {
            "hierarchy_key": hierarchy_key,
            "execution_status_hash": row["execution_status_hash"],
            "execution_input_binding_hash": (
                row["execution_input_binding_hash"]
            ),
            "assessment_execution_request_hash": (
                row["assessment_execution_request_hash"]
            ),
            "operator_result_hash": row["operator_result_hash"],
            "schema_version": row["schema_version"],
        }
        snapshot_hash = _sha256_text(
            _canonical_json(snapshot_material)
        )

        if snapshot_hash != row["snapshot_hash"]:
            raise CommercialPaidAssessmentOperatorResultStoreError(
                "operator-result snapshot hash verification failed"
            )

        return CommercialPaidAssessmentOperatorResultSnapshot(
            tenant_id=row["tenant_id"],
            client_id=row["client_id"],
            engagement_id=row["engagement_id"],
            assessment_id=row["assessment_id"],
            execution_status_hash=row["execution_status_hash"],
            execution_input_binding_hash=(
                row["execution_input_binding_hash"]
            ),
            assessment_execution_request_hash=(
                row["assessment_execution_request_hash"]
            ),
            operator_result=operator_result,
            operator_result_hash=row["operator_result_hash"],
            snapshot_hash=row["snapshot_hash"],
            schema_version=row["schema_version"],
        )
