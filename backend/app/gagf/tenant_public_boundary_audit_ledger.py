import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditResult,
)


TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID = (
    "tenant-public-boundary-audit-ledger"
)
TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION = "0.1.0"
TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION = "1.0.0"
TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH = "0" * 64


class TenantPublicBoundaryAuditLedgerError(
    RuntimeError
):
    pass


class TenantPublicBoundaryAuditIntegrityError(
    TenantPublicBoundaryAuditLedgerError
):
    pass


@dataclass(frozen=True, slots=True)
class TenantPublicBoundaryAuditRecord:
    schema_version: str
    ledger_id: str
    ledger_version: str
    sequence_number: int
    tenant_id: str
    response_kind: str
    released: bool
    audit_valid: bool
    violation_count: int
    boundary_audit_hash: str
    previous_record_hash: str
    record_hash: str

    def payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "ledger_version": self.ledger_version,
            "sequence_number": self.sequence_number,
            "tenant_id": self.tenant_id,
            "response_kind": self.response_kind,
            "released": self.released,
            "audit_valid": self.audit_valid,
            "violation_count": self.violation_count,
            "boundary_audit_hash": (
                self.boundary_audit_hash
            ),
            "previous_record_hash": (
                self.previous_record_hash
            ),
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "record_hash": self.record_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.record_hash


@dataclass(frozen=True, slots=True)
class TenantPublicBoundaryAuditLedgerVerification:
    ledger_id: str
    ledger_version: str
    valid: bool
    record_count: int
    last_sequence_number: int
    last_record_hash: str
    failure_sequence_number: int | None

    def to_dict(self) -> dict:
        return {
            "ledger_id": self.ledger_id,
            "ledger_version": self.ledger_version,
            "valid": self.valid,
            "record_count": self.record_count,
            "last_sequence_number": (
                self.last_sequence_number
            ),
            "last_record_hash": self.last_record_hash,
            "failure_sequence_number": (
                self.failure_sequence_number
            ),
        }


class TenantPublicBoundaryAuditLedger:
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize()

    def append(
        self,
        *,
        tenant_id: str,
        response_kind: str,
        released: bool,
        audit: TenantPublicBoundaryAuditResult,
    ) -> TenantPublicBoundaryAuditRecord:
        normalized_tenant_id = tenant_id.strip()
        normalized_response_kind = (
            response_kind.strip()
        )

        if not normalized_tenant_id:
            raise ValueError(
                "tenant_id must not be empty."
            )

        if not normalized_response_kind:
            raise ValueError(
                "response_kind must not be empty."
            )

        if not audit.verify():
            raise TenantPublicBoundaryAuditIntegrityError(
                "Boundary audit hash verification failed."
            )

        if released and not audit.valid:
            raise TenantPublicBoundaryAuditIntegrityError(
                "An invalid boundary audit cannot be "
                "recorded as released."
            )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            latest = connection.execute(
                """
                SELECT
                    sequence_number,
                    record_hash
                FROM tenant_public_boundary_audit_records
                ORDER BY sequence_number DESC
                LIMIT 1
                """
            ).fetchone()

            if latest is None:
                sequence_number = 1
                previous_record_hash = (
                    TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH
                )
            else:
                sequence_number = (
                    int(latest["sequence_number"]) + 1
                )
                previous_record_hash = str(
                    latest["record_hash"]
                )

            record = self._build_record(
                sequence_number=sequence_number,
                tenant_id=normalized_tenant_id,
                response_kind=(
                    normalized_response_kind
                ),
                released=released,
                audit=audit,
                previous_record_hash=(
                    previous_record_hash
                ),
            )

            connection.execute(
                """
                INSERT INTO
                    tenant_public_boundary_audit_records
                (
                    schema_version,
                    ledger_id,
                    ledger_version,
                    sequence_number,
                    tenant_id,
                    response_kind,
                    released,
                    audit_valid,
                    violation_count,
                    boundary_audit_hash,
                    previous_record_hash,
                    record_hash,
                    record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.schema_version,
                    record.ledger_id,
                    record.ledger_version,
                    record.sequence_number,
                    record.tenant_id,
                    record.response_kind,
                    int(record.released),
                    int(record.audit_valid),
                    record.violation_count,
                    record.boundary_audit_hash,
                    record.previous_record_hash,
                    record.record_hash,
                    canonical_json(record.to_dict()),
                ),
            )

            connection.commit()

        return record

    def get(
        self,
        sequence_number: int,
    ) -> TenantPublicBoundaryAuditRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_json
                FROM tenant_public_boundary_audit_records
                WHERE sequence_number = ?
                """,
                (sequence_number,),
            ).fetchone()

        if row is None:
            return None

        return self._record_from_dict(
            json.loads(row["record_json"])
        )

    def list_records(
        self,
        *,
        tenant_id: str | None = None,
    ) -> tuple[TenantPublicBoundaryAuditRecord, ...]:
        with self._connect() as connection:
            if tenant_id is None:
                rows = connection.execute(
                    """
                    SELECT record_json
                    FROM tenant_public_boundary_audit_records
                    ORDER BY sequence_number ASC
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT record_json
                    FROM tenant_public_boundary_audit_records
                    WHERE tenant_id = ?
                    ORDER BY sequence_number ASC
                    """,
                    (tenant_id,),
                ).fetchall()

        return tuple(
            self._record_from_dict(
                json.loads(row["record_json"])
            )
            for row in rows
        )

    def verify_chain(
        self,
    ) -> TenantPublicBoundaryAuditLedgerVerification:
        records = self.list_records()

        expected_previous_hash = (
            TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH
        )

        for expected_sequence, record in enumerate(
            records,
            start=1,
        ):
            if (
                record.sequence_number
                != expected_sequence
                or record.previous_record_hash
                != expected_previous_hash
                or not record.verify()
            ):
                return (
                    TenantPublicBoundaryAuditLedgerVerification(
                        ledger_id=(
                            TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID
                        ),
                        ledger_version=(
                            TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION
                        ),
                        valid=False,
                        record_count=len(records),
                        last_sequence_number=(
                            records[-1].sequence_number
                            if records
                            else 0
                        ),
                        last_record_hash=(
                            records[-1].record_hash
                            if records
                            else (
                                TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH
                            )
                        ),
                        failure_sequence_number=(
                            record.sequence_number
                        ),
                    )
                )

            expected_previous_hash = record.record_hash

        return TenantPublicBoundaryAuditLedgerVerification(
            ledger_id=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID
            ),
            ledger_version=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION
            ),
            valid=True,
            record_count=len(records),
            last_sequence_number=(
                records[-1].sequence_number
                if records
                else 0
            ),
            last_record_hash=(
                records[-1].record_hash
                if records
                else (
                    TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH
                )
            ),
            failure_sequence_number=None,
        )

    def _build_record(
        self,
        *,
        sequence_number: int,
        tenant_id: str,
        response_kind: str,
        released: bool,
        audit: TenantPublicBoundaryAuditResult,
        previous_record_hash: str,
    ) -> TenantPublicBoundaryAuditRecord:
        payload = {
            "schema_version": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION
            ),
            "ledger_id": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID
            ),
            "ledger_version": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION
            ),
            "sequence_number": sequence_number,
            "tenant_id": tenant_id,
            "response_kind": response_kind,
            "released": released,
            "audit_valid": audit.valid,
            "violation_count": audit.violation_count,
            "boundary_audit_hash": audit.audit_hash,
            "previous_record_hash": (
                previous_record_hash
            ),
        }

        return TenantPublicBoundaryAuditRecord(
            schema_version=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION
            ),
            ledger_id=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID
            ),
            ledger_version=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION
            ),
            sequence_number=sequence_number,
            tenant_id=tenant_id,
            response_kind=response_kind,
            released=released,
            audit_valid=audit.valid,
            violation_count=audit.violation_count,
            boundary_audit_hash=audit.audit_hash,
            previous_record_hash=previous_record_hash,
            record_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    def _record_from_dict(
        self,
        value: dict[str, Any],
    ) -> TenantPublicBoundaryAuditRecord:
        return TenantPublicBoundaryAuditRecord(
            schema_version=str(
                value["schema_version"]
            ),
            ledger_id=str(value["ledger_id"]),
            ledger_version=str(
                value["ledger_version"]
            ),
            sequence_number=int(
                value["sequence_number"]
            ),
            tenant_id=str(value["tenant_id"]),
            response_kind=str(
                value["response_kind"]
            ),
            released=bool(value["released"]),
            audit_valid=bool(
                value["audit_valid"]
            ),
            violation_count=int(
                value["violation_count"]
            ),
            boundary_audit_hash=str(
                value["boundary_audit_hash"]
            ),
            previous_record_hash=str(
                value["previous_record_hash"]
            ),
            record_hash=str(value["record_hash"]),
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                    tenant_public_boundary_audit_records
                (
                    sequence_number INTEGER PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    ledger_id TEXT NOT NULL,
                    ledger_version TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    response_kind TEXT NOT NULL,
                    released INTEGER NOT NULL,
                    audit_valid INTEGER NOT NULL,
                    violation_count INTEGER NOT NULL,
                    boundary_audit_hash TEXT NOT NULL,
                    previous_record_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_boundary_audit_tenant_sequence
                ON tenant_public_boundary_audit_records
                (
                    tenant_id,
                    sequence_number
                )
                """
            )

            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )
        connection.row_factory = sqlite3.Row

        return connection
