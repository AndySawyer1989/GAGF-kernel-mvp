from __future__ import annotations

import json
import math
import sqlite3

from datetime import datetime, timezone
from pathlib import Path

from backend.app.gagf.governance_agent_capability_vocabulary import (
    AgentCapabilityVocabularyError,
    normalize_agent_capabilities,
)
from backend.app.gagf.governance_agent_worker_registry_contract import (
    AgentWorkerRegistration,
    AgentWorkerRegistrationConflictError,
    AgentWorkerRegistrationIntegrityError,
    AgentWorkerRegistrationNotFoundError,
    AgentWorkerRegistryError,
)


WORKER_REGISTRY_STORE_VERSION = "0.1.0"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkerRegistryError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _normalize_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AgentWorkerRegistryError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AgentWorkerRegistryError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _datetime_text(value: datetime) -> str:
    return value.isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Persisted datetime must be timezone-aware")

    return parsed.astimezone(timezone.utc)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


class AgentWorkerRegistryStore:
    """Tenant-scoped SQLite persistence for current worker registrations."""

    def __init__(
        self,
        database_path: str | Path,
        timeout_seconds: float = 10.0,
    ) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds,
            (int, float),
        ):
            raise AgentWorkerRegistryError(
                "timeout_seconds must be a finite number greater than zero"
            )

        try:
            valid_timeout = (
                math.isfinite(float(timeout_seconds))
                and timeout_seconds > 0
            )
        except (OverflowError, ValueError):
            valid_timeout = False

        if not valid_timeout:
            raise AgentWorkerRegistryError(
                "timeout_seconds must be a finite number greater than zero"
            )

        self.database_path = Path(database_path)
        self.timeout_seconds = float(timeout_seconds)

        if str(self.database_path) == ":memory:":
            raise AgentWorkerRegistryError(
                "In-memory databases are not supported"
            )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=self.timeout_seconds,
        )

        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}"
        )

        return connection

    def _initialize(self) -> None:
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_worker_registry (
                    tenant_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    worker_type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    supported_task_types_json TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    enabled INTEGER NOT NULL
                        CHECK (enabled IN (0, 1)),
                    registration_revision INTEGER NOT NULL
                        CHECK (registration_revision >= 1),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, worker_id)
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_gagf_agent_worker_registry_matching
                ON gagf_agent_worker_registry (
                    tenant_id,
                    enabled,
                    worker_id
                )
                """
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def _record(row: sqlite3.Row) -> AgentWorkerRegistration:
        try:
            task_types = json.loads(
                row["supported_task_types_json"]
            )
            capabilities = json.loads(
                row["capabilities_json"]
            )

            if not isinstance(task_types, list):
                raise ValueError("Task types must be a JSON array")

            if not isinstance(capabilities, list):
                raise ValueError("Capabilities must be a JSON array")

            if row["enabled"] not in (0, 1):
                raise ValueError("Enabled value must be zero or one")

            return AgentWorkerRegistration(
                tenant_id=row["tenant_id"],
                worker_id=row["worker_id"],
                worker_type=row["worker_type"],
                version=row["version"],
                supported_task_types=tuple(task_types),
                capabilities=tuple(capabilities),
                enabled=bool(row["enabled"]),
                registration_revision=row["registration_revision"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )

        except (
            AgentWorkerRegistryError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError,
        ) as exc:
            raise AgentWorkerRegistrationIntegrityError(
                "Persisted worker registration failed validation"
            ) from exc

    def _get_record(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        worker_id: str,
    ) -> AgentWorkerRegistration:
        row = connection.execute(
            """
            SELECT *
            FROM gagf_agent_worker_registry
            WHERE tenant_id = ?
              AND worker_id = ?
            """,
            (tenant_id, worker_id),
        ).fetchone()

        if row is None:
            raise AgentWorkerRegistrationNotFoundError(
                "Worker registration was not found for this tenant"
            )

        return self._record(row)

    def register_worker(
        self,
        *,
        tenant_id: str,
        worker_id: str,
        worker_type: str,
        version: str,
        supported_task_types: tuple[str, ...],
        capabilities: tuple[str, ...] = (),
        enabled: bool = True,
        now: datetime | None = None,
    ) -> AgentWorkerRegistration:
        effective_now = (
            datetime.now(timezone.utc)
            if now is None
            else _normalize_datetime(now, "now")
        )

        tenant_id = _require_text(tenant_id, "tenant_id")
        worker_id = _require_text(worker_id, "worker_id")

        try:
            normalized_capabilities = normalize_agent_capabilities(
                capabilities
            )
        except AgentCapabilityVocabularyError as exc:
            raise AgentWorkerRegistryError(
                f"Invalid worker capability declaration: {exc}"
            ) from exc

        candidate = AgentWorkerRegistration(
            tenant_id=tenant_id,
            worker_id=worker_id,
            worker_type=worker_type,
            version=version,
            supported_task_types=supported_task_types,
            capabilities=normalized_capabilities,
            enabled=enabled,
            registration_revision=1,
            created_at=effective_now,
            updated_at=effective_now,
        )

        task_types_json = _canonical_json(
            list(candidate.supported_task_types)
        )
        capabilities_json = _canonical_json(
            list(candidate.capabilities)
        )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing_row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_worker_registry
                WHERE tenant_id = ?
                  AND worker_id = ?
                """,
                (tenant_id, worker_id),
            ).fetchone()

            if existing_row is None:
                connection.execute(
                    """
                    INSERT INTO gagf_agent_worker_registry (
                        tenant_id,
                        worker_id,
                        worker_type,
                        version,
                        supported_task_types_json,
                        capabilities_json,
                        enabled,
                        registration_revision,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        tenant_id,
                        worker_id,
                        candidate.worker_type,
                        candidate.version,
                        task_types_json,
                        capabilities_json,
                        int(candidate.enabled),
                        _datetime_text(effective_now),
                        _datetime_text(effective_now),
                    ),
                )

                result = self._get_record(
                    connection,
                    tenant_id=tenant_id,
                    worker_id=worker_id,
                )

                connection.commit()
                return result

            existing = self._record(existing_row)

            unchanged = (
                existing.worker_type == candidate.worker_type
                and existing.version == candidate.version
                and existing.supported_task_types
                    == candidate.supported_task_types
                and existing.capabilities == candidate.capabilities
                and existing.enabled == candidate.enabled
            )

            if unchanged:
                connection.commit()
                return existing

            if effective_now < existing.created_at:
                raise AgentWorkerRegistrationConflictError(
                    "Registration update time cannot precede creation time"
                )

            next_revision = existing.registration_revision + 1

            connection.execute(
                """
                UPDATE gagf_agent_worker_registry
                SET
                    worker_type = ?,
                    version = ?,
                    supported_task_types_json = ?,
                    capabilities_json = ?,
                    enabled = ?,
                    registration_revision = ?,
                    updated_at = ?
                WHERE tenant_id = ?
                  AND worker_id = ?
                """,
                (
                    candidate.worker_type,
                    candidate.version,
                    task_types_json,
                    capabilities_json,
                    int(candidate.enabled),
                    next_revision,
                    _datetime_text(effective_now),
                    tenant_id,
                    worker_id,
                ),
            )

            result = self._get_record(
                connection,
                tenant_id=tenant_id,
                worker_id=worker_id,
            )

            connection.commit()
            return result

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get_worker(
        self,
        *,
        tenant_id: str,
        worker_id: str,
    ) -> AgentWorkerRegistration:
        tenant_id = _require_text(tenant_id, "tenant_id")
        worker_id = _require_text(worker_id, "worker_id")

        connection = self._connect()

        try:
            return self._get_record(
                connection,
                tenant_id=tenant_id,
                worker_id=worker_id,
            )
        finally:
            connection.close()

    def list_workers(
        self,
        *,
        tenant_id: str,
        include_disabled: bool = True,
    ) -> tuple[AgentWorkerRegistration, ...]:
        tenant_id = _require_text(tenant_id, "tenant_id")

        if not isinstance(include_disabled, bool):
            raise AgentWorkerRegistryError(
                "include_disabled must be a boolean"
            )

        connection = self._connect()

        try:
            if include_disabled:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM gagf_agent_worker_registry
                    WHERE tenant_id = ?
                    ORDER BY worker_id ASC
                    """,
                    (tenant_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM gagf_agent_worker_registry
                    WHERE tenant_id = ?
                      AND enabled = 1
                    ORDER BY worker_id ASC
                    """,
                    (tenant_id,),
                ).fetchall()

            return tuple(
                self._record(row)
                for row in rows
            )

        finally:
            connection.close()