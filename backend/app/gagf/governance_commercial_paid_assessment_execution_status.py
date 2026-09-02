from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    canonical_json,
    sha256_text,
)


COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_ID = (
    "governance-commercial-paid-assessment-execution-status"
)

COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_SCHEMA_VERSION = "1.0.0"

EXECUTION_STATUS_TABLE = (
    "governance_commercial_paid_assessment_execution_status"
)

ALLOWED_EXECUTION_DISPOSITIONS = frozenset(
    {
        "executed",
        "resumed",
        "reconciled",
    }
)


class CommercialPaidAssessmentExecutionStatusError(
    RuntimeError
):
    """Raised when governed paid execution status cannot be trusted."""


class CommercialPaidAssessmentExecutionStatusConflictError(
    CommercialPaidAssessmentExecutionStatusError
):
    """Raised when immutable execution identity conflicts."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentExecutionStatus:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    disposition: str

    attempt_hash: str
    attempt_record_hash: str

    assessment_execution_request_hash: str
    execution_input_binding_hash: str

    artifact_count_before: int
    artifact_count_after: int

    status_recorded_at: str
    status_hash: str

    status_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_ID
    )

    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_VERSION
    )

    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_SCHEMA_VERSION
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

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "status_type": self.status_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "disposition": self.disposition,
            "attempt_hash": self.attempt_hash,
            "attempt_record_hash": (
                self.attempt_record_hash
            ),
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "execution_input_binding_hash": (
                self.execution_input_binding_hash
            ),
            "artifact_count_before": (
                self.artifact_count_before
            ),
            "artifact_count_after": (
                self.artifact_count_after
            ),
            "status_recorded_at": (
                self.status_recorded_at
            ),
            "status_hash": self.status_hash,
            "boundaries": {
                "status_is_read_only_evidence": True,
                "status_is_not_execution_authority": True,
                "status_is_not_recovery_authority": True,
                "status_is_not_paid_work_authorization": True,
                "status_does_not_expose_raw_evidence": True,
            },
        }


class GovernanceCommercialPaidAssessmentExecutionStatusStore:
    """
    Durable read-model record for governed paid execution outcomes.

    This store does not execute, resume, reconcile, authorize, or repair
    an assessment. It records the result of a governed execution only
    after that authoritative execution path has returned successfully.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._path = Path(
            database_path
        )

    @property
    def database_path(
        self,
    ) -> Path:
        return self._path

    def initialize(
        self,
    ) -> None:
        if (
            self._path.parent
            and not self._path.parent.exists()
        ):
            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        with sqlite3.connect(
            self._path
        ) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {EXECUTION_STATUS_TABLE} (
                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,

                    disposition TEXT NOT NULL,

                    attempt_hash TEXT NOT NULL,
                    attempt_record_hash TEXT NOT NULL,

                    assessment_execution_request_hash TEXT NOT NULL,
                    execution_input_binding_hash TEXT NOT NULL,

                    artifact_count_before INTEGER NOT NULL,
                    artifact_count_after INTEGER NOT NULL,

                    status_recorded_at TEXT NOT NULL,
                    status_hash TEXT NOT NULL,

                    schema_version TEXT NOT NULL,

                    PRIMARY KEY (
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id
                    )
                )
                """
            )

    def build_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        disposition: str,
        attempt_hash: str,
        attempt_record_hash: str,
        assessment_execution_request_hash: str,
        execution_input_binding_hash: str,
        artifact_count_before: int,
        artifact_count_after: int,
        recorded_at: datetime | None = None,
    ) -> CommercialPaidAssessmentExecutionStatus:
        hierarchy_values = (
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        )

        if any(
            not isinstance(value, str)
            or not value.strip()
            for value in hierarchy_values
        ):
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "execution-status hierarchy values "
                    "must be non-empty"
                )
            )

        if disposition not in ALLOWED_EXECUTION_DISPOSITIONS:
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "execution-status disposition is invalid"
                )
            )

        hash_values = (
            attempt_hash,
            attempt_record_hash,
            assessment_execution_request_hash,
            execution_input_binding_hash,
        )

        if any(
            not isinstance(value, str)
            or not value.strip()
            for value in hash_values
        ):
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "execution-status hashes must be non-empty"
                )
            )

        if (
            artifact_count_before < 0
            or artifact_count_after < 0
        ):
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "execution-status artifact counts "
                    "cannot be negative"
                )
            )

        if (
            artifact_count_after
            < artifact_count_before
        ):
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "execution-status artifact count cannot regress"
                )
            )

        timestamp = (
            recorded_at
            or datetime.now(
                timezone.utc
            )
        ).isoformat()

        payload = {
            "status_type": (
                COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_ID
            ),
            "version": (
                COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_VERSION
            ),
            "schema_version": (
                COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_SCHEMA_VERSION
            ),
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "hierarchy_key": "/".join(
                hierarchy_values
            ),
            "disposition": disposition,
            "attempt_hash": attempt_hash,
            "attempt_record_hash": (
                attempt_record_hash
            ),
            "assessment_execution_request_hash": (
                assessment_execution_request_hash
            ),
            "execution_input_binding_hash": (
                execution_input_binding_hash
            ),
            "artifact_count_before": (
                artifact_count_before
            ),
            "artifact_count_after": (
                artifact_count_after
            ),
            "status_recorded_at": timestamp,
        }

        status_hash = sha256_text(
            canonical_json(
                payload
            )
        )

        return (
            CommercialPaidAssessmentExecutionStatus(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                disposition=disposition,
                attempt_hash=attempt_hash,
                attempt_record_hash=(
                    attempt_record_hash
                ),
                assessment_execution_request_hash=(
                    assessment_execution_request_hash
                ),
                execution_input_binding_hash=(
                    execution_input_binding_hash
                ),
                artifact_count_before=(
                    artifact_count_before
                ),
                artifact_count_after=(
                    artifact_count_after
                ),
                status_recorded_at=timestamp,
                status_hash=status_hash,
            )
        )

    def record_status(
        self,
        *,
        status: CommercialPaidAssessmentExecutionStatus,
    ) -> CommercialPaidAssessmentExecutionStatus:
        self.initialize()

        existing = self.get_status(
            tenant_id=status.tenant_id,
            client_id=status.client_id,
            engagement_id=status.engagement_id,
            assessment_id=status.assessment_id,
        )

        if existing is not None:
            if (
                existing.attempt_hash
                != status.attempt_hash
            ):
                raise (
                    CommercialPaidAssessmentExecutionStatusConflictError(
                        "existing execution status belongs "
                        "to a different governed attempt"
                    )
                )

            if (
                existing.assessment_execution_request_hash
                != status.assessment_execution_request_hash
                or
                existing.execution_input_binding_hash
                != status.execution_input_binding_hash
            ):
                raise (
                    CommercialPaidAssessmentExecutionStatusConflictError(
                        "existing execution status identity "
                        "does not match"
                    )
                )

        with sqlite3.connect(
            self._path
        ) as connection:
            connection.execute(
                f"""
                INSERT INTO {EXECUTION_STATUS_TABLE} (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,

                    disposition,

                    attempt_hash,
                    attempt_record_hash,

                    assessment_execution_request_hash,
                    execution_input_binding_hash,

                    artifact_count_before,
                    artifact_count_after,

                    status_recorded_at,
                    status_hash,

                    schema_version
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?
                )
                ON CONFLICT (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id
                )
                DO UPDATE SET
                    disposition = excluded.disposition,
                    attempt_record_hash = excluded.attempt_record_hash,
                    artifact_count_before = excluded.artifact_count_before,
                    artifact_count_after = excluded.artifact_count_after,
                    status_recorded_at = excluded.status_recorded_at,
                    status_hash = excluded.status_hash,
                    schema_version = excluded.schema_version
                """,
                (
                    status.tenant_id,
                    status.client_id,
                    status.engagement_id,
                    status.assessment_id,

                    status.disposition,

                    status.attempt_hash,
                    status.attempt_record_hash,

                    status.assessment_execution_request_hash,
                    status.execution_input_binding_hash,

                    status.artifact_count_before,
                    status.artifact_count_after,

                    status.status_recorded_at,
                    status.status_hash,

                    status.schema_version,
                ),
            )

        return status

    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentExecutionStatus | None:
        if not self._path.exists():
            return None

        self.initialize()

        with sqlite3.connect(
            self._path
        ) as connection:
            connection.row_factory = (
                sqlite3.Row
            )

            row = connection.execute(
                f"""
                SELECT *
                FROM {EXECUTION_STATUS_TABLE}
                WHERE tenant_id = ?
                  AND client_id = ?
                  AND engagement_id = ?
                  AND assessment_id = ?
                """,
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._status_from_row(
            row
        )

    def _status_from_row(
        self,
        row: sqlite3.Row,
    ) -> CommercialPaidAssessmentExecutionStatus:
        status = (
            CommercialPaidAssessmentExecutionStatus(
                tenant_id=str(
                    row["tenant_id"]
                ),
                client_id=str(
                    row["client_id"]
                ),
                engagement_id=str(
                    row["engagement_id"]
                ),
                assessment_id=str(
                    row["assessment_id"]
                ),
                disposition=str(
                    row["disposition"]
                ),
                attempt_hash=str(
                    row["attempt_hash"]
                ),
                attempt_record_hash=str(
                    row["attempt_record_hash"]
                ),
                assessment_execution_request_hash=str(
                    row[
                        "assessment_execution_request_hash"
                    ]
                ),
                execution_input_binding_hash=str(
                    row[
                        "execution_input_binding_hash"
                    ]
                ),
                artifact_count_before=int(
                    row["artifact_count_before"]
                ),
                artifact_count_after=int(
                    row["artifact_count_after"]
                ),
                status_recorded_at=str(
                    row["status_recorded_at"]
                ),
                status_hash=str(
                    row["status_hash"]
                ),
                schema_version=str(
                    row["schema_version"]
                ),
            )
        )

        serialized = status.to_dict()

        payload = {
            key: value
            for key, value
            in serialized.items()
            if key not in {
                "status_hash",
                "boundaries",
            }
        }

        expected_hash = sha256_text(
            canonical_json(
                payload
            )
        )

        if (
            expected_hash
            != status.status_hash
        ):
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "stored execution-status hash "
                    "verification failed"
                )
            )

        if (
            status.disposition
            not in ALLOWED_EXECUTION_DISPOSITIONS
        ):
            raise (
                CommercialPaidAssessmentExecutionStatusError(
                    "stored execution-status disposition "
                    "is invalid"
                )
            )

        return status