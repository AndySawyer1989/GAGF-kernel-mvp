from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_service import (
    GovernanceCustomerTrialDeliveryReadinessStatusService,
)

from tests.test_governance_customer_trial_delivery_readiness_receipt_store import (
    build_readiness,
)


def test_status_returns_not_found_without_readiness(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=store
        )
    )

    result = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert result.receipt_found is False
    assert result.receipt is None
    assert result.hierarchy_key is None


def test_status_returns_durable_readiness_receipt(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    written = store.put(
        readiness=build_readiness()
    )

    service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=store
        )
    )

    result = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert result.receipt_found is True
    assert result.receipt is not None

    assert (
        result.receipt.receipt_hash
        == written.receipt_hash
    )


def test_status_survives_store_restart(
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

    service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=restarted_store
        )
    )

    result = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert result.receipt_found is True
    assert result.receipt is not None

    assert (
        result.receipt.receipt_hash
        == written.receipt_hash
    )


def test_status_boundaries_are_read_only(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=store
        )
    )

    payload = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "status_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "status_does_not_create_readiness"
        ]
        is True
    )

    assert (
        boundaries[
            "status_does_not_recompute_pa003_readiness"
        ]
        is True
    )

    assert (
        boundaries[
            "status_does_not_infer_readiness_from_execution_observation"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_delivery_approval"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_approved_for_human_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_delivery_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_intervention_authority"
        ]
        is True
    )