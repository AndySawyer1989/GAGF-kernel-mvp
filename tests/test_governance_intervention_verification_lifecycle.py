from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import sqlite3

import pytest

from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationLedger,
    GovernanceInterventionVerificationRecordBuilder,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH,
    GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_VERSION,
    GovernanceInterventionVerificationLifecycleEvent,
    GovernanceInterventionVerificationLifecycleIntegrityError,
    GovernanceInterventionVerificationLifecycleLedger,
    GovernanceInterventionVerificationLifecycleStatus,
    GovernanceInterventionVerificationLifecycleTenantError,
    GovernanceInterventionVerificationLifecycleTransitionError,
)
from backend.app.gagf.governance_intervention_verification_summary import (
    GovernanceInterventionVerificationSummary,
    GovernanceInterventionVerificationSummaryDisposition,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_summary(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_set_hash: str = "verification-set-1",
    disposition=(
        GovernanceInterventionVerificationSummaryDisposition.VERIFIED
    ),
    required_count: int = 3,
    verified_count: int = 3,
    not_verified_count: int = 0,
    inconclusive_count: int = 0,
) -> GovernanceInterventionVerificationSummary:
    payload = {
        "verification_summary_id": (
            "governance-intervention-verification-summary"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "contract_hash": f"contract-{intervention_id}",
        "intervention_id": intervention_id,
        "intervention_type": "POLICY_CHANGE",
        "verification_set_hash": verification_set_hash,
        "required_count": required_count,
        "verified_count": verified_count,
        "not_verified_count": not_verified_count,
        "inconclusive_count": inconclusive_count,
        "verification_disposition": disposition.value,
    }

    return GovernanceInterventionVerificationSummary(
        verification_summary_id=payload[
            "verification_summary_id"
        ],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        verification_set_hash=payload[
            "verification_set_hash"
        ],
        required_count=payload["required_count"],
        verified_count=payload["verified_count"],
        not_verified_count=payload[
            "not_verified_count"
        ],
        inconclusive_count=payload[
            "inconclusive_count"
        ],
        verification_disposition=disposition,
        verification_summary_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def persist_record(
    database_path,
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_set_hash: str = "verification-set-1",
    disposition=(
        GovernanceInterventionVerificationSummaryDisposition.VERIFIED
    ),
    required_count: int = 3,
    verified_count: int = 3,
    not_verified_count: int = 0,
    inconclusive_count: int = 0,
):
    summary = make_summary(
        tenant_id=tenant_id,
        intervention_id=intervention_id,
        verification_set_hash=verification_set_hash,
        disposition=disposition,
        required_count=required_count,
        verified_count=verified_count,
        not_verified_count=not_verified_count,
        inconclusive_count=inconclusive_count,
    )

    record = GovernanceInterventionVerificationRecordBuilder.build(
        summary=summary
    )

    verification_ledger = (
        GovernanceInterventionVerificationLedger(
            database_path
        )
    )

    verification_ledger.append(
        record=record
    )

    return summary, record


def test_lifecycle_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_ID
        == "governance-intervention-verification-lifecycle"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_SCHEMA_VERSION
        == "1.0.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
        == "0" * 64
    )


def test_lifecycle_statuses_are_exact():
    assert {
        status.value
        for status in (
            GovernanceInterventionVerificationLifecycleStatus
        )
    } == {
        "ACTIVE",
        "STALE",
        "REVERIFICATION_REQUIRED",
        "SUPERSEDED",
    }


def test_activation_requires_persisted_verification_record(
    tmp_path,
):
    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=tmp_path / "verification.db"
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleIntegrityError
    ):
        ledger.activate(
            tenant_id="tenant-a",
            verification_record_hash="missing-record",
        )


def test_first_lifecycle_transition_is_active(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    entry = ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    state = ledger.get_current_state(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert entry.sequence_number == 1
    assert (
        entry.previous_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
    )
    assert state is not None
    assert state.lifecycle_status == "ACTIVE"
    assert state.superseded_by_record_hash is None


def test_activation_replay_is_idempotent(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    first = ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    second = ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert first == second

    history = ledger.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert len(history) == 1


def test_active_can_transition_to_stale(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    state = ledger.get_current_state(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert state is not None
    assert state.lifecycle_status == "STALE"


def test_stale_replay_is_idempotent(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    first = ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    second = ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert first == second
    assert len(
        ledger.list_history(
            tenant_id="tenant-a",
            verification_record_hash=record.record_hash,
        )
    ) == 2


def test_active_can_require_reverification(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    state = ledger.get_current_state(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert state is not None
    assert (
        state.lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )


def test_stale_can_require_reverification(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    history = ledger.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert [
        event.lifecycle_status
        for event in history
    ] == [
        "ACTIVE",
        "STALE",
        "REVERIFICATION_REQUIRED",
    ]


def test_reverification_replay_is_idempotent(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    first = ledger.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    second = ledger.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert first == second


def test_stale_before_activation_is_rejected(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTransitionError
    ):
        ledger.mark_stale(
            tenant_id="tenant-a",
            verification_record_hash=record.record_hash,
        )


def test_reverification_before_activation_is_rejected(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTransitionError
    ):
        ledger.require_reverification(
            tenant_id="tenant-a",
            verification_record_hash=record.record_hash,
        )


def test_active_can_be_superseded_by_same_intervention_record(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        intervention_id="intervention-1",
        verification_set_hash="set-original",
    )

    _, replacement = persist_record(
        database_path,
        intervention_id="intervention-1",
        verification_set_hash="set-replacement",
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE
        ),
        verified_count=2,
        inconclusive_count=1,
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    ledger.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    state = ledger.get_current_state(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    assert state is not None
    assert state.lifecycle_status == "SUPERSEDED"
    assert (
        state.superseded_by_record_hash
        == replacement.record_hash
    )


def test_stale_can_be_superseded(tmp_path):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        verification_set_hash="set-a",
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="set-b",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    ledger.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    assert (
        ledger.get_current_state(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
        ).lifecycle_status
        == "SUPERSEDED"
    )


def test_reverification_required_can_be_superseded(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        verification_set_hash="set-a",
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="set-b",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    ledger.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    ledger.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    assert (
        ledger.get_current_state(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
        ).lifecycle_status
        == "SUPERSEDED"
    )


def test_supersession_replay_is_idempotent(tmp_path):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        verification_set_hash="set-a",
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="set-b",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    first = ledger.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    second = ledger.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    assert first == second
    assert len(
        ledger.list_history(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
        )
    ) == 2


def test_record_cannot_supersede_itself(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTransitionError,
        match="cannot supersede itself",
    ):
        ledger.supersede(
            tenant_id="tenant-a",
            verification_record_hash=record.record_hash,
            superseded_by_record_hash=record.record_hash,
        )


def test_superseding_record_must_be_same_intervention(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        intervention_id="intervention-a",
        verification_set_hash="set-a",
    )

    _, foreign = persist_record(
        database_path,
        intervention_id="intervention-b",
        verification_set_hash="set-b",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTransitionError,
        match="same intervention",
    ):
        ledger.supersede(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
            superseded_by_record_hash=foreign.record_hash,
        )


def test_superseding_record_cannot_cross_tenant_boundary(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        tenant_id="tenant-a",
        intervention_id="shared-intervention",
        verification_set_hash="set-a",
    )

    _, tenant_b_record = persist_record(
        database_path,
        tenant_id="tenant-b",
        intervention_id="shared-intervention",
        verification_set_hash="set-b",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleIntegrityError
    ):
        ledger.supersede(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
            superseded_by_record_hash=(
                tenant_b_record.record_hash
            ),
        )


def test_superseded_is_terminal(tmp_path):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        verification_set_hash="set-a",
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="set-b",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    ledger.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTransitionError
    ):
        ledger.mark_stale(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
        )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTransitionError
    ):
        ledger.require_reverification(
            tenant_id="tenant-a",
            verification_record_hash=original.record_hash,
        )


def test_lifecycle_events_are_frozen(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    event = ledger.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )[0]

    with pytest.raises(FrozenInstanceError):
        event.lifecycle_status = "STALE"


def test_lifecycle_event_hash_detects_tampering(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    event = ledger.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )[0]

    tampered = replace(
        event,
        lifecycle_status="STALE",
    )

    assert event.verify() is True
    assert tampered.verify() is False


def test_lifecycle_history_preserves_previous_status(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    history = ledger.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert history[0].previous_status is None
    assert history[1].previous_status == "ACTIVE"
    assert history[2].previous_status == "STALE"


def test_i_g_verification_record_is_not_mutated_by_lifecycle(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    summary, original = persist_record(
        database_path,
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .NOT_VERIFIED
        ),
        verified_count=2,
        not_verified_count=1,
    )

    lifecycle = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    lifecycle.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    verification_ledger = (
        GovernanceInterventionVerificationLedger(
            database_path
        )
    )

    stored = verification_ledger.get_by_summary_hash(
        tenant_id="tenant-a",
        verification_summary_hash=(
            summary.verification_summary_hash
        ),
    )

    assert stored == original
    assert stored.record_hash == original.record_hash
    assert (
        stored.verification_disposition
        == "NOT_VERIFIED"
    )


def test_lifecycle_does_not_change_verification_disposition(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .VERIFIED
        ),
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="replacement",
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE
        ),
        verified_count=2,
        inconclusive_count=1,
    )

    lifecycle = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    lifecycle.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    verification_ledger = (
        GovernanceInterventionVerificationLedger(
            database_path
        )
    )

    original_stored = (
        verification_ledger.list_for_intervention(
            tenant_id="tenant-a",
            intervention_id="intervention-1",
        )[0]
    )

    assert (
        original_stored.verification_disposition
        == "VERIFIED"
    )


def test_tenant_lifecycle_chains_are_independent(tmp_path):
    database_path = tmp_path / "verification.db"

    _, tenant_a = persist_record(
        database_path,
        tenant_id="tenant-a",
        verification_set_hash="tenant-a-set",
    )

    _, tenant_b = persist_record(
        database_path,
        tenant_id="tenant-b",
        verification_set_hash="tenant-b-set",
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    a_entry = ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=tenant_a.record_hash,
    )

    b_entry = ledger.activate(
        tenant_id="tenant-b",
        verification_record_hash=tenant_b.record_hash,
    )

    assert a_entry.sequence_number == 1
    assert b_entry.sequence_number == 1

    assert (
        a_entry.previous_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
    )
    assert (
        b_entry.previous_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
    )


def test_valid_lifecycle_chain_verifies(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    ledger.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert result.valid is True
    assert result.event_count == 2
    assert len(result.last_chain_hash) == 64


def test_empty_lifecycle_chain_is_valid_genesis(tmp_path):
    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=tmp_path / "verification.db"
        )
    )

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert result.valid is True
    assert result.event_count == 0
    assert (
        result.last_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LIFECYCLE_GENESIS_HASH
    )


def test_lifecycle_chain_detects_event_tampering(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_lifecycle_events
            SET lifecycle_status = ?
            WHERE tenant_id = ?
            """,
            (
                "STALE",
                "tenant-a",
            ),
        )

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert result.valid is False


def test_lifecycle_chain_detects_chain_hash_tampering(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_lifecycle_events
            SET chain_hash = ?
            WHERE tenant_id = ?
            """,
            (
                "f" * 64,
                "tenant-a",
            ),
        )

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert result.valid is False


def test_history_read_rejects_tampered_event(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_lifecycle_events
            SET lifecycle_status = ?
            WHERE tenant_id = ?
            """,
            (
                "STALE",
                "tenant-a",
            ),
        )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleIntegrityError
    ):
        ledger.list_history(
            tenant_id="tenant-a",
            verification_record_hash=record.record_hash,
        )


def test_current_state_read_rejects_tampered_event(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    ledger.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_lifecycle_events
            SET lifecycle_status = ?
            WHERE tenant_id = ?
            """,
            (
                "STALE",
                "tenant-a",
            ),
        )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleIntegrityError
    ):
        ledger.get_current_state(
            tenant_id="tenant-a",
            verification_record_hash=record.record_hash,
        )


def test_blank_tenant_is_rejected(tmp_path):
    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=tmp_path / "verification.db"
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTenantError
    ):
        ledger.get_current_state(
            tenant_id="   ",
            verification_record_hash="record",
        )


def test_noncanonical_tenant_is_rejected_on_transition(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    ledger = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationLifecycleTenantError
    ):
        ledger.activate(
            tenant_id=" tenant-a ",
            verification_record_hash=record.record_hash,
        )


def test_lifecycle_surface_has_no_execution_or_causal_authority():
    forbidden_methods = {
        "execute",
        "actuate",
        "authorize",
        "rollback",
        "continue_intervention",
        "recommend",
        "infer_causation",
        "attribute_causation",
        "evaluate_requirement",
        "verify_outcome",
    }

    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionVerificationLifecycleLedger
        )
        if not name.startswith("_")
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )


def test_lifecycle_event_contains_no_success_or_causation_fields():
    field_names = {
        field_name
        for field_name in (
            GovernanceInterventionVerificationLifecycleEvent
            .__dataclass_fields__
        )
    }

    forbidden_fields = {
        "success",
        "failure",
        "intervention_success",
        "intervention_failure",
        "causation",
        "causal_effect",
        "causal_attribution",
        "authorized",
        "rollback",
        "continue_intervention",
        "recommended_action",
        "next_action",
    }

    assert forbidden_fields.isdisjoint(
        field_names
    )