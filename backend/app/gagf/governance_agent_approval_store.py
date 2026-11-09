from __future__ import annotations

import json
import math
import sqlite3

from datetime import datetime, timezone
from pathlib import Path

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalContractError,
    AgentApprovalDecisionRecord,
    AgentApprovalRequest,
    ApprovalActionClass,
    ApprovalActorType,
    ApprovalDecision,
    ApprovalRequesterType,
    requires_human_approval,
)


APPROVAL_STORE_VERSION = "0.1.0"


class AgentApprovalStoreError(Exception):
    """Base exception for approval-store failures."""


class AgentApprovalNotFoundError(AgentApprovalStoreError):
    """Raised when a tenant-scoped approval record does not exist."""


class AgentApprovalConflictError(AgentApprovalStoreError):
    """Raised when an identifier or idempotency key conflicts."""


class AgentApprovalIntegrityError(AgentApprovalStoreError):
    """Raised when persisted approval integrity verification fails."""


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentApprovalStoreError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _parse_datetime(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AgentApprovalIntegrityError(
            f"Stored {field_name} is invalid"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AgentApprovalIntegrityError(
            f"Stored {field_name} must be timezone-aware"
        )

    return parsed


class AgentApprovalStore:
    """Tenant-scoped, append-only SQLite approval persistence."""

    def __init__(
        self,
        database_path: str | Path,
        timeout_seconds: float = 10.0,
    ) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise AgentApprovalStoreError(
                "timeout_seconds must be a finite number greater than zero"
            )

        try:
            valid_timeout = (
                math.isfinite(float(timeout_seconds))
                and timeout_seconds > 0
            )
        except (OverflowError, ValueError):
            valid_timeout = False

        if not valid_timeout:
            raise AgentApprovalStoreError(
                "timeout_seconds must be a finite number greater than zero"
            )

        self.database_path = Path(database_path)
        self.timeout_seconds = float(timeout_seconds)

        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection: sqlite3.Connection | None = None

        try:
            connection = sqlite3.connect(
                str(self.database_path),
                timeout=self.timeout_seconds,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}"
            )
            return connection

        except sqlite3.Error as exc:
            if connection is not None:
                try:
                    connection.close()
                except sqlite3.Error:
                    pass

            raise AgentApprovalStoreError(
                "Unable to establish approval-store database connection"
            ) from exc

    def _initialize(self) -> None:
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_approval_requests (
                    tenant_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    work_item_id TEXT NOT NULL,
                    action_class TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    requester_type TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    action_json TEXT NOT NULL,
                    action_hash TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    request_hash TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, request_id),
                    UNIQUE (tenant_id, idempotency_key)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_approval_decisions (
                    tenant_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    decision_id TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    work_item_id TEXT NOT NULL,
                    action_hash TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    approver_id TEXT NOT NULL,
                    approver_type TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    reason TEXT,
                    schema_version INTEGER NOT NULL,
                    decision_hash TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, request_id),
                    UNIQUE (tenant_id, decision_id),
                    UNIQUE (tenant_id, idempotency_key),
                    FOREIGN KEY (tenant_id, request_id)
                        REFERENCES gagf_agent_approval_requests (
                            tenant_id,
                            request_id
                        )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_gagf_agent_approval_requests_workflow
                ON gagf_agent_approval_requests (
                    tenant_id,
                    workflow_id,
                    work_item_id
                )
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_approval_requests_no_update
                BEFORE UPDATE ON gagf_agent_approval_requests
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'approval requests are append-only'
                    );
                END
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_approval_requests_no_delete
                BEFORE DELETE ON gagf_agent_approval_requests
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'approval requests are append-only'
                    );
                END
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_approval_decisions_no_update
                BEFORE UPDATE ON gagf_agent_approval_decisions
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'approval decisions are append-only'
                    );
                END
                """
            )

            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS
                    trg_gagf_agent_approval_decisions_no_delete
                BEFORE DELETE ON gagf_agent_approval_decisions
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'approval decisions are append-only'
                    );
                END
                """
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _request_from_row(
        row: sqlite3.Row,
    ) -> AgentApprovalRequest:
        try:
            request = AgentApprovalRequest.create(
                request_id=row["request_id"],
                tenant_id=row["tenant_id"],
                workflow_id=row["workflow_id"],
                work_item_id=row["work_item_id"],
                action_class=ApprovalActionClass(row["action_class"]),
                requester_id=row["requester_id"],
                requester_type=ApprovalRequesterType(
                    row["requester_type"]
                ),
                requested_at=_parse_datetime(
                    row["requested_at"],
                    "requested_at",
                ),
                expires_at=_parse_datetime(
                    row["expires_at"],
                    "expires_at",
                ),
                correlation_id=row["correlation_id"],
                idempotency_key=row["idempotency_key"],
                action=json.loads(row["action_json"]),
            )

            if (
                request.action_json != row["action_json"]
                or request.action_hash != row["action_hash"]
                or request.request_hash != row["request_hash"]
                or request.schema_version != row["schema_version"]
            ):
                raise AgentApprovalIntegrityError(
                    "Stored approval request integrity verification failed"
                )

            return request

        except AgentApprovalStoreError:
            raise
        except (
            AgentApprovalContractError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise AgentApprovalIntegrityError(
                "Stored approval request is invalid"
            ) from exc

    @staticmethod
    def _decision_from_row(
        row: sqlite3.Row,
    ) -> AgentApprovalDecisionRecord:
        try:
            decision = AgentApprovalDecisionRecord(
                decision_id=row["decision_id"],
                request_id=row["request_id"],
                request_hash=row["request_hash"],
                tenant_id=row["tenant_id"],
                workflow_id=row["workflow_id"],
                work_item_id=row["work_item_id"],
                action_hash=row["action_hash"],
                decision=ApprovalDecision(row["decision"]),
                approver_id=row["approver_id"],
                approver_type=ApprovalActorType(row["approver_type"]),
                decided_at=_parse_datetime(
                    row["decided_at"],
                    "decided_at",
                ),
                idempotency_key=row["idempotency_key"],
                reason=row["reason"],
                schema_version=row["schema_version"],
                decision_hash=row["decision_hash"],
            )

            if not decision.verify_integrity():
                raise AgentApprovalIntegrityError(
                    "Stored approval decision integrity verification failed"
                )

            return decision

        except AgentApprovalStoreError:
            raise
        except (
            AgentApprovalContractError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise AgentApprovalIntegrityError(
                "Stored approval decision is invalid"
            ) from exc

    def save_request(
        self,
        request: AgentApprovalRequest,
    ) -> AgentApprovalRequest:
        if not isinstance(request, AgentApprovalRequest):
            raise AgentApprovalStoreError(
                "request must be an AgentApprovalRequest"
            )

        if not requires_human_approval(request.action_class):
            raise AgentApprovalStoreError(
                "This action class does not require human approval"
            )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_requests
                WHERE tenant_id = ?
                  AND idempotency_key = ?
                """,
                (request.tenant_id, request.idempotency_key),
            ).fetchone()

            if existing is not None:
                stored = self._request_from_row(existing)

                if stored.request_hash != request.request_hash:
                    raise AgentApprovalConflictError(
                        "Request idempotency key was reused"
                    )

                connection.commit()
                return stored

            duplicate = connection.execute(
                """
                SELECT 1
                FROM gagf_agent_approval_requests
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (request.tenant_id, request.request_id),
            ).fetchone()

            if duplicate is not None:
                raise AgentApprovalConflictError(
                    "Approval request ID already exists"
                )

            connection.execute(
                """
                INSERT INTO gagf_agent_approval_requests (
                    tenant_id,
                    request_id,
                    workflow_id,
                    work_item_id,
                    action_class,
                    requester_id,
                    requester_type,
                    requested_at,
                    expires_at,
                    correlation_id,
                    idempotency_key,
                    action_json,
                    action_hash,
                    schema_version,
                    request_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.tenant_id,
                    request.request_id,
                    request.workflow_id,
                    request.work_item_id,
                    request.action_class.value,
                    request.requester_id,
                    request.requester_type.value,
                    request.requested_at.isoformat(),
                    request.expires_at.isoformat(),
                    request.correlation_id,
                    request.idempotency_key,
                    request.action_json,
                    request.action_hash,
                    request.schema_version,
                    request.request_hash,
                ),
            )

            connection.commit()
            return request

        except AgentApprovalStoreError:
            connection.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise AgentApprovalConflictError(
                "Approval request conflicts with an existing record"
            ) from exc
        except sqlite3.Error as exc:
            connection.rollback()
            raise AgentApprovalStoreError(
                "Unable to persist approval request"
            ) from exc
        finally:
            connection.close()

    def get_request(
        self,
        *,
        tenant_id: str,
        request_id: str,
    ) -> AgentApprovalRequest:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(request_id, "request_id")

        connection = self._connect()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_requests
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if row is None:
                raise AgentApprovalNotFoundError(
                    "Approval request was not found"
                )

            return self._request_from_row(row)

        except AgentApprovalStoreError:
            raise
        except sqlite3.Error as exc:
            raise AgentApprovalStoreError(
                "Unable to retrieve approval request"
            ) from exc
        finally:
            connection.close()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def record_decision(
        self,
        decision: AgentApprovalDecisionRecord,
    ) -> AgentApprovalDecisionRecord:
        if not isinstance(decision, AgentApprovalDecisionRecord):
            raise AgentApprovalStoreError(
                "decision must be an AgentApprovalDecisionRecord"
            )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            request_row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_requests
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (decision.tenant_id, decision.request_id),
            ).fetchone()

            if request_row is None:
                raise AgentApprovalNotFoundError(
                    "Persisted approval request was not found"
                )

            request = self._request_from_row(request_row)
            decision.validate_against(request)

            existing_key = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_decisions
                WHERE tenant_id = ?
                  AND idempotency_key = ?
                """,
                (decision.tenant_id, decision.idempotency_key),
            ).fetchone()

            if existing_key is not None:
                stored = self._decision_from_row(existing_key)

                if stored.decision_hash != decision.decision_hash:
                    raise AgentApprovalConflictError(
                        "Decision idempotency key was reused"
                    )

                connection.commit()
                return stored

            existing_request = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_decisions
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (decision.tenant_id, decision.request_id),
            ).fetchone()

            if existing_request is not None:
                stored = self._decision_from_row(existing_request)

                if stored.decision_hash == decision.decision_hash:
                    connection.commit()
                    return stored

                raise AgentApprovalConflictError(
                    "Approval request already has a different final decision"
                )

            current = self._now()

            if request.is_expired(current):
                raise AgentApprovalConflictError(
                    "Approval request expired before decision persistence"
                )

            connection.execute(
                """
                INSERT INTO gagf_agent_approval_decisions (
                    tenant_id,
                    request_id,
                    decision_id,
                    request_hash,
                    workflow_id,
                    work_item_id,
                    action_hash,
                    decision,
                    approver_id,
                    approver_type,
                    decided_at,
                    idempotency_key,
                    reason,
                    schema_version,
                    decision_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.tenant_id,
                    decision.request_id,
                    decision.decision_id,
                    decision.request_hash,
                    decision.workflow_id,
                    decision.work_item_id,
                    decision.action_hash,
                    decision.decision.value,
                    decision.approver_id,
                    decision.approver_type.value,
                    decision.decided_at.isoformat(),
                    decision.idempotency_key,
                    decision.reason,
                    decision.schema_version,
                    decision.decision_hash,
                ),
            )

            connection.commit()
            return decision

        except AgentApprovalStoreError:
            connection.rollback()
            raise
        except AgentApprovalContractError as exc:
            connection.rollback()
            raise AgentApprovalIntegrityError(
                "Approval decision does not match its persisted request"
            ) from exc
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise AgentApprovalConflictError(
                "Approval decision conflicts with an existing record"
            ) from exc
        except sqlite3.Error as exc:
            connection.rollback()
            raise AgentApprovalStoreError(
                "Unable to persist approval decision"
            ) from exc
        finally:
            connection.close()

    def get_decision(
        self,
        *,
        tenant_id: str,
        request_id: str,
    ) -> AgentApprovalDecisionRecord:
        tenant = _require_text(tenant_id, "tenant_id")
        identifier = _require_text(request_id, "request_id")

        connection = self._connect()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_decisions
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if row is None:
                raise AgentApprovalNotFoundError(
                    "Approval decision was not found"
                )

            decision = self._decision_from_row(row)

            request_row = connection.execute(
                """
                SELECT *
                FROM gagf_agent_approval_requests
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (tenant, identifier),
            ).fetchone()

            if request_row is None:
                raise AgentApprovalIntegrityError(
                    "Approval decision has no persisted request"
                )

            request = self._request_from_row(request_row)

            try:
                decision.validate_against(request)
            except AgentApprovalContractError as exc:
                raise AgentApprovalIntegrityError(
                    "Stored approval decision does not match its request"
                ) from exc

            return decision

        except AgentApprovalStoreError:
            raise
        except sqlite3.Error as exc:
            raise AgentApprovalStoreError(
                "Unable to retrieve approval decision"
            ) from exc
        finally:
            connection.close()