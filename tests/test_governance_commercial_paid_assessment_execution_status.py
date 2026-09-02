import sqlite3
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_execution_status import (
    EXECUTION_STATUS_TABLE,
    CommercialPaidAssessmentExecutionStatusConflictError,
    CommercialPaidAssessmentExecutionStatusError,
    GovernanceCommercialPaidAssessmentExecutionStatusStore,
)


FIXED_TIME = datetime(
    2026,
    9,
    1,
    21,
    45,
    tzinfo=timezone.utc,
)


def build_status(
    store,
    *,
    disposition="executed",
    attempt_hash="attempt-001",
    artifact_count_before=0,
    artifact_count_after=10,
):
    return store.build_status(
        tenant_id="tenant-alpha",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        disposition=disposition,
        attempt_hash=attempt_hash,
        attempt_record_hash="record-001",
        assessment_execution_request_hash="request-001",
        execution_input_binding_hash="binding-001",
        artifact_count_before=artifact_count_before,
        artifact_count_after=artifact_count_after,
        recorded_at=FIXED_TIME,
    )


def test_build_status_is_deterministic():
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            "unused.sqlite3"
        )
    )

    first = build_status(
        store
    )

    second = build_status(
        store
    )

    assert (
        first.status_hash
        == second.status_hash
    )

    assert (
        first.hierarchy_key
        == (
            "tenant-alpha/"
            "client-001/"
            "engagement-001/"
            "assessment-001"
        )
    )


def test_status_boundaries_are_non_authoritative():
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            "unused.sqlite3"
        )
    )

    status = build_status(
        store
    ).to_dict()

    assert (
        status["boundaries"]
        ["status_is_read_only_evidence"]
        is True
    )

    assert (
        status["boundaries"]
        ["status_is_not_execution_authority"]
        is True
    )

    assert (
        status["boundaries"]
        ["status_is_not_recovery_authority"]
        is True
    )

    assert (
        status["boundaries"]
        ["status_does_not_expose_raw_evidence"]
        is True
    )


@pytest.mark.parametrize(
    "disposition",
    [
        "executed",
        "resumed",
        "reconciled",
    ],
)
def test_all_governed_dispositions_are_supported(
    disposition,
):
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            "unused.sqlite3"
        )
    )

    status = build_status(
        store,
        disposition=disposition,
    )

    assert (
        status.disposition
        == disposition
    )


def test_invalid_disposition_fails_closed():
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            "unused.sqlite3"
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionStatusError
    ):
        build_status(
            store,
            disposition="completed",
        )


def test_negative_artifact_count_fails_closed():
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            "unused.sqlite3"
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionStatusError
    ):
        build_status(
            store,
            artifact_count_before=-1,
        )


def test_artifact_count_regression_fails_closed():
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            "unused.sqlite3"
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionStatusError
    ):
        build_status(
            store,
            artifact_count_before=10,
            artifact_count_after=9,
        )


def test_missing_status_returns_none(
    tmp_path,
):
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            tmp_path
            / "status.sqlite3"
        )
    )

    result = store.get_status(
        tenant_id="tenant-alpha",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert result is None


def test_record_and_read_status(
    tmp_path,
):
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            tmp_path
            / "status.sqlite3"
        )
    )

    expected = build_status(
        store
    )

    store.record_status(
        status=expected
    )

    actual = store.get_status(
        tenant_id="tenant-alpha",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert actual is not None

    assert (
        actual.to_dict()
        == expected.to_dict()
    )


def test_same_attempt_can_update_to_reconciled(
    tmp_path,
):
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            tmp_path
            / "status.sqlite3"
        )
    )

    first = build_status(
        store,
        disposition="executed",
        artifact_count_before=0,
        artifact_count_after=10,
    )

    store.record_status(
        status=first
    )

    second = store.build_status(
        tenant_id="tenant-alpha",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        disposition="reconciled",
        attempt_hash="attempt-001",
        attempt_record_hash="record-001",
        assessment_execution_request_hash="request-001",
        execution_input_binding_hash="binding-001",
        artifact_count_before=10,
        artifact_count_after=10,
        recorded_at=datetime(
            2026,
            9,
            1,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )

    store.record_status(
        status=second
    )

    actual = store.get_status(
        tenant_id="tenant-alpha",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert actual is not None
    assert (
        actual.disposition
        == "reconciled"
    )
    assert (
        actual.artifact_count_before
        == 10
    )
    assert (
        actual.artifact_count_after
        == 10
    )


def test_different_attempt_cannot_replace_status(
    tmp_path,
):
    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            tmp_path
            / "status.sqlite3"
        )
    )

    first = build_status(
        store
    )

    store.record_status(
        status=first
    )

    conflicting = build_status(
        store,
        attempt_hash="attempt-999",
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionStatusConflictError
    ):
        store.record_status(
            status=conflicting
        )


def test_tampered_status_fails_hash_verification(
    tmp_path,
):
    path = (
        tmp_path
        / "status.sqlite3"
    )

    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            path
        )
    )

    status = build_status(
        store
    )

    store.record_status(
        status=status
    )

    with sqlite3.connect(
        path
    ) as connection:
        connection.execute(
            f"""
            UPDATE {EXECUTION_STATUS_TABLE}
            SET disposition = ?
            WHERE tenant_id = ?
              AND client_id = ?
              AND engagement_id = ?
              AND assessment_id = ?
            """,
            (
                "reconciled",
                "tenant-alpha",
                "client-001",
                "engagement-001",
                "assessment-001",
            ),
        )

    with pytest.raises(
        CommercialPaidAssessmentExecutionStatusError,
        match=(
            "stored execution-status hash "
            "verification failed"
        ),
    ):
        store.get_status(
            tenant_id="tenant-alpha",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )


def test_status_table_contains_one_row_per_hierarchy(
    tmp_path,
):
    path = (
        tmp_path
        / "status.sqlite3"
    )

    store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            path
        )
    )

    status = build_status(
        store
    )

    store.record_status(
        status=status
    )

    store.record_status(
        status=status
    )

    with sqlite3.connect(
        path
    ) as connection:
        count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {EXECUTION_STATUS_TABLE}
            """
        ).fetchone()[0]

    assert count == 1