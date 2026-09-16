from dataclasses import replace

import pytest

from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    CONTROLLED_TRIAL_DELIVERY_READY,
    CustomerTrialDeliveryReadiness,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    CustomerTrialDeliveryReadinessReceiptConflictError,
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)


def build_readiness(
) -> CustomerTrialDeliveryReadiness:
    return CustomerTrialDeliveryReadiness(
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

        readiness_status=(
            CONTROLLED_TRIAL_DELIVERY_READY
        ),

        observation_receipt_hash=
            "observation-receipt-hash",
        observation_hash=
            "observation-hash",

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

        execution_status_hash=
            "execution-status-hash",
        operator_result_hash=
            "operator-result-hash",
        operator_snapshot_hash=
            "operator-snapshot-hash",

        delivery_readiness_status=(
            "ready_for_delivery_approval_review"
        ),
        recovery_disposition="executed",
        artifact_count=10,
        repository_chain_valid=True,
    )


def test_put_persists_delivery_readiness_receipt(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    receipt = store.put(
        readiness=build_readiness()
    )

    assert (
        receipt.readiness_status
        == CONTROLLED_TRIAL_DELIVERY_READY
    )

    assert (
        receipt.observation_receipt_hash
        == "observation-receipt-hash"
    )

    assert (
        receipt.execution_result_hash
        == "execution-result-hash"
    )

    assert (
        receipt.delivery_readiness_status
        == "ready_for_delivery_approval_review"
    )

    assert (
        receipt.repository_chain_valid
        is True
    )

    assert receipt.readiness_hash
    assert receipt.receipt_hash


def test_get_restores_persisted_receipt(
    tmp_path,
):
    database_path = (
        tmp_path / "delivery-readiness.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        readiness=build_readiness()
    )

    restarted_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
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

    assert (
        restored.receipt_hash
        == written.receipt_hash
    )

    assert (
        restored.readiness_hash
        == written.readiness_hash
    )

    assert (
        restored.observation_receipt_hash
        == written.observation_receipt_hash
    )

    assert (
        restored.execution_status_hash
        == written.execution_status_hash
    )


def test_put_is_idempotent_for_same_readiness(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    first = store.put(
        readiness=build_readiness()
    )

    second = store.put(
        readiness=build_readiness()
    )

    assert (
        second.receipt_hash
        == first.receipt_hash
    )


def test_put_rejects_changed_execution_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    store.put(
        readiness=build_readiness()
    )

    changed = replace(
        build_readiness(),
        execution_result_hash=(
            "different-execution-result-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessReceiptConflictError
    ):
        store.put(
            readiness=changed
        )


def test_put_rejects_changed_observation_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    store.put(
        readiness=build_readiness()
    )

    changed = replace(
        build_readiness(),
        observation_receipt_hash=(
            "different-observation-receipt-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessReceiptConflictError
    ):
        store.put(
            readiness=changed
        )


def test_put_rejects_changed_commercial_readiness_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    store.put(
        readiness=build_readiness()
    )

    changed = replace(
        build_readiness(),
        execution_status_hash=(
            "different-execution-status-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessReceiptConflictError
    ):
        store.put(
            readiness=changed
        )


def test_receipt_boundaries_are_evidence_only(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    receipt = store.put(
        readiness=build_readiness()
    )

    boundaries = receipt.boundaries

    assert (
        boundaries[
            "receipt_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_delivery_approval"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_approved_for_human_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_delivery_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_client_receipt"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa003_remains_delivery_readiness_authority"
        ]
        is True
    )


def test_receipt_serialization_preserves_lineage(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    receipt = store.put(
        readiness=build_readiness()
    )

    payload = receipt.to_dict()

    assert (
        payload[
            "observation_receipt_hash"
        ]
        == "observation-receipt-hash"
    )

    controlled_trial_lineage = (
        payload[
            "controlled_trial_lineage"
        ]
    )

    assert (
        controlled_trial_lineage[
            "handoff_hash"
        ]
        == "handoff-hash"
    )

    assert (
        controlled_trial_lineage[
            "assessment_execution_request_hash"
        ]
        == "execution-request-hash"
    )

    execution_lineage = (
        payload[
            "execution_lineage"
        ]
    )

    assert (
        execution_lineage[
            "execution_result_hash"
        ]
        == "execution-result-hash"
    )

    commercial_readiness = (
        payload[
            "commercial_readiness"
        ]
    )

    assert (
        commercial_readiness[
            "execution_status_hash"
        ]
        == "execution-status-hash"
    )

    assert (
        commercial_readiness[
            "repository_chain_valid"
        ]
        is True
    )


def test_get_returns_none_when_receipt_missing(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    restored = store.get(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="missing-assessment",
    )

    assert restored is None