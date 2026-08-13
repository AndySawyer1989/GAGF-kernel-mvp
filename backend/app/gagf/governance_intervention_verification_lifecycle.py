from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sqlite3
from typing import Any

from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationLedger,
    GovernanceInterventionVerificationRecord,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_ID = (
    "governance-intervention-verification-lifecycle"
)

GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_SCHEMA_VERSION = (
    "1.0.0"
)

GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_LEDGER_SCHEMA_VERSION = (
    "1.0.0"
)

GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH = (
    "0" * 64
)


class GovernanceInterventionVerificationLifecycleError(
    RuntimeError
):
    """Base error for governed verification lifecycle state."""


class GovernanceInterventionVerificationLifecycleIntegrityError(
    GovernanceInterventionVerificationLifecycleError
):
    """Raised when lifecycle integrity cannot be established."""


class GovernanceInterventionVerificationLifecycleTransitionError(
    GovernanceInterventionVerificationLifecycleError
):
    """Raised when a requested lifecycle transition is invalid."""


class GovernanceInterventionVerificationLifecycleTenantError(
    GovernanceInterventionVerificationLifecycleError
):
    """Raised when a lifecycle operation violates tenant scope."""


class GovernanceInterventionVerificationLifecycleStatus(
    str,
    Enum,
):
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    REVERIFICATION_REQUIRED = "REVERIFICATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"


_ALLOWED_TRANSITIONS: dict[
    GovernanceInterventionVerificationLifecycleStatus | None,
    frozenset[
        GovernanceInterventionVerificationLifecycleStatus
    ],
] = {
    None: frozenset(
        {
            GovernanceInterventionVerificationLifecycleStatus.ACTIVE,
        }
    ),
    GovernanceInterventionVerificationLifecycleStatus.ACTIVE: (
        frozenset(
            {
                GovernanceInterventionVerificationLifecycleStatus.STALE,
                GovernanceInterventionVerificationLifecycleStatus.REVERIFICATION_REQUIRED,
                GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED,
            }
        )
    ),
    GovernanceInterventionVerificationLifecycleStatus.STALE: (
        frozenset(
            {
                GovernanceInterventionVerificationLifecycleStatus.REVERIFICATION_REQUIRED,
                GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED,
            }
        )
    ),
    GovernanceInterventionVerificationLifecycleStatus.REVERIFICATION_REQUIRED: (
        frozenset(
            {
                GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED,
            }
        )
    ),
    GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED: (
        frozenset()
    ),
}


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationLifecycleEvent:
    """
    Immutable lifecycle interpretation of one persisted I-G record.

    This event never changes the underlying verification record or its
    governed verification disposition.
    """

    lifecycle_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    previous_status: str | None
    lifecycle_status: str

    superseded_by_record_hash: str | None

    lifecycle_event_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "lifecycle_id": self.lifecycle_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "previous_status": self.previous_status,
            "lifecycle_status": self.lifecycle_status,
            "superseded_by_record_hash": (
                self.superseded_by_record_hash
            ),
        }

    def verify(self) -> bool:
        return (
            self.lifecycle_event_hash
            == sha256_hex(
                canonical_json(self.payload())
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "lifecycle_event_hash": (
                self.lifecycle_event_hash
            ),
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationLifecycleEntry:
    tenant_id: str
    sequence_number: int

    lifecycle_event_hash: str
    verification_record_hash: str

    previous_chain_hash: str
    chain_hash: str

    ledger_schema_version: str

    def chain_payload(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "sequence_number": self.sequence_number,
            "lifecycle_event_hash": (
                self.lifecycle_event_hash
            ),
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
                canonical_json(self.chain_payload())
            )
        )


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationLifecycleState:
    tenant_id: str
    intervention_id: str
    verification_record_hash: str
    lifecycle_status: str
    superseded_by_record_hash: str | None
    lifecycle_event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "lifecycle_status": self.lifecycle_status,
            "superseded_by_record_hash": (
                self.superseded_by_record_hash
            ),
            "lifecycle_event_hash": (
                self.lifecycle_event_hash
            ),
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationLifecycleVerification:
    tenant_id: str
    event_count: int
    valid: bool
    last_chain_hash: str


class GovernanceInterventionVerificationLifecycleLedger:
    """
    Append-only lifecycle overlay for immutable I-G verification records.

    Invariants:
    - I-G records are never modified;
    - lifecycle history is append-only;
    - the first lifecycle state must be ACTIVE;
    - SUPERSEDED is terminal;
    - supersession requires another persisted record for the same tenant
      and intervention;
    - lifecycle state does not alter verification disposition;
    - lifecycle state does not authorize execution, rollback,
      continuation, or other future action.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self.database_path = str(database_path)

        self._verification_ledger = (
            GovernanceInterventionVerificationLedger(
                database_path
            )
        )

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                governance_intervention_verification_lifecycle_events (
                    tenant_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,

                    lifecycle_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,

                    intervention_id TEXT NOT NULL,
                    verification_record_hash TEXT NOT NULL,

                    previous_status TEXT,
                    lifecycle_status TEXT NOT NULL,

                    superseded_by_record_hash TEXT,

                    lifecycle_event_hash TEXT NOT NULL,

                    previous_chain_hash TEXT NOT NULL,
                    chain_hash TEXT NOT NULL,
                    ledger_schema_version TEXT NOT NULL,

                    PRIMARY KEY (
                        tenant_id,
                        sequence_number
                    ),

                    UNIQUE (
                        tenant_id,
                        lifecycle_event_hash
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
                idx_governance_intervention_verification_lifecycle_record
                ON governance_intervention_verification_lifecycle_events (
                    tenant_id,
                    verification_record_hash,
                    sequence_number
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_governance_intervention_verification_lifecycle_intervention
                ON governance_intervention_verification_lifecycle_events (
                    tenant_id,
                    intervention_id,
                    sequence_number
                )
                """
            )

    def activate(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        record = self._require_persisted_record(
            tenant_id=tenant_id,
            verification_record_hash=(
                verification_record_hash
            ),
        )

        return self._append_transition(
            record=record,
            lifecycle_status=(
                GovernanceInterventionVerificationLifecycleStatus.ACTIVE
            ),
            superseded_by_record_hash=None,
        )

    def mark_stale(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        record = self._require_persisted_record(
            tenant_id=tenant_id,
            verification_record_hash=(
                verification_record_hash
            ),
        )

        return self._append_transition(
            record=record,
            lifecycle_status=(
                GovernanceInterventionVerificationLifecycleStatus.STALE
            ),
            superseded_by_record_hash=None,
        )

    def require_reverification(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        record = self._require_persisted_record(
            tenant_id=tenant_id,
            verification_record_hash=(
                verification_record_hash
            ),
        )

        return self._append_transition(
            record=record,
            lifecycle_status=(
                GovernanceInterventionVerificationLifecycleStatus.REVERIFICATION_REQUIRED
            ),
            superseded_by_record_hash=None,
        )

    def supersede(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
        superseded_by_record_hash: str,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        record = self._require_persisted_record(
            tenant_id=tenant_id,
            verification_record_hash=(
                verification_record_hash
            ),
        )

        replacement = self._require_persisted_record(
            tenant_id=tenant_id,
            verification_record_hash=(
                superseded_by_record_hash
            ),
        )

        if record.record_hash == replacement.record_hash:
            raise GovernanceInterventionVerificationLifecycleTransitionError(
                "verification record cannot supersede itself"
            )

        if (
            record.intervention_id
            != replacement.intervention_id
        ):
            raise GovernanceInterventionVerificationLifecycleTransitionError(
                "superseding verification record must belong to "
                "the same intervention"
            )

        return self._append_transition(
            record=record,
            lifecycle_status=(
                GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED
            ),
            superseded_by_record_hash=(
                replacement.record_hash
            ),
        )

    def get_current_state(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> (
        GovernanceInterventionVerificationLifecycleState
        | None
    ):
        normalized_tenant = tenant_id.strip()
        normalized_record_hash = (
            verification_record_hash.strip()
        )

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLifecycleTenantError(
                "tenant_id is required"
            )

        if not normalized_record_hash:
            raise GovernanceInterventionVerificationLifecycleError(
                "verification_record_hash is required"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_lifecycle_events
                WHERE tenant_id = ?
                  AND verification_record_hash = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (
                    normalized_tenant,
                    normalized_record_hash,
                ),
            ).fetchone()

        if row is None:
            return None

        event = self._event_from_row(row)

        if not event.verify():
            raise GovernanceInterventionVerificationLifecycleIntegrityError(
                "stored lifecycle event failed deterministic "
                "verification"
            )

        return GovernanceInterventionVerificationLifecycleState(
            tenant_id=event.tenant_id,
            intervention_id=event.intervention_id,
            verification_record_hash=(
                event.verification_record_hash
            ),
            lifecycle_status=event.lifecycle_status,
            superseded_by_record_hash=(
                event.superseded_by_record_hash
            ),
            lifecycle_event_hash=(
                event.lifecycle_event_hash
            ),
        )

    def list_history(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> tuple[
        GovernanceInterventionVerificationLifecycleEvent,
        ...,
    ]:
        normalized_tenant = tenant_id.strip()
        normalized_record_hash = (
            verification_record_hash.strip()
        )

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLifecycleTenantError(
                "tenant_id is required"
            )

        if not normalized_record_hash:
            raise GovernanceInterventionVerificationLifecycleError(
                "verification_record_hash is required"
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_lifecycle_events
                WHERE tenant_id = ?
                  AND verification_record_hash = ?
                ORDER BY sequence_number ASC
                """,
                (
                    normalized_tenant,
                    normalized_record_hash,
                ),
            ).fetchall()

        events = tuple(
            self._event_from_row(row)
            for row in rows
        )

        for event in events:
            if not event.verify():
                raise GovernanceInterventionVerificationLifecycleIntegrityError(
                    "stored lifecycle event failed deterministic "
                    "verification"
                )

        return events

    def verify_tenant_chain(
        self,
        *,
        tenant_id: str,
    ) -> GovernanceInterventionVerificationLifecycleVerification:
        normalized_tenant = tenant_id.strip()

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLifecycleTenantError(
                "tenant_id is required"
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_lifecycle_events
                WHERE tenant_id = ?
                ORDER BY sequence_number ASC
                """,
                (normalized_tenant,),
            ).fetchall()

        expected_sequence = 1
        expected_previous_hash = (
            GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
        )

        for row in rows:
            event = self._event_from_row(row)
            entry = self._entry_from_row(row)

            if entry.sequence_number != expected_sequence:
                return (
                    GovernanceInterventionVerificationLifecycleVerification(
                        tenant_id=normalized_tenant,
                        event_count=len(rows),
                        valid=False,
                        last_chain_hash=(
                            expected_previous_hash
                        ),
                    )
                )

            if (
                entry.previous_chain_hash
                != expected_previous_hash
            ):
                return (
                    GovernanceInterventionVerificationLifecycleVerification(
                        tenant_id=normalized_tenant,
                        event_count=len(rows),
                        valid=False,
                        last_chain_hash=(
                            expected_previous_hash
                        ),
                    )
                )

            if not event.verify():
                return (
                    GovernanceInterventionVerificationLifecycleVerification(
                        tenant_id=normalized_tenant,
                        event_count=len(rows),
                        valid=False,
                        last_chain_hash=(
                            expected_previous_hash
                        ),
                    )
                )

            if not entry.verify_chain_hash():
                return (
                    GovernanceInterventionVerificationLifecycleVerification(
                        tenant_id=normalized_tenant,
                        event_count=len(rows),
                        valid=False,
                        last_chain_hash=(
                            expected_previous_hash
                        ),
                    )
                )

            expected_sequence += 1
            expected_previous_hash = entry.chain_hash

        return GovernanceInterventionVerificationLifecycleVerification(
            tenant_id=normalized_tenant,
            event_count=len(rows),
            valid=True,
            last_chain_hash=expected_previous_hash,
        )

    def _append_transition(
        self,
        *,
        record: GovernanceInterventionVerificationRecord,
        lifecycle_status: (
            GovernanceInterventionVerificationLifecycleStatus
        ),
        superseded_by_record_hash: str | None,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        current = self.get_current_state(
            tenant_id=record.tenant_id,
            verification_record_hash=record.record_hash,
        )

        current_status = (
            None
            if current is None
            else (
                GovernanceInterventionVerificationLifecycleStatus(
                    current.lifecycle_status
                )
            )
        )

        if (
            current is not None
            and current.lifecycle_status
            == lifecycle_status.value
            and current.superseded_by_record_hash
            == superseded_by_record_hash
        ):
            return self._entry_for_event_hash(
                tenant_id=record.tenant_id,
                lifecycle_event_hash=(
                    current.lifecycle_event_hash
                ),
            )

        allowed = _ALLOWED_TRANSITIONS[
            current_status
        ]

        if lifecycle_status not in allowed:
            previous_name = (
                "NONE"
                if current_status is None
                else current_status.value
            )

            raise GovernanceInterventionVerificationLifecycleTransitionError(
                f"lifecycle transition {previous_name} -> "
                f"{lifecycle_status.value} is not permitted"
            )

        if (
            lifecycle_status
            == GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED
        ):
            if not superseded_by_record_hash:
                raise GovernanceInterventionVerificationLifecycleTransitionError(
                    "SUPERSEDED requires superseded_by_record_hash"
                )
        elif superseded_by_record_hash is not None:
            raise GovernanceInterventionVerificationLifecycleTransitionError(
                "superseded_by_record_hash is valid only for "
                "SUPERSEDED lifecycle state"
            )

        payload: dict[str, Any] = {
            "lifecycle_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_SCHEMA_VERSION
            ),
            "tenant_id": record.tenant_id,
            "intervention_id": record.intervention_id,
            "verification_record_hash": (
                record.record_hash
            ),
            "previous_status": (
                None
                if current_status is None
                else current_status.value
            ),
            "lifecycle_status": (
                lifecycle_status.value
            ),
            "superseded_by_record_hash": (
                superseded_by_record_hash
            ),
        }

        event = (
            GovernanceInterventionVerificationLifecycleEvent(
                **payload,
                lifecycle_event_hash=sha256_hex(
                    canonical_json(payload)
                ),
            )
        )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            latest = connection.execute(
                """
                SELECT sequence_number, chain_hash
                FROM governance_intervention_verification_lifecycle_events
                WHERE tenant_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (record.tenant_id,),
            ).fetchone()

            if latest is None:
                sequence_number = 1
                previous_chain_hash = (
                    GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
                )
            else:
                sequence_number = (
                    int(latest["sequence_number"])
                    + 1
                )
                previous_chain_hash = str(
                    latest["chain_hash"]
                )

            chain_payload: dict[str, Any] = {
                "tenant_id": record.tenant_id,
                "sequence_number": sequence_number,
                "lifecycle_event_hash": (
                    event.lifecycle_event_hash
                ),
                "verification_record_hash": (
                    record.record_hash
                ),
                "previous_chain_hash": (
                    previous_chain_hash
                ),
                "ledger_schema_version": (
                    GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_LEDGER_SCHEMA_VERSION
                ),
            }

            chain_hash = sha256_hex(
                canonical_json(chain_payload)
            )

            try:
                connection.execute(
                    """
                    INSERT INTO
                    governance_intervention_verification_lifecycle_events (
                        tenant_id,
                        sequence_number,
                        lifecycle_id,
                        version,
                        schema_version,
                        intervention_id,
                        verification_record_hash,
                        previous_status,
                        lifecycle_status,
                        superseded_by_record_hash,
                        lifecycle_event_hash,
                        previous_chain_hash,
                        chain_hash,
                        ledger_schema_version
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        record.tenant_id,
                        sequence_number,
                        event.lifecycle_id,
                        event.version,
                        event.schema_version,
                        event.intervention_id,
                        event.verification_record_hash,
                        event.previous_status,
                        event.lifecycle_status,
                        event.superseded_by_record_hash,
                        event.lifecycle_event_hash,
                        previous_chain_hash,
                        chain_hash,
                        (
                            GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_LEDGER_SCHEMA_VERSION
                        ),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise GovernanceInterventionVerificationLifecycleIntegrityError(
                    "append-only verification lifecycle ledger "
                    "rejected conflicting event insertion"
                ) from exc

        return GovernanceInterventionVerificationLifecycleEntry(
            tenant_id=record.tenant_id,
            sequence_number=sequence_number,
            lifecycle_event_hash=(
                event.lifecycle_event_hash
            ),
            verification_record_hash=(
                record.record_hash
            ),
            previous_chain_hash=previous_chain_hash,
            chain_hash=chain_hash,
            ledger_schema_version=(
                GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_LEDGER_SCHEMA_VERSION
            ),
        )

    def _require_persisted_record(
        self,
        *,
        tenant_id: str,
        verification_record_hash: str,
    ) -> GovernanceInterventionVerificationRecord:
        normalized_tenant = tenant_id.strip()
        normalized_record_hash = (
            verification_record_hash.strip()
        )

        if not normalized_tenant:
            raise GovernanceInterventionVerificationLifecycleTenantError(
                "tenant_id is required"
            )

        if normalized_tenant != tenant_id:
            raise GovernanceInterventionVerificationLifecycleTenantError(
                "tenant_id must already be canonical"
            )

        if not normalized_record_hash:
            raise GovernanceInterventionVerificationLifecycleError(
                "verification_record_hash is required"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT intervention_id
                FROM governance_intervention_verification_records
                WHERE tenant_id = ?
                  AND record_hash = ?
                """,
                (
                    normalized_tenant,
                    normalized_record_hash,
                ),
            ).fetchone()

        if row is None:
            raise GovernanceInterventionVerificationLifecycleIntegrityError(
                "lifecycle operation requires an existing "
                "persisted verification record"
            )

        intervention_id = str(
            row["intervention_id"]
        )

        records = (
            self._verification_ledger.list_for_intervention(
                tenant_id=normalized_tenant,
                intervention_id=intervention_id,
            )
        )

        for record in records:
            if record.record_hash == normalized_record_hash:
                if not record.verify():
                    raise GovernanceInterventionVerificationLifecycleIntegrityError(
                        "persisted verification record failed "
                        "deterministic verification"
                    )

                return record

        raise GovernanceInterventionVerificationLifecycleIntegrityError(
            "persisted verification record could not be "
            "reconstructed through the governed ledger"
        )

    def _entry_for_event_hash(
        self,
        *,
        tenant_id: str,
        lifecycle_event_hash: str,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM governance_intervention_verification_lifecycle_events
                WHERE tenant_id = ?
                  AND lifecycle_event_hash = ?
                """,
                (
                    tenant_id,
                    lifecycle_event_hash,
                ),
            ).fetchone()

        if row is None:
            raise GovernanceInterventionVerificationLifecycleIntegrityError(
                "existing lifecycle event could not be recovered"
            )

        return self._entry_from_row(row)

    @staticmethod
    def _event_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionVerificationLifecycleEvent:
        return (
            GovernanceInterventionVerificationLifecycleEvent(
                lifecycle_id=str(
                    row["lifecycle_id"]
                ),
                version=str(row["version"]),
                schema_version=str(
                    row["schema_version"]
                ),
                tenant_id=str(row["tenant_id"]),
                intervention_id=str(
                    row["intervention_id"]
                ),
                verification_record_hash=str(
                    row["verification_record_hash"]
                ),
                previous_status=(
                    None
                    if row["previous_status"] is None
                    else str(row["previous_status"])
                ),
                lifecycle_status=str(
                    row["lifecycle_status"]
                ),
                superseded_by_record_hash=(
                    None
                    if (
                        row[
                            "superseded_by_record_hash"
                        ]
                        is None
                    )
                    else str(
                        row[
                            "superseded_by_record_hash"
                        ]
                    )
                ),
                lifecycle_event_hash=str(
                    row["lifecycle_event_hash"]
                ),
            )
        )

    @staticmethod
    def _entry_from_row(
        row: sqlite3.Row,
    ) -> GovernanceInterventionVerificationLifecycleEntry:
        return (
            GovernanceInterventionVerificationLifecycleEntry(
                tenant_id=str(row["tenant_id"]),
                sequence_number=int(
                    row["sequence_number"]
                ),
                lifecycle_event_hash=str(
                    row["lifecycle_event_hash"]
                ),
                verification_record_hash=str(
                    row["verification_record_hash"]
                ),
                previous_chain_hash=str(
                    row["previous_chain_hash"]
                ),
                chain_hash=str(
                    row["chain_hash"]
                ),
                ledger_schema_version=str(
                    row["ledger_schema_version"]
                ),
            )
        )