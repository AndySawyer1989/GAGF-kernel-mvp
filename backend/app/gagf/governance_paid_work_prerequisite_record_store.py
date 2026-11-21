from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock

from backend.app.gagf.governance_paid_work_prerequisite_record import (
    PAID_WORK_PREREQUISITE_RECORD_TYPE,
    PAID_WORK_PREREQUISITE_RECORD_VERSION,
    PAID_WORK_PREREQUISITE_SCHEMA_VERSION,
    SUPPORTED_PREREQUISITE_KINDS,
    GovernancePaidWorkPrerequisiteRecord,
    GovernancePaidWorkPrerequisiteRecordError,
    paid_work_prerequisite_record_from_dict,
)


GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_STORE_VERSION = "0.1.0"
GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE = (
    "governance_paid_work_prerequisite_records"
)


class GovernancePaidWorkPrerequisiteRecordStoreError(RuntimeError):
    """Base error for durable paid-work prerequisite storage."""


class GovernancePaidWorkPrerequisiteRecordStoreNotFoundError(
    GovernancePaidWorkPrerequisiteRecordStoreError
):
    """Raised when an authoritative prerequisite record is missing."""


class GovernancePaidWorkPrerequisiteRecordStoreConflictError(
    GovernancePaidWorkPrerequisiteRecordStoreError
):
    """Raised when a prerequisite identity is reused for different content."""


class GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
    GovernancePaidWorkPrerequisiteRecordStoreError
):
    """Raised when stored prerequisite state fails integrity validation."""


def _require_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise GovernancePaidWorkPrerequisiteRecordStoreError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernancePaidWorkPrerequisiteRecordStoreError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_kind(
    value: object,
) -> str:
    normalized = _require_text(
        value,
        "prerequisite_kind",
    )

    if normalized not in SUPPORTED_PREREQUISITE_KINDS:
        raise GovernancePaidWorkPrerequisiteRecordStoreError(
            "unsupported prerequisite_kind"
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


class GovernancePaidWorkPrerequisiteRecordStore:
    """
    Durable server-side source for PA-001 prerequisite evidence.

    This store persists already-produced, hierarchy-bound prerequisite
    records. Persistence does not create PA-001, authenticate an actor,
    execute an assessment, approve delivery, or confer intervention
    authority.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(
            database_path
        )
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
                {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE} (
                    prerequisite_kind TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,

                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,
                    hierarchy_key TEXT NOT NULL,

                    source_event_type TEXT NOT NULL,
                    source_status TEXT NOT NULL,
                    source_timestamp TEXT NOT NULL,

                    artifact_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    record_json TEXT NOT NULL,

                    record_type TEXT NOT NULL,
                    record_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    store_version TEXT NOT NULL,

                    PRIMARY KEY (
                        prerequisite_kind,
                        artifact_id
                    )
                )
                """
            )

            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                idx_paid_work_prerequisite_hierarchy
                ON {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
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
                idx_paid_work_prerequisite_hierarchy_kind
                ON {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
                (
                    hierarchy_key,
                    prerequisite_kind
                )
                """
            )

            connection.commit()

    def save(
        self,
        *,
        record: GovernancePaidWorkPrerequisiteRecord,
    ) -> GovernancePaidWorkPrerequisiteRecord:
        if not isinstance(
            record,
            GovernancePaidWorkPrerequisiteRecord,
        ):
            raise GovernancePaidWorkPrerequisiteRecordStoreError(
                "record must be a "
                "GovernancePaidWorkPrerequisiteRecord"
            )

        record.verify()

        record_payload = record.to_dict()
        record_json = _canonical_json(
            record_payload
        )

        values = (
            record.prerequisite_kind,
            record.artifact_id,
            record.tenant_id,
            record.client_id,
            record.engagement_id,
            record.assessment_id,
            record.hierarchy_key,
            record.source_event_type,
            record.source_status,
            record.source_timestamp,
            record.artifact_hash,
            record.record_hash,
            record_json,
            record.record_type,
            record.record_version,
            record.schema_version,
            GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_STORE_VERSION,
        )

        try:
            with (
                self._lock,
                self._connect() as connection,
            ):
                connection.execute(
                    f"""
                    INSERT INTO
                    {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
                    (
                        prerequisite_kind,
                        artifact_id,
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id,
                        hierarchy_key,
                        source_event_type,
                        source_status,
                        source_timestamp,
                        artifact_hash,
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
                prerequisite_kind=(
                    record.prerequisite_kind
                ),
                artifact_id=record.artifact_id,
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
                    GovernancePaidWorkPrerequisiteRecordStoreConflictError(
                        "prerequisite identity already exists with "
                        "different record content"
                    )
                ) from exc

            raise GovernancePaidWorkPrerequisiteRecordStoreError(
                "failed to persist prerequisite record"
            ) from exc

        stored = self.get(
            prerequisite_kind=(
                record.prerequisite_kind
            ),
            artifact_id=record.artifact_id,
        )

        if stored.record_hash != record.record_hash:
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "persisted prerequisite record does not match source record"
            )

        return stored

    def get(
        self,
        *,
        prerequisite_kind: str,
        artifact_id: str,
    ) -> GovernancePaidWorkPrerequisiteRecord:
        normalized_kind = _require_kind(
            prerequisite_kind
        )
        normalized_artifact_id = _require_text(
            artifact_id,
            "artifact_id",
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            row = connection.execute(
                f"""
                SELECT *
                FROM {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
                WHERE prerequisite_kind = ?
                  AND artifact_id = ?
                """,
                (
                    normalized_kind,
                    normalized_artifact_id,
                ),
            ).fetchone()

        if row is None:
            raise GovernancePaidWorkPrerequisiteRecordStoreNotFoundError(
                "paid-work prerequisite record not found"
            )

        return self._row_to_record(
            row
        )

    def get_optional(
        self,
        *,
        prerequisite_kind: str,
        artifact_id: str,
    ) -> GovernancePaidWorkPrerequisiteRecord | None:
        normalized_kind = _require_kind(
            prerequisite_kind
        )
        normalized_artifact_id = _require_text(
            artifact_id,
            "artifact_id",
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            row = connection.execute(
                f"""
                SELECT *
                FROM {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
                WHERE prerequisite_kind = ?
                  AND artifact_id = ?
                """,
                (
                    normalized_kind,
                    normalized_artifact_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_record(
            row
        )

    def require_for_issuance(
        self,
        *,
        prerequisite_kind: str,
        artifact_id: str,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> GovernancePaidWorkPrerequisiteRecord:
        record = self.get(
            prerequisite_kind=prerequisite_kind,
            artifact_id=artifact_id,
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
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "prerequisite hierarchy does not match issuance request"
            )

        record.verify()

        return record

    @staticmethod
    def _row_to_record(
        row: sqlite3.Row,
    ) -> GovernancePaidWorkPrerequisiteRecord:
        if (
            row["store_version"]
            != GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_STORE_VERSION
        ):
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "unsupported prerequisite record store version"
            )

        if (
            row["record_type"]
            != PAID_WORK_PREREQUISITE_RECORD_TYPE
        ):
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite record type mismatch"
            )

        if (
            row["record_version"]
            != PAID_WORK_PREREQUISITE_RECORD_VERSION
        ):
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite record version mismatch"
            )

        if (
            row["schema_version"]
            != PAID_WORK_PREREQUISITE_SCHEMA_VERSION
        ):
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite schema version mismatch"
            )

        try:
            payload = json.loads(
                row["record_json"]
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite record JSON is invalid"
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite record JSON must be an object"
            )

        try:
            record = (
                paid_work_prerequisite_record_from_dict(
                    payload
                )
            )
        except GovernancePaidWorkPrerequisiteRecordError as exc:
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite record failed integrity verification"
            ) from exc

        expected_columns = {
            "prerequisite_kind": (
                record.prerequisite_kind
            ),
            "artifact_id": record.artifact_id,
            "tenant_id": record.tenant_id,
            "client_id": record.client_id,
            "engagement_id": (
                record.engagement_id
            ),
            "assessment_id": (
                record.assessment_id
            ),
            "hierarchy_key": (
                record.hierarchy_key
            ),
            "source_event_type": (
                record.source_event_type
            ),
            "source_status": (
                record.source_status
            ),
            "source_timestamp": (
                record.source_timestamp
            ),
            "artifact_hash": (
                record.artifact_hash
            ),
            "record_hash": (
                record.record_hash
            ),
        }

        for (
            column_name,
            expected_value,
        ) in expected_columns.items():
            if row[column_name] != expected_value:
                raise (
                    GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                        f"stored prerequisite {column_name} mismatch"
                    )
                )

        expected_record_json = _canonical_json(
            record.to_dict()
        )

        if row["record_json"] != expected_record_json:
            raise GovernancePaidWorkPrerequisiteRecordStoreIntegrityError(
                "stored prerequisite canonical JSON mismatch"
            )

        return record
