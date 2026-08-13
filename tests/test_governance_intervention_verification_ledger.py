from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import sqlite3

import pytest

from backend.app.gagf.governance_intervention_verification_ledger import (
    GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH,
    GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_VERSION,
    GovernanceInterventionVerificationLedger,
    GovernanceInterventionVerificationLedgerError,
    GovernanceInterventionVerificationLedgerIntegrityError,
    GovernanceInterventionVerificationLedgerTenantError,
    GovernanceInterventionVerificationRecordBuilder,
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
    verification_set_hash: str = "verification-set-hash-1",
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


def make_record(**kwargs):
    summary = make_summary(**kwargs)

    return GovernanceInterventionVerificationRecordBuilder.build(
        summary=summary
    )


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_ID
        == "governance-intervention-verification-record"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_RECORD_SCHEMA_VERSION
        == "1.0.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_SCHEMA_VERSION
        == "1.0.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
        == "0" * 64
    )


def test_record_builder_preserves_summary_lineage():
    summary = make_summary()

    record = GovernanceInterventionVerificationRecordBuilder.build(
        summary=summary
    )

    assert record.tenant_id == summary.tenant_id
    assert record.contract_hash == summary.contract_hash
    assert record.intervention_id == summary.intervention_id
    assert record.intervention_type == summary.intervention_type

    assert (
        record.verification_set_hash
        == summary.verification_set_hash
    )
    assert (
        record.verification_summary_hash
        == summary.verification_summary_hash
    )

    assert record.required_count == summary.required_count
    assert record.verified_count == summary.verified_count
    assert (
        record.not_verified_count
        == summary.not_verified_count
    )
    assert (
        record.inconclusive_count
        == summary.inconclusive_count
    )

    assert (
        record.verification_disposition
        == summary.verification_disposition.value
    )


def test_record_hash_is_deterministic():
    first = make_record()
    second = make_record()

    assert first == second
    assert first.record_hash == second.record_hash
    assert first.verify() is True


def test_record_is_frozen():
    record = make_record()

    with pytest.raises(FrozenInstanceError):
        record.record_hash = "tampered"


def test_record_tampering_fails_verification():
    record = make_record()

    tampered = replace(
        record,
        intervention_id="different-intervention",
    )

    assert tampered.verify() is False


def test_builder_rejects_tampered_summary():
    summary = make_summary()

    tampered = replace(
        summary,
        required_count=999,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationLedgerIntegrityError
    ):
        GovernanceInterventionVerificationRecordBuilder.build(
            summary=tampered
        )


def test_append_creates_genesis_entry(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record()

    entry = ledger.append(record=record)

    assert entry.tenant_id == "tenant-a"
    assert entry.sequence_number == 1
    assert entry.record_hash == record.record_hash
    assert (
        entry.verification_summary_hash
        == record.verification_summary_hash
    )
    assert (
        entry.previous_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
    )
    assert entry.verify_chain_hash() is True


def test_second_record_chains_to_first(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    first = ledger.append(
        record=make_record(
            intervention_id="intervention-1",
            verification_set_hash="set-1",
        )
    )

    second = ledger.append(
        record=make_record(
            intervention_id="intervention-2",
            verification_set_hash="set-2",
        )
    )

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert second.previous_chain_hash == first.chain_hash
    assert second.verify_chain_hash() is True


def test_replaying_same_record_is_idempotent(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record()

    first = ledger.append(record=record)
    second = ledger.append(record=record)

    assert second == first

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.record_count == 1


def test_same_intervention_can_accumulate_historical_records(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    first_record = make_record(
        intervention_id="intervention-1",
        verification_set_hash="set-1",
    )

    second_record = make_record(
        intervention_id="intervention-1",
        verification_set_hash="set-2",
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE
        ),
        verified_count=2,
        inconclusive_count=1,
    )

    ledger.append(record=first_record)
    ledger.append(record=second_record)

    records = ledger.list_for_intervention(
        tenant_id="tenant-a",
        intervention_id="intervention-1",
    )

    assert records == (
        first_record,
        second_record,
    )


def test_get_by_summary_hash_returns_exact_record(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record()
    ledger.append(record=record)

    stored = ledger.get_by_summary_hash(
        tenant_id="tenant-a",
        verification_summary_hash=(
            record.verification_summary_hash
        ),
    )

    assert stored == record


def test_get_by_summary_hash_missing_returns_none(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    assert (
        ledger.get_by_summary_hash(
            tenant_id="tenant-a",
            verification_summary_hash="missing",
        )
        is None
    )


def test_tenant_query_does_not_cross_boundary(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record(tenant_id="tenant-a")
    ledger.append(record=record)

    assert (
        ledger.get_by_summary_hash(
            tenant_id="tenant-b",
            verification_summary_hash=(
                record.verification_summary_hash
            ),
        )
        is None
    )

    assert (
        ledger.list_for_intervention(
            tenant_id="tenant-b",
            intervention_id=record.intervention_id,
        )
        == ()
    )


def test_tenants_have_independent_genesis_chains(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    alpha = ledger.append(
        record=make_record(
            tenant_id="tenant-a",
            intervention_id="alpha",
            verification_set_hash="alpha-set",
        )
    )

    beta = ledger.append(
        record=make_record(
            tenant_id="tenant-b",
            intervention_id="beta",
            verification_set_hash="beta-set",
        )
    )

    assert alpha.sequence_number == 1
    assert beta.sequence_number == 1

    assert (
        alpha.previous_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
    )
    assert (
        beta.previous_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
    )


def test_verify_tenant_chain_reports_valid_history(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    first = ledger.append(
        record=make_record(
            intervention_id="one",
            verification_set_hash="set-one",
        )
    )
    second = ledger.append(
        record=make_record(
            intervention_id="two",
            verification_set_hash="set-two",
        )
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.record_count == 2
    assert verification.last_chain_hash == second.chain_hash
    assert first.chain_hash != second.chain_hash


def test_empty_tenant_chain_is_valid_genesis_state(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is True
    assert verification.record_count == 0
    assert (
        verification.last_chain_hash
        == GOVERNANCE_INTERVENTION_VERIFICATION_LEDGER_GENESIS_HASH
    )


def test_chain_tampering_is_detected(tmp_path):
    database_path = tmp_path / "verification.sqlite3"

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    ledger.append(
        record=make_record(
            intervention_id="one",
            verification_set_hash="set-one",
        )
    )

    ledger.append(
        record=make_record(
            intervention_id="two",
            verification_set_hash="set-two",
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_records
            SET previous_chain_hash = ?
            WHERE tenant_id = ?
              AND sequence_number = ?
            """,
            (
                "f" * 64,
                "tenant-a",
                2,
            ),
        )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is False


def test_record_tampering_is_detected_by_chain_verification(tmp_path):
    database_path = tmp_path / "verification.sqlite3"

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    ledger.append(record=make_record())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_records
            SET verification_disposition = ?
            WHERE tenant_id = ?
              AND sequence_number = ?
            """,
            (
                "NOT_VERIFIED",
                "tenant-a",
                1,
            ),
        )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.valid is False


def test_get_rejects_tampered_stored_record(tmp_path):
    database_path = tmp_path / "verification.sqlite3"

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    record = make_record()
    ledger.append(record=record)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_records
            SET intervention_type = ?
            WHERE tenant_id = ?
              AND verification_summary_hash = ?
            """,
            (
                "TAMPERED",
                "tenant-a",
                record.verification_summary_hash,
            ),
        )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerIntegrityError
    ):
        ledger.get_by_summary_hash(
            tenant_id="tenant-a",
            verification_summary_hash=(
                record.verification_summary_hash
            ),
        )


def test_list_rejects_tampered_stored_record(tmp_path):
    database_path = tmp_path / "verification.sqlite3"

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    record = make_record()
    ledger.append(record=record)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_intervention_verification_records
            SET verified_count = ?
            WHERE tenant_id = ?
              AND sequence_number = ?
            """,
            (
                999,
                "tenant-a",
                1,
            ),
        )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerIntegrityError
    ):
        ledger.list_for_intervention(
            tenant_id="tenant-a",
            intervention_id=record.intervention_id,
        )


def test_ledger_survives_process_style_reopen(tmp_path):
    database_path = tmp_path / "verification.sqlite3"

    first_ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    record = make_record()

    entry = first_ledger.append(record=record)

    reopened = GovernanceInterventionVerificationLedger(
        database_path
    )

    stored = reopened.get_by_summary_hash(
        tenant_id="tenant-a",
        verification_summary_hash=(
            record.verification_summary_hash
        ),
    )

    verification = reopened.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert stored == record
    assert verification.valid is True
    assert verification.record_count == 1
    assert verification.last_chain_hash == entry.chain_hash


def test_conflicting_record_for_same_summary_hash_is_rejected(
    tmp_path,
):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record()
    ledger.append(record=record)

    conflicting_payload = {
        **record.payload(),
        "intervention_type": "DIFFERENT_TYPE",
    }

    conflicting = replace(
        record,
        intervention_type="DIFFERENT_TYPE",
        record_hash=sha256_hex(
            canonical_json(conflicting_payload)
        ),
    )

    assert conflicting.verify() is True
    assert (
        conflicting.verification_summary_hash
        == record.verification_summary_hash
    )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerIntegrityError
    ):
        ledger.append(record=conflicting)


def test_append_rejects_tampered_record(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record()

    tampered = replace(
        record,
        required_count=999,
    )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerIntegrityError
    ):
        ledger.append(record=tampered)


def test_append_rejects_blank_tenant(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record(tenant_id="")

    with pytest.raises(
        GovernanceInterventionVerificationLedgerTenantError
    ):
        ledger.append(record=record)


def test_append_rejects_noncanonical_tenant(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    record = make_record(
        tenant_id=" tenant-a "
    )

    assert record.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationLedgerTenantError
    ):
        ledger.append(record=record)


@pytest.mark.parametrize(
    "tenant_id",
    ("", "   "),
)
def test_queries_require_tenant(tmp_path, tenant_id):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerTenantError
    ):
        ledger.get_by_summary_hash(
            tenant_id=tenant_id,
            verification_summary_hash="hash",
        )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerTenantError
    ):
        ledger.list_for_intervention(
            tenant_id=tenant_id,
            intervention_id="intervention",
        )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerTenantError
    ):
        ledger.verify_tenant_chain(
            tenant_id=tenant_id
        )


def test_get_requires_summary_hash(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerError
    ):
        ledger.get_by_summary_hash(
            tenant_id="tenant-a",
            verification_summary_hash="   ",
        )


def test_list_requires_intervention_id(tmp_path):
    ledger = GovernanceInterventionVerificationLedger(
        tmp_path / "verification.sqlite3"
    )

    with pytest.raises(
        GovernanceInterventionVerificationLedgerError
    ):
        ledger.list_for_intervention(
            tenant_id="tenant-a",
            intervention_id="   ",
        )


def test_no_update_or_delete_mutation_api():
    forbidden_methods = (
        "update",
        "delete",
        "replace",
        "overwrite",
        "mutate",
        "supersede",
        "mark_stale",
    )

    for method in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionVerificationLedger,
            method,
        )


def test_ledger_has_no_causal_or_future_action_authority():
    forbidden_methods = (
        "attribute_causation",
        "determine_success",
        "determine_failure",
        "authorize",
        "approve",
        "rollback",
        "continue_intervention",
        "recommend_action",
        "execute",
        "actuate",
    )

    for method in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionVerificationLedger,
            method,
        )