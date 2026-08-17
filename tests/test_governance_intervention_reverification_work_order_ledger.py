from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.governance_intervention_reverification_work_order_ledger import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_GENESIS_HASH,
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_VERSION,
    GovernanceInterventionReverificationWorkOrderLedger,
    GovernanceInterventionReverificationWorkOrderLedgerIntegrityError,
    GovernanceInterventionReverificationWorkOrderLedgerTenantError,
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
        "reverification_scope": (
            reverification_scope
        ),
        "trigger_codes": list(
            trigger_codes
        ),
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
        trigger_codes=trigger_codes,
        work_order_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def test_ledger_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_ID
        == "governance-intervention-reverification-work-order-ledger"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_SCHEMA_VERSION
        == "1.0.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_LEDGER_GENESIS_HASH
        == "0" * 64
    )


def test_first_work_order_uses_genesis_hash(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    work_order = make_work_order()

    entry = ledger.append(
        work_order=work_order
    )

    assert entry.sequence_number == 1
    assert (
        entry.previous_chain_hash
        == "0" * 64
    )
    assert entry.work_order_hash == work_order.work_order_hash
    assert entry.request_hash == work_order.request_hash
    assert entry.attempt_id == work_order.attempt_id
    assert entry.verify_chain_hash() is True


def test_same_work_order_replay_is_idempotent(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    work_order = make_work_order()

    first = ledger.append(
        work_order=work_order
    )

    second = ledger.append(
        work_order=work_order
    )

    assert second == first

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.work_order_count == 1


def test_second_work_order_advances_chain(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    first = ledger.append(
        work_order=make_work_order(
            request_hash="request-1",
            attempt_id="attempt-1",
        )
    )

    second = ledger.append(
        work_order=make_work_order(
            request_hash="request-2",
            request_ledger_chain_hash="request-chain-2",
            attempt_id="attempt-2",
        )
    )

    assert second.sequence_number == 2
    assert second.previous_chain_hash == first.chain_hash


def test_work_order_can_be_read_by_hash(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    work_order = make_work_order()

    ledger.append(
        work_order=work_order
    )

    stored = ledger.get_by_work_order_hash(
        tenant_id="tenant-a",
        work_order_hash=work_order.work_order_hash,
    )

    assert stored == work_order


def test_missing_work_order_returns_none(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    assert (
        ledger.get_by_work_order_hash(
            tenant_id="tenant-a",
            work_order_hash="missing",
        )
        is None
    )


def test_list_for_request_returns_canonical_order(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    first = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-1",
    )

    second = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-2",
    )

    ledger.append(
        work_order=first
    )

    ledger.append(
        work_order=second
    )

    stored = ledger.list_for_request(
        tenant_id="tenant-a",
        request_hash="request-1",
    )

    assert stored == (
        first,
        second,
    )


def test_work_orders_are_tenant_scoped(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    tenant_a = make_work_order(
        tenant_id="tenant-a"
    )

    tenant_b = make_work_order(
        tenant_id="tenant-b"
    )

    ledger.append(
        work_order=tenant_a
    )

    ledger.append(
        work_order=tenant_b
    )

    assert (
        ledger.get_by_work_order_hash(
            tenant_id="tenant-b",
            work_order_hash=tenant_a.work_order_hash,
        )
        is None
    )


def test_tenant_chains_are_independent(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    entry_a = ledger.append(
        work_order=make_work_order(
            tenant_id="tenant-a"
        )
    )

    entry_b = ledger.append(
        work_order=make_work_order(
            tenant_id="tenant-b"
        )
    )

    assert entry_a.sequence_number == 1
    assert entry_b.sequence_number == 1

    assert (
        entry_a.previous_chain_hash
        == "0" * 64
    )

    assert (
        entry_b.previous_chain_hash
        == "0" * 64
    )


def test_same_request_attempt_pair_cannot_bind_two_orders(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    first = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-1",
        reverification_scope="POLICY",
    )

    second = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-1",
        reverification_scope="FULL",
        trigger_codes=(
            "CONTRACT_CHANGED",
        ),
    )

    assert first.work_order_hash != second.work_order_hash

    ledger.append(
        work_order=first
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderLedgerIntegrityError,
        match="already bound",
    ):
        ledger.append(
            work_order=second
        )


def test_same_request_can_have_distinct_attempts(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    first = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-1",
    )

    second = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-2",
    )

    first_entry = ledger.append(
        work_order=first
    )

    second_entry = ledger.append(
        work_order=second
    )

    assert first_entry.sequence_number == 1
    assert second_entry.sequence_number == 2


def test_same_attempt_id_can_exist_for_different_requests(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    first = make_work_order(
        request_hash="request-1",
        attempt_id="attempt-shared",
    )

    second = make_work_order(
        request_hash="request-2",
        request_ledger_chain_hash="request-chain-2",
        attempt_id="attempt-shared",
    )

    ledger.append(
        work_order=first
    )

    ledger.append(
        work_order=second
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.work_order_count == 2
    assert verification.valid is True


def test_valid_chain_verifies(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    ledger.append(
        work_order=make_work_order()
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.work_order_count == 1
    assert len(
        verification.last_chain_hash
    ) == 64


def test_empty_chain_is_valid_genesis(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.work_order_count == 0

    assert (
        verification.last_chain_hash
        == "0" * 64
    )


def test_tampered_work_order_payload_breaks_chain_verification(
    tmp_path,
):
    database_path = tmp_path / "work-orders.db"

    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        database_path
    )

    work_order = make_work_order()

    ledger.append(
        work_order=work_order
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_reverification_work_orders
            SET reverification_scope = ?
            WHERE tenant_id = ?
              AND work_order_hash = ?
            """,
            (
                "FULL",
                "tenant-a",
                work_order.work_order_hash,
            ),
        )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is False


def test_tampered_chain_hash_breaks_verification(
    tmp_path,
):
    database_path = tmp_path / "work-orders.db"

    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        database_path
    )

    work_order = make_work_order()

    ledger.append(
        work_order=work_order
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_reverification_work_orders
            SET chain_hash = ?
            WHERE tenant_id = ?
              AND work_order_hash = ?
            """,
            (
                "f" * 64,
                "tenant-a",
                work_order.work_order_hash,
            ),
        )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is False


def test_read_rejects_tampered_work_order(
    tmp_path,
):
    database_path = tmp_path / "work-orders.db"

    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        database_path
    )

    work_order = make_work_order()

    ledger.append(
        work_order=work_order
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_reverification_work_orders
            SET attempt_id = ?
            WHERE tenant_id = ?
              AND work_order_hash = ?
            """,
            (
                "tampered-attempt",
                "tenant-a",
                work_order.work_order_hash,
            ),
        )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderLedgerIntegrityError,
        match="failed deterministic verification",
    ):
        ledger.get_by_work_order_hash(
            tenant_id="tenant-a",
            work_order_hash=work_order.work_order_hash,
        )


def test_tampered_work_order_cannot_be_appended(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    work_order = make_work_order()

    tampered = replace(
        work_order,
        attempt_id="attempt-2",
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderLedgerIntegrityError,
        match="failed deterministic verification",
    ):
        ledger.append(
            work_order=tampered
        )


def test_blank_tenant_is_rejected(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderLedgerTenantError,
        match="tenant_id is required",
    ):
        ledger.verify_tenant_chain(
            tenant_id=""
        )


def test_noncanonical_tenant_is_rejected(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationWorkOrderLedger(
        tmp_path / "work-orders.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderLedgerTenantError,
        match="must already be canonical",
    ):
        ledger.verify_tenant_chain(
            tenant_id=" tenant-a "
        )


def test_ledger_has_no_execution_or_completion_methods():
    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionReverificationWorkOrderLedger
        )
        if not name.startswith("_")
    }

    forbidden_methods = {
        "execute",
        "start",
        "complete",
        "mark_completed",
        "reverify",
        "measure",
        "observe",
        "verify_outcome",
        "authorize",
        "actuate",
        "rollback",
        "supersede",
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )