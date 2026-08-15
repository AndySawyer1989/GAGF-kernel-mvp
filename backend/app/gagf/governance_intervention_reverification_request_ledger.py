from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any

from backend.app.gagf.governance_intervention_reverification_request import (
    GovernanceInterventionReverificationRequest,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_ID = (
    "governance-intervention-reverification-request-ledger"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_SCHEMA_VERSION = (
    "1.0.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_GENESIS_HASH = (
    "0" * 64
)


class GovernanceInterventionReverificationRequestLedgerError(
    RuntimeError
):
    """Base error for the governed reverification-request ledger."""


class GovernanceInterventionReverificationRequestLedgerIntegrityError(
    GovernanceInterventionReverificationRequestLedgerError
):
    """Raised when persisted request-ledger integrity cannot be proven."""


class GovernanceInterventionReverificationRequestLedgerTenantError(
    GovernanceInterventionReverificationRequestLedgerError
):
    """Raised when tenant identity is missing or non-canonical."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationRequestLedgerEntry:
    tenant_id: str
    sequence_number: int
    request_hash: str
    verification_record_hash: str
    previous_chain_hash: str
    chain_hash: str
    ledger_schema_version: str

    def chain_payload(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "sequence_number": self.sequence_number,
            "request_hash": self.request_hash,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "previous_chain_hash": (
                self.previous_chain_hash
            ),
            "ledger_schema_version": (
                self.ledger_schema_version
            ),
        }

    def verify_chain_hash(self) -> bool:
        return (
            self.chain_hash
            == sha256_hex(
                canonical_json(
                    self.chain_payload()
                )
            )
        )


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationRequestLedgerVerification:
    tenant_id: str
    request_count: int
    valid: bool
    last_chain_hash: str


class GovernanceInterventionReverificationRequestLedger:
    """
    Append-only tenant-scoped ledger of governed reverification requests.

    Guarantees:
    - only deterministically valid request artifacts may be appended;
    - each tenant has an independent hash chain;
    - replay of the same request is idempotent;
    - persisted request payloads are immutable;
    - historical requests are never rewritten.

    This ledger does not:
    - execute reverification;
    - determine completion;
    - alter lifecycle state;
    - mutate verification records;
    - authorize intervention activity;
    - infer causation.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._database_path = Path(
            database_path
        )

        self._database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def append(
        self,
        *,
        request: GovernanceInterventionReverificationRequest,
    ) -> GovernanceInterventionReverificationRequestLedgerEntry:
        self._validate_request(
            request
        )

        with self._connect() as connection:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            existing = connection.execute(
                """
                SELECT
                    tenant_id,
                    sequence_number,
                    request_hash,
                    verification_record_hash,
                    previous_chain_hash,
                    chain_hash,
                    ledger_schema_version
                FROM governance_intervention_reverification_requests
                WHERE tenant_id = ?
                  AND request_hash = ?
                """,
                (
                    request.tenant_id,
                    request.request_hash,
                ),
            ).fetchone()

            if existing is not None:
                entry = self._entry_from_row(
                    existing
                )

                self._verify_persisted_request(
                    connection=connection,
                    request=request,
                )

                if not entry.verify_chain_hash():
                    raise (
                        GovernanceInterventionReverificationRequestLedgerIntegrityError(
                            "persisted reverification request "
                            "chain hash is invalid"
                        )
                    )

                return entry

            tail = connection.execute(
                """
                SELECT
                    sequence_number,
                    chain_hash
                FROM governance_intervention_reverification_requests
                WHERE tenant_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (
                    request.tenant_id,
                ),
            ).fetchone()

            if tail is None:
                sequence_number = 1
                previous_chain_hash = (
                    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_GENESIS_HASH
                )
            else:
                sequence_number = (
                    int(tail["sequence_number"])
                    + 1
                )
                previous_chain_hash = tail[
                    "chain_hash"
                ]

            chain_payload = {
                "tenant_id": request.tenant_id,
                "sequence_number": sequence_number,
                "request_hash": request.request_hash,
                "verification_record_hash": (
                    request.verification_record_hash
                ),
                "previous_chain_hash": (
                    previous_chain_hash
                ),
                "ledger_schema_version": (
                    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_SCHEMA_VERSION
                ),
            }

            chain_hash = sha256_hex(
                canonical_json(
                    chain_payload
                )
            )

            connection.execute(
                """
                INSERT INTO governance_intervention_reverification_requests (
                    tenant_id,
                    sequence_number,
                    request_id,
                    version,
                    schema_version,
                    intervention_id,
                    verification_record_hash,
                    lifecycle_event_hash,
                    freshness_evaluation_hash,
                    reverification_scope,
                    trigger_codes_json,
                    request_hash,
                    previous_chain_hash,
                    chain_hash,
                    ledger_schema_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.tenant_id,
                    sequence_number,
                    request.request_id,
                    request.version,
                    request.schema_version,
                    request.intervention_id,
                    request.verification_record_hash,
                    request.lifecycle_event_hash,
                    request.freshness_evaluation_hash,
                    request.reverification_scope,
                    canonical_json(
                        list(
                            request.trigger_codes
                        )
                    ),
                    request.request_hash,
                    previous_chain_hash,
                    chain_hash,
                    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_SCHEMA_VERSION,
                ),
            )

            return GovernanceInterventionReverificationRequestLedgerEntry(
                tenant_id=request.tenant_id,
                sequence_number=sequence_number,
                request_hash=request.request_hash,
                verification_record_hash=(
                    request.verification_record_hash
                ),
                previous_chain_hash=(
                    previous_chain_hash
                ),
                chain_hash=chain_hash,
                ledger_schema_version=(
                    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_SCHEMA_VERSION
                ),
            )

    def get_by_request_hash(
        self,
        *,
        tenant_id: str,
        request_hash: str,
    ) -> GovernanceInterventionReverificationRequest | None:
        normalized_tenant_id = self._validate_tenant(
            tenant_id
        )

        if not request_hash.strip():
            raise GovernanceInterventionReverificationRequestLedgerError(
                "request_hash is required"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_requests
                WHERE tenant_id = ?
                  AND request_hash = ?
                """,
                (
                    normalized_tenant_id,
                    request_hash,
                ),
            ).fetchone()

        if row is None:
            return None

        request = self._request_from_row(
            row
        )

        if not request.verify():
            raise (
                GovernanceInterventionReverificationRequestLedgerIntegrityError(
                    "persisted reverification request failed "
                    "deterministic verification"
                )
            )

        return request

    def list_for_verification_record(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> tuple[
        GovernanceInterventionReverificationRequest,
        ...,
    ]:
        normalized_tenant_id = self._validate_tenant(
            tenant_id
        )

        if not verification_record_hash.strip():
            raise GovernanceInterventionReverificationRequestLedgerError(
                "verification_record_hash is required"
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_requests
                WHERE tenant_id = ?
                  AND verification_record_hash = ?
                ORDER BY sequence_number ASC
                """,
                (
                    normalized_tenant_id,
                    verification_record_hash,
                ),
            ).fetchall()

        requests: list[
            GovernanceInterventionReverificationRequest
        ] = []

        for row in rows:
            request = self._request_from_row(
                row
            )

            if not request.verify():
                raise (
                    GovernanceInterventionReverificationRequestLedgerIntegrityError(
                        "persisted reverification request failed "
                        "deterministic verification"
                    )
                )

            requests.append(
                request
            )

        return tuple(
            requests
        )

    def verify_tenant_chain(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionReverificationRequestLedgerVerification:
        normalized_tenant_id = self._validate_tenant(
            tenant_id
        )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_requests
                WHERE tenant_id = ?
                ORDER BY sequence_number ASC
                """,
                (
                    normalized_tenant_id,
                ),
            ).fetchall()

        previous_chain_hash = (
            GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_GENESIS_HASH
        )

        expected_sequence = 1

        for row in rows:
            request = self._request_from_row(
                row
            )

            if not request.verify():
                return GovernanceInterventionReverificationRequestLedgerVerification(
                    tenant_id=normalized_tenant_id,
                    request_count=len(rows),
                    valid=False,
                    last_chain_hash=previous_chain_hash,
                )

            entry = self._entry_from_row(
                row
            )

            if (
                entry.sequence_number
                != expected_sequence
            ):
                return GovernanceInterventionReverificationRequestLedgerVerification(
                    tenant_id=normalized_tenant_id,
                    request_count=len(rows),
                    valid=False,
                    last_chain_hash=previous_chain_hash,
                )

            if (
                entry.previous_chain_hash
                != previous_chain_hash
            ):
                return GovernanceInterventionReverificationRequestLedgerVerification(
                    tenant_id=normalized_tenant_id,
                    request_count=len(rows),
                    valid=False,
                    last_chain_hash=previous_chain_hash,
                )

            if not entry.verify_chain_hash():
                return GovernanceInterventionReverificationRequestLedgerVerification(
                    tenant_id=normalized_tenant_id,
                    request_count=len(rows),
                    valid=False,
                    last_chain_hash=previous_chain_hash,
                )

            previous_chain_hash = (
                entry.chain_hash
            )

            expected_sequence += 1

        return GovernanceInterventionReverificationRequestLedgerVerification(
            tenant_id=normalized_tenant_id,
            request_count=len(rows),
            valid=True,
            last_chain_hash=previous_chain_hash,
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                governance_intervention_reverification_requests (
                    tenant_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,

                    request_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,

                    intervention_id TEXT NOT NULL,
                    verification_record_hash TEXT NOT NULL,

                    lifecycle_event_hash TEXT NOT NULL,
                    freshness_evaluation_hash TEXT NOT NULL,

                    reverification_scope TEXT NOT NULL,
                    trigger_codes_json TEXT NOT NULL,

                    request_hash TEXT NOT NULL,

                    previous_chain_hash TEXT NOT NULL,
                    chain_hash TEXT NOT NULL,
                    ledger_schema_version TEXT NOT NULL,

                    PRIMARY KEY (
                        tenant_id,
                        sequence_number
                    ),

                    UNIQUE (
                        tenant_id,
                        request_hash
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
                idx_reverification_requests_record
                ON governance_intervention_reverification_requests (
                    tenant_id,
                    verification_record_hash
                )
                """
            )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    @staticmethod
    def _validate_tenant(
        tenant_id: str,
    ) -> str:
        normalized = tenant_id.strip()

        if not normalized:
            raise GovernanceInterventionReverificationRequestLedgerTenantError(
                "tenant_id is required"
            )

        if normalized != tenant_id:
            raise GovernanceInterventionReverificationRequestLedgerTenantError(
                "tenant_id must already be canonical"
            )

        return normalized

    @classmethod
    def _validate_request(
        cls,
        request: GovernanceInterventionReverificationRequest,
    ) -> None:
        cls._validate_tenant(
            request.tenant_id
        )

        if not request.verify():
            raise (
                GovernanceInterventionReverificationRequestLedgerIntegrityError(
                    "reverification request failed deterministic verification"
                )
            )

    @classmethod
    def _verify_persisted_request(
        cls,
        *,
        connection: sqlite3.Connection,
        request: GovernanceInterventionReverificationRequest,
    ) -> None:
        row = connection.execute(
            """
            SELECT *
            FROM governance_intervention_reverification_requests
            WHERE tenant_id = ?
              AND request_hash = ?
            """,
            (
                request.tenant_id,
                request.request_hash,
            ),
        ).fetchone()

        if row is None:
            raise (
                GovernanceInterventionReverificationRequestLedgerIntegrityError(
                    "persisted request disappeared during idempotent replay"
                )
            )

        persisted = cls._request_from_row(
            row
        )

        if (
            persisted != request
            or not persisted.verify()
        ):
            raise (
                GovernanceInterventionReverificationRequestLedgerIntegrityError(
                    "persisted reverification request does not match replay"
                )
            )

    @staticmethod
    def _request_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionReverificationRequest:
        import json

        trigger_codes = tuple(
            json.loads(
                row["trigger_codes_json"]
            )
        )

        return GovernanceInterventionReverificationRequest(
            request_id=row["request_id"],
            version=row["version"],
            schema_version=row["schema_version"],
            tenant_id=row["tenant_id"],
            intervention_id=row[
                "intervention_id"
            ],
            verification_record_hash=row[
                "verification_record_hash"
            ],
            lifecycle_event_hash=row[
                "lifecycle_event_hash"
            ],
            freshness_evaluation_hash=row[
                "freshness_evaluation_hash"
            ],
            reverification_scope=row[
                "reverification_scope"
            ],
            trigger_codes=trigger_codes,
            request_hash=row["request_hash"],
        )

    @staticmethod
    def _entry_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionReverificationRequestLedgerEntry:
        return GovernanceInterventionReverificationRequestLedgerEntry(
            tenant_id=row["tenant_id"],
            sequence_number=int(
                row["sequence_number"]
            ),
            request_hash=row["request_hash"],
            verification_record_hash=row[
                "verification_record_hash"
            ],
            previous_chain_hash=row[
                "previous_chain_hash"
            ],
            chain_hash=row["chain_hash"],
            ledger_schema_version=row[
                "ledger_schema_version"
            ],
        )