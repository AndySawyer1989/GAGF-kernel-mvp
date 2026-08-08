from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_ID = (
    "governance-intervention-actuation-journal"
)

GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_VERSION = "0.1.0"


class GovernanceInterventionActuationState(str, Enum):
    ACCEPTED = "ACCEPTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    ROLLED_BACK = "ROLLED_BACK"


class GovernanceInterventionActuationJournalError(
    RuntimeError
):
    pass


class GovernanceInterventionActuationConflictError(
    GovernanceInterventionActuationJournalError
):
    pass


class GovernanceInterventionActuationTransitionError(
    GovernanceInterventionActuationJournalError
):
    pass


@dataclass(frozen=True, slots=True)
class GovernanceInterventionActuationJournalRecord:
    actuation_id: str
    tenant_id: str
    contract_hash: str
    idempotency_key: str
    current_state: GovernanceInterventionActuationState
    transition_count: int
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "actuation_id": self.actuation_id,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "idempotency_key": self.idempotency_key,
            "current_state": self.current_state.value,
            "transition_count": self.transition_count,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionActuationTransition:
    transition_sequence: int
    actuation_id: str
    state: GovernanceInterventionActuationState
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_sequence": self.transition_sequence,
            "actuation_id": self.actuation_id,
            "state": self.state.value,
            "details": dict(self.details),
        }


_ALLOWED_TRANSITIONS = {
    GovernanceInterventionActuationState.ACCEPTED: {
        GovernanceInterventionActuationState.STARTED,
        GovernanceInterventionActuationState.ABORTED,
    },
    GovernanceInterventionActuationState.STARTED: {
        GovernanceInterventionActuationState.COMPLETED,
        GovernanceInterventionActuationState.FAILED,
        GovernanceInterventionActuationState.ABORTED,
        GovernanceInterventionActuationState.ROLLBACK_REQUIRED,
    },
    GovernanceInterventionActuationState.FAILED: {
        GovernanceInterventionActuationState.ROLLBACK_REQUIRED,
    },
    GovernanceInterventionActuationState.ROLLBACK_REQUIRED: {
        GovernanceInterventionActuationState.ROLLED_BACK,
        GovernanceInterventionActuationState.FAILED,
    },
    GovernanceInterventionActuationState.COMPLETED: set(),
    GovernanceInterventionActuationState.ABORTED: set(),
    GovernanceInterventionActuationState.ROLLED_BACK: set(),
}


class GovernanceInterventionActuationJournal:
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

    @staticmethod
    def derive_actuation_id(
        *,
        tenant_id: str,
        contract_hash: str,
        idempotency_key: str,
    ) -> str:
        payload = {
            "journal_id": (
                GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_ID
            ),
            "journal_version": (
                GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_VERSION
            ),
            "tenant_id": tenant_id,
            "contract_hash": contract_hash,
            "idempotency_key": idempotency_key,
        }

        return sha256_hex(
            canonical_json(payload)
        )

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
                governance_intervention_actuations (
                    actuation_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    contract_hash TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    transition_count INTEGER NOT NULL,
                    details_json TEXT NOT NULL,
                    UNIQUE (
                        tenant_id,
                        idempotency_key
                    ),
                    CHECK (transition_count >= 1)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                governance_intervention_actuation_transitions (
                    transition_sequence
                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    actuation_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY (actuation_id)
                    REFERENCES governance_intervention_actuations(
                        actuation_id
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_governance_actuation_transitions
                ON governance_intervention_actuation_transitions (
                    actuation_id,
                    transition_sequence
                )
                """
            )

    def begin(
        self,
        *,
        tenant_id: str,
        contract_hash: str,
        idempotency_key: str,
        details: dict[str, Any] | None = None,
    ) -> GovernanceInterventionActuationJournalRecord:
        normalized_tenant = tenant_id.strip()
        normalized_contract = contract_hash.strip()
        normalized_key = idempotency_key.strip()

        if not normalized_tenant:
            raise GovernanceInterventionActuationJournalError(
                "tenant_id is required"
            )

        if not normalized_contract:
            raise GovernanceInterventionActuationJournalError(
                "contract_hash is required"
            )

        if not normalized_key:
            raise GovernanceInterventionActuationJournalError(
                "idempotency_key is required"
            )

        normalized_details = (
            dict(details)
            if details is not None
            else {}
        )

        actuation_id = self.derive_actuation_id(
            tenant_id=normalized_tenant,
            contract_hash=normalized_contract,
            idempotency_key=normalized_key,
        )

        serialized_details = canonical_json(
            normalized_details
        )

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    actuation_id,
                    tenant_id,
                    contract_hash,
                    idempotency_key,
                    current_state,
                    transition_count,
                    details_json
                FROM governance_intervention_actuations
                WHERE tenant_id = ?
                  AND idempotency_key = ?
                """,
                (
                    normalized_tenant,
                    normalized_key,
                ),
            ).fetchone()

            if existing is not None:
                record = self._record(existing)

                if (
                    record.actuation_id != actuation_id
                    or record.contract_hash
                    != normalized_contract
                ):
                    raise (
                        GovernanceInterventionActuationConflictError(
                            "Idempotency key already belongs to "
                            "a different actuation contract."
                        )
                    )

                return record

            connection.execute(
                """
                INSERT INTO governance_intervention_actuations (
                    actuation_id,
                    tenant_id,
                    contract_hash,
                    idempotency_key,
                    current_state,
                    transition_count,
                    details_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actuation_id,
                    normalized_tenant,
                    normalized_contract,
                    normalized_key,
                    GovernanceInterventionActuationState
                    .ACCEPTED.value,
                    1,
                    serialized_details,
                ),
            )

            connection.execute(
                """
                INSERT INTO
                governance_intervention_actuation_transitions (
                    actuation_id,
                    state,
                    details_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    actuation_id,
                    GovernanceInterventionActuationState
                    .ACCEPTED.value,
                    serialized_details,
                ),
            )

        record = self.get(actuation_id)

        if record is None:
            raise GovernanceInterventionActuationJournalError(
                "Actuation journal failed to create record."
            )

        return record

    def transition(
        self,
        *,
        actuation_id: str,
        state: GovernanceInterventionActuationState,
        details: dict[str, Any] | None = None,
    ) -> GovernanceInterventionActuationJournalRecord:
        normalized_details = (
            dict(details)
            if details is not None
            else {}
        )

        serialized_details = canonical_json(
            normalized_details
        )

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    actuation_id,
                    tenant_id,
                    contract_hash,
                    idempotency_key,
                    current_state,
                    transition_count,
                    details_json
                FROM governance_intervention_actuations
                WHERE actuation_id = ?
                """,
                (actuation_id,),
            ).fetchone()

            if existing is None:
                raise GovernanceInterventionActuationJournalError(
                    "Cannot transition an unknown actuation."
                )

            current_state = (
                GovernanceInterventionActuationState(
                    existing["current_state"]
                )
            )

            if current_state == state:
                return self._record(existing)

            allowed = _ALLOWED_TRANSITIONS[
                current_state
            ]

            if state not in allowed:
                raise (
                    GovernanceInterventionActuationTransitionError(
                        "Illegal actuation transition: "
                        f"{current_state.value} -> "
                        f"{state.value}"
                    )
                )

            connection.execute(
                """
                INSERT INTO
                governance_intervention_actuation_transitions (
                    actuation_id,
                    state,
                    details_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    actuation_id,
                    state.value,
                    serialized_details,
                ),
            )

            connection.execute(
                """
                UPDATE governance_intervention_actuations
                SET
                    current_state = ?,
                    transition_count =
                        transition_count + 1,
                    details_json = ?
                WHERE actuation_id = ?
                """,
                (
                    state.value,
                    serialized_details,
                    actuation_id,
                ),
            )

        record = self.get(actuation_id)

        if record is None:
            raise GovernanceInterventionActuationJournalError(
                "Actuation disappeared after transition."
            )

        return record

    def get(
        self,
        actuation_id: str,
    ) -> GovernanceInterventionActuationJournalRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    actuation_id,
                    tenant_id,
                    contract_hash,
                    idempotency_key,
                    current_state,
                    transition_count,
                    details_json
                FROM governance_intervention_actuations
                WHERE actuation_id = ?
                """,
                (actuation_id,),
            ).fetchone()

        if row is None:
            return None

        return self._record(row)

    def list_transitions(
        self,
        actuation_id: str,
    ) -> tuple[
        GovernanceInterventionActuationTransition,
        ...,
    ]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    transition_sequence,
                    actuation_id,
                    state,
                    details_json
                FROM
                    governance_intervention_actuation_transitions
                WHERE actuation_id = ?
                ORDER BY transition_sequence ASC
                """,
                (actuation_id,),
            ).fetchall()

        return tuple(
            GovernanceInterventionActuationTransition(
                transition_sequence=(
                    row["transition_sequence"]
                ),
                actuation_id=row["actuation_id"],
                state=(
                    GovernanceInterventionActuationState(
                        row["state"]
                    )
                ),
                details=json.loads(
                    row["details_json"]
                ),
            )
            for row in rows
        )

    @staticmethod
    def _record(
        row: sqlite3.Row,
    ) -> GovernanceInterventionActuationJournalRecord:
        return GovernanceInterventionActuationJournalRecord(
            actuation_id=row["actuation_id"],
            tenant_id=row["tenant_id"],
            contract_hash=row["contract_hash"],
            idempotency_key=row["idempotency_key"],
            current_state=(
                GovernanceInterventionActuationState(
                    row["current_state"]
                )
            ),
            transition_count=row["transition_count"],
            details=json.loads(row["details_json"]),
        )
