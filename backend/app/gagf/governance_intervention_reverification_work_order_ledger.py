from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any

from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_ID = (
    "governance-intervention-reverification-work-order-ledger"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_SCHEMA_VERSION = (
    "1.0.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_GENESIS_HASH = (
    "0" * 64
)


class GovernanceInterventionReverificationWorkOrderLedgerError(
    RuntimeError
):
    """Base error for the governed reverification work-order ledger."""


class GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
    GovernanceInterventionReverificationWorkOrderLedgerError
):
    """Raised when persisted work-order integrity cannot be proven."""


class GovernanceInterventionReverificationWorkOrderLedgerTenantError(
    GovernanceInterventionReverificationWorkOrderLedgerError
):
    """Raised when tenant identity is missing or non-canonical."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationWorkOrderLedgerEntry:
    tenant_id: str
    sequence_number: int
    work_order_hash: str
    request_hash: str
    attempt_id: str
    previous_chain_hash: str
    chain_hash: str
    ledger_schema_version: str

    def chain_payload(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "sequence_number": self.sequence_number,
            "work_order_hash": self.work_order_hash,
            "request_hash": self.request_hash,
            "attempt_id": self.attempt_id,
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
class GovernanceInterventionReverificationWorkOrderLedgerVerification:
    tenant_id: str
    work_order_count: int
    valid: bool
    last_chain_hash: str


class GovernanceInterventionReverificationWorkOrderLedger:
    """
    Append-only tenant-scoped ledger of governed reverification work orders.

    This ledger preserves exact request-to-attempt commitments before future
    reverification execution or measurement occurs.

    It does not:
    - start or execute reverification;
    - collect observations;
    - perform measurement;
    - claim completion;
    - issue a new verification result;
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
        work_order: GovernanceInterventionReverificationWorkOrder,
    ) -> GovernanceInterventionReverificationWorkOrderLedgerEntry:
        self._validate_work_order(
            work_order
        )

        with self._connect() as connection:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            existing = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_work_orders
                WHERE tenant_id = ?
                  AND work_order_hash = ?
                """,
                (
                    work_order.tenant_id,
                    work_order.work_order_hash,
                ),
            ).fetchone()

            if existing is not None:
                persisted = self._work_order_from_row(
                    existing
                )

                if (
                    persisted != work_order
                    or not persisted.verify()
                ):
                    raise (
                        GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                            "persisted work order does not match replay"
                        )
                    )

                entry = self._entry_from_row(
                    existing
                )

                if not entry.verify_chain_hash():
                    raise (
                        GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                            "persisted work-order chain hash is invalid"
                        )
                    )

                return entry

            duplicate_attempt = connection.execute(
                """
                SELECT work_order_hash
                FROM governance_intervention_reverification_work_orders
                WHERE tenant_id = ?
                  AND request_hash = ?
                  AND attempt_id = ?
                """,
                (
                    work_order.tenant_id,
                    work_order.request_hash,
                    work_order.attempt_id,
                ),
            ).fetchone()

            if duplicate_attempt is not None:
                raise (
                    GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                        "request and attempt_id are already bound "
                        "to another work order"
                    )
                )

            tail = connection.execute(
                """
                SELECT
                    sequence_number,
                    chain_hash
                FROM governance_intervention_reverification_work_orders
                WHERE tenant_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (
                    work_order.tenant_id,
                ),
            ).fetchone()

            if tail is None:
                sequence_number = 1
                previous_chain_hash = (
                    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_GENESIS_HASH
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
                "tenant_id": work_order.tenant_id,
                "sequence_number": sequence_number,
                "work_order_hash": work_order.work_order_hash,
                "request_hash": work_order.request_hash,
                "attempt_id": work_order.attempt_id,
                "previous_chain_hash": (
                    previous_chain_hash
                ),
                "ledger_schema_version": (
                    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_SCHEMA_VERSION
                ),
            }

            chain_hash = sha256_hex(
                canonical_json(
                    chain_payload
                )
            )

            connection.execute(
                """
                INSERT INTO governance_intervention_reverification_work_orders (
                    tenant_id,
                    sequence_number,

                    work_order_id,
                    version,
                    schema_version,

                    intervention_id,
                    verification_record_hash,

                    request_hash,
                    request_ledger_chain_hash,

                    attempt_id,
                    reverification_scope,
                    trigger_codes_json,

                    work_order_hash,

                    previous_chain_hash,
                    chain_hash,
                    ledger_schema_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    work_order.tenant_id,
                    sequence_number,

                    work_order.work_order_id,
                    work_order.version,
                    work_order.schema_version,

                    work_order.intervention_id,
                    work_order.verification_record_hash,

                    work_order.request_hash,
                    work_order.request_ledger_chain_hash,

                    work_order.attempt_id,
                    work_order.reverification_scope,
                    canonical_json(
                        list(
                            work_order.trigger_codes
                        )
                    ),

                    work_order.work_order_hash,

                    previous_chain_hash,
                    chain_hash,
                    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_SCHEMA_VERSION,
                ),
            )

            return GovernanceInterventionReverificationWorkOrderLedgerEntry(
                tenant_id=work_order.tenant_id,
                sequence_number=sequence_number,
                work_order_hash=(
                    work_order.work_order_hash
                ),
                request_hash=work_order.request_hash,
                attempt_id=work_order.attempt_id,
                previous_chain_hash=(
                    previous_chain_hash
                ),
                chain_hash=chain_hash,
                ledger_schema_version=(
                    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_SCHEMA_VERSION
                ),
            )

    def get_by_work_order_hash(
        self,
        *,
        tenant_id: str,
        work_order_hash: str,
    ) -> GovernanceInterventionReverificationWorkOrder | None:
        normalized_tenant_id = self._validate_tenant(
            tenant_id
        )

        if not work_order_hash.strip():
            raise GovernanceInterventionReverificationWorkOrderLedgerError(
                "work_order_hash is required"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_work_orders
                WHERE tenant_id = ?
                  AND work_order_hash = ?
                """,
                (
                    normalized_tenant_id,
                    work_order_hash,
                ),
            ).fetchone()

        if row is None:
            return None

        work_order = self._work_order_from_row(
            row
        )

        if not work_order.verify():
            raise (
                GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                    "persisted work order failed deterministic verification"
                )
            )

        return work_order

    def list_for_request(
        self,
        *,
        tenant_id: str,
        request_hash: str,
    ) -> tuple[
        GovernanceInterventionReverificationWorkOrder,
        ...,
    ]:
        normalized_tenant_id = self._validate_tenant(
            tenant_id
        )

        if not request_hash.strip():
            raise GovernanceInterventionReverificationWorkOrderLedgerError(
                "request_hash is required"
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_work_orders
                WHERE tenant_id = ?
                  AND request_hash = ?
                ORDER BY sequence_number ASC
                """,
                (
                    normalized_tenant_id,
                    request_hash,
                ),
            ).fetchall()

        result: list[
            GovernanceInterventionReverificationWorkOrder
        ] = []

        for row in rows:
            work_order = self._work_order_from_row(
                row
            )

            if not work_order.verify():
                raise (
                    GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                        "persisted work order failed deterministic verification"
                    )
                )

            result.append(
                work_order
            )

        return tuple(
            result
        )

    def verify_tenant_chain(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionReverificationWorkOrderLedgerVerification:
        normalized_tenant_id = self._validate_tenant(
            tenant_id
        )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_reverification_work_orders
                WHERE tenant_id = ?
                ORDER BY sequence_number ASC
                """,
                (
                    normalized_tenant_id,
                ),
            ).fetchall()

        previous_chain_hash = (
            GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_GENESIS_HASH
        )

        expected_sequence = 1

        for row in rows:
            work_order = self._work_order_from_row(
                row
            )

            if not work_order.verify():
                return (
                    GovernanceInterventionReverificationWorkOrderLedgerVerification(
                        tenant_id=normalized_tenant_id,
                        work_order_count=len(rows),
                        valid=False,
                        last_chain_hash=previous_chain_hash,
                    )
                )

            entry = self._entry_from_row(
                row
            )

            if (
                entry.sequence_number
                != expected_sequence
            ):
                return (
                    GovernanceInterventionReverificationWorkOrderLedgerVerification(
                        tenant_id=normalized_tenant_id,
                        work_order_count=len(rows),
                        valid=False,
                        last_chain_hash=previous_chain_hash,
                    )
                )

            if (
                entry.previous_chain_hash
                != previous_chain_hash
            ):
                return (
                    GovernanceInterventionReverificationWorkOrderLedgerVerification(
                        tenant_id=normalized_tenant_id,
                        work_order_count=len(rows),
                        valid=False,
                        last_chain_hash=previous_chain_hash,
                    )
                )

            if not entry.verify_chain_hash():
                return (
                    GovernanceInterventionReverificationWorkOrderLedgerVerification(
                        tenant_id=normalized_tenant_id,
                        work_order_count=len(rows),
                        valid=False,
                        last_chain_hash=previous_chain_hash,
                    )
                )

            previous_chain_hash = (
                entry.chain_hash
            )

            expected_sequence += 1

        return (
            GovernanceInterventionReverificationWorkOrderLedgerVerification(
                tenant_id=normalized_tenant_id,
                work_order_count=len(rows),
                valid=True,
                last_chain_hash=previous_chain_hash,
            )
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                governance_intervention_reverification_work_orders (
                    tenant_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,

                    work_order_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,

                    intervention_id TEXT NOT NULL,
                    verification_record_hash TEXT NOT NULL,

                    request_hash TEXT NOT NULL,
                    request_ledger_chain_hash TEXT NOT NULL,

                    attempt_id TEXT NOT NULL,
                    reverification_scope TEXT NOT NULL,
                    trigger_codes_json TEXT NOT NULL,

                    work_order_hash TEXT NOT NULL,

                    previous_chain_hash TEXT NOT NULL,
                    chain_hash TEXT NOT NULL,
                    ledger_schema_version TEXT NOT NULL,

                    PRIMARY KEY (
                        tenant_id,
                        sequence_number
                    ),

                    UNIQUE (
                        tenant_id,
                        work_order_hash
                    ),

                    UNIQUE (
                        tenant_id,
                        chain_hash
                    ),

                    UNIQUE (
                        tenant_id,
                        request_hash,
                        attempt_id
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_reverification_work_orders_request
                ON governance_intervention_reverification_work_orders (
                    tenant_id,
                    request_hash
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
            raise GovernanceInterventionReverificationWorkOrderLedgerTenantError(
                "tenant_id is required"
            )

        if normalized != tenant_id:
            raise GovernanceInterventionReverificationWorkOrderLedgerTenantError(
                "tenant_id must already be canonical"
            )

        return normalized

    @classmethod
    def _validate_work_order(
        cls,
        work_order: GovernanceInterventionReverificationWorkOrder,
    ) -> None:
        cls._validate_tenant(
            work_order.tenant_id
        )

        if not work_order.verify():
            raise (
                GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                    "reverification work order failed deterministic verification"
                )
            )

        if not work_order.attempt_id.strip():
            raise (
                GovernanceInterventionReverificationWorkOrderLedgerIntegrityError(
                    "attempt_id is required"
                )
            )

    @staticmethod
    def _work_order_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionReverificationWorkOrder:
        import json

        return GovernanceInterventionReverificationWorkOrder(
            work_order_id=row["work_order_id"],
            version=row["version"],
            schema_version=row["schema_version"],
            tenant_id=row["tenant_id"],
            intervention_id=row["intervention_id"],
            verification_record_hash=row[
                "verification_record_hash"
            ],
            request_hash=row["request_hash"],
            request_ledger_chain_hash=row[
                "request_ledger_chain_hash"
            ],
            attempt_id=row["attempt_id"],
            reverification_scope=row[
                "reverification_scope"
            ],
            trigger_codes=tuple(
                json.loads(
                    row["trigger_codes_json"]
                )
            ),
            work_order_hash=row[
                "work_order_hash"
            ],
        )

    @staticmethod
    def _entry_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionReverificationWorkOrderLedgerEntry:
        return GovernanceInterventionReverificationWorkOrderLedgerEntry(
            tenant_id=row["tenant_id"],
            sequence_number=int(
                row["sequence_number"]
            ),
            work_order_hash=row[
                "work_order_hash"
            ],
            request_hash=row[
                "request_hash"
            ],
            attempt_id=row[
                "attempt_id"
            ],
            previous_chain_hash=row[
                "previous_chain_hash"
            ],
            chain_hash=row[
                "chain_hash"
            ],
            ledger_schema_version=row[
                "ledger_schema_version"
            ],
        )