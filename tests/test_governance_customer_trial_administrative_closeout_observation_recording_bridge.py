from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationService,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_recording_bridge import (
    CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError,
    GovernanceCustomerTrialAdministrativeCloseoutObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)

from tests.test_governance_customer_trial_administrative_closeout_observation import (
    build_fixture,
)


def build_bridge(
    tmp_path: Path,
):
    response_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path
            / "controlled-trial-client-response-observation.sqlite3"
        )
    )

    closeout_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path
            / "controlled-trial-administrative-closeout-observation.sqlite3"
        )
    )

    bridge = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationRecordingBridge(
            client_response_observation_receipt_store=(
                response_store
            ),
            observation_service=(
                GovernanceCustomerTrialAdministrativeCloseoutObservationService()
            ),
            observation_receipt_store=(
                closeout_store
            ),
        )
    )

    return (
        bridge,
        response_store,
        closeout_store,
    )


def test_capture_not_applicable_without_client_response_observation(
    tmp_path: Path,
) -> None:
    bridge, _, closeout_store = (
        build_bridge(
            tmp_path
        )
    )

    #
    # Commercial closeout is authoritative, but the controlled-trial
    # 09B prerequisite is intentionally stored in another directory.
    #
    _, commercial_closeout = (
        build_fixture(
            tmp_path / "different-controlled-trial"
        )
    )

    result = bridge.capture(
        commercial_closeout=(
            commercial_closeout
        )
    )

    assert result.applicable is False
    assert result.receipt is None

    assert (
        closeout_store.get(
            tenant_id=commercial_closeout.tenant_id,
            client_id=commercial_closeout.client_id,
            engagement_id=commercial_closeout.engagement_id,
            assessment_id=commercial_closeout.assessment_id,
        )
        is None
    )


def test_capture_persists_administrative_closeout_observation(
    tmp_path: Path,
) -> None:
    #
    # build_fixture seeds the 09B receipt at the exact database path
    # used by build_bridge().
    #
    response_receipt, commercial_closeout = (
        build_fixture(
            tmp_path
        )
    )

    bridge, _, closeout_store = (
        build_bridge(
            tmp_path
        )
    )

    result = bridge.capture(
        commercial_closeout=(
            commercial_closeout
        )
    )

    assert result.applicable is True
    assert result.receipt is not None

    assert (
        result.receipt.observation_status
        == "administrative_closeout_observed"
    )

    assert (
        result.receipt.controlled_trial_status
        == "controlled_trial_complete"
    )

    assert (
        result.receipt.controlled_trial_complete
        is True
    )

    assert (
        result.receipt.client_response_observation_receipt_hash
        == response_receipt.receipt_hash
    )

    assert (
        result.receipt.closeout_artifact_hash
        == commercial_closeout.closeout_artifact_hash
    )

    restored = closeout_store.get(
        tenant_id=commercial_closeout.tenant_id,
        client_id=commercial_closeout.client_id,
        engagement_id=commercial_closeout.engagement_id,
        assessment_id=commercial_closeout.assessment_id,
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == result.receipt.receipt_hash
    )


def test_capture_is_idempotent(
    tmp_path: Path,
) -> None:
    _, commercial_closeout = (
        build_fixture(
            tmp_path
        )
    )

    bridge, _, _ = (
        build_bridge(
            tmp_path
        )
    )

    first = bridge.capture(
        commercial_closeout=(
            commercial_closeout
        )
    )

    second = bridge.capture(
        commercial_closeout=(
            commercial_closeout
        )
    )

    assert first.receipt is not None
    assert second.receipt is not None

    assert (
        second.receipt.receipt_hash
        == first.receipt.receipt_hash
    )


def test_capture_rejects_wrong_result_type(
    tmp_path: Path,
) -> None:
    bridge, _, _ = (
        build_bridge(
            tmp_path
        )
    )

    with pytest.raises(
        CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError,
        match="commercial_closeout",
    ):
        bridge.capture(
            commercial_closeout=object()
        )


def test_bridge_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    bridge, _, _ = (
        build_bridge(
            tmp_path
        )
    )

    _, commercial_closeout = (
        build_fixture(
            tmp_path / "ordinary-paid-assessment"
        )
    )

    result = bridge.capture(
        commercial_closeout=(
            commercial_closeout
        )
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "bridge_observes_existing_pa010_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_create_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "controlled_trial_complete_is_administrative_only"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_implement_recommendations"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_authorize_intervention"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_verify_causation"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_verify_roi"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_verify_customer_outcome"
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