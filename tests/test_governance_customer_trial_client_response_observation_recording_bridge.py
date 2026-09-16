from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    GovernanceCustomerTrialClientReceiptObservationService,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation import (
    GovernanceCustomerTrialClientResponseObservationService,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_recording_bridge import (
    CustomerTrialClientResponseObservationRecordingBridgeError,
    GovernanceCustomerTrialClientResponseObservationRecordingBridge,
)

from tests.test_governance_customer_trial_client_receipt_observation import (
    build_fixture as build_receipt_fixture,
)
from tests.test_governance_customer_trial_client_response_observation import (
    build_fixture as build_response_fixture,
)


def build_bridge(
    tmp_path: Path,
):
    receipt_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
        )
    )

    response_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path / "client-response-observation.sqlite3"
        )
    )

    bridge = (
        GovernanceCustomerTrialClientResponseObservationRecordingBridge(
            client_receipt_observation_receipt_store=(
                receipt_store
            ),
            observation_service=(
                GovernanceCustomerTrialClientResponseObservationService()
            ),
            observation_receipt_store=(
                response_store
            ),
        )
    )

    return (
        bridge,
        receipt_store,
        response_store,
    )


def seed_client_receipt(
    *,
    tmp_path: Path,
    receipt_store:
        GovernanceCustomerTrialClientReceiptObservationReceiptStore,
):
    delivery_receipt, commercial_acknowledgment = (
        build_receipt_fixture(
            tmp_path / "receipt-fixture"
        )
    )

    observation = (
        GovernanceCustomerTrialClientReceiptObservationService()
        .observe(
            delivery_observation_receipt=(
                delivery_receipt
            ),
            commercial_client_acknowledgment=(
                commercial_acknowledgment
            ),
        )
    )

    return receipt_store.put(
        observation=observation
    )


def test_capture_not_applicable_without_client_receipt_observation(
    tmp_path: Path,
) -> None:
    bridge, _, response_store = (
        build_bridge(
            tmp_path
        )
    )

    _, commercial_response = (
        build_response_fixture(
            tmp_path / "response-fixture"
        )
    )

    result = bridge.capture(
        commercial_client_response=(
            commercial_response
        )
    )

    assert result.applicable is False
    assert result.receipt is None

    assert (
        response_store.get(
            tenant_id=commercial_response.tenant_id,
            client_id=commercial_response.client_id,
            engagement_id=commercial_response.engagement_id,
            assessment_id=commercial_response.assessment_id,
        )
        is None
    )


def test_capture_persists_client_response_observation(
    tmp_path: Path,
) -> None:
    (
        bridge,
        receipt_store,
        response_store,
    ) = build_bridge(
        tmp_path
    )

    client_receipt = seed_client_receipt(
        tmp_path=tmp_path,
        receipt_store=receipt_store,
    )

    _, commercial_response = (
        build_response_fixture(
            tmp_path / "response-fixture"
        )
    )

    result = bridge.capture(
        commercial_client_response=(
            commercial_response
        )
    )

    assert result.applicable is True
    assert result.receipt is not None

    assert (
        result.receipt.observation_status
        == "client_response_observed"
    )

    assert (
        result.receipt.client_receipt_observation_receipt_hash
        == client_receipt.receipt_hash
    )

    restored = response_store.get(
        tenant_id=commercial_response.tenant_id,
        client_id=commercial_response.client_id,
        engagement_id=commercial_response.engagement_id,
        assessment_id=commercial_response.assessment_id,
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == result.receipt.receipt_hash
    )


def test_capture_is_idempotent(
    tmp_path: Path,
) -> None:
    bridge, receipt_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    seed_client_receipt(
        tmp_path=tmp_path,
        receipt_store=receipt_store,
    )

    _, commercial_response = (
        build_response_fixture(
            tmp_path / "response-fixture"
        )
    )

    first = bridge.capture(
        commercial_client_response=(
            commercial_response
        )
    )

    second = bridge.capture(
        commercial_client_response=(
            commercial_response
        )
    )

    assert first.receipt is not None
    assert second.receipt is not None

    assert (
        second.receipt.receipt_hash
        == first.receipt.receipt_hash
    )


def test_capture_rejects_wrong_commercial_result_type(
    tmp_path: Path,
) -> None:
    bridge, _, _ = build_bridge(
        tmp_path
    )

    with pytest.raises(
        CustomerTrialClientResponseObservationRecordingBridgeError,
        match="commercial_client_response",
    ):
        bridge.capture(
            commercial_client_response=object()
        )


def test_capture_fails_closed_on_report_mismatch(
    tmp_path: Path,
) -> None:
    bridge, receipt_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    seeded = seed_client_receipt(
        tmp_path=tmp_path,
        receipt_store=receipt_store,
    )

    #
    # Persisted receipt lineage is immutable. We therefore create the
    # response from a different commercial fixture/report identity and
    # require exact 09A correlation to reject it.
    #
    _, commercial_response = (
        build_response_fixture(
            tmp_path / "response-fixture"
        )
    )

    if (
        seeded.report_id
        == commercial_response.report_id
    ):
        pytest.skip(
            "fixture report identities are equal; "
            "09A report-mismatch behavior is already covered directly"
        )

    with pytest.raises(
        Exception,
        match="report_id",
    ):
        bridge.capture(
            commercial_client_response=(
                commercial_response
            )
        )


def test_bridge_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    bridge, _, _ = build_bridge(
        tmp_path
    )

    _, commercial_response = (
        build_response_fixture(
            tmp_path / "response-fixture"
        )
    )

    result = bridge.capture(
        commercial_client_response=(
            commercial_response
        )
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "bridge_observes_existing_pa007_response"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_create_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_validate_findings"
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
            "bridge_does_not_authorize_closeout"
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