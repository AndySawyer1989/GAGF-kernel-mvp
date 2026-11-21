from __future__ import annotations

import json
import sqlite3

import pytest

from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    build_paid_work_prerequisite_record,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE,
    GovernancePaidWorkPrerequisiteRecordStore,
    GovernancePaidWorkPrerequisiteRecordStoreConflictError,
    GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
    GovernancePaidWorkPrerequisiteRecordStoreNotFoundError,
)


HIERARCHY = {
    "tenant_id": "tenant-alpha",
    "client_id": "client-acme",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}


def authorization_package() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_paid_assessment_authorization_package"
        ),
        "package_status": "ready_for_paid_assessment_authorization",
        "authorization_id": "package-001",
        "prepared_at": "2026-10-14T18:00:00+00:00",
        "human_authorization": {
            "human_operator_authorized_package": True,
            "paid_assessment_authorized": False,
        },
        "commercial_boundary": {
            "authorization_package_ready": True,
            "paid_assessment_authorized": False,
        },
    }


def contract_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "recorded_at": "2026-10-14T18:10:00+00:00",
        "execution_evidence": {
            "contract_executed": True,
        },
        "commercial_boundary": {
            "contract_executed": True,
            "paid_assessment_authorized": False,
        },
    }


def payment_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_payment_confirmation_event"
        ),
        "event_status": "payment_confirmed",
        "payment_confirmation_event_id": "payment-event-001",
        "recorded_at": "2026-10-14T18:20:00+00:00",
        "payment_confirmation_record": {
            "payment_confirmed": True,
        },
        "commercial_boundary": {
            "payment_confirmed": True,
            "paid_assessment_authorized": False,
        },
    }


def build_store(tmp_path):
    return GovernancePaidWorkPrerequisiteRecordStore(
        database_path=(
            tmp_path
            / "paid-work-prerequisites.sqlite3"
        )
    )


@pytest.mark.parametrize(
    ("kind", "factory", "artifact_id"),
    [
        (
            AUTHORIZATION_PACKAGE_KIND,
            authorization_package,
            "package-001",
        ),
        (
            CONTRACT_EXECUTION_EVENT_KIND,
            contract_event,
            "contract-event-001",
        ),
        (
            PAYMENT_CONFIRMATION_EVENT_KIND,
            payment_event,
            "payment-event-001",
        ),
    ],
)
def test_store_round_trip_for_each_prerequisite_kind(
    tmp_path,
    kind,
    factory,
    artifact_id,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=kind,
        artifact=factory(),
        **HIERARCHY,
    )

    stored = store.save(
        record=record
    )

    loaded = store.get(
        prerequisite_kind=kind,
        artifact_id=artifact_id,
    )

    assert stored == record
    assert loaded == record
    loaded.verify()


def test_duplicate_identical_record_is_idempotent(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
        artifact=authorization_package(),
        **HIERARCHY,
    )

    first = store.save(
        record=record
    )
    second = store.save(
        record=record
    )

    assert first == second
    assert first.record_hash == second.record_hash


def test_same_kind_and_artifact_id_with_different_content_conflicts(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    first = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=payment_event(),
        **HIERARCHY,
    )

    modified = payment_event()
    modified["commercial_boundary"]["extra_reviewed"] = True

    second = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=modified,
        **HIERARCHY,
    )

    store.save(
        record=first
    )

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreConflictError,
        match="different record content",
    ):
        store.save(
            record=second
        )


def test_same_artifact_id_can_exist_for_different_kinds(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    package = authorization_package()
    package["authorization_id"] = "shared-001"

    contract = contract_event()
    contract["contract_execution_event_id"] = "shared-001"

    package_record = build_paid_work_prerequisite_record(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
        artifact=package,
        **HIERARCHY,
    )
    contract_record = build_paid_work_prerequisite_record(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact=contract,
        **HIERARCHY,
    )

    store.save(
        record=package_record
    )
    store.save(
        record=contract_record
    )

    assert (
        store.get(
            prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
            artifact_id="shared-001",
        )
        == package_record
    )
    assert (
        store.get(
            prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
            artifact_id="shared-001",
        )
        == contract_record
    )


def test_get_optional_returns_none_for_missing_record(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    assert (
        store.get_optional(
            prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
            artifact_id="missing",
        )
        is None
    )


def test_get_raises_for_missing_record(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreNotFoundError,
        match="not found",
    ):
        store.get(
            prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
            artifact_id="missing",
        )


def test_require_for_issuance_accepts_exact_hierarchy(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact=contract_event(),
        **HIERARCHY,
    )

    store.save(
        record=record
    )

    resolved = store.require_for_issuance(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact_id=record.artifact_id,
        **HIERARCHY,
    )

    assert resolved == record


def test_require_for_issuance_rejects_cross_hierarchy_resolution(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact=contract_event(),
        **HIERARCHY,
    )

    store.save(
        record=record
    )

    wrong = dict(HIERARCHY)
    wrong["assessment_id"] = "assessment-other"

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
        match="hierarchy",
    ):
        store.require_for_issuance(
            prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
            artifact_id=record.artifact_id,
            **wrong,
        )


def test_tampered_record_json_is_detected(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
        artifact=authorization_package(),
        **HIERARCHY,
    )

    store.save(
        record=record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        payload = record.to_dict()
        payload["artifact"]["authorization_id"] = "tampered"

        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
            SET record_json = ?
            WHERE prerequisite_kind = ?
              AND artifact_id = ?
            """,
            (
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ),
                record.prerequisite_kind,
                record.artifact_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
        match="integrity verification",
    ):
        store.get(
            prerequisite_kind=record.prerequisite_kind,
            artifact_id=record.artifact_id,
        )


def test_tampered_indexed_hierarchy_column_is_detected(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=payment_event(),
        **HIERARCHY,
    )

    store.save(
        record=record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
            SET hierarchy_key = ?
            WHERE prerequisite_kind = ?
              AND artifact_id = ?
            """,
            (
                "tenant-alpha/client-acme/engagement-001/assessment-other",
                record.prerequisite_kind,
                record.artifact_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
        match="hierarchy_key mismatch",
    ):
        store.get(
            prerequisite_kind=record.prerequisite_kind,
            artifact_id=record.artifact_id,
        )


def test_tampered_artifact_hash_column_is_detected(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=payment_event(),
        **HIERARCHY,
    )

    store.save(
        record=record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE {GOVERNANCE_PAID_WORK_PREREQUISITE_RECORD_TABLE}
            SET artifact_hash = ?
            WHERE prerequisite_kind = ?
              AND artifact_id = ?
            """,
            (
                "0" * 64,
                record.prerequisite_kind,
                record.artifact_id,
            ),
        )
        connection.commit()

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
        match="artifact_hash mismatch",
    ):
        store.get(
            prerequisite_kind=record.prerequisite_kind,
            artifact_id=record.artifact_id,
        )


def test_store_does_not_expose_authority_creation_method(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    assert not hasattr(
        store,
        "issue"
    )
    assert not hasattr(
        store,
        "authorize"
    )
    assert not hasattr(
        store,
        "execute"
    )
