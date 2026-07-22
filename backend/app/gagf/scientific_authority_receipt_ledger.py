import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from backend.app.gagf.scientific_authority_guard import (
    AuthorityDecisionReceipt,
    canonical_json,
)
from backend.app.gagf.scientific_authority_replay_verifier import (
    ScientificAuthorityReceiptReplayVerifier,
)


AUTHORITY_RECEIPT_LEDGER_ID = "scientific-authority-receipt-ledger"
AUTHORITY_RECEIPT_LEDGER_VERSION = "0.1.0"


class AuthorityReceiptLedgerError(RuntimeError):
    pass


class InvalidAuthorityReceiptError(AuthorityReceiptLedgerError):
    pass


class AuthorityReceiptConflictError(AuthorityReceiptLedgerError):
    pass


@dataclass(frozen=True, slots=True)
class AuthorityReceiptLedgerRecord:
    sequence_number: int
    receipt: AuthorityDecisionReceipt

    def to_dict(self) -> dict:
        return {
            "sequence_number": self.sequence_number,
            "receipt": self.receipt.to_dict(),
        }


class ScientificAuthorityReceiptLedger:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scientific_authority_receipts (
                    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_hash TEXT NOT NULL UNIQUE,
                    receipt_schema_version TEXT NOT NULL,
                    policy_id TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    calculation_id TEXT NOT NULL,
                    calculation_version TEXT NOT NULL,
                    current_authority TEXT NOT NULL,
                    requested_authority TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    decision_json TEXT NOT NULL,
                    receipt_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scientific_authority_receipts_calculation
                ON scientific_authority_receipts (
                    calculation_id,
                    calculation_version,
                    sequence_number
                )
                """
            )

    def append(
        self,
        receipt: AuthorityDecisionReceipt,
    ) -> AuthorityReceiptLedgerRecord:
        replay_result = (
            ScientificAuthorityReceiptReplayVerifier()
            .verify(receipt)
        )

        if not replay_result.valid:
            raise InvalidAuthorityReceiptError(
                "Authority receipt failed replay verification: "
                + "; ".join(replay_result.errors)
            )

        serialized_receipt = canonical_json(receipt.to_dict())

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    sequence_number,
                    receipt_json
                FROM scientific_authority_receipts
                WHERE receipt_hash = ?
                """,
                (receipt.receipt_hash,),
            ).fetchone()

            if existing is not None:
                if existing["receipt_json"] != serialized_receipt:
                    raise AuthorityReceiptConflictError(
                        "Receipt hash already exists with different content."
                    )

                return AuthorityReceiptLedgerRecord(
                    sequence_number=existing["sequence_number"],
                    receipt=receipt,
                )

            cursor = connection.execute(
                """
                INSERT INTO scientific_authority_receipts (
                    receipt_hash,
                    receipt_schema_version,
                    policy_id,
                    policy_version,
                    calculation_id,
                    calculation_version,
                    current_authority,
                    requested_authority,
                    evidence_json,
                    decision_json,
                    receipt_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_hash,
                    receipt.receipt_schema_version,
                    receipt.policy_id,
                    receipt.policy_version,
                    receipt.calculation_id,
                    receipt.calculation_version,
                    receipt.current_authority,
                    receipt.requested_authority,
                    canonical_json(receipt.evidence),
                    canonical_json(receipt.decision),
                    serialized_receipt,
                ),
            )

            sequence_number = cursor.lastrowid

        if sequence_number is None:
            raise AuthorityReceiptLedgerError(
                "Receipt append did not produce a sequence number."
            )

        return AuthorityReceiptLedgerRecord(
            sequence_number=sequence_number,
            receipt=receipt,
        )

    def get_by_hash(
        self,
        receipt_hash: str,
    ) -> AuthorityReceiptLedgerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sequence_number,
                    receipt_json
                FROM scientific_authority_receipts
                WHERE receipt_hash = ?
                """,
                (receipt_hash,),
            ).fetchone()

        if row is None:
            return None

        return AuthorityReceiptLedgerRecord(
            sequence_number=row["sequence_number"],
            receipt=self._deserialize_receipt(
                row["receipt_json"]
            ),
        )

    def list_records(
        self,
        *,
        calculation_id: str | None = None,
    ) -> tuple[AuthorityReceiptLedgerRecord, ...]:
        query = """
            SELECT
                sequence_number,
                receipt_json
            FROM scientific_authority_receipts
        """
        parameters: tuple[str, ...] = ()

        if calculation_id is not None:
            query += " WHERE calculation_id = ?"
            parameters = (calculation_id,)

        query += " ORDER BY sequence_number ASC"

        with self._connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return tuple(
            AuthorityReceiptLedgerRecord(
                sequence_number=row["sequence_number"],
                receipt=self._deserialize_receipt(
                    row["receipt_json"]
                ),
            )
            for row in rows
        )

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS record_count
                FROM scientific_authority_receipts
                """
            ).fetchone()

        return int(row["record_count"])

    def verify_all(self) -> bool:
        verifier = ScientificAuthorityReceiptReplayVerifier()

        return all(
            verifier.verify(record.receipt).valid
            for record in self.list_records()
        )

    def append_many(
        self,
        receipts: Iterable[AuthorityDecisionReceipt],
    ) -> tuple[AuthorityReceiptLedgerRecord, ...]:
        return tuple(
            self.append(receipt)
            for receipt in receipts
        )

    def _deserialize_receipt(
        self,
        serialized_receipt: str,
    ) -> AuthorityDecisionReceipt:
        data = json.loads(serialized_receipt)

        return AuthorityDecisionReceipt(
            receipt_schema_version=data[
                "receipt_schema_version"
            ],
            policy_id=data["policy_id"],
            policy_version=data["policy_version"],
            calculation_id=data["calculation_id"],
            calculation_version=data["calculation_version"],
            current_authority=data["current_authority"],
            requested_authority=data["requested_authority"],
            evidence=dict(data["evidence"]),
            decision=dict(data["decision"]),
            receipt_hash=data["receipt_hash"],
        )
