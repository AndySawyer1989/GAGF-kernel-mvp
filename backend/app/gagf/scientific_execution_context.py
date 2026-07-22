import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    RecoverableScientificPipelineResult,
)


SCIENTIFIC_EXECUTION_CONTEXT_ID = (
    "scientific-authority-execution-context"
)
SCIENTIFIC_EXECUTION_CONTEXT_VERSION = "0.1.0"
SCIENTIFIC_EXECUTION_CONTEXT_SCHEMA_VERSION = "1.0.0"

SCIENTIFIC_CONTEXT_BINDING_LEDGER_ID = (
    "scientific-authority-context-binding-ledger"
)
SCIENTIFIC_CONTEXT_BINDING_LEDGER_VERSION = "0.1.0"


class ScientificExecutionContextError(ValueError):
    pass


class ScientificContextBindingLedgerError(RuntimeError):
    pass


class InvalidScientificContextBindingError(
    ScientificContextBindingLedgerError
):
    pass


class ScientificContextBindingConflictError(
    ScientificContextBindingLedgerError
):
    pass


def _require_identifier(
    *,
    field_name: str,
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ScientificExecutionContextError(
            f"{field_name} must not be empty."
        )

    if len(normalized) > 256:
        raise ScientificExecutionContextError(
            f"{field_name} must not exceed 256 characters."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class ScientificExecutionContext:
    tenant_id: str
    actor_id: str
    credential_id: str
    session_id: str
    role_id: str
    policy_scope: str
    request_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "actor_id",
            "credential_id",
            "session_id",
            "role_id",
            "policy_scope",
            "request_id",
            "correlation_id",
        ):
            normalized = _require_identifier(
                field_name=field_name,
                value=getattr(self, field_name),
            )
            object.__setattr__(
                self,
                field_name,
                normalized,
            )

    def payload(self) -> dict[str, str]:
        return {
            "context_schema_version": (
                SCIENTIFIC_EXECUTION_CONTEXT_SCHEMA_VERSION
            ),
            "context_id": SCIENTIFIC_EXECUTION_CONTEXT_ID,
            "context_version": (
                SCIENTIFIC_EXECUTION_CONTEXT_VERSION
            ),
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "credential_id": self.credential_id,
            "session_id": self.session_id,
            "role_id": self.role_id,
            "policy_scope": self.policy_scope,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
        }

    @property
    def context_hash(self) -> str:
        return sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, str]:
        return {
            **self.payload(),
            "context_hash": self.context_hash,
        }


@dataclass(frozen=True, slots=True)
class ScientificExecutionContextBinding:
    binding_schema_version: str
    binding_id: str
    binding_version: str
    context: dict[str, str]
    context_hash: str
    execution_id: str
    execution_receipt_hash: str
    authority_receipt_hash: str
    audit_receipt_hash: str
    checkpoint_hash: str
    binding_hash: str

    def payload(self) -> dict:
        return {
            "binding_schema_version": (
                self.binding_schema_version
            ),
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
            "context": dict(self.context),
            "context_hash": self.context_hash,
            "execution_id": self.execution_id,
            "execution_receipt_hash": (
                self.execution_receipt_hash
            ),
            "authority_receipt_hash": (
                self.authority_receipt_hash
            ),
            "audit_receipt_hash": self.audit_receipt_hash,
            "checkpoint_hash": self.checkpoint_hash,
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "binding_hash": self.binding_hash,
        }

    def verify(self) -> bool:
        expected_context_hash = sha256_hex(
            canonical_json(self.context)
        )
        expected_binding_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return (
            expected_context_hash == self.context_hash
            and expected_binding_hash == self.binding_hash
        )


class ScientificExecutionContextBindingBuilder:
    def build(
        self,
        *,
        context: ScientificExecutionContext,
        result: RecoverableScientificPipelineResult,
    ) -> ScientificExecutionContextBinding:
        context_payload = context.payload()
        context_hash = context.context_hash

        payload = {
            "binding_schema_version": "1.0.0",
            "binding_id": (
                "scientific-authority-execution-context-binding"
            ),
            "binding_version": "0.1.0",
            "context": context_payload,
            "context_hash": context_hash,
            "execution_id": result.execution_id,
            "execution_receipt_hash": (
                result.execution_receipt.receipt_hash
            ),
            "authority_receipt_hash": (
                result.pipeline_result.authority_receipt_hash
            ),
            "audit_receipt_hash": (
                result.pipeline_result.audit_receipt_hash
            ),
            "checkpoint_hash": (
                result.pipeline_result.checkpoint_hash
            ),
        }

        binding_hash = sha256_hex(
            canonical_json(payload)
        )

        return ScientificExecutionContextBinding(
            binding_schema_version="1.0.0",
            binding_id=(
                "scientific-authority-execution-context-binding"
            ),
            binding_version="0.1.0",
            context=context_payload,
            context_hash=context_hash,
            execution_id=result.execution_id,
            execution_receipt_hash=(
                result.execution_receipt.receipt_hash
            ),
            authority_receipt_hash=(
                result.pipeline_result.authority_receipt_hash
            ),
            audit_receipt_hash=(
                result.pipeline_result.audit_receipt_hash
            ),
            checkpoint_hash=(
                result.pipeline_result.checkpoint_hash
            ),
            binding_hash=binding_hash,
        )


@dataclass(frozen=True, slots=True)
class ScientificContextBindingLedgerRecord:
    sequence_number: int
    binding: ScientificExecutionContextBinding

    def to_dict(self) -> dict:
        return {
            "sequence_number": self.sequence_number,
            "binding": self.binding.to_dict(),
        }


class ScientificContextBindingLedger:
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = str(database_path)

        Path(self.database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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
                scientific_execution_context_bindings (
                    sequence_number
                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    binding_hash TEXT NOT NULL UNIQUE,
                    context_hash TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    credential_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    policy_scope TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    execution_receipt_hash TEXT NOT NULL,
                    authority_receipt_hash TEXT NOT NULL,
                    audit_receipt_hash TEXT NOT NULL,
                    checkpoint_hash TEXT NOT NULL,
                    binding_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_tenant_sequence
                ON scientific_execution_context_bindings (
                    tenant_id,
                    sequence_number
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_bindings_execution
                ON scientific_execution_context_bindings (
                    execution_id
                )
                """
            )

            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_context_bindings_tenant_request
                ON scientific_execution_context_bindings (
                    tenant_id,
                    request_id
                )
                """
            )

    def append(
        self,
        binding: ScientificExecutionContextBinding,
    ) -> ScientificContextBindingLedgerRecord:
        if not binding.verify():
            raise InvalidScientificContextBindingError(
                "Scientific execution context binding failed "
                "hash verification."
            )

        serialized_binding = canonical_json(
            binding.to_dict()
        )

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    sequence_number,
                    binding_json
                FROM scientific_execution_context_bindings
                WHERE binding_hash = ?
                """,
                (binding.binding_hash,),
            ).fetchone()

            if existing is not None:
                if (
                    existing["binding_json"]
                    != serialized_binding
                ):
                    raise ScientificContextBindingConflictError(
                        "Binding hash already exists with "
                        "different content."
                    )

                return ScientificContextBindingLedgerRecord(
                    sequence_number=existing[
                        "sequence_number"
                    ],
                    binding=binding,
                )

            request_binding = connection.execute(
                """
                SELECT
                    binding_hash,
                    binding_json
                FROM scientific_execution_context_bindings
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (
                    binding.context["tenant_id"],
                    binding.context["request_id"],
                ),
            ).fetchone()

            if request_binding is not None:
                if (
                    request_binding["binding_hash"]
                    != binding.binding_hash
                ):
                    raise ScientificContextBindingConflictError(
                        "Tenant request ID is already bound to a "
                        "different execution context."
                    )

            cursor = connection.execute(
                """
                INSERT INTO scientific_execution_context_bindings (
                    binding_hash,
                    context_hash,
                    tenant_id,
                    actor_id,
                    credential_id,
                    session_id,
                    role_id,
                    policy_scope,
                    request_id,
                    correlation_id,
                    execution_id,
                    execution_receipt_hash,
                    authority_receipt_hash,
                    audit_receipt_hash,
                    checkpoint_hash,
                    binding_json
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    binding.binding_hash,
                    binding.context_hash,
                    binding.context["tenant_id"],
                    binding.context["actor_id"],
                    binding.context["credential_id"],
                    binding.context["session_id"],
                    binding.context["role_id"],
                    binding.context["policy_scope"],
                    binding.context["request_id"],
                    binding.context["correlation_id"],
                    binding.execution_id,
                    binding.execution_receipt_hash,
                    binding.authority_receipt_hash,
                    binding.audit_receipt_hash,
                    binding.checkpoint_hash,
                    serialized_binding,
                ),
            )

            sequence_number = cursor.lastrowid

        if sequence_number is None:
            raise ScientificContextBindingLedgerError(
                "Context binding append did not produce a "
                "sequence number."
            )

        return ScientificContextBindingLedgerRecord(
            sequence_number=sequence_number,
            binding=binding,
        )

    def get_by_hash(
        self,
        binding_hash: str,
    ) -> ScientificContextBindingLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    binding_json
                FROM scientific_execution_context_bindings
                WHERE binding_hash = ?
                """,
                (binding_hash,),
            ).fetchone()

        if row is None:
            return None

        return ScientificContextBindingLedgerRecord(
            sequence_number=row["sequence_number"],
            binding=self._deserialize_binding(
                row["binding_json"]
            ),
        )

    def get_by_execution_id(
        self,
        execution_id: str,
    ) -> ScientificContextBindingLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    binding_json
                FROM scientific_execution_context_bindings
                WHERE execution_id = ?
                ORDER BY sequence_number ASC
                LIMIT 1
                """,
                (execution_id,),
            ).fetchone()

        if row is None:
            return None

        return ScientificContextBindingLedgerRecord(
            sequence_number=row["sequence_number"],
            binding=self._deserialize_binding(
                row["binding_json"]
            ),
        )

    def list_for_tenant(
        self,
        tenant_id: str,
    ) -> tuple[
        ScientificContextBindingLedgerRecord,
        ...,
    ]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    sequence_number,
                    binding_json
                FROM scientific_execution_context_bindings
                WHERE tenant_id = ?
                ORDER BY sequence_number ASC
                """,
                (tenant_id,),
            ).fetchall()

        return tuple(
            ScientificContextBindingLedgerRecord(
                sequence_number=row["sequence_number"],
                binding=self._deserialize_binding(
                    row["binding_json"]
                ),
            )
            for row in rows
        )

    def count(
        self,
        *,
        tenant_id: str | None = None,
    ) -> int:
        query = """
            SELECT COUNT(*) AS record_count
            FROM scientific_execution_context_bindings
        """
        parameters: tuple[str, ...] = ()

        if tenant_id is not None:
            query += " WHERE tenant_id = ?"
            parameters = (tenant_id,)

        with self._connect() as connection:
            row = connection.execute(
                query,
                parameters,
            ).fetchone()

        return int(row["record_count"])

    def verify_all(self) -> bool:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT binding_json
                FROM scientific_execution_context_bindings
                ORDER BY sequence_number ASC
                """
            ).fetchall()

        return all(
            self._deserialize_binding(
                row["binding_json"]
            ).verify()
            for row in rows
        )

    def _deserialize_binding(
        self,
        serialized_binding: str,
    ) -> ScientificExecutionContextBinding:
        data = json.loads(serialized_binding)

        return ScientificExecutionContextBinding(
            binding_schema_version=data[
                "binding_schema_version"
            ],
            binding_id=data["binding_id"],
            binding_version=data["binding_version"],
            context=dict(data["context"]),
            context_hash=data["context_hash"],
            execution_id=data["execution_id"],
            execution_receipt_hash=data[
                "execution_receipt_hash"
            ],
            authority_receipt_hash=data[
                "authority_receipt_hash"
            ],
            audit_receipt_hash=data[
                "audit_receipt_hash"
            ],
            checkpoint_hash=data["checkpoint_hash"],
            binding_hash=data["binding_hash"],
        )
