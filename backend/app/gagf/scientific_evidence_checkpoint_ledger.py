import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
)
from backend.app.gagf.scientific_evidence_checkpoint import (
    ScientificEvidenceCheckpoint,
)
from backend.app.gagf.scientific_evidence_checkpoint_replay_verifier import (
    ScientificEvidenceCheckpointReplayVerifier,
)


SCIENTIFIC_EVIDENCE_CHECKPOINT_LEDGER_ID = (
    "scientific-evidence-checkpoint-ledger"
)
SCIENTIFIC_EVIDENCE_CHECKPOINT_LEDGER_VERSION = "0.1.0"


class ScientificEvidenceCheckpointLedgerError(RuntimeError):
    pass


class InvalidScientificEvidenceCheckpointError(
    ScientificEvidenceCheckpointLedgerError
):
    pass


class ScientificEvidenceCheckpointConflictError(
    ScientificEvidenceCheckpointLedgerError
):
    pass


@dataclass(frozen=True, slots=True)
class ScientificEvidenceCheckpointLedgerRecord:
    sequence_number: int
    checkpoint: ScientificEvidenceCheckpoint

    def to_dict(self) -> dict:
        return {
            "sequence_number": self.sequence_number,
            "checkpoint": self.checkpoint.to_dict(),
        }


class ScientificEvidenceCheckpointLedger:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)

        parent = Path(self.database_path).parent
        parent.mkdir(parents=True, exist_ok=True)

        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                scientific_evidence_checkpoints (
                    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    checkpoint_hash TEXT NOT NULL UNIQUE,
                    checkpoint_schema_version TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    checkpoint_version TEXT NOT NULL,
                    authority_ledger_identity TEXT NOT NULL,
                    audit_ledger_identity TEXT NOT NULL,
                    authority_audit_json TEXT NOT NULL,
                    audit_ledger_audit_json TEXT NOT NULL,
                    checkpoint_valid INTEGER NOT NULL,
                    checkpoint_json TEXT NOT NULL,
                    CHECK (checkpoint_valid IN (0, 1))
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scientific_evidence_checkpoints_validity
                ON scientific_evidence_checkpoints (
                    checkpoint_valid,
                    sequence_number
                )
                """
            )

    def append(
        self,
        *,
        checkpoint: ScientificEvidenceCheckpoint,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
    ) -> ScientificEvidenceCheckpointLedgerRecord:
        replay_result = (
            ScientificEvidenceCheckpointReplayVerifier()
            .verify(
                checkpoint=checkpoint,
                authority_database_path=authority_database_path,
                audit_database_path=audit_database_path,
            )
        )

        if not replay_result.valid:
            raise InvalidScientificEvidenceCheckpointError(
                "Scientific evidence checkpoint failed replay "
                "verification: "
                + "; ".join(replay_result.errors)
            )

        serialized_checkpoint = canonical_json(
            checkpoint.to_dict()
        )

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    sequence_number,
                    checkpoint_json
                FROM scientific_evidence_checkpoints
                WHERE checkpoint_hash = ?
                """,
                (checkpoint.checkpoint_hash,),
            ).fetchone()

            if existing is not None:
                if (
                    existing["checkpoint_json"]
                    != serialized_checkpoint
                ):
                    raise ScientificEvidenceCheckpointConflictError(
                        "Checkpoint hash already exists with "
                        "different content."
                    )

                return ScientificEvidenceCheckpointLedgerRecord(
                    sequence_number=existing["sequence_number"],
                    checkpoint=checkpoint,
                )

            cursor = connection.execute(
                """
                INSERT INTO scientific_evidence_checkpoints (
                    checkpoint_hash,
                    checkpoint_schema_version,
                    checkpoint_id,
                    checkpoint_version,
                    authority_ledger_identity,
                    audit_ledger_identity,
                    authority_audit_json,
                    audit_ledger_audit_json,
                    checkpoint_valid,
                    checkpoint_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_hash,
                    checkpoint.checkpoint_schema_version,
                    checkpoint.checkpoint_id,
                    checkpoint.checkpoint_version,
                    checkpoint.authority_ledger_identity,
                    checkpoint.audit_ledger_identity,
                    canonical_json(checkpoint.authority_audit),
                    canonical_json(
                        checkpoint.audit_ledger_audit
                    ),
                    int(checkpoint.valid),
                    serialized_checkpoint,
                ),
            )

            sequence_number = cursor.lastrowid

        if sequence_number is None:
            raise ScientificEvidenceCheckpointLedgerError(
                "Checkpoint append did not produce a sequence "
                "number."
            )

        return ScientificEvidenceCheckpointLedgerRecord(
            sequence_number=sequence_number,
            checkpoint=checkpoint,
        )

    def append_many(
        self,
        *,
        checkpoints: Iterable[ScientificEvidenceCheckpoint],
        authority_database_path: str | Path,
        audit_database_path: str | Path,
    ) -> tuple[
        ScientificEvidenceCheckpointLedgerRecord,
        ...,
    ]:
        return tuple(
            self.append(
                checkpoint=checkpoint,
                authority_database_path=authority_database_path,
                audit_database_path=audit_database_path,
            )
            for checkpoint in checkpoints
        )

    def get_by_hash(
        self,
        checkpoint_hash: str,
    ) -> ScientificEvidenceCheckpointLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    checkpoint_json
                FROM scientific_evidence_checkpoints
                WHERE checkpoint_hash = ?
                """,
                (checkpoint_hash,),
            ).fetchone()

        if row is None:
            return None

        return ScientificEvidenceCheckpointLedgerRecord(
            sequence_number=row["sequence_number"],
            checkpoint=self._deserialize_checkpoint(
                row["checkpoint_json"]
            ),
        )

    def list_records(
        self,
        *,
        valid: bool | None = None,
    ) -> tuple[
        ScientificEvidenceCheckpointLedgerRecord,
        ...,
    ]:
        query = """
            SELECT
                sequence_number,
                checkpoint_json
            FROM scientific_evidence_checkpoints
        """
        parameters: tuple[int, ...] = ()

        if valid is not None:
            query += " WHERE checkpoint_valid = ?"
            parameters = (int(valid),)

        query += " ORDER BY sequence_number ASC"

        with self._connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return tuple(
            ScientificEvidenceCheckpointLedgerRecord(
                sequence_number=row["sequence_number"],
                checkpoint=self._deserialize_checkpoint(
                    row["checkpoint_json"]
                ),
            )
            for row in rows
        )

    def count(
        self,
        *,
        valid: bool | None = None,
    ) -> int:
        query = """
            SELECT COUNT(*) AS record_count
            FROM scientific_evidence_checkpoints
        """
        parameters: tuple[int, ...] = ()

        if valid is not None:
            query += " WHERE checkpoint_valid = ?"
            parameters = (int(valid),)

        with self._connect() as connection:
            row = connection.execute(
                query,
                parameters,
            ).fetchone()

        return int(row["record_count"])

    def verify_all_hashes(self) -> bool:
        return all(
            record.checkpoint.verify()
            for record in self.list_records()
        )

    def _deserialize_checkpoint(
        self,
        serialized_checkpoint: str,
    ) -> ScientificEvidenceCheckpoint:
        data = json.loads(serialized_checkpoint)

        return ScientificEvidenceCheckpoint(
            checkpoint_schema_version=data[
                "checkpoint_schema_version"
            ],
            checkpoint_id=data["checkpoint_id"],
            checkpoint_version=data["checkpoint_version"],
            authority_ledger_identity=data[
                "authority_ledger_identity"
            ],
            audit_ledger_identity=data[
                "audit_ledger_identity"
            ],
            authority_audit=dict(data["authority_audit"]),
            audit_ledger_audit=dict(
                data["audit_ledger_audit"]
            ),
            valid=data["valid"],
            checkpoint_hash=data["checkpoint_hash"],
        )
