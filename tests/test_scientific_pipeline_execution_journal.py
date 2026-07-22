from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_ID,
    SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_VERSION,
    SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_ID,
    SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_VERSION,
    ScientificPipelineExecutionConflictError,
    ScientificPipelineExecutionJournal,
    ScientificPipelineExecutionState,
    ScientificPipelineRecoveryCoordinator,
)


def complete_evidence() -> AuthorityEscalationEvidence:
    return AuthorityEscalationEvidence(
        deterministic_replay_verified=True,
        canonical_input_binding_verified=True,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=True,
    )


def build_coordinator(
    tmp_path,
    *,
    stage_hook=None,
):
    return ScientificPipelineRecoveryCoordinator(
        authority_database_path=tmp_path / "authority.db",
        audit_database_path=tmp_path / "audit.db",
        checkpoint_database_path=tmp_path / "checkpoint.db",
        journal_database_path=tmp_path / "journal.db",
        stage_hook=stage_hook,
    )


class FailOnceAtStage:
    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.triggered = False

    def __call__(self, current_stage: str) -> None:
        if (
            current_stage == self.stage
            and not self.triggered
        ):
            self.triggered = True
            raise RuntimeError(
                f"Injected failure at {current_stage}"
            )


def test_journal_and_coordinator_have_stable_identity():
    assert SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_ID == (
        "scientific-pipeline-execution-journal"
    )
    assert SCIENTIFIC_PIPELINE_EXECUTION_JOURNAL_VERSION == (
        "0.1.0"
    )
    assert SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_ID == (
        "scientific-pipeline-recovery-coordinator"
    )
    assert SCIENTIFIC_PIPELINE_RECOVERY_COORDINATOR_VERSION == (
        "0.1.0"
    )


def test_journal_begin_creates_started_record(tmp_path):
    journal = ScientificPipelineExecutionJournal(
        tmp_path / "journal.db"
    )

    record = journal.begin(
        execution_id="execution-1",
        request_hash="request-1",
    )

    assert record.state == ScientificPipelineExecutionState.STARTED
    assert record.transition_count == 1
    assert journal.count() == 1


def test_journal_begin_is_idempotent(tmp_path):
    journal = ScientificPipelineExecutionJournal(
        tmp_path / "journal.db"
    )

    first = journal.begin(
        execution_id="execution-1",
        request_hash="request-1",
    )
    second = journal.begin(
        execution_id="execution-1",
        request_hash="request-1",
    )

    assert first == second
    assert journal.count() == 1
    assert len(
        journal.list_transitions("execution-1")
    ) == 1


def test_conflicting_request_hash_is_rejected(tmp_path):
    journal = ScientificPipelineExecutionJournal(
        tmp_path / "journal.db"
    )
    journal.begin(
        execution_id="execution-1",
        request_hash="request-1",
    )

    with pytest.raises(
        ScientificPipelineExecutionConflictError,
        match="different request hash",
    ):
        journal.begin(
            execution_id="execution-1",
            request_hash="request-2",
        )


def test_transitions_are_append_only_and_ordered(tmp_path):
    journal = ScientificPipelineExecutionJournal(
        tmp_path / "journal.db"
    )
    journal.begin(
        execution_id="execution-1",
        request_hash="request-1",
    )
    journal.transition(
        execution_id="execution-1",
        state=(
            ScientificPipelineExecutionState.AUTHORITY_RECORDED
        ),
        details={"receipt_hash": "authority"},
    )
    journal.transition(
        execution_id="execution-1",
        state=ScientificPipelineExecutionState.COMPLETED,
        details={"receipt_hash": "execution"},
    )

    transitions = journal.list_transitions("execution-1")

    assert [
        transition.state
        for transition in transitions
    ] == [
        ScientificPipelineExecutionState.STARTED,
        ScientificPipelineExecutionState.AUTHORITY_RECORDED,
        ScientificPipelineExecutionState.COMPLETED,
    ]
    assert [
        transition.transition_sequence
        for transition in transitions
    ] == [1, 2, 3]


def test_complete_execution_reaches_completed_state(tmp_path):
    coordinator = build_coordinator(tmp_path)

    result = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    journal_record = coordinator.journal.get(
        result.execution_id
    )

    assert journal_record is not None
    assert journal_record.state == (
        ScientificPipelineExecutionState.COMPLETED
    )
    assert result.resumed is False
    assert result.execution_receipt.verify() is True


def test_complete_execution_persists_all_layers(tmp_path):
    coordinator = build_coordinator(tmp_path)

    coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 1
    assert coordinator.journal.count() == 1


def test_repeated_completed_execution_is_idempotent(tmp_path):
    coordinator = build_coordinator(tmp_path)

    first = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    first_transition_count = len(
        coordinator.journal.list_transitions(
            first.execution_id
        )
    )

    second = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    second_transition_count = len(
        coordinator.journal.list_transitions(
            second.execution_id
        )
    )

    assert first.execution_id == second.execution_id
    assert first.execution_receipt == second.execution_receipt
    assert second.resumed is True
    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 1
    assert first_transition_count == second_transition_count


def test_failure_after_authority_is_recorded(tmp_path):
    failure = FailOnceAtStage("authority_persisted")
    coordinator = build_coordinator(
        tmp_path,
        stage_hook=failure,
    )

    with pytest.raises(
        RuntimeError,
        match="authority_persisted",
    ):
        coordinator.execute(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=(
                CalculationAuthority.ADVISORY
            ),
            evidence=complete_evidence(),
        )

    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 0
    assert coordinator.checkpoint_ledger.count() == 0
    assert coordinator.journal.count() == 1

    with coordinator.journal._connect() as connection:
        row = connection.execute(
            """
            SELECT execution_id
            FROM scientific_pipeline_executions
            """
        ).fetchone()

    record = coordinator.journal.get(row["execution_id"])

    assert record is not None
    assert record.state == (
        ScientificPipelineExecutionState.FAILED
    )
    assert record.details["error_type"] == "RuntimeError"

def test_failure_after_authority_can_resume(tmp_path):
    failure = FailOnceAtStage("authority_persisted")
    coordinator = build_coordinator(
        tmp_path,
        stage_hook=failure,
    )

    with pytest.raises(RuntimeError):
        coordinator.execute(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=(
                CalculationAuthority.ADVISORY
            ),
            evidence=complete_evidence(),
        )

    recovered = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert recovered.resumed is True
    assert recovered.execution_receipt.verify() is True
    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 1

    journal_record = coordinator.journal.get(
        recovered.execution_id
    )
    assert journal_record is not None
    assert journal_record.state == (
        ScientificPipelineExecutionState.COMPLETED
    )


def test_failure_after_audit_can_resume(tmp_path):
    failure = FailOnceAtStage("audit_persisted")
    coordinator = build_coordinator(
        tmp_path,
        stage_hook=failure,
    )

    with pytest.raises(RuntimeError):
        coordinator.execute(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=(
                CalculationAuthority.ADVISORY
            ),
            evidence=complete_evidence(),
        )

    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 0

    recovered = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert recovered.resumed is True
    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 1


def test_failure_after_checkpoint_can_resume(tmp_path):
    failure = FailOnceAtStage("checkpoint_persisted")
    coordinator = build_coordinator(
        tmp_path,
        stage_hook=failure,
    )

    with pytest.raises(RuntimeError):
        coordinator.execute(
            contract=EVIDENCE_CONFIDENCE_CONTRACT,
            requested_authority=(
                CalculationAuthority.ADVISORY
            ),
            evidence=complete_evidence(),
        )

    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 1

    recovered = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert recovered.resumed is True
    assert coordinator.authority_ledger.count() == 1
    assert coordinator.audit_ledger.count() == 1
    assert coordinator.checkpoint_ledger.count() == 1


def test_denied_decision_completes_recovery_pipeline(tmp_path):
    coordinator = build_coordinator(tmp_path)

    result = coordinator.execute(
        contract=LEGACY_METRIC_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert result.pipeline_result.decision_allowed is False
    assert result.pipeline_result.checkpoint_valid is True
    assert result.execution_receipt.verify() is True


def test_distinct_requests_receive_distinct_execution_ids(
    tmp_path,
):
    coordinator = build_coordinator(tmp_path)

    advisory = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )
    authoritative = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=(
            CalculationAuthority.AUTHORITATIVE
        ),
        evidence=complete_evidence(),
    )

    assert advisory.execution_id != authoritative.execution_id
    assert coordinator.journal.count() == 2


def test_recovery_result_is_immutable(tmp_path):
    coordinator = build_coordinator(tmp_path)

    result = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    with pytest.raises(FrozenInstanceError):
        result.resumed = True


def test_completed_journal_binds_all_final_hashes(tmp_path):
    coordinator = build_coordinator(tmp_path)

    result = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    record = coordinator.journal.get(result.execution_id)

    assert record is not None
    assert record.details["execution_receipt_hash"] == (
        result.execution_receipt.receipt_hash
    )
    assert record.details["authority_receipt_hash"] == (
        result.pipeline_result.authority_receipt_hash
    )
    assert record.details["audit_receipt_hash"] == (
        result.pipeline_result.audit_receipt_hash
    )
    assert record.details["checkpoint_hash"] == (
        result.pipeline_result.checkpoint_hash
    )

