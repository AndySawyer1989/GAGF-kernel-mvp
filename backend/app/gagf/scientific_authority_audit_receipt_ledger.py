import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
)
from backend.app.gagf.scientific_authority_ledger_audit_receipt import (
    AuthorityLedgerAuditReceipt,
)


AUTHORITY_AUDIT_RECEIPT_LEDGER_ID = (
    "scientific-authority-audit-receipt-ledger"
)
AUTHORITY_AUDIT_RECEIPT_LEDGER_VERSION = "0.1.0"


class AuthorityAuditReceiptLedgerError(RuntimeError):
    pass


class InvalidAuthorityAuditReceiptError(
    AuthorityAuditReceiptLedgerError
):
    pass


class AuthorityAuditReceiptConflictError(
    AuthorityAuditReceiptLedgerError
):
    pass


@dataclass(frozen=True, slots=True)
class AuthorityAuditReceiptLedgerRecord:
    sequence_number: int
    receipt: AuthorityLedgerAuditReceipt

    def to_dict(self) -> dict:
        return {
            "sequence_number": self.sequence_number,
            "receipt": self.receipt.to_dict(),
        }


class ScientificAuthorityAuditReceiptLedger:
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
                scientific_authority_audit_receipts (
                    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_hash TEXT NOT NULL UNIQUE,
                    receipt_schema_version TEXT NOT NULL,
                    receipt_id TEXT NOT NULL,
                    receipt_version TEXT NOT NULL,
                    auditor_id TEXT NOT NULL,
                    auditor_version TEXT NOT NULL,
                    audit_valid INTEGER NOT NULL,
                    record_count INTEGER NOT NULL,
                    checks_json TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    CHECK (audit_valid IN (0, 1)),
                    CHECK (record_count >= 0)
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scientific_authority_audit_receipts_validity
                ON scientific_authority_audit_receipts (
                    audit_valid,
                    sequence_number
                )
                """
            )

    def append(
        self,
        receipt: AuthorityLedgerAuditReceipt,
    ) -> AuthorityAuditReceiptLedgerRecord:
        if not receipt.verify():
            raise InvalidAuthorityAuditReceiptError(
                "Authority audit receipt failed hash verification."
            )

        serialized_receipt = canonical_json(receipt.to_dict())

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    sequence_number,
                    receipt_json
                FROM scientific_authority_audit_receipts
                WHERE receipt_hash = ?
                """,
                (receipt.receipt_hash,),
            ).fetchone()

            if existing is not None:
                if existing["receipt_json"] != serialized_receipt:
                    raise AuthorityAuditReceiptConflictError(
                        "Audit receipt hash already exists with "
                        "different content."
                    )

                return AuthorityAuditReceiptLedgerRecord(
                    sequence_number=existing["sequence_number"],
                    receipt=receipt,
                )

            cursor = connection.execute(
                """
                INSERT INTO scientific_authority_audit_receipts (
                    receipt_hash,
                    receipt_schema_version,
                    receipt_id,
                    receipt_version,
                    auditor_id,
                    auditor_version,
                    audit_valid,
                    record_count,
                    checks_json,
                    findings_json,
                    receipt_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_hash,
                    receipt.receipt_schema_version,
                    receipt.receipt_id,
                    receipt.receipt_version,
                    receipt.auditor_id,
                    receipt.auditor_version,
                    int(receipt.valid),
                    receipt.record_count,
                    canonical_json(receipt.checks),
                    canonical_json(
                        {
                            "findings": [
                                dict(finding)
                                for finding in receipt.findings
                            ]
                        }
                    ),
                    serialized_receipt,
                ),
            )

            sequence_number = cursor.lastrowid

        if sequence_number is None:
            raise AuthorityAuditReceiptLedgerError(
                "Audit receipt append did not produce a sequence number."
            )

        return AuthorityAuditReceiptLedgerRecord(
            sequence_number=sequence_number,
            receipt=receipt,
        )

    def append_many(
        self,
        receipts: Iterable[AuthorityLedgerAuditReceipt],
    ) -> tuple[AuthorityAuditReceiptLedgerRecord, ...]:
        return tuple(
            self.append(receipt)
            for receipt in receipts
        )

    def get_by_hash(
        self,
        receipt_hash: str,
    ) -> AuthorityAuditReceiptLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    receipt_json
                FROM scientific_authority_audit_receipts
                WHERE receipt_hash = ?
                """,
                (receipt_hash,),
            ).fetchone()

        if row is None:
            return None

        return AuthorityAuditReceiptLedgerRecord(
            sequence_number=row["sequence_number"],
            receipt=self._deserialize_receipt(
                row["receipt_json"]
            ),
        )

    def list_records(
        self,
        *,
        valid: bool | None = None,
    ) -> tuple[AuthorityAuditReceiptLedgerRecord, ...]:
        query = """
            SELECT
                sequence_number,
                receipt_json
            FROM scientific_authority_audit_receipts
        """
        parameters: tuple[int, ...] = ()

        if valid is not None:
            query += " WHERE audit_valid = ?"
            parameters = (int(valid),)

        query += " ORDER BY sequence_number ASC"

        with self._connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return tuple(
            AuthorityAuditReceiptLedgerRecord(
                sequence_number=row["sequence_number"],
                receipt=self._deserialize_receipt(
                    row["receipt_json"]
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
            FROM scientific_authority_audit_receipts
        """
        parameters: tuple[int, ...] = ()

        if valid is not None:
            query += " WHERE audit_valid = ?"
            parameters = (int(valid),)

        with self._connect() as connection:
            row = connection.execute(
                query,
                parameters,
            ).fetchone()

        return int(row["record_count"])

    def verify_all(self) -> bool:
        return all(
            record.receipt.verify()
            for record in self.list_records()
        )

    def _deserialize_receipt(
        self,
        serialized_receipt: str,
    ) -> AuthorityLedgerAuditReceipt:
        data = json.loads(serialized_receipt)

        return AuthorityLedgerAuditReceipt(
            receipt_schema_version=data[
                "receipt_schema_version"
            ],
            receipt_id=data["receipt_id"],
            receipt_version=data["receipt_version"],
            auditor_id=data["auditor_id"],
            auditor_version=data["auditor_version"],
            valid=data["valid"],
            record_count=data["record_count"],
            checks=dict(data["checks"]),
            findings=tuple(
                dict(finding)
                for finding in data["findings"]
            ),
            receipt_hash=data["receipt_hash"],
        )
