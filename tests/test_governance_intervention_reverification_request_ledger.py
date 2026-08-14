from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from backend.app.gagf.governance_intervention_reverification_request import (
    GovernanceInterventionReverificationRequest,
)
from backend.app.gagf.governance_intervention_reverification_request_ledger import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_GENESIS_HASH,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_VERSION,
    GovernanceInterventionReverificationRequestLedger,
    GovernanceInterventionReverificationRequestLedgerIntegrityError,
    GovernanceInterventionReverificationRequestLedgerTenantError,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_request(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_record_hash: str = "record-1",
    lifecycle_event_hash: str = "lifecycle-event-1",
    freshness_evaluation_hash: str = "freshness-1",
    reverification_scope: str = "POLICY",
    trigger_codes: tuple[str, ...] = (
        "POLICY_CHANGED",
    ),
) -> GovernanceInterventionReverificationRequest:
    payload = {
        "request_id": (
            "governance-intervention-reverification-request"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "intervention_id": intervention_id,
        "verification_record_hash": (
            verification_record_hash
        ),
        "lifecycle_event_hash": (
            lifecycle_event_hash
        ),
        "freshness_evaluation_hash": (
            freshness_evaluation_hash
        ),
        "reverification_scope": (
            reverification_scope
        ),
        "trigger_codes": list(
            trigger_codes
        ),
    }

    return GovernanceInterventionReverificationRequest(
        request_id=payload["request_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        intervention_id=payload["intervention_id"],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        lifecycle_event_hash=payload[
            "lifecycle_event_hash"
        ],
        freshness_evaluation_hash=payload[
            "freshness_evaluation_hash"
        ],
        reverification_scope=payload[
            "reverification_scope"
        ],
        trigger_codes=trigger_codes,
        request_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def test_ledger_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_ID
        == "governance-intervention-reverification-request-ledger"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_SCHEMA_VERSION
        == "1.0.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_LEDGER_GENESIS_HASH
        == "0" * 64
    )


def test_first_request_uses_genesis_hash(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    request = make_request()

    entry = ledger.append(
        request=request
    )

    assert entry.sequence_number == 1
    assert (
        entry.previous_chain_hash
        == "0" * 64
    )
    assert entry.verify_chain_hash() is True


def test_same_request_replay_is_idempotent(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    request = make_request()

    first = ledger.append(
        request=request
    )

    second = ledger.append(
        request=request
    )

    assert second == first

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.request_count == 1


def test_second_request_advances_chain(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    first = ledger.append(
        request=make_request(
            freshness_evaluation_hash="freshness-1"
        )
    )

    second = ledger.append(
        request=make_request(
            lifecycle_event_hash="lifecycle-event-2",
            freshness_evaluation_hash="freshness-2",
            trigger_codes=(
                "REQUIREMENTS_CHANGED",
            ),
            reverification_scope="REQUIREMENTS",
        )
    )

    assert second.sequence_number == 2
    assert (
        second.previous_chain_hash
        == first.chain_hash
    )


def test_request_can_be_read_by_hash(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    request = make_request()

    ledger.append(
        request=request
    )

    stored = ledger.get_by_request_hash(
        tenant_id="tenant-a",
        request_hash=request.request_hash,
    )

    assert stored == request


def test_missing_request_returns_none(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    assert (
        ledger.get_by_request_hash(
            tenant_id="tenant-a",
            request_hash="missing",
        )
        is None
    )


def test_list_for_record_returns_canonical_order(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    first = make_request(
        lifecycle_event_hash="event-1",
        freshness_evaluation_hash="freshness-1",
    )

    second = make_request(
        lifecycle_event_hash="event-2",
        freshness_evaluation_hash="freshness-2",
    )

    ledger.append(
        request=first
    )

    ledger.append(
        request=second
    )

    stored = ledger.list_for_verification_record(
        tenant_id="tenant-a",
        verification_record_hash="record-1",
    )

    assert stored == (
        first,
        second,
    )


def test_requests_are_tenant_scoped(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    tenant_a = make_request(
        tenant_id="tenant-a"
    )

    tenant_b = make_request(
        tenant_id="tenant-b"
    )

    ledger.append(
        request=tenant_a
    )

    ledger.append(
        request=tenant_b
    )

    assert (
        ledger.get_by_request_hash(
            tenant_id="tenant-b",
            request_hash=tenant_a.request_hash,
        )
        is None
    )


def test_tenant_chains_are_independent(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    entry_a = ledger.append(
        request=make_request(
            tenant_id="tenant-a"
        )
    )

    entry_b = ledger.append(
        request=make_request(
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


def test_valid_chain_verifies(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    ledger.append(
        request=make_request()
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.request_count == 1
    assert len(
        verification.last_chain_hash
    ) == 64


def test_empty_chain_is_valid_genesis(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.request_count == 0

    assert (
        verification.last_chain_hash
        == "0" * 64
    )


def test_tampered_request_payload_breaks_chain_verification(
    tmp_path,
):
    database_path = tmp_path / "requests.db"

    ledger = GovernanceInterventionReverificationRequestLedger(
        database_path
    )

    request = make_request()

    ledger.append(
        request=request
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_reverification_requests
            SET reverification_scope = ?
            WHERE tenant_id = ?
              AND request_hash = ?
            """,
            (
                "FULL",
                "tenant-a",
                request.request_hash,
            ),
        )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is False


def test_tampered_chain_hash_breaks_verification(
    tmp_path,
):
    database_path = tmp_path / "requests.db"

    ledger = GovernanceInterventionReverificationRequestLedger(
        database_path
    )

    request = make_request()

    ledger.append(
        request=request
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_reverification_requests
            SET chain_hash = ?
            WHERE tenant_id = ?
              AND request_hash = ?
            """,
            (
                "f" * 64,
                "tenant-a",
                request.request_hash,
            ),
        )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is False


def test_read_rejects_tampered_request(
    tmp_path,
):
    database_path = tmp_path / "requests.db"

    ledger = GovernanceInterventionReverificationRequestLedger(
        database_path
    )

    request = make_request()

    ledger.append(
        request=request
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_reverification_requests
            SET intervention_id = ?
            WHERE tenant_id = ?
              AND request_hash = ?
            """,
            (
                "tampered",
                "tenant-a",
                request.request_hash,
            ),
        )

    with pytest.raises(
        GovernanceInterventionReverificationRequestLedgerIntegrityError,
        match="failed deterministic verification",
    ):
        ledger.get_by_request_hash(
            tenant_id="tenant-a",
            request_hash=request.request_hash,
        )


def test_tampered_request_cannot_be_appended(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    request = make_request()

    tampered = replace(
        request,
        reverification_scope="FULL",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestLedgerIntegrityError,
        match="failed deterministic verification",
    ):
        ledger.append(
            request=tampered
        )


def test_blank_tenant_is_rejected(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestLedgerTenantError,
        match="tenant_id is required",
    ):
        ledger.verify_tenant_chain(
            tenant_id=""
        )


def test_noncanonical_tenant_is_rejected(
    tmp_path,
):
    ledger = GovernanceInterventionReverificationRequestLedger(
        tmp_path / "requests.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestLedgerTenantError,
        match="must already be canonical",
    ):
        ledger.verify_tenant_chain(
            tenant_id=" tenant-a "
        )


def test_ledger_has_no_reverification_execution_methods():
    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionReverificationRequestLedger
        )
        if not name.startswith("_")
    }

    forbidden_methods = {
        "execute",
        "reverify",
        "verify_outcome",
        "complete",
        "mark_completed",
        "authorize",
        "actuate",
        "rollback",
        "supersede",
        "require_reverification",
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )