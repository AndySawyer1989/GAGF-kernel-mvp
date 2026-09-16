from pathlib import Path

from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_service import (
    GovernanceCustomerTrialDeliveryObservationStatusService,
)

from tests.test_governance_customer_trial_delivery_observation_receipt_store import (
    build_observation,
)


def test_status_returns_not_found_without_receipt(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=store
        )
    )

    result = service.status(
        tenant_id="tenant-missing",
        client_id="client-missing",
        engagement_id="engagement-missing",
        assessment_id="assessment-missing",
    )

    assert result.receipt_found is False
    assert result.receipt is None
    assert result.hierarchy_key is None


def test_status_returns_persisted_receipt(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    written = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=store
        )
    )

    result = service.status(
        tenant_id=written.tenant_id,
        client_id=written.client_id,
        engagement_id=written.engagement_id,
        assessment_id=written.assessment_id,
    )

    assert result.receipt_found is True
    assert result.receipt is not None

    assert (
        result.receipt.receipt_hash
        == written.receipt_hash
    )


def test_status_survives_restart(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "delivery-observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=build_observation(
            tmp_path
        )
    )

    restarted_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            database_path
        )
    )

    result = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=restarted_store
        )
        .status(
            tenant_id=written.tenant_id,
            client_id=written.client_id,
            engagement_id=written.engagement_id,
            assessment_id=written.assessment_id,
        )
    )

    assert result.receipt_found is True
    assert result.receipt is not None

    assert (
        result.receipt.receipt_hash
        == written.receipt_hash
    )


def test_status_boundaries_are_read_only(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    payload = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=store
        )
        .status(
            tenant_id="tenant",
            client_id="client",
            engagement_id="engagement",
            assessment_id="assessment",
        )
        .to_dict()
    )

    boundaries = payload["boundaries"]

    assert boundaries["status_is_read_only"] is True
    assert (
        boundaries[
            "status_does_not_create_delivery_observation"
        ]
        is True
    )
    assert (
        boundaries[
            "status_does_not_recompute_pa005_delivery"
        ]
        is True
    )
    assert (
        boundaries[
            "status_does_not_infer_observation_from_delivery_status"
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
            "status_is_not_client_receipt"
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