from __future__ import annotations

import sqlite3

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_operator_result_store import (
    CommercialPaidAssessmentOperatorResultStoreError,
    GovernanceCommercialPaidAssessmentOperatorResultStore,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def build_operator_result():
    return {
        "operator_run_passed": True,
        "result": {
            "disposition": "executed",
            "attempt_hash": "d" * 64,
            "record_hash": "e" * 64,
            "hierarchy_key": (
                "tenant-001/client-001/"
                "engagement-001/assessment-001"
            ),
            "artifact_count_after": 10,
            "execution_result": {
                "execution_status": "complete"
            },
        },
    }


def build_store(tmp_path):
    return GovernanceCommercialPaidAssessmentOperatorResultStore(
        database_path=tmp_path / "operator-results.sqlite3"
    )


def put(store, operator_result=None):
    return store.put(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        execution_status_hash=HASH_A,
        execution_input_binding_hash=HASH_B,
        assessment_execution_request_hash=HASH_C,
        operator_result=(
            operator_result
            if operator_result is not None
            else build_operator_result()
        ),
    )


def test_store_round_trips_exact_operator_result(tmp_path):
    store = build_store(tmp_path)
    expected = build_operator_result()

    written = put(store, expected)

    restored = store.get(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert restored is not None
    assert restored.operator_result == expected
    assert restored.snapshot_hash == written.snapshot_hash
    assert restored.operator_result_hash == written.operator_result_hash


def test_store_is_idempotent_for_identical_snapshot(tmp_path):
    store = build_store(tmp_path)

    first = put(store)
    second = put(store)

    assert second.snapshot_hash == first.snapshot_hash


def test_store_allows_same_attempt_to_advance_disposition(tmp_path):
    store = build_store(tmp_path)

    first = put(store)

    changed = build_operator_result()
    changed["result"]["disposition"] = "reconciled"

    second = put(store, changed)

    assert second.snapshot_hash != first.snapshot_hash
    assert (
        second.operator_result["result"]["disposition"]
        == "reconciled"
    )


def test_store_rejects_different_attempt_replacement(tmp_path):
    store = build_store(tmp_path)

    put(store)

    changed = build_operator_result()
    changed["result"]["attempt_hash"] = "f" * 64

    with pytest.raises(
        CommercialPaidAssessmentOperatorResultStoreError,
        match="different governed PA015 attempt_hash",
    ):
        put(store, changed)

def test_store_rejects_unsuccessful_operator_result(tmp_path):
    store = build_store(tmp_path)

    payload = build_operator_result()
    payload["operator_run_passed"] = False

    with pytest.raises(
        CommercialPaidAssessmentOperatorResultStoreError,
        match="successful PA015 operator run",
    ):
        put(store, payload)


def test_store_rejects_hierarchy_mismatch(tmp_path):
    store = build_store(tmp_path)

    payload = build_operator_result()
    payload["result"]["hierarchy_key"] = "wrong/hierarchy/value/here"

    with pytest.raises(
        CommercialPaidAssessmentOperatorResultStoreError,
        match="hierarchy",
    ):
        put(store, payload)


def test_store_detects_payload_tampering(tmp_path):
    store = build_store(tmp_path)
    put(store)

    with sqlite3.connect(store.database_path) as connection:
        row = connection.execute(
            """
            SELECT hierarchy_key, operator_result_json
            FROM governance_commercial_paid_assessment_operator_results
            """
        ).fetchone()

        assert row is not None

        tampered = row[1].replace(
            '"disposition":"executed"',
            '"disposition":"reconciled"',
        )

        connection.execute(
            """
            UPDATE governance_commercial_paid_assessment_operator_results
            SET operator_result_json = ?
            WHERE hierarchy_key = ?
            """,
            (tampered, row[0]),
        )
        connection.commit()

    with pytest.raises(
        CommercialPaidAssessmentOperatorResultStoreError,
        match="payload hash",
    ):
        store.get(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
