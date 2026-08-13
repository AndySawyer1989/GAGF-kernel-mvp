from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any

from backend.app.gagf.governance_intervention_verification_summary import (
    GovernanceInterventionVerificationSummary,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_ID = (
    "governance-intervention-verification-record"
)
GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_SCHEMA_VERSION = "1.0.0"

GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_SCHEMA_VERSION = "1.0.0"

GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH = "0" * 64


class GovernanceInterventionVerificationLedgerError(RuntimeError):
    """Base error for governed verification persistence."""


class GovernanceInterventionVerificationLedgerIntegrityError(
    GovernanceInterventionVerificationLedgerError
):
    """Raised when governed verification integrity cannot be established."""


class GovernanceInterventionVerificationLedgerTenantError(
    GovernanceInterventionVerificationLedgerError
):
    """Raised when tenant-scoped access is invalid."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationRecord:
    """
    Immutable canonical operational verification record.

    The record identity is derived only from the governed I-F summary.
    Ledger location and chain position are deliberately excluded from the
    record hash so the same governed summary always yields the same record.
    """

    record_id: str
    version: str
    schema_version: str

    tenant_id: str
    contract_hash: str
    intervention_id: str
    intervention_type: str

    verification_set_hash: str
    verification_summary_hash: str

    required_count: int
    verified_count: int
    not_verified_count: int
    inconclusive_count: int

    verification_disposition: str

    record_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "verification_set_hash": self.verification_set_hash,
            "verification_summary_hash": self.verification_summary_hash,
            "required_count": self.required_count,
            "verified_count": self.verified_count,
            "not_verified_count": self.not_verified_count,
            "inconclusive_count": self.inconclusive_count,
            "verification_disposition": self.verification_disposition,
        }

    def verify(self) -> bool:
        return self.record_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "record_hash": self.record_hash,
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationLedgerEntry:
    """
    Append-only ledger envelope for one canonical verification record.

    record_hash identifies the governed operational result.
    chain_hash identifies this record's immutable position in tenant history.
    """

    tenant_id: str
    sequence_number: int

    record_hash: str
    verification_summary_hash: str

    previous_chain_hash: str
    chain_hash: str

    ledger_schema_version: str

    def chain_payload(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "sequence_number": self.sequence_number,
            "record_hash": self.record_hash,
            "verification_summary_hash": self.verification_summary_hash,
            "previous_chain_hash": self.previous_chain_hash,
            "ledger_schema_version": self.ledger_schema_version,
        }

    def verify_chain_hash(self) -> bool:
        return self.chain_hash == sha256_hex(
            canonical_json(self.chain_payload())
        )


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationLedgerVerification:
    tenant_id: str
    record_count: int
    valid: bool
    last_chain_hash: str


class GovernanceInterventionVerificationRecordBuilder:
    """
    Builds one deterministic operational record from a verified I-F summary.

    This builder performs no persistence, causal inference, authorization,
    rollback, continuation, or future-action selection.
    """

    @classmethod
    def build(
        cls,
        *,
        summary: GovernanceInterventionVerificationSummary,
    ) -> GovernanceInterventionVerificationRecord:
        if not summary.verify():
            raise GovernanceInterventionVerificationLedgerIntegrityError(
                "verification summary failed deterministic verification"
            )

        payload: dict[str, Any] = {
            "record_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_SCHEMA_VERSION
            ),
            "tenant_id": summary.tenant_id,
            "contract_hash": summary.contract_hash,
            "intervention_id": summary.intervention_id,
            "intervention_type": summary.intervention_type,
            "verification_set_hash": summary.verification_set_hash,
            "verification_summary_hash": (
                summary.verification_summary_hash
            ),
            "required_count": summary.required_count,
            "verified_count": summary.verified_count,
            "not_verified_count": summary.not_verified_count,
            "inconclusive_count": summary.inconclusive_count,
            "verification_disposition": (
                summary.verification_disposition.value
            ),
        }

        return GovernanceInterventionVerificationRecord(
            **payload,
            record_hash=sha256_hex(
                canonical_json(payload)
            ),
        )


class GovernanceInterventionVerificationLedger:
    """
    SQLite-backed append-only operational verification ledger.

    Ledger invariants:
    - records are immutable after insertion;
    - one tenant + verification_summary_hash maps to one canonical record;
    - replay of the same canonical record is idempotent;
    - records for different tenants occupy independent hash chains;
    - retrieval requires an explicit tenant boundary;
    - chain integrity can be independently verified.

    This ledger does not implement supersession or reverification semantics.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                governance_intervention_verification_records (
                    tenant_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,

                    record_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,

                    contract_hash TEXT NOT NULL,
                    intervention_id TEXT NOT NULL,
                    intervention_type TEXT NOT NULL,

                    verification_set_hash TEXT NOT NULL,
                    verification_summary_hash TEXT NOT NULL,

                    required_count INTEGER NOT NULL,
                    verified_count INTEGER NOT NULL,
                    not_verified_count INTEGER NOT NULL,
                    inconclusive_count INTEGER NOT NULL,

                    verification_disposition TEXT NOT NULL,

                    record_hash TEXT NOT NULL,

                    previous_chain_hash TEXT NOT NULL,
                    chain_hash TEXT NOT NULL,
                    ledger_schema_version TEXT NOT NULL,

                    PRIMARY KEY (
                        tenant_id,
                        sequence_number
                    ),

                    UNIQUE (
                        tenant_id,
                        verification_summary_hash
                    ),

                    UNIQUE (
                        tenant_id,
                        record_hash
                    ),

                    UNIQUE (
                        tenant_id,
                        chain_hash
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_governance_intervention_verification_intervention
                ON governance_intervention_verification_records (
                    tenant_id,
                    intervention_id,
                    sequence_number
                )
                """
            )

    def append(
        self,
        *,
        record: GovernanceInterventionVerificationRecord,
    ) -> GovernanceInterventionVerificationLedgerEntry:
        if not record.verify():
            raise GovernanceInterventionVerificationLedgerIntegrityError(
                "verification record failed deterministic verification"
            )

        tenant_id = record.tenant_id.strip()

        if not tenant_id:
            raise GovernanceInterventionVerificationLedgerTenantError(
                "tenant_id is required"
            )

        if tenant_id != record.tenant_id:
            raise GovernanceInterventionVerificationLedgerTenantError(
                "record tenant_id must already be canonical"
            )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_records
                WHERE tenant_id = ?
                  AND verification_summary_hash = ?
                """,
                (
                    tenant_id,
                    record.verification_summary_hash,
                ),
            ).fetchone()

            if existing is not None:
                stored_record = self._record_from_row(existing)

                if stored_record != record:
                    raise GovernanceInterventionVerificationLedgerIntegrityError(
                        "verification summary hash is already bound to a "
                        "different canonical verification record"
                    )

                return self._entry_from_row(existing)

            latest = connection.execute(
                """
                SELECT sequence_number, chain_hash
                FROM governance_intervention_verification_records
                WHERE tenant_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (tenant_id,),
            ).fetchone()

            if latest is None:
                sequence_number = 1
                previous_chain_hash = (
                    GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
                )
            else:
                sequence_number = int(
                    latest["sequence_number"]
                ) + 1

                previous_chain_hash = str(
                    latest["chain_hash"]
                )

            entry_payload: dict[str, Any] = {
                "tenant_id": tenant_id,
                "sequence_number": sequence_number,
                "record_hash": record.record_hash,
                "verification_summary_hash": (
                    record.verification_summary_hash
                ),
                "previous_chain_hash": previous_chain_hash,
                "ledger_schema_version": (
                    GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_SCHEMA_VERSION
                ),
            }

            chain_hash = sha256_hex(
                canonical_json(entry_payload)
            )

            try:
                connection.execute(
                    """
                    INSERT INTO governance_intervention_verification_records (
                        tenant_id,
                        sequence_number,
                        record_id,
                        version,
                        schema_version,
                        contract_hash,
                        intervention_id,
                        intervention_type,
                        verification_set_hash,
                        verification_summary_hash,
                        required_count,
                        verified_count,
                        not_verified_count,
                        inconclusive_count,
                        verification_disposition,
                        record_hash,
                        previous_chain_hash,
                        chain_hash,
                        ledger_schema_version
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        tenant_id,
                        sequence_number,
                        record.record_id,
                        record.version,
                        record.schema_version,
                        record.contract_hash,
                        record.intervention_id,
                        record.intervention_type,
                        record.verification_set_hash,
                        record.verification_summary_hash,
                        record.required_count,
                        record.verified_count,
                        record.not_verified_count,
                        record.inconclusive_count,
                        record.verification_disposition,
                        record.record_hash,
                        previous_chain_hash,
                        chain_hash,
                        (
                            GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_SCHEMA_VERSION
                        ),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise GovernanceInterventionVerificationLedgerIntegrityError(
                    "append-only verification ledger rejected conflicting "
                    "record insertion"
                ) from exc

            return GovernanceInterventionVerificationLedgerEntry(
                tenant_id=tenant_id,
                sequence_number=sequence_number,
                record_hash=record.record_hash,
                verification_summary_hash=(
                    record.verification_summary_hash
                ),
                previous_chain_hash=previous_chain_hash,
                chain_hash=chain_hash,
                ledger_schema_version=(
                    GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_SCHEMA_VERSION
                ),
            )

    def get_by_summary_hash(
        self,
        *,
        tenant_id: str,
        verification_summary_hash: str,
    ) -> GovernanceInterventionVerificationRecord | None:
        normalized_tenant = tenant_id.strip()
        normalized_hash = verification_summary_hash.strip()

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLedgerTenantError(
                "tenant_id is required"
            )

        if not normalized_hash:
            raise GovernanceInterventionVerificationLedgerError(
                "verification_summary_hash is required"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_records
                WHERE tenant_id = ?
                  AND verification_summary_hash = ?
                """,
                (
                    normalized_tenant,
                    normalized_hash,
                ),
            ).fetchone()

        if row is None:
            return None

        record = self._record_from_row(row)

        if not record.verify():
            raise GovernanceInterventionVerificationLedgerIntegrityError(
                "stored verification record failed deterministic verification"
            )

        return record

    def list_for_intervention(
        self,
        *,
        tenant_id: str,
        intervention_id: str,
    ) -> tuple[GovernanceInterventionVerificationRecord, ...]:
        normalized_tenant = tenant_id.strip()
        normalized_intervention = intervention_id.strip()

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLedgerTenantError(
                "tenant_id is required"
            )

        if not normalized_intervention:
            raise GovernanceInterventionVerificationLedgerError(
                "intervention_id is required"
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_records
                WHERE tenant_id = ?
                  AND intervention_id = ?
                ORDER BY sequence_number ASC
                """,
                (
                    normalized_tenant,
                    normalized_intervention,
                ),
            ).fetchall()

        records = tuple(
            self._record_from_row(row)
            for row in rows
        )

        for record in records:
            if not record.verify():
                raise GovernanceInterventionVerificationLedgerIntegrityError(
                    "stored verification record failed deterministic "
                    "verification"
                )

        return records

    def verify_tenant_chain(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionVerificationLedgerVerification:
        normalized_tenant = tenant_id.strip()

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLedgerTenantError(
                "tenant_id is required"
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_records
                WHERE tenant_id = ?
                ORDER BY sequence_number ASC
                """,
                (normalized_tenant,),
            ).fetchall()

        expected_previous_hash = (
            GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
        )

        expected_sequence = 1

        for row in rows:
            entry = self._entry_from_row(row)
            record = self._record_from_row(row)

            if entry.sequence_number != expected_sequence:
                return GovernanceInterventionVerificationLedgerVerification(
                    tenant_id=normalized_tenant,
                    record_count=len(rows),
                    valid=False,
                    last_chain_hash=expected_previous_hash,
                )

            if (
                entry.previous_chain_hash
                != expected_previous_hash
            ):
                return GovernanceInterventionVerificationLedgerVerification(
                    tenant_id=normalized_tenant,
                    record_count=len(rows),
                    valid=False,
                    last_chain_hash=expected_previous_hash,
                )

            if not record.verify():
                return GovernanceInterventionVerificationLedgerVerification(
                    tenant_id=normalized_tenant,
                    record_count=len(rows),
                    valid=False,
                    last_chain_hash=expected_previous_hash,
                )

            if not entry.verify_chain_hash():
                return GovernanceInterventionVerificationLedgerVerification(
                    tenant_id=normalized_tenant,
                    record_count=len(rows),
                    valid=False,
                    last_chain_hash=expected_previous_hash,
                )

            expected_previous_hash = entry.chain_hash
            expected_sequence += 1

        return GovernanceInterventionVerificationLedgerVerification(
            tenant_id=normalized_tenant,
            record_count=len(rows),
            valid=True,
            last_chain_hash=expected_previous_hash,
        )

    @staticmethod
    def _record_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionVerificationRecord:
        return GovernanceInterventionVerificationRecord(
            record_id=str(row["record_id"]),
            version=str(row["version"]),
            schema_version=str(row["schema_version"]),
            tenant_id=str(row["tenant_id"]),
            contract_hash=str(row["contract_hash"]),
            intervention_id=str(row["intervention_id"]),
            intervention_type=str(row["intervention_type"]),
            verification_set_hash=str(
                row["verification_set_hash"]
            ),
            verification_summary_hash=str(
                row["verification_summary_hash"]
            ),
            required_count=int(row["required_count"]),
            verified_count=int(row["verified_count"]),
            not_verified_count=int(
                row["not_verified_count"]
            ),
            inconclusive_count=int(
                row["inconclusive_count"]
            ),
            verification_disposition=str(
                row["verification_disposition"]
            ),
            record_hash=str(row["record_hash"]),
        )

    @staticmethod
    def _entry_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionVerificationLedgerEntry:
        return GovernanceInterventionVerificationLedgerEntry(
            tenant_id=str(row["tenant_id"]),
            sequence_number=int(row["sequence_number"]),
            record_hash=str(row["record_hash"]),
            verification_summary_hash=str(
                row["verification_summary_hash"]
            ),
            previous_chain_hash=str(
                row["previous_chain_hash"]
            ),
            chain_hash=str(row["chain_hash"]),
            ledger_schema_version=str(
                row["ledger_schema_version"]
            ),
        )