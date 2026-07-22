import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from backend.app.gagf.scientific_authority_audit_receipt_ledger import (
    ScientificAuthorityAuditReceiptLedger,
)
from backend.app.gagf.scientific_authority_evidence_pipeline import (
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID,
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION,
    ScientificAuthorityEvidencePipelineResult,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_authority_ledger_audit_receipt import (
    ScientificAuthorityLedgerAuditReceiptBuilder,
)
from backend.app.gagf.scientific_authority_ledger_auditor import (
    ScientificAuthorityLedgerIntegrityAuditor,
)
from backend.app.gagf.scientific_authority_receipt_ledger import (
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    ScientificCalculationContract,
)
from backend.app.gagf.scientific_evidence_checkpoint import (
    ScientificEvidenceCheckpointBuilder,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    ScientificEvidenceCheckpointLedger,
)
from backend.app.gagf.scientific_pipeline_execution_receipt import (
    ScientificPipelineExecutionReceipt,
    ScientificPipelineExecutionReceiptBuilder,
)


SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_ID = (
    "scientific-pipeline-execution-journal"
)
SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_VERSION = "0.1.0"

SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_ID = (
    "scientific-pipeline-recovery-coordinator"
)
SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_VERSION = "0.1.0"


class ScientificPipelineExecutionState(str, Enum):
    STARTED = "STARTED"
    AUTHORITY_RECORDED = "AUTHORITY_RECORDED"
    AUDIT_RECORDED = "AUDIT_RECORDED"
    CHECKPOINT_RECORDED = "CHECKPOINT_RECORDED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScientificPipelineExecutionJournalError(RuntimeError):
    pass


class ScientificPipelineExecutionConflictError(
    ScientificPipelineExecutionJournalError
):
    pass


@dataclass(frozen=True, slots=True)
class ScientificPipelineJournalRecord:
    execution_id: str
    request_hash: str
    state: ScientificPipelineExecutionState
    details: dict
    transition_count: int

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "request_hash": self.request_hash,
            "state": self.state.value,
            "details": dict(self.details),
            "transition_count": self.transition_count,
        }


@dataclass(frozen=True, slots=True)
class ScientificPipelineJournalTransition:
    transition_sequence: int
    execution_id: str
    state: ScientificPipelineExecutionState
    details: dict

    def to_dict(self) -> dict:
        return {
            "transition_sequence": self.transition_sequence,
            "execution_id": self.execution_id,
            "state": self.state.value,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class RecoverableScientificPipelineResult:
    coordinator_id: str
    coordinator_version: str
    execution_id: str
    resumed: bool
    pipeline_result: ScientificAuthorityEvidencePipelineResult
    execution_receipt: ScientificPipelineExecutionReceipt

    def to_dict(self) -> dict:
        return {
            "coordinator_id": self.coordinator_id,
            "coordinator_version": self.coordinator_version,
            "execution_id": self.execution_id,
            "resumed": self.resumed,
            "pipeline_result": self.pipeline_result.to_dict(),
            "execution_receipt": self.execution_receipt.to_dict(),
        }


class ScientificPipelineExecutionJournal:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)

        Path(self.database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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
                scientific_pipeline_executions (
                    execution_id TEXT PRIMARY KEY,
                    request_hash TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    current_details_json TEXT NOT NULL,
                    transition_count INTEGER NOT NULL,
                    CHECK (transition_count >= 1)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                scientific_pipeline_execution_transitions (
                    transition_sequence
                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY (execution_id)
                        REFERENCES scientific_pipeline_executions(
                            execution_id
                        )
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scientific_pipeline_transitions_execution
                ON scientific_pipeline_execution_transitions (
                    execution_id,
                    transition_sequence
                )
                """
            )

    def begin(
        self,
        *,
        execution_id: str,
        request_hash: str,
    ) -> ScientificPipelineJournalRecord:
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    execution_id,
                    request_hash,
                    current_state,
                    current_details_json,
                    transition_count
                FROM scientific_pipeline_executions
                WHERE execution_id = ?
                """,
                (execution_id,),
            ).fetchone()

            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise ScientificPipelineExecutionConflictError(
                        "Execution ID already exists with a "
                        "different request hash."
                    )

                return self._record_from_row(existing)

            details = {
                "journal_id": (
                    SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_ID
                ),
                "journal_version": (
                    SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_VERSION
                ),
            }
            serialized_details = canonical_json(details)

            connection.execute(
                """
                INSERT INTO scientific_pipeline_executions (
                    execution_id,
                    request_hash,
                    current_state,
                    current_details_json,
                    transition_count
                )
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    execution_id,
                    request_hash,
                    ScientificPipelineExecutionState.STARTED.value,
                    serialized_details,
                ),
            )

            connection.execute(
                """
                INSERT INTO
                scientific_pipeline_execution_transitions (
                    execution_id,
                    state,
                    details_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    execution_id,
                    ScientificPipelineExecutionState.STARTED.value,
                    serialized_details,
                ),
            )

        record = self.get(execution_id)

        if record is None:
            raise ScientificPipelineExecutionJournalError(
                "Execution journal failed to create a record."
            )

        return record

    def transition(
        self,
        *,
        execution_id: str,
        state: ScientificPipelineExecutionState,
        details: dict,
    ) -> ScientificPipelineJournalRecord:
        serialized_details = canonical_json(details)

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    execution_id,
                    request_hash,
                    current_state,
                    current_details_json,
                    transition_count
                FROM scientific_pipeline_executions
                WHERE execution_id = ?
                """,
                (execution_id,),
            ).fetchone()

            if existing is None:
                raise ScientificPipelineExecutionJournalError(
                    "Cannot transition an unknown execution."
                )

            if (
                existing["current_state"] == state.value
                and existing["current_details_json"]
                == serialized_details
            ):
                return self._record_from_row(existing)

            connection.execute(
                """
                INSERT INTO
                scientific_pipeline_execution_transitions (
                    execution_id,
                    state,
                    details_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    execution_id,
                    state.value,
                    serialized_details,
                ),
            )

            connection.execute(
                """
                UPDATE scientific_pipeline_executions
                SET
                    current_state = ?,
                    current_details_json = ?,
                    transition_count = transition_count + 1
                WHERE execution_id = ?
                """,
                (
                    state.value,
                    serialized_details,
                    execution_id,
                ),
            )

        record = self.get(execution_id)

        if record is None:
            raise ScientificPipelineExecutionJournalError(
                "Execution disappeared after transition."
            )

        return record

    def fail(
        self,
        *,
        execution_id: str,
        error: Exception,
    ) -> ScientificPipelineJournalRecord:
        return self.transition(
            execution_id=execution_id,
            state=ScientificPipelineExecutionState.FAILED,
            details={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    def get(
        self,
        execution_id: str,
    ) -> ScientificPipelineJournalRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    execution_id,
                    request_hash,
                    current_state,
                    current_details_json,
                    transition_count
                FROM scientific_pipeline_executions
                WHERE execution_id = ?
                """,
                (execution_id,),
            ).fetchone()

        if row is None:
            return None

        return self._record_from_row(row)

    def list_transitions(
        self,
        execution_id: str,
    ) -> tuple[ScientificPipelineJournalTransition, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    transition_sequence,
                    execution_id,
                    state,
                    details_json
                FROM scientific_pipeline_execution_transitions
                WHERE execution_id = ?
                ORDER BY transition_sequence ASC
                """,
                (execution_id,),
            ).fetchall()

        return tuple(
            ScientificPipelineJournalTransition(
                transition_sequence=row["transition_sequence"],
                execution_id=row["execution_id"],
                state=ScientificPipelineExecutionState(
                    row["state"]
                ),
                details=json.loads(row["details_json"]),
            )
            for row in rows
        )

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS record_count
                FROM scientific_pipeline_executions
                """
            ).fetchone()

        return int(row["record_count"])

    def _record_from_row(
        self,
        row: sqlite3.Row,
    ) -> ScientificPipelineJournalRecord:
        return ScientificPipelineJournalRecord(
            execution_id=row["execution_id"],
            request_hash=row["request_hash"],
            state=ScientificPipelineExecutionState(
                row["current_state"]
            ),
            details=json.loads(
                row["current_details_json"]
            ),
            transition_count=row["transition_count"],
        )


class ScientificPipelineRecoveryCoordinator:
    def __init__(
        self,
        *,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
        checkpoint_database_path: str | Path,
        journal_database_path: str | Path,
        stage_hook: Callable[[str], None] | None = None,
    ) -> None:
        self.authority_database_path = Path(
            authority_database_path
        )
        self.audit_database_path = Path(
            audit_database_path
        )
        self.checkpoint_database_path = Path(
            checkpoint_database_path
        )
        self.journal_database_path = Path(
            journal_database_path
        )
        self.stage_hook = stage_hook

        for path in (
            self.authority_database_path,
            self.audit_database_path,
            self.checkpoint_database_path,
            self.journal_database_path,
        ):
            path.parent.mkdir(parents=True, exist_ok=True)

        self.authority_ledger = ScientificAuthorityReceiptLedger(
            self.authority_database_path
        )
        self.audit_ledger = ScientificAuthorityAuditReceiptLedger(
            self.audit_database_path
        )
        self.checkpoint_ledger = ScientificEvidenceCheckpointLedger(
            self.checkpoint_database_path
        )
        self.journal = ScientificPipelineExecutionJournal(
            self.journal_database_path
        )

    def execute(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
    ) -> RecoverableScientificPipelineResult:
        request_payload = self._request_payload(
            contract=contract,
            requested_authority=requested_authority,
            evidence=evidence,
        )
        request_hash = sha256_hex(
            canonical_json(request_payload)
        )
        execution_id = sha256_hex(
            canonical_json(
                {
                    "execution_type": (
                        SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_ID
                    ),
                    "request_hash": request_hash,
                }
            )
        )

        existing = self.journal.get(execution_id)
        resumed = existing is not None

        journal_record = self.journal.begin(
            execution_id=execution_id,
            request_hash=request_hash,
        )
        journal_updates_enabled = (
            journal_record.state
            != ScientificPipelineExecutionState.COMPLETED
        )

        try:
            _, authority_receipt = (
                ScientificAuthorityEscalationGuard()
                .evaluate_with_receipt(
                    contract=contract,
                    requested_authority=requested_authority,
                    evidence=evidence,
                )
            )

            authority_record = self.authority_ledger.append(
                authority_receipt
            )
            self._invoke_stage_hook("authority_persisted")

            if journal_updates_enabled:
                self.journal.transition(
                    execution_id=execution_id,
                    state=(
                        ScientificPipelineExecutionState
                        .AUTHORITY_RECORDED
                    ),
                    details={
                        "sequence_number": (
                            authority_record.sequence_number
                        ),
                        "receipt_hash": (
                            authority_receipt.receipt_hash
                        ),
                    },
                )

            authority_audit = (
                ScientificAuthorityLedgerIntegrityAuditor()
                .audit(self.authority_database_path)
            )
            audit_receipt = (
                ScientificAuthorityLedgerAuditReceiptBuilder()
                .build(authority_audit)
            )
            audit_record = self.audit_ledger.append(
                audit_receipt
            )
            self._invoke_stage_hook("audit_persisted")

            if journal_updates_enabled:
                self.journal.transition(
                    execution_id=execution_id,
                    state=(
                        ScientificPipelineExecutionState
                        .AUDIT_RECORDED
                    ),
                    details={
                        "sequence_number": (
                            audit_record.sequence_number
                        ),
                        "receipt_hash": audit_receipt.receipt_hash,
                        "authority_audit_valid": (
                            authority_audit.valid
                        ),
                    },
                )

            checkpoint = ScientificEvidenceCheckpointBuilder().build(
                authority_database_path=(
                    self.authority_database_path
                ),
                audit_database_path=self.audit_database_path,
            )
            checkpoint_record = self.checkpoint_ledger.append(
                checkpoint=checkpoint,
                authority_database_path=(
                    self.authority_database_path
                ),
                audit_database_path=self.audit_database_path,
            )
            self._invoke_stage_hook("checkpoint_persisted")

            if journal_updates_enabled:
                self.journal.transition(
                    execution_id=execution_id,
                    state=(
                        ScientificPipelineExecutionState
                        .CHECKPOINT_RECORDED
                    ),
                    details={
                        "sequence_number": (
                            checkpoint_record.sequence_number
                        ),
                        "checkpoint_hash": (
                            checkpoint.checkpoint_hash
                        ),
                        "checkpoint_valid": checkpoint.valid,
                    },
                )

            pipeline_result = (
                ScientificAuthorityEvidencePipelineResult(
                    pipeline_id=(
                        SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID
                    ),
                    pipeline_version=(
                        SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION
                    ),
                    calculation_id=contract.calculation_id,
                    calculation_version=(
                        contract.calculation_version
                    ),
                    requested_authority=(
                        requested_authority.value
                    ),
                    decision_allowed=bool(
                        authority_receipt.decision["allowed"]
                    ),
                    authority_receipt_sequence=(
                        authority_record.sequence_number
                    ),
                    authority_receipt_hash=(
                        authority_receipt.receipt_hash
                    ),
                    authority_ledger_audit_valid=(
                        authority_audit.valid
                    ),
                    audit_receipt_sequence=(
                        audit_record.sequence_number
                    ),
                    audit_receipt_hash=(
                        audit_receipt.receipt_hash
                    ),
                    checkpoint_sequence=(
                        checkpoint_record.sequence_number
                    ),
                    checkpoint_hash=(
                        checkpoint.checkpoint_hash
                    ),
                    checkpoint_valid=checkpoint.valid,
                )
            )

            execution_receipt = (
                ScientificPipelineExecutionReceiptBuilder()
                .build(
                    contract=contract,
                    requested_authority=requested_authority,
                    evidence=evidence,
                    pipeline_result=pipeline_result,
                )
            )
            self._invoke_stage_hook("execution_receipt_built")

            if journal_updates_enabled:
                self.journal.transition(
                    execution_id=execution_id,
                    state=(
                        ScientificPipelineExecutionState.COMPLETED
                    ),
                    details={
                        "execution_receipt_hash": (
                            execution_receipt.receipt_hash
                        ),
                        "authority_receipt_hash": (
                            authority_receipt.receipt_hash
                        ),
                        "audit_receipt_hash": (
                            audit_receipt.receipt_hash
                        ),
                        "checkpoint_hash": (
                            checkpoint.checkpoint_hash
                        ),
                    },
                )

            return RecoverableScientificPipelineResult(
                coordinator_id=(
                    SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_ID
                ),
                coordinator_version=(
                    SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_VERSION
                ),
                execution_id=execution_id,
                resumed=resumed,
                pipeline_result=pipeline_result,
                execution_receipt=execution_receipt,
            )
        except Exception as exc:
            self.journal.fail(
                execution_id=execution_id,
                error=exc,
            )
            raise

    def _invoke_stage_hook(self, stage: str) -> None:
        if self.stage_hook is not None:
            self.stage_hook(stage)

    def _request_payload(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
    ) -> dict:
        return {
            "calculation_id": contract.calculation_id,
            "calculation_version": (
                contract.calculation_version
            ),
            "requested_authority": requested_authority.value,
            "evidence": {
                "deterministic_replay_verified": (
                    evidence.deterministic_replay_verified
                ),
                "canonical_input_binding_verified": (
                    evidence.canonical_input_binding_verified
                ),
                "calculation_version_frozen": (
                    evidence.calculation_version_frozen
                ),
                "regression_suite_passed": (
                    evidence.regression_suite_passed
                ),
                "validation_report_present": (
                    evidence.validation_report_present
                ),
                "constitutional_approval_present": (
                    evidence.constitutional_approval_present
                ),
            },
        }
