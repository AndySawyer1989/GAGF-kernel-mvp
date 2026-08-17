from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_attempt import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_VERSION,
    GovernanceInterventionReverificationAttemptConflictError,
    GovernanceInterventionReverificationAttemptIntegrityError,
    GovernanceInterventionReverificationAttemptJournal,
    GovernanceInterventionReverificationAttemptState,
    GovernanceInterventionReverificationAttemptTransitionError,
)
from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_work_order(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_record_hash: str = "record-1",
    request_hash: str = "request-1",
    request_ledger_chain_hash: str = "request-chain-1",
    attempt_id: str = "attempt-1",
    reverification_scope: str = "POLICY",
    trigger_codes: tuple[str, ...] = (
        "POLICY_CHANGED",
    ),
) -> GovernanceInterventionReverificationWorkOrder:
    payload = {
        "work_order_id": (
            "governance-intervention-reverification-work-order"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "intervention_id": intervention_id,
        "verification_record_hash": (
            verification_record_hash
        ),
        "request_hash": request_hash,
        "request_ledger_chain_hash": (
            request_ledger_chain_hash
        ),
        "attempt_id": attempt_id,
        "reverification_scope": reverification_scope,
        "trigger_codes": list(trigger_codes),
    }

    return GovernanceInterventionReverificationWorkOrder(
        work_order_id=payload["work_order_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        intervention_id=payload["intervention_id"],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        request_hash=payload["request_hash"],
        request_ledger_chain_hash=payload[
            "request_ledger_chain_hash"
        ],
        attempt_id=payload["attempt_id"],
        reverification_scope=payload[
            "reverification_scope"
        ],
        trigger_codes=tuple(
            payload["trigger_codes"]
        ),
        work_order_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def test_attempt_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_ID
        == "governance-intervention-reverification-attempt"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_ATTEMPT_VERSION
        == "0.1.0"
    )


def test_attempt_state_enum_is_exact():
    assert {
        state.value
        for state in GovernanceInterventionReverificationAttemptState
    } == {
        "STARTED",
        "COMPLETED",
        "FAILED",
    }


def test_begin_creates_started_attempt(tmp_path):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    record = journal.begin(
        work_order=work_order
    )

    assert (
        record.current_state
        is GovernanceInterventionReverificationAttemptState.STARTED
    )

    assert record.transition_count == 1

    assert record.tenant_id == work_order.tenant_id
    assert (
        record.intervention_id
        == work_order.intervention_id
    )
    assert (
        record.verification_record_hash
        == work_order.verification_record_hash
    )
    assert record.request_hash == work_order.request_hash
    assert (
        record.work_order_hash
        == work_order.work_order_hash
    )
    assert record.attempt_id == work_order.attempt_id

    assert (
        record.reverification_scope
        == work_order.reverification_scope
    )


def test_attempt_execution_id_is_deterministic(tmp_path):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    first = journal.derive_attempt_execution_id(
        work_order=work_order
    )

    second = journal.derive_attempt_execution_id(
        work_order=work_order
    )

    assert first == second
    assert len(first) == 64


def test_different_work_orders_change_attempt_execution_id(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    first = make_work_order(
        attempt_id="attempt-1"
    )

    second = make_work_order(
        attempt_id="attempt-2"
    )

    assert (
        journal.derive_attempt_execution_id(
            work_order=first
        )
        != journal.derive_attempt_execution_id(
            work_order=second
        )
    )


def test_begin_is_idempotent_for_same_work_order(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    first = journal.begin(
        work_order=work_order,
        details={
            "source": "first"
        },
    )

    second = journal.begin(
        work_order=work_order,
        details={
            "source": "second"
        },
    )

    assert first == second

    transitions = journal.list_transitions(
        attempt_execution_id=(
            first.attempt_execution_id
        )
    )

    assert len(transitions) == 1

    assert (
        transitions[0].state
        is GovernanceInterventionReverificationAttemptState.STARTED
    )


def test_tampered_work_order_is_rejected(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    tampered = replace(
        work_order,
        intervention_id="tampered-intervention",
    )

    assert not tampered.verify()

    with pytest.raises(
        GovernanceInterventionReverificationAttemptIntegrityError,
        match=(
            "reverification work order failed "
            "deterministic verification"
        ),
    ):
        journal.begin(
            work_order=tampered
        )


def test_started_can_transition_to_completed(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    started = journal.begin(
        work_order=work_order
    )

    completed = journal.complete(
        work_order=work_order,
        details={
            "worker_status": "complete"
        },
    )

    assert (
        started.current_state
        is GovernanceInterventionReverificationAttemptState.STARTED
    )

    assert (
        completed.current_state
        is GovernanceInterventionReverificationAttemptState.COMPLETED
    )

    assert completed.transition_count == 2


def test_started_can_transition_to_failed(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    journal.begin(
        work_order=work_order
    )

    error = RuntimeError(
        "evidence source unavailable"
    )

    failed = journal.fail(
        work_order=work_order,
        error=error,
    )

    assert (
        failed.current_state
        is GovernanceInterventionReverificationAttemptState.FAILED
    )

    assert failed.transition_count == 2

    assert failed.details == {
        "error_type": "RuntimeError",
        "error_message": "evidence source unavailable",
    }


def test_completed_is_terminal(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    journal.begin(
        work_order=work_order
    )

    journal.complete(
        work_order=work_order
    )

    with pytest.raises(
        GovernanceInterventionReverificationAttemptTransitionError,
        match=(
            "illegal reverification attempt transition: "
            "COMPLETED -> FAILED"
        ),
    ):
        journal.fail(
            work_order=work_order,
            error=RuntimeError("late failure"),
        )


def test_failed_is_terminal(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    journal.begin(
        work_order=work_order
    )

    journal.fail(
        work_order=work_order,
        error=RuntimeError("worker failure"),
    )

    with pytest.raises(
        GovernanceInterventionReverificationAttemptTransitionError,
        match=(
            "illegal reverification attempt transition: "
            "FAILED -> COMPLETED"
        ),
    ):
        journal.complete(
            work_order=work_order
        )


def test_repeating_terminal_state_is_idempotent(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    journal.begin(
        work_order=work_order
    )

    first = journal.complete(
        work_order=work_order,
        details={
            "worker_status": "complete"
        },
    )

    second = journal.complete(
        work_order=work_order,
        details={
            "worker_status": "different"
        },
    )

    assert first == second
    assert second.transition_count == 2


def test_transition_history_is_append_ordered(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    started = journal.begin(
        work_order=work_order,
        details={
            "phase": "started"
        },
    )

    journal.complete(
        work_order=work_order,
        details={
            "phase": "complete"
        },
    )

    transitions = journal.list_transitions(
        attempt_execution_id=(
            started.attempt_execution_id
        )
    )

    assert len(transitions) == 2

    assert [
        transition.state
        for transition in transitions
    ] == [
        GovernanceInterventionReverificationAttemptState.STARTED,
        GovernanceInterventionReverificationAttemptState.COMPLETED,
    ]

    assert (
        transitions[0].transition_sequence
        < transitions[1].transition_sequence
    )

    assert transitions[0].details == {
        "phase": "started"
    }

    assert transitions[1].details == {
        "phase": "complete"
    }


def test_get_for_work_order_is_tenant_scoped(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order(
        tenant_id="tenant-a"
    )

    journal.begin(
        work_order=work_order
    )

    assert (
        journal.get_for_work_order(
            tenant_id="tenant-a",
            work_order_hash=(
                work_order.work_order_hash
            ),
        )
        is not None
    )

    assert (
        journal.get_for_work_order(
            tenant_id="tenant-b",
            work_order_hash=(
                work_order.work_order_hash
            ),
        )
        is None
    )


def test_distinct_tenants_have_distinct_attempts(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    tenant_a = make_work_order(
        tenant_id="tenant-a",
        attempt_id="attempt-shared",
    )

    tenant_b = make_work_order(
        tenant_id="tenant-b",
        attempt_id="attempt-shared",
    )

    first = journal.begin(
        work_order=tenant_a
    )

    second = journal.begin(
        work_order=tenant_b
    )

    assert (
        first.attempt_execution_id
        != second.attempt_execution_id
    )

    assert first.tenant_id == "tenant-a"
    assert second.tenant_id == "tenant-b"


def test_persisted_lineage_conflict_is_detected(
    tmp_path,
):
    database_path = (
        tmp_path / "verification.db"
    )

    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            database_path
        )
    )

    work_order = make_work_order()

    original = journal.begin(
        work_order=work_order
    )

    with journal._connect() as connection:
        connection.execute(
            """
            UPDATE
                governance_intervention_reverification_attempts
            SET intervention_id = ?
            WHERE attempt_execution_id = ?
            """,
            (
                "tampered-intervention",
                original.attempt_execution_id,
            ),
        )

    with pytest.raises(
        GovernanceInterventionReverificationAttemptConflictError,
        match=(
            "persisted reverification attempt does not "
            "match I-L work-order lineage"
        ),
    ):
        journal.begin(
            work_order=work_order
        )


@pytest.mark.parametrize(
    "terminal_state",
    [
        "COMPLETED",
        "FAILED",
    ],
)
def test_terminal_attempt_state_does_not_claim_verification_disposition(
    tmp_path,
    terminal_state,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    work_order = make_work_order()

    journal.begin(
        work_order=work_order
    )

    if terminal_state == "COMPLETED":
        record = journal.complete(
            work_order=work_order
        )
    else:
        record = journal.fail(
            work_order=work_order,
            error=RuntimeError(
                "attempt infrastructure failure"
            ),
        )

    payload = record.to_dict()

    forbidden = {
        "verification_disposition",
        "verified",
        "not_verified",
        "inconclusive",
        "reverified",
        "reverification_completed",
        "verification_result",
        "verification_result_hash",
        "measurement",
        "measurement_hash",
        "observation",
        "observation_hash",
        "success",
        "intervention_success",
        "intervention_failure",
        "causation",
        "causal_effect",
        "superseded",
        "superseded_record_hash",
        "authorized",
        "recommended_action",
        "next_action",
        "rollback",
    }

    assert forbidden.isdisjoint(payload)


def test_attempt_journal_exposes_no_verification_or_action_authority():
    forbidden_methods = {
        "verify_outcome",
        "evaluate_requirement",
        "measure",
        "observe",
        "issue_verification",
        "create_verification_result",
        "supersede",
        "require_reverification",
        "authorize",
        "execute_intervention",
        "rollback",
        "recommend_action",
    }

    public_names = {
        name
        for name in dir(
            GovernanceInterventionReverificationAttemptJournal
        )
        if not name.startswith("_")
    }

    assert forbidden_methods.isdisjoint(
        public_names
    )