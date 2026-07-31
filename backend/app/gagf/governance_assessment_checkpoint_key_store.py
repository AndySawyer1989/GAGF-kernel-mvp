from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


ASSESSMENT_CHECKPOINT_KEY_STORE_VERSION = "1.1.0"


@dataclass(frozen=True)
class AssessmentCheckpointSigningKeyMetadata:
    tenant_id: str
    key_id: str
    secret_reference: str
    active: bool
    created_at: str
    retired_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "key_id": self.key_id,
            "secret_reference": self.secret_reference,
            "active": self.active,
            "created_at": self.created_at,
            "retired_at": self.retired_at,
        }


class AssessmentCheckpointSigningKeyMetadataStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                assessment_checkpoint_signing_keys (
                    tenant_id TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    secret_reference TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    retired_at TEXT,
                    PRIMARY KEY (tenant_id, key_id)
                )
                """
            )
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_assessment_checkpoint_active_key
                ON assessment_checkpoint_signing_keys(
                    tenant_id
                )
                WHERE active = 1
                """
            )
            connection.commit()

    def insert(
        self,
        metadata: AssessmentCheckpointSigningKeyMetadata,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessment_checkpoint_signing_keys (
                    tenant_id,
                    key_id,
                    secret_reference,
                    active,
                    created_at,
                    retired_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.tenant_id,
                    metadata.key_id,
                    metadata.secret_reference,
                    int(metadata.active),
                    metadata.created_at,
                    metadata.retired_at,
                ),
            )
            connection.commit()

    def replace(
        self,
        metadata: AssessmentCheckpointSigningKeyMetadata,
    ) -> None:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE assessment_checkpoint_signing_keys
                SET secret_reference = ?,
                    active = ?,
                    created_at = ?,
                    retired_at = ?
                WHERE tenant_id = ?
                  AND key_id = ?
                """,
                (
                    metadata.secret_reference,
                    int(metadata.active),
                    metadata.created_at,
                    metadata.retired_at,
                    metadata.tenant_id,
                    metadata.key_id,
                ),
            )

            if cursor.rowcount != 1:
                raise KeyError(
                    "checkpoint signing key metadata was not found"
                )

            connection.commit()

    def rotate_active_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
        retired_at: str,
    ) -> AssessmentCheckpointSigningKeyMetadata:
        with self._lock, self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")

                selected_row = connection.execute(
                    """
                    SELECT *
                    FROM assessment_checkpoint_signing_keys
                    WHERE tenant_id = ?
                      AND key_id = ?
                    """,
                    (tenant_id, key_id),
                ).fetchone()

                if selected_row is None:
                    raise KeyError(
                        "checkpoint signing key metadata was not found"
                    )

                selected = self._row_to_metadata(selected_row)

                if selected.active:
                    connection.commit()
                    return selected

                connection.execute(
                    """
                    UPDATE assessment_checkpoint_signing_keys
                    SET active = 0,
                        retired_at = ?
                    WHERE tenant_id = ?
                      AND active = 1
                    """,
                    (retired_at, tenant_id),
                )

                cursor = connection.execute(
                    """
                    UPDATE assessment_checkpoint_signing_keys
                    SET active = 1,
                        retired_at = NULL
                    WHERE tenant_id = ?
                      AND key_id = ?
                    """,
                    (tenant_id, key_id),
                )

                if cursor.rowcount != 1:
                    raise KeyError(
                        "checkpoint signing key metadata was not found"
                    )

                activated_row = connection.execute(
                    """
                    SELECT *
                    FROM assessment_checkpoint_signing_keys
                    WHERE tenant_id = ?
                      AND key_id = ?
                    """,
                    (tenant_id, key_id),
                ).fetchone()

                if activated_row is None:
                    raise KeyError(
                        "checkpoint signing key metadata was not found"
                    )

                connection.commit()
                return self._row_to_metadata(activated_row)

            except Exception:
                connection.rollback()
                raise

    def get_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
    ) -> AssessmentCheckpointSigningKeyMetadata:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM assessment_checkpoint_signing_keys
                WHERE tenant_id = ?
                  AND key_id = ?
                """,
                (tenant_id, key_id),
            ).fetchone()

        if row is None:
            raise KeyError(
                "checkpoint signing key metadata was not found"
            )

        return self._row_to_metadata(row)

    def get_active_key(
        self,
        *,
        tenant_id: str,
    ) -> AssessmentCheckpointSigningKeyMetadata:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM assessment_checkpoint_signing_keys
                WHERE tenant_id = ?
                  AND active = 1
                """,
                (tenant_id,),
            ).fetchone()

        if row is None:
            raise KeyError(
                "active checkpoint signing key metadata was not found"
            )

        return self._row_to_metadata(row)

    def list_keys(
        self,
        *,
        tenant_id: str,
    ) -> list[AssessmentCheckpointSigningKeyMetadata]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM assessment_checkpoint_signing_keys
                WHERE tenant_id = ?
                ORDER BY created_at DESC, key_id DESC
                """,
                (tenant_id,),
            ).fetchall()

        return [self._row_to_metadata(row) for row in rows]

    @staticmethod
    def _row_to_metadata(
        row: sqlite3.Row,
    ) -> AssessmentCheckpointSigningKeyMetadata:
        return AssessmentCheckpointSigningKeyMetadata(
            tenant_id=row["tenant_id"],
            key_id=row["key_id"],
            secret_reference=row["secret_reference"],
            active=bool(row["active"]),
            created_at=row["created_at"],
            retired_at=row["retired_at"],
        )
