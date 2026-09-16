from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    GovernanceCustomerTrialClientReceiptObservationService,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    CustomerTrialClientReceiptObservationReceiptConflictError,
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)

from tests.test_governance_customer_trial_client_receipt_observation import (
    build_fixture,
)


def build_observation(
    tmp_path: Path,
):
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    return (
        GovernanceCustomerTrialClientReceiptObservationService()
        .observe(
            delivery_observation_receipt=(
                delivery_receipt
            ),
            commercial_client_acknowledgment=(
                commercial_result
            ),
        )
    )


def test_put_persists_client_receipt_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    assert (
        receipt.observation_status
        == "client_receipt_observed"
    )

    assert receipt.acknowledgment_id
    assert receipt.acknowledgment_artifact_hash
    assert receipt.acknowledgment_chain_hash
    assert receipt.observation_hash
    assert receipt.receipt_hash


def test_get_restores_receipt_after_restart(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "client-receipt-observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=build_observation(
            tmp_path
        )
    )

    restarted_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
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
        restored.acknowledgment_artifact_hash
        == written.acknowledgment_artifact_hash
    )


def test_put_is_idempotent_for_same_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
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


def test_put_rejects_changed_delivery_observation_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
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
        delivery_observation_hash=(
            "different-delivery-observation-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialClientReceiptObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_acknowledgment_artifact_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
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
        acknowledgment_artifact_hash=(
            "different-artifact-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialClientReceiptObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_acknowledgment_reference(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
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
        acknowledgment_reference=(
            "different-client-receipt-reference"
        ),
    )

    with pytest.raises(
        CustomerTrialClientReceiptObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_receipt_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
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
            "receipt_is_not_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_findings_acceptance"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_recommendation_acceptance"
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
            "pa006_remains_client_receipt_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa012_remains_lifecycle_persistence_authority"
        ]
        is True
    )


def test_receipt_serialization_preserves_exact_lineage(
    tmp_path: Path,
) -> None:
    observation = build_observation(
        tmp_path
    )

    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=observation
    )

    payload = receipt.to_dict()

    controlled = payload[
        "controlled_trial_lineage"
    ]

    persistence = payload[
        "persistence_lineage"
    ]

    assert (
        controlled[
            "delivery_observation_receipt_hash"
        ]
        == observation.delivery_observation_receipt_hash
    )

    assert (
        controlled[
            "delivery_observation_hash"
        ]
        == observation.delivery_observation_hash
    )

    assert (
        persistence[
            "acknowledgment_artifact_id"
        ]
        == observation.acknowledgment_artifact_id
    )

    assert (
        persistence[
            "acknowledgment_artifact_hash"
        ]
        == observation.acknowledgment_artifact_hash
    )

    assert (
        persistence[
            "acknowledgment_chain_hash"
        ]
        == observation.acknowledgment_chain_hash
    )


def test_get_missing_receipt_returns_none(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
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