from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_client_response_observation import (
    GovernanceCustomerTrialClientResponseObservationService,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    CustomerTrialClientResponseObservationReceiptConflictError,
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)

from tests.test_governance_customer_trial_client_response_observation import (
    build_fixture,
)


def build_observation(
    tmp_path: Path,
):
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    return (
        GovernanceCustomerTrialClientResponseObservationService()
        .observe(
            client_receipt_observation_receipt=(
                receipt
            ),
            commercial_client_response=(
                commercial_result
            ),
        )
    )


def test_put_persists_client_response_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    assert (
        receipt.observation_status
        == "client_response_observed"
    )

    assert receipt.response_id
    assert receipt.observation_hash
    assert receipt.receipt_hash


def test_get_restores_receipt_after_restart(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "client-response-observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=build_observation(
            tmp_path
        )
    )

    restarted_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
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
        restored.response_id
        == written.response_id
    )


def test_put_is_idempotent_for_same_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
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


def test_put_rejects_changed_client_receipt_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
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
        client_receipt_observation_hash=(
            "different-client-receipt-observation-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialClientResponseObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_response_reference(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
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
        response_reference=(
            "different-response-reference"
        ),
    )

    with pytest.raises(
        CustomerTrialClientResponseObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_findings_disposition(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
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
        findings_disposition="disputed",
    )

    with pytest.raises(
        CustomerTrialClientResponseObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_receipt_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
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
            "receipt_does_not_create_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_does_not_validate_findings"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_does_not_implement_recommendations"
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
            "pa007_remains_client_response_authority"
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
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=observation
    )

    payload = receipt.to_dict()

    lineage = payload[
        "controlled_trial_lineage"
    ]

    response = payload[
        "client_response"
    ]

    assert (
        lineage[
            "client_receipt_observation_receipt_hash"
        ]
        == observation.client_receipt_observation_receipt_hash
    )

    assert (
        lineage[
            "client_receipt_observation_hash"
        ]
        == observation.client_receipt_observation_hash
    )

    assert (
        response[
            "response_id"
        ]
        == observation.response_id
    )

    assert (
        response[
            "findings_disposition"
        ]
        == observation.findings_disposition
    )

    assert (
        response[
            "recommendations_disposition"
        ]
        == observation.recommendations_disposition
    )


def test_get_missing_receipt_returns_none(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
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