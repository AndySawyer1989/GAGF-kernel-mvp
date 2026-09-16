from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationService,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    CustomerTrialAdministrativeCloseoutObservationReceiptConflictError,
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)

from tests.test_governance_customer_trial_administrative_closeout_observation import (
    build_fixture,
)


def build_observation(
    tmp_path: Path,
):
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    return (
        GovernanceCustomerTrialAdministrativeCloseoutObservationService()
        .observe(
            client_response_observation_receipt=(
                response_receipt
            ),
            commercial_closeout=(
                commercial_closeout
            ),
        )
    )


def test_put_persists_administrative_closeout_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    assert (
        receipt.observation_status
        == "administrative_closeout_observed"
    )

    assert (
        receipt.controlled_trial_status
        == "controlled_trial_complete"
    )

    assert (
        receipt.controlled_trial_complete
        is True
    )

    assert receipt.closeout_artifact_id
    assert receipt.closeout_artifact_hash
    assert receipt.observation_hash
    assert receipt.receipt_hash

    assert (
        receipt.repository_chain_valid
        is True
    )


def test_get_restores_receipt_after_restart(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "administrative-closeout-observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=build_observation(
            tmp_path
        )
    )

    restarted_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
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
        restored.closeout_artifact_hash
        == written.closeout_artifact_hash
    )

    assert (
        restored.controlled_trial_complete
        is True
    )


def test_put_is_idempotent_for_same_observation(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
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


def test_put_rejects_changed_client_response_lineage(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
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
        client_response_observation_hash=(
            "different-client-response-observation-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialAdministrativeCloseoutObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_closeout_artifact_hash(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
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
        closeout_artifact_hash=(
            "different-closeout-artifact-hash"
        ),
    )

    with pytest.raises(
        CustomerTrialAdministrativeCloseoutObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_put_rejects_changed_closeout_reason(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
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
        closeout_reason=(
            "Different administrative closeout reason."
        ),
    )

    with pytest.raises(
        CustomerTrialAdministrativeCloseoutObservationReceiptConflictError
    ):
        store.put(
            observation=changed
        )


def test_receipt_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
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
            "receipt_does_not_create_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_complete_is_administrative_only"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_complete_is_not_recommendation_implementation"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_complete_is_not_intervention_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_complete_is_not_causal_success"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_complete_is_not_roi_verification"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_complete_is_not_customer_outcome_verification"
        ]
        is True
    )

    assert (
        boundaries[
            "pa010_remains_administrative_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa012_remains_lifecycle_persistence_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa013_remains_operator_coordination_authority"
        ]
        is True
    )


def test_receipt_serialization_preserves_exact_closeout_lineage(
    tmp_path: Path,
) -> None:
    observation = build_observation(
        tmp_path
    )

    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
        )
    )

    receipt = store.put(
        observation=observation
    )

    payload = receipt.to_dict()

    lineage = payload[
        "controlled_trial_lineage"
    ]

    closeout = payload[
        "administrative_closeout"
    ]

    completion = payload[
        "trial_completion"
    ]

    assert (
        lineage[
            "client_response_observation_receipt_hash"
        ]
        == observation.client_response_observation_receipt_hash
    )

    assert (
        lineage[
            "client_response_observation_hash"
        ]
        == observation.client_response_observation_hash
    )

    assert (
        closeout[
            "closeout_artifact_id"
        ]
        == observation.closeout_artifact_id
    )

    assert (
        closeout[
            "closeout_artifact_hash"
        ]
        == observation.closeout_artifact_hash
    )

    assert (
        closeout[
            "repository_chain_valid"
        ]
        is True
    )

    assert (
        completion[
            "controlled_trial_complete"
        ]
        is True
    )


def test_get_missing_receipt_returns_none(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
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