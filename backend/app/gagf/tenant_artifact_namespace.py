import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


TENANT_ARTIFACT_NAMESPACE_ID = (
    "tenant-scientific-artifact-namespace"
)
TENANT_ARTIFACT_NAMESPACE_VERSION = "0.1.0"
TENANT_ARTIFACT_NAMESPACE_SCHEMA_VERSION = "1.0.0"

TENANT_ARTIFACT_NAMESPACE_LEDGER_ID = (
    "tenant-scientific-artifact-namespace-ledger"
)
TENANT_ARTIFACT_NAMESPACE_LEDGER_VERSION = "0.1.0"


TenantNamespacedArtifactType = Literal[
    "execution",
    "execution_receipt",
    "authority_receipt",
    "audit_receipt",
    "checkpoint",
    "context_binding",
]


class TenantArtifactNamespaceError(ValueError):
    pass


class TenantArtifactNamespaceLedgerError(RuntimeError):
    pass


class TenantArtifactNamespaceConflictError(
    TenantArtifactNamespaceLedgerError
):
    pass


class InvalidTenantArtifactNamespaceRecordError(
    TenantArtifactNamespaceLedgerError
):
    pass


def _require_value(
    *,
    field_name: str,
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise TenantArtifactNamespaceError(
            f"{field_name} must not be empty."
        )

    if len(normalized) > 256:
        raise TenantArtifactNamespaceError(
            f"{field_name} must not exceed 256 characters."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class TenantArtifactNamespace:
    tenant_id: str
    artifact_type: TenantNamespacedArtifactType
    canonical_artifact_id: str
    namespace_id: str
    namespace_version: str
    schema_version: str
    namespaced_artifact_id: str

    def payload(self) -> dict[str, str]:
        return {
            "tenant_id": self.tenant_id,
            "artifact_type": self.artifact_type,
            "canonical_artifact_id": (
                self.canonical_artifact_id
            ),
            "namespace_id": self.namespace_id,
            "namespace_version": self.namespace_version,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, str]:
        return {
            **self.payload(),
            "namespaced_artifact_id": (
                self.namespaced_artifact_id
            ),
        }

    def verify(self) -> bool:
        expected = sha256_hex(
            canonical_json(self.payload())
        )

        return expected == self.namespaced_artifact_id


class TenantArtifactNamespaceDeriver:
    def derive(
        self,
        *,
        tenant_id: str,
        artifact_type: TenantNamespacedArtifactType,
        canonical_artifact_id: str,
    ) -> TenantArtifactNamespace:
        normalized_tenant_id = _require_value(
            field_name="tenant_id",
            value=tenant_id,
        )
        normalized_artifact_id = _require_value(
            field_name="canonical_artifact_id",
            value=canonical_artifact_id,
        )

        payload = {
            "tenant_id": normalized_tenant_id,
            "artifact_type": artifact_type,
            "canonical_artifact_id": (
                normalized_artifact_id
            ),
            "namespace_id": TENANT_ARTIFACT_NAMESPACE_ID,
            "namespace_version": (
                TENANT_ARTIFACT_NAMESPACE_VERSION
            ),
            "schema_version": (
                TENANT_ARTIFACT_NAMESPACE_SCHEMA_VERSION
            ),
        }

        return TenantArtifactNamespace(
            tenant_id=normalized_tenant_id,
            artifact_type=artifact_type,
            canonical_artifact_id=(
                normalized_artifact_id
            ),
            namespace_id=TENANT_ARTIFACT_NAMESPACE_ID,
            namespace_version=(
                TENANT_ARTIFACT_NAMESPACE_VERSION
            ),
            schema_version=(
                TENANT_ARTIFACT_NAMESPACE_SCHEMA_VERSION
            ),
            namespaced_artifact_id=sha256_hex(
                canonical_json(payload)
            ),
        )


@dataclass(frozen=True, slots=True)
class TenantArtifactNamespaceBundle:
    tenant_id: str
    execution: TenantArtifactNamespace
    execution_receipt: TenantArtifactNamespace
    authority_receipt: TenantArtifactNamespace
    audit_receipt: TenantArtifactNamespace
    checkpoint: TenantArtifactNamespace
    context_binding: TenantArtifactNamespace

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "execution": self.execution.to_dict(),
            "execution_receipt": (
                self.execution_receipt.to_dict()
            ),
            "authority_receipt": (
                self.authority_receipt.to_dict()
            ),
            "audit_receipt": (
                self.audit_receipt.to_dict()
            ),
            "checkpoint": self.checkpoint.to_dict(),
            "context_binding": (
                self.context_binding.to_dict()
            ),
        }

    def verify(self) -> bool:
        records = (
            self.execution,
            self.execution_receipt,
            self.authority_receipt,
            self.audit_receipt,
            self.checkpoint,
            self.context_binding,
        )

        return all(
            record.tenant_id == self.tenant_id
            and record.verify()
            for record in records
        )


class TenantArtifactNamespaceBundleBuilder:
    def __init__(self) -> None:
        self.deriver = TenantArtifactNamespaceDeriver()

    def build(
        self,
        *,
        tenant_id: str,
        execution_id: str,
        execution_receipt_hash: str,
        authority_receipt_hash: str,
        audit_receipt_hash: str,
        checkpoint_hash: str,
        context_binding_hash: str,
    ) -> TenantArtifactNamespaceBundle:
        return TenantArtifactNamespaceBundle(
            tenant_id=tenant_id.strip(),
            execution=self.deriver.derive(
                tenant_id=tenant_id,
                artifact_type="execution",
                canonical_artifact_id=execution_id,
            ),
            execution_receipt=self.deriver.derive(
                tenant_id=tenant_id,
                artifact_type="execution_receipt",
                canonical_artifact_id=(
                    execution_receipt_hash
                ),
            ),
            authority_receipt=self.deriver.derive(
                tenant_id=tenant_id,
                artifact_type="authority_receipt",
                canonical_artifact_id=(
                    authority_receipt_hash
                ),
            ),
            audit_receipt=self.deriver.derive(
                tenant_id=tenant_id,
                artifact_type="audit_receipt",
                canonical_artifact_id=audit_receipt_hash,
            ),
            checkpoint=self.deriver.derive(
                tenant_id=tenant_id,
                artifact_type="checkpoint",
                canonical_artifact_id=checkpoint_hash,
            ),
            context_binding=self.deriver.derive(
                tenant_id=tenant_id,
                artifact_type="context_binding",
                canonical_artifact_id=(
                    context_binding_hash
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class TenantArtifactNamespaceLedgerRecord:
    sequence_number: int
    namespace: TenantArtifactNamespace

    def to_dict(self) -> dict:
        return {
            "sequence_number": self.sequence_number,
            "namespace": self.namespace.to_dict(),
        }


class TenantArtifactNamespaceLedger:
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
                tenant_artifact_namespaces (
                    sequence_number
                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    canonical_artifact_id TEXT NOT NULL,
                    namespaced_artifact_id TEXT NOT NULL UNIQUE,
                    namespace_json TEXT NOT NULL,
                    UNIQUE (
                        tenant_id,
                        artifact_type,
                        canonical_artifact_id
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_tenant_namespace_lookup
                ON tenant_artifact_namespaces (
                    tenant_id,
                    artifact_type,
                    namespaced_artifact_id
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_canonical_namespace_lookup
                ON tenant_artifact_namespaces (
                    artifact_type,
                    canonical_artifact_id
                )
                """
            )

    def append(
        self,
        namespace: TenantArtifactNamespace,
    ) -> TenantArtifactNamespaceLedgerRecord:
        if not namespace.verify():
            raise InvalidTenantArtifactNamespaceRecordError(
                "Tenant artifact namespace failed hash "
                "verification."
            )

        serialized = canonical_json(
            namespace.to_dict()
        )

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    sequence_number,
                    namespace_json
                FROM tenant_artifact_namespaces
                WHERE tenant_id = ?
                  AND artifact_type = ?
                  AND canonical_artifact_id = ?
                """,
                (
                    namespace.tenant_id,
                    namespace.artifact_type,
                    namespace.canonical_artifact_id,
                ),
            ).fetchone()

            if existing is not None:
                if existing["namespace_json"] != serialized:
                    raise TenantArtifactNamespaceConflictError(
                        "Tenant artifact namespace already "
                        "exists with different content."
                    )

                return TenantArtifactNamespaceLedgerRecord(
                    sequence_number=existing[
                        "sequence_number"
                    ],
                    namespace=namespace,
                )

            namespaced_match = connection.execute(
                """
                SELECT namespace_json
                FROM tenant_artifact_namespaces
                WHERE namespaced_artifact_id = ?
                """,
                (namespace.namespaced_artifact_id,),
            ).fetchone()

            if namespaced_match is not None:
                if namespaced_match["namespace_json"] != serialized:
                    raise TenantArtifactNamespaceConflictError(
                        "Namespaced artifact ID already exists "
                        "with different content."
                    )

            cursor = connection.execute(
                """
                INSERT INTO tenant_artifact_namespaces (
                    tenant_id,
                    artifact_type,
                    canonical_artifact_id,
                    namespaced_artifact_id,
                    namespace_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    namespace.tenant_id,
                    namespace.artifact_type,
                    namespace.canonical_artifact_id,
                    namespace.namespaced_artifact_id,
                    serialized,
                ),
            )

            sequence_number = cursor.lastrowid

        if sequence_number is None:
            raise TenantArtifactNamespaceLedgerError(
                "Tenant namespace append did not produce a "
                "sequence number."
            )

        return TenantArtifactNamespaceLedgerRecord(
            sequence_number=sequence_number,
            namespace=namespace,
        )

    def append_bundle(
        self,
        bundle: TenantArtifactNamespaceBundle,
    ) -> tuple[
        TenantArtifactNamespaceLedgerRecord,
        ...,
    ]:
        if not bundle.verify():
            raise InvalidTenantArtifactNamespaceRecordError(
                "Tenant artifact namespace bundle failed "
                "verification."
            )

        namespaces = (
            bundle.execution,
            bundle.execution_receipt,
            bundle.authority_receipt,
            bundle.audit_receipt,
            bundle.checkpoint,
            bundle.context_binding,
        )

        return tuple(
            self.append(namespace)
            for namespace in namespaces
        )

    def get_by_namespaced_id(
        self,
        *,
        tenant_id: str,
        artifact_type: TenantNamespacedArtifactType,
        namespaced_artifact_id: str,
    ) -> TenantArtifactNamespaceLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    namespace_json
                FROM tenant_artifact_namespaces
                WHERE tenant_id = ?
                  AND artifact_type = ?
                  AND namespaced_artifact_id = ?
                """,
                (
                    tenant_id,
                    artifact_type,
                    namespaced_artifact_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return TenantArtifactNamespaceLedgerRecord(
            sequence_number=row["sequence_number"],
            namespace=self._deserialize(
                row["namespace_json"]
            ),
        )

    def get_by_canonical_id(
        self,
        *,
        tenant_id: str,
        artifact_type: TenantNamespacedArtifactType,
        canonical_artifact_id: str,
    ) -> TenantArtifactNamespaceLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    namespace_json
                FROM tenant_artifact_namespaces
                WHERE tenant_id = ?
                  AND artifact_type = ?
                  AND canonical_artifact_id = ?
                """,
                (
                    tenant_id,
                    artifact_type,
                    canonical_artifact_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return TenantArtifactNamespaceLedgerRecord(
            sequence_number=row["sequence_number"],
            namespace=self._deserialize(
                row["namespace_json"]
            ),
        )

    def list_for_tenant(
        self,
        tenant_id: str,
    ) -> tuple[
        TenantArtifactNamespaceLedgerRecord,
        ...,
    ]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    sequence_number,
                    namespace_json
                FROM tenant_artifact_namespaces
                WHERE tenant_id = ?
                ORDER BY sequence_number ASC
                """,
                (tenant_id,),
            ).fetchall()

        return tuple(
            TenantArtifactNamespaceLedgerRecord(
                sequence_number=row["sequence_number"],
                namespace=self._deserialize(
                    row["namespace_json"]
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
            FROM tenant_artifact_namespaces
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
                SELECT namespace_json
                FROM tenant_artifact_namespaces
                ORDER BY sequence_number ASC
                """
            ).fetchall()

        return all(
            self._deserialize(
                row["namespace_json"]
            ).verify()
            for row in rows
        )

    def _deserialize(
        self,
        serialized: str,
    ) -> TenantArtifactNamespace:
        data = json.loads(serialized)

        return TenantArtifactNamespace(
            tenant_id=data["tenant_id"],
            artifact_type=data["artifact_type"],
            canonical_artifact_id=data[
                "canonical_artifact_id"
            ],
            namespace_id=data["namespace_id"],
            namespace_version=data["namespace_version"],
            schema_version=data["schema_version"],
            namespaced_artifact_id=data[
                "namespaced_artifact_id"
            ],
        )
