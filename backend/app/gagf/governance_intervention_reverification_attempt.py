from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_ID = (
    "governance-intervention-reverification-attempt"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_VERSION = (
    "0.1.0"
)


class GovernanceInterventionReverificationAttemptState(
    str,
    Enum,
):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GovernanceInterventionReverificationAttemptError(
    RuntimeError
):
    """Base error for the governed reverification-attempt journal."""


class GovernanceInterventionReverificationAttemptIntegrityError(
    GovernanceInterventionReverificationAttemptError
):
    """Raised when I-L work-order lineage cannot be proven."""


class GovernanceInterventionReverificationAttemptConflictError(
    GovernanceInterventionReverificationAttemptError
):
    """Raised when an attempt identity is rebound inconsistently."""


class GovernanceInterventionReverificationAttemptTransitionError(
    GovernanceInterventionReverificationAttemptError
):
    """Raised when an illegal attempt transition is requested."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationAttemptRecord:
    """
    Current persisted lifecycle state for one I-L reverification attempt.

    STARTED means only that governed reverification work has begun.

    COMPLETED means only that the bounded attempt process reported completion.
    It does not mean VERIFIED, NOT_VERIFIED, or INCONCLUSIVE.

    FAILED means only that the attempt process terminated unsuccessfully.
    It does not mean the intervention failed or that its prior verification
    disposition changed.
    """

    attempt_execution_id: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    request_hash: str
    work_order_hash: str
    attempt_id: str
    reverification_scope: str

    current_state: (
        GovernanceInterventionReverificationAttemptState
    )

    transition_count: int
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_execution_id": (
                self.attempt_execution_id
            ),
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "request_hash": self.request_hash,
            "work_order_hash": self.work_order_hash,
            "attempt_id": self.attempt_id,
            "reverification_scope": (
                self.reverification_scope
            ),
            "current_state": self.current_state.value,
            "transition_count": self.transition_count,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationAttemptTransition:
    transition_sequence: int
    attempt_execution_id: str
    state: GovernanceInterventionReverificationAttemptState
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_sequence": (
                self.transition_sequence
            ),
            "attempt_execution_id": (
                self.attempt_execution_id
            ),
            "state": self.state.value,
            "details": dict(self.details),
        }


_ALLOWED_TRANSITIONS = {
    GovernanceInterventionReverificationAttemptState.STARTED: {
        GovernanceInterventionReverificationAttemptState.COMPLETED,
        GovernanceInterventionReverificationAttemptState.FAILED,
    },
    GovernanceInterventionReverificationAttemptState.COMPLETED: set(),
    GovernanceInterventionReverificationAttemptState.FAILED: set(),
}


class GovernanceInterventionReverificationAttemptJournal:
    """
    Append-history/current-state journal for governed reverification attempts.

    Authority boundary:

    - validates and binds one deterministic I-L work order;
    - records that its attempt lifecycle started;
    - records bounded lifecycle completion or failure;
    - does not collect evidence;
    - does not create outcome observations;
    - does not perform measurement;
    - does not evaluate verification requirements;
    - does not issue verification dispositions;
    - does not supersede verification records;
    - does not mutate I-I verification lifecycle;
    - does not authorize intervention activity;
    - does not perform causal inference.
    """

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
    def derive_attempt_execution_id(
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
    ) -> str:
        if not work_order.verify():
            raise (
                GovernanceInterventionReverificationAttemptIntegrityError(
                    "reverification work order failed "
                    "deterministic verification"
                )
            )

        payload = {
            "attempt_journal_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_ID
            ),
            "attempt_journal_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_VERSION
            ),
            "tenant_id": work_order.tenant_id,
            "work_order_hash": (
                work_order.work_order_hash
            ),
            "attempt_id": work_order.attempt_id,
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
                governance_intervention_reverification_attempts (
                    attempt_execution_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    intervention_id TEXT NOT NULL,
                    verification_record_hash TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    work_order_hash TEXT NOT NULL,
                    attempt_id TEXT NOT NULL,
                    reverification_scope TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    transition_count INTEGER NOT NULL,
                    details_json TEXT NOT NULL,
                    UNIQUE (
                        tenant_id,
                        work_order_hash
                    ),
                    CHECK (transition_count >= 1)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                governance_intervention_reverification_attempt_transitions (
                    transition_sequence
                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempt_execution_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY (attempt_execution_id)
                    REFERENCES
                    governance_intervention_reverification_attempts(
                        attempt_execution_id
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_reverification_attempt_transitions
                ON
                governance_intervention_reverification_attempt_transitions (
                    attempt_execution_id,
                    transition_sequence
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_reverification_attempts_work_order
                ON governance_intervention_reverification_attempts (
                    tenant_id,
                    work_order_hash
                )
                """
            )

    def begin(
        self,
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        details: dict[str, Any] | None = None,
    ) -> GovernanceInterventionReverificationAttemptRecord:
        self._validate_work_order(work_order)

        attempt_execution_id = (
            self.derive_attempt_execution_id(
                work_order=work_order
            )
        )

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
                    attempt_execution_id,
                    tenant_id,
                    intervention_id,
                    verification_record_hash,
                    request_hash,
                    work_order_hash,
                    attempt_id,
                    reverification_scope,
                    current_state,
                    transition_count,
                    details_json
                FROM
                    governance_intervention_reverification_attempts
                WHERE tenant_id = ?
                  AND work_order_hash = ?
                """,
                (
                    work_order.tenant_id,
                    work_order.work_order_hash,
                ),
            ).fetchone()

            if existing is not None:
                record = self._record(existing)

                self._validate_existing_binding(
                    record=record,
                    work_order=work_order,
                    attempt_execution_id=(
                        attempt_execution_id
                    ),
                )

                return record

            connection.execute(
                """
                INSERT INTO
                governance_intervention_reverification_attempts (
                    attempt_execution_id,
                    tenant_id,
                    intervention_id,
                    verification_record_hash,
                    request_hash,
                    work_order_hash,
                    attempt_id,
                    reverification_scope,
                    current_state,
                    transition_count,
                    details_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_execution_id,
                    work_order.tenant_id,
                    work_order.intervention_id,
                    work_order.verification_record_hash,
                    work_order.request_hash,
                    work_order.work_order_hash,
                    work_order.attempt_id,
                    work_order.reverification_scope,
                    (
                        GovernanceInterventionReverificationAttemptState
                        .STARTED.value
                    ),
                    1,
                    serialized_details,
                ),
            )

            connection.execute(
                """
                INSERT INTO
                governance_intervention_reverification_attempt_transitions (
                    attempt_execution_id,
                    state,
                    details_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    attempt_execution_id,
                    (
                        GovernanceInterventionReverificationAttemptState
                        .STARTED.value
                    ),
                    serialized_details,
                ),
            )

        record = self.get(
            attempt_execution_id=attempt_execution_id
        )

        if record is None:
            raise (
                GovernanceInterventionReverificationAttemptError(
                    "reverification attempt journal failed "
                    "to create record"
                )
            )

        return record

    def transition(
        self,
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        state: (
            GovernanceInterventionReverificationAttemptState
        ),
        details: dict[str, Any] | None = None,
    ) -> GovernanceInterventionReverificationAttemptRecord:
        self._validate_work_order(work_order)

        attempt_execution_id = (
            self.derive_attempt_execution_id(
                work_order=work_order
            )
        )

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
                    attempt_execution_id,
                    tenant_id,
                    intervention_id,
                    verification_record_hash,
                    request_hash,
                    work_order_hash,
                    attempt_id,
                    reverification_scope,
                    current_state,
                    transition_count,
                    details_json
                FROM
                    governance_intervention_reverification_attempts
                WHERE attempt_execution_id = ?
                """,
                (attempt_execution_id,),
            ).fetchone()

            if existing is None:
                raise (
                    GovernanceInterventionReverificationAttemptError(
                        "cannot transition an unknown "
                        "reverification attempt"
                    )
                )

            record = self._record(existing)

            self._validate_existing_binding(
                record=record,
                work_order=work_order,
                attempt_execution_id=(
                    attempt_execution_id
                ),
            )

            current_state = record.current_state

            if current_state == state:
                return record

            allowed = _ALLOWED_TRANSITIONS[
                current_state
            ]

            if state not in allowed:
                raise (
                    GovernanceInterventionReverificationAttemptTransitionError(
                        "illegal reverification attempt transition: "
                        f"{current_state.value} -> "
                        f"{state.value}"
                    )
                )

            connection.execute(
                """
                INSERT INTO
                governance_intervention_reverification_attempt_transitions (
                    attempt_execution_id,
                    state,
                    details_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    attempt_execution_id,
                    state.value,
                    serialized_details,
                ),
            )

            connection.execute(
                """
                UPDATE
                    governance_intervention_reverification_attempts
                SET
                    current_state = ?,
                    transition_count =
                        transition_count + 1,
                    details_json = ?
                WHERE attempt_execution_id = ?
                """,
                (
                    state.value,
                    serialized_details,
                    attempt_execution_id,
                ),
            )

        record = self.get(
            attempt_execution_id=attempt_execution_id
        )

        if record is None:
            raise (
                GovernanceInterventionReverificationAttemptError(
                    "reverification attempt disappeared "
                    "after transition"
                )
            )

        return record

    def complete(
        self,
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        details: dict[str, Any] | None = None,
    ) -> GovernanceInterventionReverificationAttemptRecord:
        return self.transition(
            work_order=work_order,
            state=(
                GovernanceInterventionReverificationAttemptState
                .COMPLETED
            ),
            details=details,
        )

    def fail(
        self,
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        error: Exception,
    ) -> GovernanceInterventionReverificationAttemptRecord:
        return self.transition(
            work_order=work_order,
            state=(
                GovernanceInterventionReverificationAttemptState
                .FAILED
            ),
            details={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    def get(
        self,
        *,
        attempt_execution_id: str,
    ) -> (
        GovernanceInterventionReverificationAttemptRecord
        | None
    ):
        normalized_id = attempt_execution_id.strip()

        if not normalized_id:
            raise (
                GovernanceInterventionReverificationAttemptError(
                    "attempt_execution_id is required"
                )
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    attempt_execution_id,
                    tenant_id,
                    intervention_id,
                    verification_record_hash,
                    request_hash,
                    work_order_hash,
                    attempt_id,
                    reverification_scope,
                    current_state,
                    transition_count,
                    details_json
                FROM
                    governance_intervention_reverification_attempts
                WHERE attempt_execution_id = ?
                """,
                (normalized_id,),
            ).fetchone()

        if row is None:
            return None

        return self._record(row)

    def get_for_work_order(
        self,
        *,
        tenant_id: str,
        work_order_hash: str,
    ) -> (
        GovernanceInterventionReverificationAttemptRecord
        | None
    ):
        normalized_tenant = tenant_id.strip()
        normalized_hash = work_order_hash.strip()

        if not normalized_tenant:
            raise (
                GovernanceInterventionReverificationAttemptError(
                    "tenant_id is required"
                )
            )

        if not normalized_hash:
            raise (
                GovernanceInterventionReverificationAttemptError(
                    "work_order_hash is required"
                )
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    attempt_execution_id,
                    tenant_id,
                    intervention_id,
                    verification_record_hash,
                    request_hash,
                    work_order_hash,
                    attempt_id,
                    reverification_scope,
                    current_state,
                    transition_count,
                    details_json
                FROM
                    governance_intervention_reverification_attempts
                WHERE tenant_id = ?
                  AND work_order_hash = ?
                """,
                (
                    normalized_tenant,
                    normalized_hash,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._record(row)

    def list_transitions(
        self,
        *,
        attempt_execution_id: str,
    ) -> tuple[
        GovernanceInterventionReverificationAttemptTransition,
        ...,
    ]:
        normalized_id = attempt_execution_id.strip()

        if not normalized_id:
            raise (
                GovernanceInterventionReverificationAttemptError(
                    "attempt_execution_id is required"
                )
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    transition_sequence,
                    attempt_execution_id,
                    state,
                    details_json
                FROM
                    governance_intervention_reverification_attempt_transitions
                WHERE attempt_execution_id = ?
                ORDER BY transition_sequence ASC
                """,
                (normalized_id,),
            ).fetchall()

        return tuple(
            GovernanceInterventionReverificationAttemptTransition(
                transition_sequence=(
                    row["transition_sequence"]
                ),
                attempt_execution_id=(
                    row["attempt_execution_id"]
                ),
                state=(
                    GovernanceInterventionReverificationAttemptState(
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
    def _validate_work_order(
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
    ) -> None:
        if not work_order.verify():
            raise (
                GovernanceInterventionReverificationAttemptIntegrityError(
                    "reverification work order failed "
                    "deterministic verification"
                )
            )

        required = {
            "tenant_id": work_order.tenant_id,
            "intervention_id": work_order.intervention_id,
            "verification_record_hash": (
                work_order.verification_record_hash
            ),
            "request_hash": work_order.request_hash,
            "work_order_hash": work_order.work_order_hash,
            "attempt_id": work_order.attempt_id,
            "reverification_scope": (
                work_order.reverification_scope
            ),
        }

        for field_name, value in required.items():
            if not value.strip():
                raise (
                    GovernanceInterventionReverificationAttemptIntegrityError(
                        f"{field_name} is required"
                    )
                )

    @staticmethod
    def _validate_existing_binding(
        *,
        record: GovernanceInterventionReverificationAttemptRecord,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        attempt_execution_id: str,
    ) -> None:
        expected = (
            attempt_execution_id,
            work_order.tenant_id,
            work_order.intervention_id,
            work_order.verification_record_hash,
            work_order.request_hash,
            work_order.work_order_hash,
            work_order.attempt_id,
            work_order.reverification_scope,
        )

        actual = (
            record.attempt_execution_id,
            record.tenant_id,
            record.intervention_id,
            record.verification_record_hash,
            record.request_hash,
            record.work_order_hash,
            record.attempt_id,
            record.reverification_scope,
        )

        if actual != expected:
            raise (
                GovernanceInterventionReverificationAttemptConflictError(
                    "persisted reverification attempt does not "
                    "match I-L work-order lineage"
                )
            )

    @staticmethod
    def _record(
        row: sqlite3.Row,
    ) -> GovernanceInterventionReverificationAttemptRecord:
        return GovernanceInterventionReverificationAttemptRecord(
            attempt_execution_id=(
                row["attempt_execution_id"]
            ),
            tenant_id=row["tenant_id"],
            intervention_id=row["intervention_id"],
            verification_record_hash=(
                row["verification_record_hash"]
            ),
            request_hash=row["request_hash"],
            work_order_hash=row["work_order_hash"],
            attempt_id=row["attempt_id"],
            reverification_scope=(
                row["reverification_scope"]
            ),
            current_state=(
                GovernanceInterventionReverificationAttemptState(
                    row["current_state"]
                )
            ),
            transition_count=row["transition_count"],
            details=json.loads(
                row["details_json"]
            ),
        )