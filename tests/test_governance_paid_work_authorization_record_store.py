from __future__ import annotations

import sqlite3

import pytest

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_paid_work_authorization_record import (
    build_paid_work_authorization_record,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE,
    GovernancePaidWorkAuthorizationRecordStore,
    GovernancePaidWorkAuthorizationRecordStoreConflictError,
    GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
    GovernancePaidWorkAuthorizationRecordStoreNotFoundError,
)


def build_authorization(
    *,
    authorization_id: str = "pa-001-auth-001",
    authorized_by: str = "operator-001",
) -> PaidAssessmentWorkAuthorization:
    return PaidAssessmentWorkAuthorization(
        authorization_id=authorization_id,
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        contract_execution_event_id="contract-event-001",
        authorized_by=authorized_by,
        authorized_at="2026-10-13T19:00:00+00:00",
        paid_assessment_authorized=True,
    )


def build_record(
    *,
    authorization_id: str = "pa-001-auth-001",
    authorized_by: str = "operator-001",
):
    return build_paid_work_authorization_record(
        authorization=build_authorization(
            authorization_id=authorization_id,
            authorized_by=authorized_by,
        )
    )


def test_store_round_trip(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    record = build_record()

    stored = store.save(
        record=record
    )

    loaded = store.get(
        authorization_id=record.authorization_id
    )

    assert stored == record
    assert loaded == record
    assert loaded.record_hash == record.record_hash
    assert (
        loaded.authorization_hash
        == record.authorization_hash
    )


def test_store_same_record_is_idempotent(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    record = build_record()

    first = store.save(
        record=record
    )
    second = store.save(
        record=record
    )

    assert first == second
    assert second.record_hash == record.record_hash


def test_store_rejects_same_id_with_different_record(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    first = build_record(
        authorized_by="operator-001"
    )
    conflicting = build_record(
        authorized_by="operator-002"
    )

    store.save(
        record=first
    )

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreConflictError,
        match="authorization_id already exists",
    ):
        store.save(
            record=conflicting
        )


def test_store_get_missing_fails_closed(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreNotFoundError,
        match="not found",
    ):
        store.get(
            authorization_id="missing-authorization"
        )


def test_store_get_optional_missing_returns_none(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    assert (
        store.get_optional(
            authorization_id="missing-authorization"
        )
        is None
    )


def test_store_require_for_execution_binds_hierarchy_and_contract(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    record = build_record()

    store.save(
        record=record
    )

    resolved = store.require_for_execution(
        authorization_id=record.authorization_id,
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        contract_execution_event_id="contract-event-001",
    )

    assert resolved == record


def test_store_require_for_execution_rejects_hierarchy_mismatch(
    tmp_path,
):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    record = build_record()

    store.save(
        record=record
    )

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
        match="hierarchy",
    ):
        store.require_for_execution(
            authorization_id=record.authorization_id,
            tenant_id="tenant-other",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
            contract_execution_event_id="contract-event-001",
        )


def test_store_require_for_execution_rejects_contract_event_mismatch(
    tmp_path,
):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    record = build_record()

    store.save(
        record=record
    )

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
        match="contract execution event",
    ):
        store.require_for_execution(
            authorization_id=record.authorization_id,
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
            contract_execution_event_id="contract-event-other",
        )


def test_store_detects_record_json_corruption(tmp_path):
    database_path = (
        tmp_path
        / "paid-work-authorizations.sqlite3"
    )

    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=database_path
    )

    record = build_record()

    store.save(
        record=record
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
            SET record_json = ?
            WHERE authorization_id = ?
            """,
            (
                '{"corrupted":true}',
                record.authorization_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
        match="integrity verification",
    ):
        store.get(
            authorization_id=record.authorization_id
        )


def test_store_detects_record_hash_column_corruption(tmp_path):
    database_path = (
        tmp_path
        / "paid-work-authorizations.sqlite3"
    )

    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=database_path
    )

    record = build_record()

    store.save(
        record=record
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
            SET record_hash = ?
            WHERE authorization_id = ?
            """,
            (
                "f" * 64,
                record.authorization_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
        match="record_hash mismatch",
    ):
        store.get(
            authorization_id=record.authorization_id
        )


def test_store_detects_authorization_hash_column_corruption(tmp_path):
    database_path = (
        tmp_path
        / "paid-work-authorizations.sqlite3"
    )

    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=database_path
    )

    record = build_record()

    store.save(
        record=record
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
            SET authorization_hash = ?
            WHERE authorization_id = ?
            """,
            (
                "e" * 64,
                record.authorization_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
        match="authorization_hash mismatch",
    ):
        store.get(
            authorization_id=record.authorization_id
        )


def test_store_detects_hierarchy_column_corruption(tmp_path):
    database_path = (
        tmp_path
        / "paid-work-authorizations.sqlite3"
    )

    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=database_path
    )

    record = build_record()

    store.save(
        record=record
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TABLE}
            SET hierarchy_key = ?
            WHERE authorization_id = ?
            """,
            (
                "tenant-other/client-001/engagement-001/assessment-001",
                record.authorization_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordStoreIntegrityError,
        match="hierarchy_key mismatch",
    ):
        store.get(
            authorization_id=record.authorization_id
        )


def test_store_survives_new_instance_restart(tmp_path):
    database_path = (
        tmp_path
        / "paid-work-authorizations.sqlite3"
    )

    first_store = (
        GovernancePaidWorkAuthorizationRecordStore(
            database_path=database_path
        )
    )

    record = build_record()

    first_store.save(
        record=record
    )

    second_store = (
        GovernancePaidWorkAuthorizationRecordStore(
            database_path=database_path
        )
    )

    loaded = second_store.get(
        authorization_id=record.authorization_id
    )

    assert loaded == record
    assert loaded.record_hash == record.record_hash