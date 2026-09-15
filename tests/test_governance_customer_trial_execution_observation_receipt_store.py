from dataclasses import replace

import pytest

from backend.app.gagf.governance_customer_trial_execution_observation import (
    CustomerTrialExecutionObservation,
    EXECUTION_OBSERVED,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    CustomerTrialExecutionObservationReceiptConflictError,
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)


def build_observation(
) -> CustomerTrialExecutionObservation:
    return CustomerTrialExecutionObservation(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
        hierarchy_key=(
            "tenant-controlled/"
            "client-controlled/"
            "engagement-controlled/"
            "assessment-controlled"
        ),
        observation_status=
            EXECUTION_OBSERVED,
        handoff_receipt_hash=
            "handoff-receipt-hash",
        handoff_lineage_hash=
            "handoff-lineage-hash",
        handoff_hash=
            "handoff-hash",
        assessment_execution_request_hash=
            "execution-request-hash",
        execution_result_hash=
            "execution-result-hash",
        application_hash=
            "application-hash",
        persistence_hash=
            "persistence-hash",
        report_id=
            "report-controlled",
        report_package_hash=
            "report-package-hash",
        application_completed=
            True,
        repository_chain_valid=
            True,
    )


def test_put_persists_observation_receipt(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=
            build_observation()
    )

    assert receipt.observation_status == (
        EXECUTION_OBSERVED
    )

    assert receipt.handoff_hash == (
        "handoff-hash"
    )

    assert (
        receipt.assessment_execution_request_hash
        == "execution-request-hash"
    )

    assert receipt.execution_result_hash == (
        "execution-result-hash"
    )

    assert receipt.receipt_hash


def test_get_restores_persisted_receipt(
    tmp_path,
):
    database_path = (
        tmp_path / "observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=
            build_observation()
    )

    restarted_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            database_path
        )
    )

    restored = restarted_store.get(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert restored is not None

    assert restored.receipt_hash == (
        written.receipt_hash
    )

    assert restored.observation_hash == (
        written.observation_hash
    )


def test_put_is_idempotent_for_same_observation(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    first = store.put(
        observation=
            build_observation()
    )

    second = store.put(
        observation=
            build_observation()
    )

    assert second.receipt_hash == (
        first.receipt_hash
    )


def test_put_rejects_changed_execution_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    store.put(
        observation=
            build_observation()
    )

    changed = replace(
        build_observation(),
        execution_result_hash=
            "different-execution-result-hash",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationReceiptConflictError
    ):
        store.put(
            observation=
                changed
        )


def test_put_rejects_changed_handoff_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    store.put(
        observation=
            build_observation()
    )

    changed = replace(
        build_observation(),
        handoff_hash=
            "different-handoff-hash",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationReceiptConflictError
    ):
        store.put(
            observation=
                changed
        )


def test_receipt_boundaries_are_audit_only(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=
            build_observation()
    )

    boundaries = receipt.boundaries

    assert boundaries[
        "receipt_is_audit_evidence_only"
    ] is True

    assert boundaries[
        "receipt_is_not_execution_authority"
    ] is True

    assert boundaries[
        "receipt_is_not_recovery_authority"
    ] is True

    assert boundaries[
        "receipt_is_not_delivery_authority"
    ] is True

    assert boundaries[
        "receipt_is_not_closeout_authority"
    ] is True

    assert boundaries[
        "receipt_is_not_intervention_authority"
    ] is True


def test_receipt_serialization_preserves_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=
            build_observation()
    )

    payload = receipt.to_dict()

    assert payload[
        "handoff_receipt_hash"
    ] == "handoff-receipt-hash"

    lineage = payload[
        "execution_lineage"
    ]

    assert isinstance(
        lineage,
        dict,
    )

    assert lineage[
        "handoff_hash"
    ] == "handoff-hash"

    assert lineage[
        "assessment_execution_request_hash"
    ] == "execution-request-hash"

    assert lineage[
        "execution_result_hash"
    ] == "execution-result-hash"


def test_get_returns_none_when_receipt_missing(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    restored = store.get(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="missing-assessment",
    )

    assert restored is None