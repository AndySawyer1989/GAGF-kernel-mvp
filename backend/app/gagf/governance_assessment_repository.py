from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


ASSESSMENT_REPOSITORY_SCHEMA_VERSION = "1.0.0"


class AssessmentRepositoryError(RuntimeError):
    """Base repository failure."""


class AssessmentAlreadyExistsError(AssessmentRepositoryError):
    """Raised when an assessment record already exists."""


class AssessmentRecordNotFoundError(AssessmentRepositoryError):
    """Raised when an assessment record cannot be found."""


class ArtifactAlreadyExistsError(AssessmentRepositoryError):
    """Raised when an immutable artifact already exists."""


class ArtifactIntegrityError(AssessmentRepositoryError):
    """Raised when stored artifact content fails verification."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise AssessmentRepositoryError(
            f"{field_name} must not be empty"
        )

    return normalized


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass(frozen=True, slots=True)
class PersistedAssessmentRecord:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    assessment_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    record_hash: str
    schema_version: str = ASSESSMENT_REPOSITORY_SCHEMA_VERSION

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
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "assessment_name": self.assessment_name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "record_hash": self.record_hash,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class ImmutableAssessmentArtifact:
    artifact_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    artifact_type: str
    artifact_hash: str
    payload_json: str
    created_at: datetime
    sequence_number: int
    previous_artifact_hash: str | None
    chain_hash: str
    schema_version: str = ASSESSMENT_REPOSITORY_SCHEMA_VERSION

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
    def payload(self) -> Any:
        return json.loads(self.payload_json)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "sequence_number": self.sequence_number,
            "previous_artifact_hash": (
                self.previous_artifact_hash
            ),
            "chain_hash": self.chain_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS governance_assessments ("
                "tenant_id TEXT NOT NULL,"
                "client_id TEXT NOT NULL,"
                "engagement_id TEXT NOT NULL,"
                "assessment_id TEXT NOT NULL,"
                "assessment_name TEXT NOT NULL,"
                "status TEXT NOT NULL,"
                "created_at TEXT NOT NULL,"
                "updated_at TEXT NOT NULL,"
                "record_hash TEXT NOT NULL,"
                "schema_version TEXT NOT NULL,"
                "PRIMARY KEY ("
                "tenant_id, client_id, engagement_id, assessment_id"
                ")"
                ")"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS governance_assessment_artifacts ("
                "artifact_id TEXT PRIMARY KEY,"
                "tenant_id TEXT NOT NULL,"
                "client_id TEXT NOT NULL,"
                "engagement_id TEXT NOT NULL,"
                "assessment_id TEXT NOT NULL,"
                "artifact_type TEXT NOT NULL,"
                "artifact_hash TEXT NOT NULL,"
                "payload_json TEXT NOT NULL,"
                "created_at TEXT NOT NULL,"
                "sequence_number INTEGER NOT NULL,"
                "previous_artifact_hash TEXT,"
                "chain_hash TEXT NOT NULL,"
                "schema_version TEXT NOT NULL,"
                "UNIQUE ("
                "tenant_id, client_id, engagement_id, assessment_id,"
                "artifact_type, artifact_hash"
                "),"
                "UNIQUE ("
                "tenant_id, client_id, engagement_id, assessment_id,"
                "sequence_number"
                "),"
                "FOREIGN KEY ("
                "tenant_id, client_id, engagement_id, assessment_id"
                ") REFERENCES governance_assessments ("
                "tenant_id, client_id, engagement_id, assessment_id"
                ")"
                ")"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS "
                "idx_governance_assessment_artifacts_hierarchy "
                "ON governance_assessment_artifacts ("
                "tenant_id, client_id, engagement_id, assessment_id,"
                "sequence_number"
                ")"
            )

    def create_assessment(
        self,
        *,
        context: CommercialHierarchyContext,
        assessment_name: str,
        status: str = "draft",
        created_at: datetime | None = None,
    ) -> PersistedAssessmentRecord:
        self._require_complete_context(context)
        normalized_name = require_text(
            assessment_name,
            "assessment_name",
        )
        normalized_status = require_text(status, "status")
        timestamp = created_at or utc_now()

        payload = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": context.engagement_id,
            "assessment_id": context.assessment_id,
            "assessment_name": normalized_name,
            "status": normalized_status,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "schema_version": ASSESSMENT_REPOSITORY_SCHEMA_VERSION,
        }
        record_hash = sha256_text(canonical_json(payload))

        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO governance_assessments ("
                    "tenant_id, client_id, engagement_id, assessment_id,"
                    "assessment_name, status, created_at, updated_at,"
                    "record_hash, schema_version"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        context.tenant_id,
                        context.client_id,
                        context.engagement_id,
                        context.assessment_id,
                        normalized_name,
                        normalized_status,
                        timestamp.isoformat(),
                        timestamp.isoformat(),
                        record_hash,
                        ASSESSMENT_REPOSITORY_SCHEMA_VERSION,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise AssessmentAlreadyExistsError(
                "assessment already exists"
            ) from exc

        return PersistedAssessmentRecord(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            assessment_name=normalized_name,
            status=normalized_status,
            created_at=timestamp,
            updated_at=timestamp,
            record_hash=record_hash,
        )

    def get_assessment(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> PersistedAssessmentRecord:
        self._require_complete_context(context)

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governance_assessments "
                "WHERE tenant_id = ? AND client_id = ? "
                "AND engagement_id = ? AND assessment_id = ?",
                (
                    context.tenant_id,
                    context.client_id,
                    context.engagement_id,
                    context.assessment_id,
                ),
            ).fetchone()

        if row is None:
            raise AssessmentRecordNotFoundError(
                "assessment not found"
            )

        return self._assessment_from_row(row)

    def list_assessments(
        self,
        *,
        tenant_id: str,
        client_id: str | None = None,
        engagement_id: str | None = None,
    ) -> tuple[PersistedAssessmentRecord, ...]:
        normalized_tenant = require_text(tenant_id, "tenant_id")
        clauses = ["tenant_id = ?"]
        values: list[str] = [normalized_tenant]

        if client_id is not None:
            clauses.append("client_id = ?")
            values.append(require_text(client_id, "client_id"))

        if engagement_id is not None:
            if client_id is None:
                raise AssessmentRepositoryError(
                    "engagement_id requires client_id"
                )

            clauses.append("engagement_id = ?")
            values.append(
                require_text(engagement_id, "engagement_id")
            )

        query = (
            "SELECT * FROM governance_assessments WHERE "
            + " AND ".join(clauses)
            + " ORDER BY client_id, engagement_id, assessment_id"
        )

        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()

        return tuple(
            self._assessment_from_row(row)
            for row in rows
        )

    def append_artifact(
        self,
        *,
        context: CommercialHierarchyContext,
        artifact_type: str,
        payload: Any,
        created_at: datetime | None = None,
    ) -> ImmutableAssessmentArtifact:
        self.get_assessment(context=context)
        normalized_type = require_text(
            artifact_type,
            "artifact_type",
        )
        payload_json = canonical_json(payload)
        artifact_hash = sha256_text(payload_json)
        timestamp = created_at or utc_now()

        with self._connect() as connection:
            previous = connection.execute(
                "SELECT artifact_hash, chain_hash, sequence_number "
                "FROM governance_assessment_artifacts "
                "WHERE tenant_id = ? AND client_id = ? "
                "AND engagement_id = ? AND assessment_id = ? "
                "ORDER BY sequence_number DESC LIMIT 1",
                (
                    context.tenant_id,
                    context.client_id,
                    context.engagement_id,
                    context.assessment_id,
                ),
            ).fetchone()

            sequence_number = (
                int(previous["sequence_number"]) + 1
                if previous is not None
                else 1
            )
            previous_hash = (
                str(previous["artifact_hash"])
                if previous is not None
                else None
            )
            previous_chain_hash = (
                str(previous["chain_hash"])
                if previous is not None
                else "GENESIS"
            )

            chain_payload = {
                "hierarchy_key": context.hierarchy_key,
                "artifact_type": normalized_type,
                "artifact_hash": artifact_hash,
                "sequence_number": sequence_number,
                "previous_chain_hash": previous_chain_hash,
                "schema_version": (
                    ASSESSMENT_REPOSITORY_SCHEMA_VERSION
                ),
            }
            chain_hash = sha256_text(
                canonical_json(chain_payload)
            )
            artifact_id = sha256_text(
                canonical_json(
                    {
                        "hierarchy_key": context.hierarchy_key,
                        "artifact_type": normalized_type,
                        "artifact_hash": artifact_hash,
                    }
                )
            )[:24]

            try:
                connection.execute(
                    "INSERT INTO governance_assessment_artifacts ("
                    "artifact_id, tenant_id, client_id, engagement_id,"
                    "assessment_id, artifact_type, artifact_hash,"
                    "payload_json, created_at, sequence_number,"
                    "previous_artifact_hash, chain_hash, schema_version"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        artifact_id,
                        context.tenant_id,
                        context.client_id,
                        context.engagement_id,
                        context.assessment_id,
                        normalized_type,
                        artifact_hash,
                        payload_json,
                        timestamp.isoformat(),
                        sequence_number,
                        previous_hash,
                        chain_hash,
                        ASSESSMENT_REPOSITORY_SCHEMA_VERSION,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ArtifactAlreadyExistsError(
                    "immutable artifact already exists"
                ) from exc

        return ImmutableAssessmentArtifact(
            artifact_id=artifact_id,
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            artifact_type=normalized_type,
            artifact_hash=artifact_hash,
            payload_json=payload_json,
            created_at=timestamp,
            sequence_number=sequence_number,
            previous_artifact_hash=previous_hash,
            chain_hash=chain_hash,
        )

    def get_artifact(
        self,
        *,
        context: CommercialHierarchyContext,
        artifact_id: str,
    ) -> ImmutableAssessmentArtifact:
        self._require_complete_context(context)
        normalized_id = require_text(artifact_id, "artifact_id")

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governance_assessment_artifacts "
                "WHERE artifact_id = ? AND tenant_id = ? "
                "AND client_id = ? AND engagement_id = ? "
                "AND assessment_id = ?",
                (
                    normalized_id,
                    context.tenant_id,
                    context.client_id,
                    context.engagement_id,
                    context.assessment_id,
                ),
            ).fetchone()

        if row is None:
            raise AssessmentRecordNotFoundError(
                "artifact not found"
            )

        artifact = self._artifact_from_row(row)
        self.verify_artifact(artifact)
        return artifact

    def list_artifacts(
        self,
        *,
        context: CommercialHierarchyContext,
        artifact_type: str | None = None,
    ) -> tuple[ImmutableAssessmentArtifact, ...]:
        self._require_complete_context(context)
        clauses = [
            "tenant_id = ?",
            "client_id = ?",
            "engagement_id = ?",
            "assessment_id = ?",
        ]
        values: list[str] = [
            context.tenant_id,
            context.client_id,
            context.engagement_id or "",
            context.assessment_id or "",
        ]

        if artifact_type is not None:
            clauses.append("artifact_type = ?")
            values.append(
                require_text(artifact_type, "artifact_type")
            )

        query = (
            "SELECT * FROM governance_assessment_artifacts WHERE "
            + " AND ".join(clauses)
            + " ORDER BY sequence_number"
        )

        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()

        artifacts = tuple(
            self._artifact_from_row(row)
            for row in rows
        )

        for artifact in artifacts:
            self.verify_artifact(artifact)

        return artifacts

    def verify_artifact(
        self,
        artifact: ImmutableAssessmentArtifact,
    ) -> None:
        recalculated_hash = sha256_text(
            artifact.payload_json
        )

        if recalculated_hash != artifact.artifact_hash:
            raise ArtifactIntegrityError(
                "artifact payload hash verification failed"
            )

    def verify_chain(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> bool:
        artifacts = self.list_artifacts(context=context)
        previous_chain_hash = "GENESIS"

        for expected_sequence, artifact in enumerate(
            artifacts,
            start=1,
        ):
            if artifact.sequence_number != expected_sequence:
                raise ArtifactIntegrityError(
                    "artifact sequence is not contiguous"
                )

            chain_payload = {
                "hierarchy_key": context.hierarchy_key,
                "artifact_type": artifact.artifact_type,
                "artifact_hash": artifact.artifact_hash,
                "sequence_number": artifact.sequence_number,
                "previous_chain_hash": previous_chain_hash,
                "schema_version": artifact.schema_version,
            }
            expected_chain_hash = sha256_text(
                canonical_json(chain_payload)
            )

            if expected_chain_hash != artifact.chain_hash:
                raise ArtifactIntegrityError(
                    "artifact chain verification failed"
                )

            previous_chain_hash = artifact.chain_hash

        return True

    def _require_complete_context(
        self,
        context: CommercialHierarchyContext,
    ) -> None:
        if context.engagement_id is None:
            raise AssessmentRepositoryError(
                "repository operation requires engagement_id"
            )

        if context.assessment_id is None:
            raise AssessmentRepositoryError(
                "repository operation requires assessment_id"
            )

    def _assessment_from_row(
        self,
        row: sqlite3.Row,
    ) -> PersistedAssessmentRecord:
        return PersistedAssessmentRecord(
            tenant_id=str(row["tenant_id"]),
            client_id=str(row["client_id"]),
            engagement_id=str(row["engagement_id"]),
            assessment_id=str(row["assessment_id"]),
            assessment_name=str(row["assessment_name"]),
            status=str(row["status"]),
            created_at=parse_datetime(str(row["created_at"])),
            updated_at=parse_datetime(str(row["updated_at"])),
            record_hash=str(row["record_hash"]),
            schema_version=str(row["schema_version"]),
        )

    def _artifact_from_row(
        self,
        row: sqlite3.Row,
    ) -> ImmutableAssessmentArtifact:
        return ImmutableAssessmentArtifact(
            artifact_id=str(row["artifact_id"]),
            tenant_id=str(row["tenant_id"]),
            client_id=str(row["client_id"]),
            engagement_id=str(row["engagement_id"]),
            assessment_id=str(row["assessment_id"]),
            artifact_type=str(row["artifact_type"]),
            artifact_hash=str(row["artifact_hash"]),
            payload_json=str(row["payload_json"]),
            created_at=parse_datetime(str(row["created_at"])),
            sequence_number=int(row["sequence_number"]),
            previous_artifact_hash=(
                str(row["previous_artifact_hash"])
                if row["previous_artifact_hash"] is not None
                else None
            ),
            chain_hash=str(row["chain_hash"]),
            schema_version=str(row["schema_version"]),
        )
