from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    CustomerTrialDeliveryObservationReceiptConflictError,
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)

from tests.test_governance_customer_trial_delivery_observation import (
    build_fixture,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    GovernanceCustomerTrialDeliveryObservationService,
)


def build_observation(
    tmp_path: Path,
):
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    return (
        GovernanceCustomerTrialDeliveryObservationService()
        .observe(
            readiness_receipt=(
                readiness_receipt
            ),
            commercial_delivery_recording=(
                recording
            ),
        )
    )


def test_put_persists_delivery_observation_receipt(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    assert (
        receipt.observation_status
        == "delivery_observed"
    )

    assert receipt.delivery_event_id
    assert receipt.delivery_event_hash
    assert receipt.observation_hash
    assert receipt.receipt_hash


def test_get_restores_persisted_receipt_after_restart(
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

    restored = restarted_store.get(
        tenant_id=written.tenant_id,
        client_id=written.client_id,
        engagement_id=written.engagement_id,
        assessment_id=written.assessment_id,
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == written.receipt_hash
    )

    assert (
        restored.observation_hash
        == written.observation_hash
    )

    assert (
        restored.delivery_event_hash
        == written.delivery_event_hash
    )


def test_put_is_idempotent_for_same_delivery_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    observation = build_observation(
        tmp_path
    )

    first = store.put(
        observation=observation
    )

    second = store.put(
        observation=observation
    )

    assert (
        second.receipt_hash
        == first.receipt_hash
    )


def test_put_rejects_changed_delivery_event_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    observation = build_observation(
        tmp_path
    )

    store.put(
        observation=observation
    )

    changed = replace(
        observation,
        delivery_event_hash=(
            "different-delivery-event-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_readiness_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    observation = build_observation(
        tmp_path
    )

    store.put(
        observation=observation
    )

    changed = replace(
        observation,
        delivery_readiness_hash=(
            "different-readiness-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_human_confirmation_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    observation = build_observation(
        tmp_path
    )

    store.put(
        observation=observation
    )

    changed = replace(
        observation,
        human_delivery_confirmation_hash=(
            "different-confirmation-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_receipt_boundaries_are_audit_only(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=build_observation(
            tmp_path
        )
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
            "receipt_is_not_client_response"
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
            "pa005_remains_delivery_event_authority"
        ]
        is True
    )


def test_receipt_serialization_preserves_delivery_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    observation = build_observation(
        tmp_path
    )

    receipt = store.put(
        observation=observation
    )

    payload = receipt.to_dict()

    controlled = payload[
        "controlled_trial_lineage"
    ]

    delivery = payload[
        "delivery_lineage"
    ]

    assert (
        controlled[
            "delivery_readiness_receipt_hash"
        ]
        == observation.delivery_readiness_receipt_hash
    )

    assert (
        controlled[
            "delivery_readiness_hash"
        ]
        == observation.delivery_readiness_hash
    )

    assert (
        delivery[
            "delivery_event_id"
        ]
        == observation.delivery_event_id
    )

    assert (
        delivery[
            "delivery_event_hash"
        ]
        == observation.delivery_event_hash
    )

    assert (
        delivery[
            "human_delivery_confirmation_hash"
        ]
        == observation.human_delivery_confirmation_hash
    )

    assert (
        delivery[
            "approved_delivery_snapshot_hash"
        ]
        == observation.approved_delivery_snapshot_hash
    )


def test_get_missing_receipt_returns_none(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    assert (
        store.get(
            tenant_id="missing-tenant",
            client_id="missing-client",
            engagement_id="missing-engagement",
            assessment_id="missing-assessment",
        )
        is None
    )