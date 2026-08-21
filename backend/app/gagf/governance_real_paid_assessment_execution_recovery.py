from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_demonstration_persistence import (
    GovernanceAssessmentDemonstrationPersistenceService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoff,
    PaidAssessmentWorkAuthorization,
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    RealPaidAssessmentAuthorizationBridge,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    RealPaidAssessmentExecutionEvidenceBinding,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    EXPECTED_CORE_ARTIFACT_COUNT,
    GovernanceRealPaidAssessmentExecutionService,
)


REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_ID = (
    "governance-real-paid-assessment-execution-recovery"
)
REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_SCHEMA_VERSION = "1.0.0"

EXECUTION_ATTEMPT_STATUS_RECORDED = "attempt_recorded"

EXECUTION_ATTEMPT_TABLE = (
    "governance_paid_assessment_execution_attempts"
)


class RealPaidAssessmentExecutionRecoveryError(RuntimeError):
    """Raised when real paid-assessment execution recovery cannot proceed."""


class RealPaidAssessmentExecutionAttemptConflictError(
    RealPaidAssessmentExecutionRecoveryError
):
    """Raised when an existing execution attempt does not match the request."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentExecutionAttempt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    database_path: str

    contract_execution_event_id: str
    contract_execution_event_hash: str

    paid_work_authorization_id: str
    paid_work_authorization_hash: str

    assessment_execution_request_hash: str
    handoff_hash: str

    authorization_bridge_hash: str
    execution_evidence_binding_hash: str

    attempt_status: str
    recorded_at: str
    attempt_hash: str
    record_hash: str

    recovery_type: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_ID
    )
    version: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_VERSION
    )
    schema_version: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_type": self.recovery_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "database_path": self.database_path,
            "contract_execution_event_id": (
                self.contract_execution_event_id
            ),
            "contract_execution_event_hash": (
                self.contract_execution_event_hash
            ),
            "paid_work_authorization_id": (
                self.paid_work_authorization_id
            ),
            "paid_work_authorization_hash": (
                self.paid_work_authorization_hash
            ),
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "handoff_hash": self.handoff_hash,
            "authorization_bridge_hash": (
                self.authorization_bridge_hash
            ),
            "execution_evidence_binding_hash": (
                self.execution_evidence_binding_hash
            ),
            "attempt_status": self.attempt_status,
            "recorded_at": self.recorded_at,
            "attempt_hash": self.attempt_hash,
            "record_hash": self.record_hash,
            "boundaries": {
                "attempt_record_is_not_execution_authority": True,
                "attempt_record_is_not_application_execution": True,
                "attempt_record_is_not_customer_delivery": True,
                "recovery_is_not_duplicate_execution": True,
                "existing_database_is_not_matching_attempt": True,
            },
        }


class GovernanceRealPaidAssessmentExecutionAttemptStore:
    """
    Durable identity binding for one governed real paid-assessment execution.

    This store does not authorize execution and is not an assessment-artifact
    ledger. It exists only to prove whether an existing database belongs to
    the exact governed execution attempt being requested.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._path = Path(database_path)

    @property
    def database_path(self) -> Path:
        return self._path

    def initialize(self) -> None:
        if self._path.parent and not self._path.parent.exists():
            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        with sqlite3.connect(self._path) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {EXECUTION_ATTEMPT_TABLE} (
                    attempt_hash TEXT PRIMARY KEY,
                    record_hash TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,
                    database_path TEXT NOT NULL,
                    contract_execution_event_id TEXT NOT NULL,
                    contract_execution_event_hash TEXT NOT NULL,
                    paid_work_authorization_id TEXT NOT NULL,
                    paid_work_authorization_hash TEXT NOT NULL,
                    assessment_execution_request_hash TEXT NOT NULL,
                    handoff_hash TEXT NOT NULL,
                    authorization_bridge_hash TEXT NOT NULL,
                    execution_evidence_binding_hash TEXT NOT NULL,
                    attempt_status TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    schema_version TEXT NOT NULL
                )
                """
            )

            connection.execute(
                f"""
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_paid_assessment_execution_attempt_hierarchy
                ON {EXECUTION_ATTEMPT_TABLE} (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id
                )
                """
            )

    def build_attempt(
        self,
        *,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        evidence_binding: RealPaidAssessmentExecutionEvidenceBinding,
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        handoff: PaidAssessmentExecutionHandoff,
        request: AssessmentExecutionRequest,
        recorded_at: datetime | None = None,
    ) -> RealPaidAssessmentExecutionAttempt:
        expected_hierarchy = handoff.hierarchy_key

        supplied_hierarchies = (
            authorization_bridge.hierarchy_key,
            evidence_binding.hierarchy_key,
            request.context.hierarchy_key,
        )

        if any(
            hierarchy != expected_hierarchy
            for hierarchy in supplied_hierarchies
        ):
            raise RealPaidAssessmentExecutionRecoveryError(
                "execution-attempt hierarchy inputs do not match"
            )

        if (
            paid_work_authorization.authorization_id
            != handoff.paid_work_authorization_id
        ):
            raise RealPaidAssessmentExecutionRecoveryError(
                "paid-work authorization identity does not match handoff"
            )

        if (
            paid_work_authorization.authorization_hash
            != handoff.paid_work_authorization_hash
        ):
            raise RealPaidAssessmentExecutionRecoveryError(
                "paid-work authorization hash does not match handoff"
            )

        request_hash = sha256_text(
            canonical_json(request.to_dict())
        )

        if (
            request_hash
            != handoff.assessment_execution_request_hash
        ):
            raise RealPaidAssessmentExecutionRecoveryError(
                "assessment execution request hash does not match handoff"
            )

        bridge_hash = sha256_text(
            canonical_json(
                authorization_bridge.to_dict()
            )
        )

        evidence_binding_hash = sha256_text(
            canonical_json(
                evidence_binding.to_dict()
            )
        )

        timestamp = (
            recorded_at
            or datetime.now(timezone.utc)
        ).isoformat()

        identity_payload = {
            "recovery_type": (
                REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_ID
            ),
            "version": (
                REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_VERSION
            ),
            "schema_version": (
                REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_SCHEMA_VERSION
            ),
            "tenant_id": handoff.tenant_id,
            "client_id": handoff.client_id,
            "engagement_id": handoff.engagement_id,
            "assessment_id": handoff.assessment_id,
            "hierarchy_key": handoff.hierarchy_key,
            "database_path": str(self._path),
            "contract_execution_event_id": (
                handoff.contract_execution_event_id
            ),
            "contract_execution_event_hash": (
                handoff.contract_execution_event_hash
            ),
            "paid_work_authorization_id": (
                handoff.paid_work_authorization_id
            ),
            "paid_work_authorization_hash": (
                handoff.paid_work_authorization_hash
            ),
            "assessment_execution_request_hash": (
                handoff.assessment_execution_request_hash
            ),
            "handoff_hash": handoff.handoff_hash,
            "authorization_bridge_hash": bridge_hash,
            "execution_evidence_binding_hash": (
                evidence_binding_hash
            ),
        }

        attempt_hash = sha256_text(
            canonical_json(identity_payload)
        )

        record_payload = {
            **identity_payload,
            "attempt_status": (
                EXECUTION_ATTEMPT_STATUS_RECORDED
            ),
            "recorded_at": timestamp,
            "attempt_hash": attempt_hash,
        }

        record_hash = sha256_text(
            canonical_json(record_payload)
        )

        return RealPaidAssessmentExecutionAttempt(
            tenant_id=handoff.tenant_id,
            client_id=handoff.client_id,
            engagement_id=handoff.engagement_id,
            assessment_id=handoff.assessment_id,
            database_path=str(self._path),
            contract_execution_event_id=(
                handoff.contract_execution_event_id
            ),
            contract_execution_event_hash=(
                handoff.contract_execution_event_hash
            ),
            paid_work_authorization_id=(
                handoff.paid_work_authorization_id
            ),
            paid_work_authorization_hash=(
                handoff.paid_work_authorization_hash
            ),
            assessment_execution_request_hash=(
                handoff.assessment_execution_request_hash
            ),
            handoff_hash=handoff.handoff_hash,
            authorization_bridge_hash=bridge_hash,
            execution_evidence_binding_hash=(
                evidence_binding_hash
            ),
            attempt_status=EXECUTION_ATTEMPT_STATUS_RECORDED,
            recorded_at=timestamp,
            attempt_hash=attempt_hash,
            record_hash=record_hash,
        )

    def record_attempt(
        self,
        *,
        attempt: RealPaidAssessmentExecutionAttempt,
    ) -> RealPaidAssessmentExecutionAttempt:
        self.initialize()

        existing = self.get_attempt_for_hierarchy(
            tenant_id=attempt.tenant_id,
            client_id=attempt.client_id,
            engagement_id=attempt.engagement_id,
            assessment_id=attempt.assessment_id,
        )

        if existing is not None:
            if existing.attempt_hash == attempt.attempt_hash:
                return existing

            raise RealPaidAssessmentExecutionAttemptConflictError(
                "existing execution attempt does not match "
                "requested execution attempt"
            )

        try:
            with sqlite3.connect(self._path) as connection:
                connection.execute(
                    f"""
                    INSERT INTO {EXECUTION_ATTEMPT_TABLE} (
                        attempt_hash,
                        record_hash,
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id,
                        database_path,
                        contract_execution_event_id,
                        contract_execution_event_hash,
                        paid_work_authorization_id,
                        paid_work_authorization_hash,
                        assessment_execution_request_hash,
                        handoff_hash,
                        authorization_bridge_hash,
                        execution_evidence_binding_hash,
                        attempt_status,
                        recorded_at,
                        schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt.attempt_hash,
                        attempt.record_hash,
                        attempt.tenant_id,
                        attempt.client_id,
                        attempt.engagement_id,
                        attempt.assessment_id,
                        attempt.database_path,
                        attempt.contract_execution_event_id,
                        attempt.contract_execution_event_hash,
                        attempt.paid_work_authorization_id,
                        attempt.paid_work_authorization_hash,
                        attempt.assessment_execution_request_hash,
                        attempt.handoff_hash,
                        attempt.authorization_bridge_hash,
                        attempt.execution_evidence_binding_hash,
                        attempt.attempt_status,
                        attempt.recorded_at,
                        attempt.schema_version,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise RealPaidAssessmentExecutionAttemptConflictError(
                "execution-attempt identity could not be recorded"
            ) from exc

        return attempt

    def attempt_table_exists(self) -> bool:
        if not self._path.exists():
            return False

        with sqlite3.connect(self._path) as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
                """,
                (EXECUTION_ATTEMPT_TABLE,),
            ).fetchone()

        return row is not None

    def get_attempt_for_hierarchy(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> RealPaidAssessmentExecutionAttempt | None:
        if not self._path.exists():
            return None

        self.initialize()

        with sqlite3.connect(self._path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                f"""
                SELECT *
                FROM {EXECUTION_ATTEMPT_TABLE}
                WHERE tenant_id = ?
                  AND client_id = ?
                  AND engagement_id = ?
                  AND assessment_id = ?
                """,
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._attempt_from_row(row)

    def _attempt_from_row(
        self,
        row: sqlite3.Row,
    ) -> RealPaidAssessmentExecutionAttempt:
        attempt = RealPaidAssessmentExecutionAttempt(
            tenant_id=str(row["tenant_id"]),
            client_id=str(row["client_id"]),
            engagement_id=str(row["engagement_id"]),
            assessment_id=str(row["assessment_id"]),
            database_path=str(row["database_path"]),
            contract_execution_event_id=str(
                row["contract_execution_event_id"]
            ),
            contract_execution_event_hash=str(
                row["contract_execution_event_hash"]
            ),
            paid_work_authorization_id=str(
                row["paid_work_authorization_id"]
            ),
            paid_work_authorization_hash=str(
                row["paid_work_authorization_hash"]
            ),
            assessment_execution_request_hash=str(
                row["assessment_execution_request_hash"]
            ),
            handoff_hash=str(row["handoff_hash"]),
            authorization_bridge_hash=str(
                row["authorization_bridge_hash"]
            ),
            execution_evidence_binding_hash=str(
                row["execution_evidence_binding_hash"]
            ),
            attempt_status=str(row["attempt_status"]),
            recorded_at=str(row["recorded_at"]),
            attempt_hash=str(row["attempt_hash"]),
            record_hash=str(row["record_hash"]),
            schema_version=str(row["schema_version"]),
        )

        serialized = attempt.to_dict()

        identity_payload = {
            key: value
            for key, value in serialized.items()
            if key not in {
                "attempt_status",
                "recorded_at",
                "attempt_hash",
                "record_hash",
                "boundaries",
            }
        }

        expected_attempt_hash = sha256_text(
            canonical_json(identity_payload)
        )

        if expected_attempt_hash != attempt.attempt_hash:
            raise RealPaidAssessmentExecutionRecoveryError(
                "stored execution-attempt identity hash "
                "verification failed"
            )

        record_payload = {
            key: value
            for key, value in serialized.items()
            if key not in {
                "record_hash",
                "boundaries",
            }
        }

        expected_record_hash = sha256_text(
            canonical_json(record_payload)
        )

        if expected_record_hash != attempt.record_hash:
            raise RealPaidAssessmentExecutionRecoveryError(
                "stored execution-attempt record hash "
                "verification failed"
            )

        return attempt

RECOVERY_DISPOSITION_EXECUTED = "executed"
RECOVERY_DISPOSITION_RESUMED = "resumed"
RECOVERY_DISPOSITION_RECONCILED = "reconciled"


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentExecutionRecoveryResult:
    attempt: RealPaidAssessmentExecutionAttempt
    execution_result: Any
    disposition: str
    artifact_count_before: int
    artifact_count_after: int

    recovery_type: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_ID
    )
    version: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_VERSION
    )
    schema_version: str = (
        REAL_PAID_ASSESSMENT_EXECUTION_RECOVERY_SCHEMA_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_type": self.recovery_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "attempt_hash": self.attempt.attempt_hash,
            "record_hash": self.attempt.record_hash,
            "hierarchy_key": self.attempt.hierarchy_key,
            "disposition": self.disposition,
            "artifact_count_before": self.artifact_count_before,
            "artifact_count_after": self.artifact_count_after,
            "execution_result": self.execution_result.to_dict(),
            "boundaries": {
                "recovery_is_not_second_execution_authority": True,
                "replay_is_not_duplicate_business_event": True,
                "artifact_reuse_is_not_new_artifact": True,
                "completion_is_not_customer_outcome": True,
                "sequential_recovery_is_not_distributed_exactly_once": True,
            },
        }


class GovernanceRealPaidAssessmentExecutionRecoveryService:
    """
    Reconcile or resume one exact governed paid-assessment execution attempt.

    Execution authority remains with the existing PA-001/PA-002 path.
    This service proves durable attempt identity before permitting an
    existing database to enter that path.
    """

    def execute(
        self,
        *,
        database_path: str | Path,
        intake: Any,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        evidence_binding: RealPaidAssessmentExecutionEvidenceBinding,
        contract_execution_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        request: AssessmentExecutionRequest,
        recorded_at: datetime | None = None,
    ) -> RealPaidAssessmentExecutionRecoveryResult:
        path = Path(database_path)
        database_existed = path.exists()

        handoff = (
            GovernancePaidAssessmentExecutionHandoffService()
            .build_handoff(
                contract_execution_event=contract_execution_event,
                paid_work_authorization=paid_work_authorization,
                assessment_execution_request=request,
            )
        )

        store = GovernanceRealPaidAssessmentExecutionAttemptStore(
            path
        )

        requested_attempt = store.build_attempt(
            authorization_bridge=authorization_bridge,
            evidence_binding=evidence_binding,
            paid_work_authorization=paid_work_authorization,
            handoff=handoff,
            request=request,
            recorded_at=recorded_at,
        )

        if database_existed:
            if not store.attempt_table_exists():
                raise RealPaidAssessmentExecutionRecoveryError(
                    "existing database has no governed "
                    "execution-attempt identity"
                )

            existing_attempt = store.get_attempt_for_hierarchy(
                tenant_id=requested_attempt.tenant_id,
                client_id=requested_attempt.client_id,
                engagement_id=requested_attempt.engagement_id,
                assessment_id=requested_attempt.assessment_id,
            )

            if existing_attempt is None:
                raise RealPaidAssessmentExecutionRecoveryError(
                    "existing database does not contain "
                    "the requested execution attempt"
                )

            if (
                existing_attempt.attempt_hash
                != requested_attempt.attempt_hash
            ):
                raise RealPaidAssessmentExecutionAttemptConflictError(
                    "existing execution attempt does not match "
                    "requested execution attempt"
                )

            durable_attempt = existing_attempt
        else:
            durable_attempt = store.record_attempt(
                attempt=requested_attempt
            )

        repository = GovernanceAssessmentRepository(path)

        artifacts_before = repository.list_artifacts(
            context=request.context
        )

        artifact_count_before = len(artifacts_before)

        expected_order = (
            GovernanceAssessmentDemonstrationPersistenceService
            .ARTIFACT_ORDER
        )

        existing_order = tuple(
            artifact.artifact_type
            for artifact in artifacts_before
        )

        expected_prefix = expected_order[
            :artifact_count_before
        ]

        if existing_order != expected_prefix:
            raise RealPaidAssessmentExecutionRecoveryError(
                "existing core artifacts are not an exact "
                "prefix of the governed artifact order"
            )

        if artifact_count_before > EXPECTED_CORE_ARTIFACT_COUNT:
            raise RealPaidAssessmentExecutionRecoveryError(
                "repository contains more than the expected "
                "ten core assessment artifacts"
            )

        if artifact_count_before:
            chain_valid_before = repository.verify_chain(
                context=request.context
            )

            if chain_valid_before is not True:
                raise RealPaidAssessmentExecutionRecoveryError(
                    "repository chain is invalid before recovery"
                )

        execution_result = (
            GovernanceRealPaidAssessmentExecutionService()
            .execute(
                database_path=path,
                intake=intake,
                authorization_bridge=authorization_bridge,
                evidence_binding=evidence_binding,
                contract_execution_event=contract_execution_event,
                paid_work_authorization=paid_work_authorization,
                request=request,
                allow_existing_database=True,
            )
        )

        artifacts_after = repository.list_artifacts(
            context=request.context
        )

        artifact_count_after = len(artifacts_after)

        if artifact_count_after != EXPECTED_CORE_ARTIFACT_COUNT:
            raise RealPaidAssessmentExecutionRecoveryError(
                "recovered execution did not produce exactly "
                "ten core artifacts"
            )

        chain_valid_after = repository.verify_chain(
            context=request.context
        )

        if chain_valid_after is not True:
            raise RealPaidAssessmentExecutionRecoveryError(
                "repository chain is invalid after recovery"
            )

        if not database_existed:
            disposition = RECOVERY_DISPOSITION_EXECUTED
        elif artifact_count_before < EXPECTED_CORE_ARTIFACT_COUNT:
            disposition = RECOVERY_DISPOSITION_RESUMED
        else:
            disposition = RECOVERY_DISPOSITION_RECONCILED

        return RealPaidAssessmentExecutionRecoveryResult(
            attempt=durable_attempt,
            execution_result=execution_result,
            disposition=disposition,
            artifact_count_before=artifact_count_before,
            artifact_count_after=artifact_count_after,
        )