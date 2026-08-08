from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_intervention_actuation_journal import (
    GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_ID,
    GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_VERSION,
    GovernanceInterventionActuationConflictError,
    GovernanceInterventionActuationJournal,
    GovernanceInterventionActuationJournalError,
    GovernanceInterventionActuationState,
    GovernanceInterventionActuationTransitionError,
)


def _journal(tmp_path):
    return GovernanceInterventionActuationJournal(
        tmp_path / "actuation-journal.sqlite3"
    )


def _begin(
    journal,
    *,
    tenant_id="tenant-a",
    contract_hash="contract-hash-001",
    idempotency_key="actuation-001",
    details=None,
):
    return journal.begin(
        tenant_id=tenant_id,
        contract_hash=contract_hash,
        idempotency_key=idempotency_key,
        details=details,
    )


def test_journal_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_ID
        == "governance-intervention-actuation-journal"
    )
    assert (
        GOVERNANCE_INTERVENTION_ACTUATION_JOURNAL_VERSION
        == "0.1.0"
    )


def test_begin_creates_accepted_actuation(tmp_path):
    journal = _journal(tmp_path)

    record = _begin(
        journal,
        details={"adapter_id": "test-adapter"},
    )

    assert record.tenant_id == "tenant-a"
    assert record.contract_hash == "contract-hash-001"
    assert record.idempotency_key == "actuation-001"
    assert (
        record.current_state
        is GovernanceInterventionActuationState.ACCEPTED
    )
    assert record.transition_count == 1
    assert record.details == {
        "adapter_id": "test-adapter",
    }


def test_actuation_id_is_deterministic():
    first = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id="tenant-a",
            contract_hash="contract-hash-001",
            idempotency_key="actuation-001",
        )
    )

    second = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id="tenant-a",
            contract_hash="contract-hash-001",
            idempotency_key="actuation-001",
        )
    )

    assert first == second
    assert len(first) == 64


def test_actuation_id_changes_with_contract():
    first = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id="tenant-a",
            contract_hash="contract-hash-001",
            idempotency_key="actuation-001",
        )
    )

    second = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id="tenant-a",
            contract_hash="contract-hash-002",
            idempotency_key="actuation-001",
        )
    )

    assert first != second


def test_actuation_id_changes_with_tenant():
    first = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id="tenant-a",
            contract_hash="contract-hash-001",
            idempotency_key="actuation-001",
        )
    )

    second = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id="tenant-b",
            contract_hash="contract-hash-001",
            idempotency_key="actuation-001",
        )
    )

    assert first != second


def test_begin_is_idempotent_for_same_request(tmp_path):
    journal = _journal(tmp_path)

    first = _begin(journal)
    second = _begin(journal)

    assert first == second
    assert first.transition_count == 1

    transitions = journal.list_transitions(
        first.actuation_id
    )

    assert len(transitions) == 1
    assert (
        transitions[0].state
        is GovernanceInterventionActuationState.ACCEPTED
    )


def test_same_tenant_and_key_cannot_bind_different_contract(
    tmp_path,
):
    journal = _journal(tmp_path)

    _begin(
        journal,
        contract_hash="contract-hash-001",
        idempotency_key="same-key",
    )

    with pytest.raises(
        GovernanceInterventionActuationConflictError
    ):
        _begin(
            journal,
            contract_hash="contract-hash-002",
            idempotency_key="same-key",
        )


def test_same_idempotency_key_isolated_by_tenant(tmp_path):
    journal = _journal(tmp_path)

    first = _begin(
        journal,
        tenant_id="tenant-a",
        idempotency_key="shared-key",
    )

    second = _begin(
        journal,
        tenant_id="tenant-b",
        idempotency_key="shared-key",
    )

    assert first.actuation_id != second.actuation_id
    assert first.tenant_id == "tenant-a"
    assert second.tenant_id == "tenant-b"


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("tenant_id", ""),
        ("tenant_id", "   "),
        ("contract_hash", ""),
        ("contract_hash", "   "),
        ("idempotency_key", ""),
        ("idempotency_key", "   "),
    ),
)
def test_begin_requires_identifiers(
    tmp_path,
    field_name,
    value,
):
    journal = _journal(tmp_path)

    kwargs = {
        "tenant_id": "tenant-a",
        "contract_hash": "contract-hash-001",
        "idempotency_key": "actuation-001",
    }

    kwargs[field_name] = value

    with pytest.raises(
        GovernanceInterventionActuationJournalError
    ):
        journal.begin(**kwargs)


def test_begin_normalizes_identifiers(tmp_path):
    journal = _journal(tmp_path)

    record = journal.begin(
        tenant_id="  tenant-a  ",
        contract_hash="  contract-hash-001  ",
        idempotency_key="  actuation-001  ",
    )

    assert record.tenant_id == "tenant-a"
    assert record.contract_hash == "contract-hash-001"
    assert record.idempotency_key == "actuation-001"


def test_accepted_can_transition_to_started_and_completed(
    tmp_path,
):
    journal = _journal(tmp_path)
    record = _begin(journal)

    started = journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
        details={"attempt": 1},
    )

    assert (
        started.current_state
        is GovernanceInterventionActuationState.STARTED
    )
    assert started.transition_count == 2

    completed = journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.COMPLETED,
        details={"adapter_result": "completed"},
    )

    assert (
        completed.current_state
        is GovernanceInterventionActuationState.COMPLETED
    )
    assert completed.transition_count == 3


def test_accepted_can_abort_before_start(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    aborted = journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.ABORTED,
        details={"reason": "precondition_failed"},
    )

    assert (
        aborted.current_state
        is GovernanceInterventionActuationState.ABORTED
    )
    assert aborted.transition_count == 2


def test_started_can_fail_and_require_rollback(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
    )

    failed = journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.FAILED,
        details={"reason": "adapter_failure"},
    )

    assert (
        failed.current_state
        is GovernanceInterventionActuationState.FAILED
    )

    rollback_required = journal.transition(
        actuation_id=record.actuation_id,
        state=(
            GovernanceInterventionActuationState
            .ROLLBACK_REQUIRED
        ),
    )

    assert (
        rollback_required.current_state
        is GovernanceInterventionActuationState
        .ROLLBACK_REQUIRED
    )

    rolled_back = journal.transition(
        actuation_id=record.actuation_id,
        state=(
            GovernanceInterventionActuationState
            .ROLLED_BACK
        ),
    )

    assert (
        rolled_back.current_state
        is GovernanceInterventionActuationState
        .ROLLED_BACK
    )


def test_started_can_require_rollback_directly(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
    )

    rollback_required = journal.transition(
        actuation_id=record.actuation_id,
        state=(
            GovernanceInterventionActuationState
            .ROLLBACK_REQUIRED
        ),
        details={"reason": "abort_criterion_triggered"},
    )

    assert (
        rollback_required.current_state
        is GovernanceInterventionActuationState
        .ROLLBACK_REQUIRED
    )


@pytest.mark.parametrize(
    "terminal_state",
    (
        GovernanceInterventionActuationState.COMPLETED,
        GovernanceInterventionActuationState.ABORTED,
        GovernanceInterventionActuationState.ROLLED_BACK,
    ),
)
def test_terminal_states_reject_further_transition(
    tmp_path,
    terminal_state,
):
    journal = _journal(tmp_path)
    record = _begin(journal)

    if (
        terminal_state
        is GovernanceInterventionActuationState.COMPLETED
    ):
        journal.transition(
            actuation_id=record.actuation_id,
            state=GovernanceInterventionActuationState.STARTED,
        )
        journal.transition(
            actuation_id=record.actuation_id,
            state=terminal_state,
        )

    elif (
        terminal_state
        is GovernanceInterventionActuationState.ABORTED
    ):
        journal.transition(
            actuation_id=record.actuation_id,
            state=terminal_state,
        )

    else:
        journal.transition(
            actuation_id=record.actuation_id,
            state=GovernanceInterventionActuationState.STARTED,
        )
        journal.transition(
            actuation_id=record.actuation_id,
            state=(
                GovernanceInterventionActuationState
                .ROLLBACK_REQUIRED
            ),
        )
        journal.transition(
            actuation_id=record.actuation_id,
            state=terminal_state,
        )

    with pytest.raises(
        GovernanceInterventionActuationTransitionError
    ):
        journal.transition(
            actuation_id=record.actuation_id,
            state=GovernanceInterventionActuationState.STARTED,
        )


def test_illegal_transition_is_rejected(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    with pytest.raises(
        GovernanceInterventionActuationTransitionError
    ):
        journal.transition(
            actuation_id=record.actuation_id,
            state=GovernanceInterventionActuationState.COMPLETED,
        )


def test_same_state_transition_is_idempotent(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    started = journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
        details={"attempt": 1},
    )

    repeated = journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
        details={"attempt": 99},
    )

    assert repeated == started
    assert repeated.transition_count == 2
    assert repeated.details == {"attempt": 1}

    transitions = journal.list_transitions(
        record.actuation_id
    )

    assert len(transitions) == 2


def test_unknown_actuation_cannot_transition(tmp_path):
    journal = _journal(tmp_path)

    with pytest.raises(
        GovernanceInterventionActuationJournalError
    ):
        journal.transition(
            actuation_id="missing-actuation",
            state=GovernanceInterventionActuationState.STARTED,
        )


def test_transition_history_is_ordered(tmp_path):
    journal = _journal(tmp_path)

    record = _begin(
        journal,
        details={"stage": "accepted"},
    )

    journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
        details={"stage": "started"},
    )

    journal.transition(
        actuation_id=record.actuation_id,
        state=GovernanceInterventionActuationState.FAILED,
        details={"stage": "failed"},
    )

    journal.transition(
        actuation_id=record.actuation_id,
        state=(
            GovernanceInterventionActuationState
            .ROLLBACK_REQUIRED
        ),
        details={"stage": "rollback-required"},
    )

    journal.transition(
        actuation_id=record.actuation_id,
        state=(
            GovernanceInterventionActuationState
            .ROLLED_BACK
        ),
        details={"stage": "rolled-back"},
    )

    transitions = journal.list_transitions(
        record.actuation_id
    )

    assert tuple(
        transition.state
        for transition in transitions
    ) == (
        GovernanceInterventionActuationState.ACCEPTED,
        GovernanceInterventionActuationState.STARTED,
        GovernanceInterventionActuationState.FAILED,
        GovernanceInterventionActuationState
        .ROLLBACK_REQUIRED,
        GovernanceInterventionActuationState.ROLLED_BACK,
    )

    assert tuple(
        transition.transition_sequence
        for transition in transitions
    ) == tuple(
        sorted(
            transition.transition_sequence
            for transition in transitions
        )
    )


def test_journal_persists_across_instances(tmp_path):
    database_path = (
        tmp_path / "actuation-journal.sqlite3"
    )

    first_journal = (
        GovernanceInterventionActuationJournal(
            database_path
        )
    )

    created = _begin(first_journal)

    first_journal.transition(
        actuation_id=created.actuation_id,
        state=GovernanceInterventionActuationState.STARTED,
        details={"attempt": 1},
    )

    second_journal = (
        GovernanceInterventionActuationJournal(
            database_path
        )
    )

    restored = second_journal.get(
        created.actuation_id
    )

    assert restored is not None
    assert restored.actuation_id == created.actuation_id
    assert (
        restored.current_state
        is GovernanceInterventionActuationState.STARTED
    )
    assert restored.transition_count == 2
    assert restored.details == {"attempt": 1}

    transitions = second_journal.list_transitions(
        created.actuation_id
    )

    assert len(transitions) == 2


def test_record_is_frozen(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    with pytest.raises(FrozenInstanceError):
        record.transition_count = 99


def test_transition_record_is_frozen(tmp_path):
    journal = _journal(tmp_path)
    record = _begin(journal)

    transition = journal.list_transitions(
        record.actuation_id
    )[0]

    with pytest.raises(FrozenInstanceError):
        transition.transition_sequence = 999


def test_record_serialization_preserves_lineage(tmp_path):
    journal = _journal(tmp_path)

    record = _begin(
        journal,
        details={"adapter_id": "adapter-001"},
    )

    serialized = record.to_dict()

    assert serialized == {
        "actuation_id": record.actuation_id,
        "tenant_id": "tenant-a",
        "contract_hash": "contract-hash-001",
        "idempotency_key": "actuation-001",
        "current_state": "ACCEPTED",
        "transition_count": 1,
        "details": {
            "adapter_id": "adapter-001",
        },
    }


def test_journal_exposes_no_execute_method(tmp_path):
    journal = _journal(tmp_path)

    assert not hasattr(journal, "execute")
    assert not hasattr(journal, "dispatch")
    assert not hasattr(journal, "actuate")
