from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock

from backend.app.gagf.governance_paid_work_authorization_record import (
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION,
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE,
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION,
    GovernancePaidWorkAuthorizationRecord,
    GovernancePaidWorkAuthorizationRecordError,
    GovernancePaidWorkAuthorizationRecordIntegrityError,
    paid_work_authorization_record_from_dict,
)


GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_STORE_VERSION = "0.1.0"
GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE = (
    "governance_paid_work_authorization_records"
)


class GovernancePaidWorkAuthorizationRecordStoreError(RuntimeError):
    """Base error for durable PA-001 authorization storage."""


class GovernancePaidWorkAuthorizationRecordStoreNotFoundError(
    GovernancePaidWorkAuthorizationRecordStoreError
):
    """Raised when an authoritative PA-001 record does not exist."""


class GovernancePaidWorkAuthorizationRecordStoreConflictError(
    GovernancePaidWorkAuthorizationRecordStoreError
):
    """Raised when an authorization ID is reused for different content."""


class GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
    GovernancePaidWorkAuthorizationRecordStoreError
):
    """Raised when stored PA-001 state fails integrity validation."""


def _require_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise GovernancePaidWorkAuthorizationRecordStoreError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernancePaidWorkAuthorizationRecordStoreError(
            f"{field_name} must not be empty"
        )

    return normalized


def _canonical_json(
    payload: dict[str, object],
) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


class GovernancePaidWorkAuthorizationRecordStore:
    """
    Durable server-side source for PA-001 paid-work authorization records.

    This store records and resolves an already-created authorization.
    Persistence does not create paid-work authority, authenticate an actor,
    authorize a trial, execute an assessment, approve delivery, or confer
    intervention authority.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with (
            self._lock,
            self._connect() as connection,
        ):
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE} (
                    authorization_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,
                    hierarchy_key TEXT NOT NULL,
                    contract_execution_event_id TEXT NOT NULL,
                    authorized_by TEXT NOT NULL,
                    authorized_at TEXT NOT NULL,
                    paid_assessment_authorized INTEGER NOT NULL,
                    authorization_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    record_type TEXT NOT NULL,
                    record_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    store_version TEXT NOT NULL
                )
                """
            )

            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                idx_paid_work_authorization_hierarchy
                ON {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id
                )
                """
            )

            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                idx_paid_work_authorization_contract_event
                ON {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
                (
                    contract_execution_event_id
                )
                """
            )

            connection.commit()

    def save(
        self,
        *,
        record: GovernancePaidWorkAuthorizationRecord,
    ) -> GovernancePaidWorkAuthorizationRecord:
        if not isinstance(
            record,
            GovernancePaidWorkAuthorizationRecord,
        ):
            raise GovernancePaidWorkAuthorizationRecordStoreError(
                "record must be a "
                "GovernancePaidWorkAuthorizationRecord"
            )

        record_payload = record.to_dict()
        record_json = _canonical_json(
            record_payload
        )

        values = (
            record.authorization_id,
            record.tenant_id,
            record.client_id,
            record.engagement_id,
            record.assessment_id,
            record.hierarchy_key,
            record.contract_execution_event_id,
            record.authorized_by,
            record.authorized_at,
            1,
            record.authorization_hash,
            record.record_hash,
            record_json,
            record.record_type,
            record.version,
            record.schema_version,
            GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_STORE_VERSION,
        )

        try:
            with (
                self._lock,
                self._connect() as connection,
            ):
                connection.execute(
                    f"""
                    INSERT INTO
                    {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
                    (
                        authorization_id,
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id,
                        hierarchy_key,
                        contract_execution_event_id,
                        authorized_by,
                        authorized_at,
                        paid_assessment_authorized,
                        authorization_hash,
                        record_hash,
                        record_json,
                        record_type,
                        record_version,
                        schema_version,
                        store_version
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    values,
                )

                connection.commit()

        except sqlite3.IntegrityError as exc:
            existing = self.get_optional(
                authorization_id=record.authorization_id
            )

            if existing is not None:
                if (
                    existing.record_hash
                    == record.record_hash
                    and existing.to_dict()
                    == record.to_dict()
                ):
                    return existing

                raise (
                    GovernancePaidWorkAuthorizationRecordStoreConflictError(
                        "authorization_id already exists with "
                        "different PA-001 record content"
                    )
                ) from exc

            raise GovernancePaidWorkAuthorizationRecordStoreError(
                "failed to persist PA-001 authorization record"
            ) from exc

        stored = self.get(
            authorization_id=record.authorization_id
        )

        if stored.record_hash != record.record_hash:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "persisted PA-001 record does not match source record"
            )

        return stored

    def get(
        self,
        *,
        authorization_id: str,
    ) -> GovernancePaidWorkAuthorizationRecord:
        normalized_authorization_id = _require_text(
            authorization_id,
            "authorization_id",
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            row = connection.execute(
                f"""
                SELECT *
                FROM {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
                WHERE authorization_id = ?
                """,
                (
                    normalized_authorization_id,
                ),
            ).fetchone()

        if row is None:
            raise GovernancePaidWorkAuthorizationRecordStoreNotFoundError(
                "PA-001 authorization record not found"
            )

        return self._row_to_record(
            row
        )

    def get_optional(
        self,
        *,
        authorization_id: str,
    ) -> GovernancePaidWorkAuthorizationRecord | None:
        normalized_authorization_id = _require_text(
            authorization_id,
            "authorization_id",
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            row = connection.execute(
                f"""
                SELECT *
                FROM {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
                WHERE authorization_id = ?
                """,
                (
                    normalized_authorization_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_record(
            row
        )

    def require_for_execution(
        self,
        *,
        authorization_id: str,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        contract_execution_event_id: str,
    ) -> GovernancePaidWorkAuthorizationRecord:
        record = self.get(
            authorization_id=authorization_id
        )

        expected_hierarchy = "/".join(
            (
                _require_text(
                    tenant_id,
                    "tenant_id",
                ),
                _require_text(
                    client_id,
                    "client_id",
                ),
                _require_text(
                    engagement_id,
                    "engagement_id",
                ),
                _require_text(
                    assessment_id,
                    "assessment_id",
                ),
            )
        )

        if record.hierarchy_key != expected_hierarchy:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "PA-001 authorization hierarchy does not "
                "match execution request"
            )

        expected_contract_event_id = _require_text(
            contract_execution_event_id,
            "contract_execution_event_id",
        )

        if (
            record.contract_execution_event_id
            != expected_contract_event_id
        ):
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "PA-001 contract execution event does not "
                "match execution request"
            )

        if record.paid_assessment_authorized is not True:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "PA-001 authorization is not affirmative"
            )

        return record

    @staticmethod
    def _row_to_record(
        row: sqlite3.Row,
    ) -> GovernancePaidWorkAuthorizationRecord:
        if (
            row["store_version"]
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_STORE_VERSION
        ):
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "unsupported PA-001 record store version"
            )

        if (
            row["record_type"]
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE
        ):
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 record type mismatch"
            )

        if (
            row["record_version"]
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION
        ):
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 record version mismatch"
            )

        if (
            row["schema_version"]
            != GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION
        ):
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 schema version mismatch"
            )

        try:
            payload = json.loads(
                row["record_json"]
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 record JSON is invalid"
            ) from exc

        if not isinstance(payload, dict):
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 record JSON must be an object"
            )

        try:
            record = (
                paid_work_authorization_record_from_dict(
                    payload
                )
            )
        except (
            GovernancePaidWorkAuthorizationRecordError,
            GovernancePaidWorkAuthorizationRecordIntegrityError,
        ) as exc:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 record failed integrity verification"
            ) from exc

        expected_columns = {
            "authorization_id": record.authorization_id,
            "tenant_id": record.tenant_id,
            "client_id": record.client_id,
            "engagement_id": record.engagement_id,
            "assessment_id": record.assessment_id,
            "hierarchy_key": record.hierarchy_key,
            "contract_execution_event_id": (
                record.contract_execution_event_id
            ),
            "authorized_by": record.authorized_by,
            "authorized_at": record.authorized_at,
            "authorization_hash": record.authorization_hash,
            "record_hash": record.record_hash,
        }

        for (
            column_name,
            expected_value,
        ) in expected_columns.items():
            if row[column_name] != expected_value:
                raise (
                    GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                        f"stored PA-001 {column_name} mismatch"
                    )
                )

        if row["paid_assessment_authorized"] != 1:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 affirmative authorization flag mismatch"
            )

        expected_record_json = _canonical_json(
            record.to_dict()
        )

        if row["record_json"] != expected_record_json:
            raise GovernancePaidWorkAuthorizationRecordStoreIntegrityError(
                "stored PA-001 canonical JSON mismatch"
            )

        return record