import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.app.gagf.scientific_execution_context import (
    ScientificContextBindingLedger,
    ScientificContextBindingLedgerRecord,
)


SCIENTIFIC_CONTEXT_BINDING_INDEX_ID = (
    "scientific-context-binding-artifact-index"
)
SCIENTIFIC_CONTEXT_BINDING_INDEX_VERSION = "0.1.0"


IndexedScientificArtifactType = Literal[
    "authority_receipt",
    "checkpoint",
    "execution",
    "context_binding",
]


class ScientificContextBindingIndexError(RuntimeError):
    pass


class DuplicateScientificArtifactBindingError(
    ScientificContextBindingIndexError
):
    pass


@dataclass(frozen=True, slots=True)
class ScientificArtifactBindingOwner:
    artifact_type: IndexedScientificArtifactType
    artifact_id: str
    tenant_id: str
    binding_hash: str
    execution_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "tenant_id": self.tenant_id,
            "binding_hash": self.binding_hash,
            "execution_id": self.execution_id,
        }


class ScientificContextBindingArtifactIndex:
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = str(database_path)
        Path(self.database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.ledger = ScientificContextBindingLedger(
            self.database_path
        )
        self._initialize_indexes()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_indexes(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_tenant_authority_receipt
                ON scientific_execution_context_bindings (
                    tenant_id,
                    authority_receipt_hash
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_tenant_checkpoint
                ON scientific_execution_context_bindings (
                    tenant_id,
                    checkpoint_hash
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_tenant_execution
                ON scientific_execution_context_bindings (
                    tenant_id,
                    execution_id
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_tenant_binding
                ON scientific_execution_context_bindings (
                    tenant_id,
                    binding_hash
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_authority_receipt
                ON scientific_execution_context_bindings (
                    authority_receipt_hash
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_checkpoint
                ON scientific_execution_context_bindings (
                    checkpoint_hash
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_execution_lookup
                ON scientific_execution_context_bindings (
                    execution_id
                )
                """
            )

    def find_for_tenant(
        self,
        *,
        tenant_id: str,
        artifact_type: IndexedScientificArtifactType,
        artifact_id: str,
    ) -> ScientificContextBindingLedgerRecord | None:
        column_name = self._column_for_artifact_type(
            artifact_type
        )

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT binding_hash
                FROM scientific_execution_context_bindings
                WHERE tenant_id = ?
                  AND {column_name} = ?
                ORDER BY sequence_number ASC
                """,
                (tenant_id, artifact_id),
            ).fetchall()

        return self._resolve_single_record(
            rows=rows,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
        )

    def find_owner(
        self,
        *,
        artifact_type: IndexedScientificArtifactType,
        artifact_id: str,
    ) -> ScientificArtifactBindingOwner | None:
        column_name = self._column_for_artifact_type(
            artifact_type
        )

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    tenant_id,
                    binding_hash,
                    execution_id
                FROM scientific_execution_context_bindings
                WHERE {column_name} = ?
                ORDER BY sequence_number ASC
                """,
                (artifact_id,),
            ).fetchall()

        if not rows:
            return None

        owners = {
            (
                row["tenant_id"],
                row["binding_hash"],
                row["execution_id"],
            )
            for row in rows
        }

        if len(owners) != 1:
            raise DuplicateScientificArtifactBindingError(
                "Scientific artifact is bound to multiple "
                "execution contexts."
            )

        tenant_id, binding_hash, execution_id = next(
            iter(owners)
        )

        return ScientificArtifactBindingOwner(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            tenant_id=tenant_id,
            binding_hash=binding_hash,
            execution_id=execution_id,
        )

    def belongs_to_tenant(
        self,
        *,
        tenant_id: str,
        artifact_type: IndexedScientificArtifactType,
        artifact_id: str,
    ) -> bool:
        return (
            self.find_for_tenant(
                tenant_id=tenant_id,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
            )
            is not None
        )

    def _resolve_single_record(
        self,
        *,
        rows: list[sqlite3.Row],
        artifact_type: IndexedScientificArtifactType,
        artifact_id: str,
    ) -> ScientificContextBindingLedgerRecord | None:
        if not rows:
            return None

        binding_hashes = {
            row["binding_hash"]
            for row in rows
        }

        if len(binding_hashes) != 1:
            raise DuplicateScientificArtifactBindingError(
                "Scientific artifact is bound to multiple "
                "tenant context bindings."
            )

        binding_hash = next(iter(binding_hashes))
        record = self.ledger.get_by_hash(binding_hash)

        if record is None:
            raise ScientificContextBindingIndexError(
                "Binding index referenced a missing context "
                "binding record."
            )

        return record

    def _column_for_artifact_type(
        self,
        artifact_type: IndexedScientificArtifactType,
    ) -> str:
        columns = {
            "authority_receipt": "authority_receipt_hash",
            "checkpoint": "checkpoint_hash",
            "execution": "execution_id",
            "context_binding": "binding_hash",
        }

        try:
            return columns[artifact_type]
        except KeyError as exc:
            raise ScientificContextBindingIndexError(
                "Unsupported scientific artifact type: "
                f"{artifact_type}"
            ) from exc
