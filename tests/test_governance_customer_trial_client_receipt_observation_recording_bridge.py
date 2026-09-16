from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    GovernanceCustomerTrialClientReceiptObservationService,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_recording_bridge import (
    CustomerTrialClientReceiptObservationRecordingBridgeError,
    GovernanceCustomerTrialClientReceiptObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    CustomerTrialDeliveryObservation,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)

from tests.test_governance_customer_trial_client_receipt_observation import (
    build_fixture,
)


def build_bridge(
    tmp_path: Path,
):
    delivery_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    receipt_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            tmp_path / "client-receipt-observation.sqlite3"
        )
    )

    bridge = (
        GovernanceCustomerTrialClientReceiptObservationRecordingBridge(
            delivery_observation_receipt_store=(
                delivery_store
            ),
            observation_service=(
                GovernanceCustomerTrialClientReceiptObservationService()
            ),
            observation_receipt_store=(
                receipt_store
            ),
        )
    )

    return (
        bridge,
        delivery_store,
        receipt_store,
    )


def seed_delivery_observation(
    *,
    delivery_store:
        GovernanceCustomerTrialDeliveryObservationReceiptStore,
    source_receipt,
):
    observation = (
        CustomerTrialDeliveryObservation(
            tenant_id=
                source_receipt.tenant_id,
            client_id=
                source_receipt.client_id,
            engagement_id=
                source_receipt.engagement_id,
            assessment_id=
                source_receipt.assessment_id,
            hierarchy_key=
                source_receipt.hierarchy_key,

            observation_status=
                source_receipt.observation_status,

            delivery_readiness_receipt_hash=(
                source_receipt
                .delivery_readiness_receipt_hash
            ),
            delivery_readiness_hash=(
                source_receipt
                .delivery_readiness_hash
            ),

            delivery_event_id=
                source_receipt.delivery_event_id,
            delivery_event_hash=
                source_receipt.delivery_event_hash,

            report_id=
                source_receipt.report_id,

            delivered_by=
                source_receipt.delivered_by,
            delivered_at=
                source_receipt.delivered_at,
            delivery_method=
                source_receipt.delivery_method,
            delivery_reference=
                source_receipt.delivery_reference,

            human_delivery_confirmation_hash=(
                source_receipt
                .human_delivery_confirmation_hash
            ),
            approved_delivery_snapshot_hash=(
                source_receipt
                .approved_delivery_snapshot_hash
            ),
        )
    )

    return delivery_store.put(
        observation=observation
    )


def test_capture_not_applicable_without_delivery_observation(
    tmp_path: Path,
) -> None:
    bridge, _, receipt_store = (
        build_bridge(
            tmp_path
        )
    )

    _, commercial_result = (
        build_fixture(
            tmp_path / "fixture"
        )
    )

    result = bridge.capture(
        commercial_client_acknowledgment=(
            commercial_result
        )
    )

    assert result.applicable is False
    assert result.receipt is None

    assert (
        receipt_store.get(
            tenant_id=commercial_result.tenant_id,
            client_id=commercial_result.client_id,
            engagement_id=commercial_result.engagement_id,
            assessment_id=commercial_result.assessment_id,
        )
        is None
    )


def test_capture_persists_client_receipt_observation(
    tmp_path: Path,
) -> None:
    (
        bridge,
        delivery_store,
        receipt_store,
    ) = build_bridge(
        tmp_path
    )

    source_delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path / "fixture"
        )
    )

    persisted_delivery_receipt = (
        seed_delivery_observation(
            delivery_store=delivery_store,
            source_receipt=(
                source_delivery_receipt
            ),
        )
    )

    result = bridge.capture(
        commercial_client_acknowledgment=(
            commercial_result
        )
    )

    assert result.applicable is True
    assert result.receipt is not None

    assert (
        result.receipt.observation_status
        == "client_receipt_observed"
    )

    assert (
        result.receipt.delivery_observation_receipt_hash
        == persisted_delivery_receipt.receipt_hash
    )

    restored = receipt_store.get(
        tenant_id=commercial_result.tenant_id,
        client_id=commercial_result.client_id,
        engagement_id=commercial_result.engagement_id,
        assessment_id=commercial_result.assessment_id,
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == result.receipt.receipt_hash
    )


def test_capture_is_idempotent(
    tmp_path: Path,
) -> None:
    bridge, delivery_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path / "fixture"
        )
    )

    seed_delivery_observation(
        delivery_store=delivery_store,
        source_receipt=delivery_receipt,
    )

    first = bridge.capture(
        commercial_client_acknowledgment=(
            commercial_result
        )
    )

    second = bridge.capture(
        commercial_client_acknowledgment=(
            commercial_result
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
        CustomerTrialClientReceiptObservationRecordingBridgeError,
        match="commercial_client_acknowledgment",
    ):
        bridge.capture(
            commercial_client_acknowledgment=object()
        )


def test_capture_fails_closed_on_report_mismatch(
    tmp_path: Path,
) -> None:
    bridge, delivery_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path / "fixture"
        )
    )

    observation = (
        CustomerTrialDeliveryObservation(
            tenant_id=
                delivery_receipt.tenant_id,
            client_id=
                delivery_receipt.client_id,
            engagement_id=
                delivery_receipt.engagement_id,
            assessment_id=
                delivery_receipt.assessment_id,
            hierarchy_key=
                delivery_receipt.hierarchy_key,

            observation_status="delivery_observed",

            delivery_readiness_receipt_hash=(
                delivery_receipt
                .delivery_readiness_receipt_hash
            ),
            delivery_readiness_hash=(
                delivery_receipt
                .delivery_readiness_hash
            ),

            delivery_event_id=
                delivery_receipt.delivery_event_id,
            delivery_event_hash=
                delivery_receipt.delivery_event_hash,

            report_id="different-report",

            delivered_by=
                delivery_receipt.delivered_by,
            delivered_at=
                delivery_receipt.delivered_at,
            delivery_method=
                delivery_receipt.delivery_method,
            delivery_reference=
                delivery_receipt.delivery_reference,

            human_delivery_confirmation_hash=(
                delivery_receipt
                .human_delivery_confirmation_hash
            ),
            approved_delivery_snapshot_hash=(
                delivery_receipt
                .approved_delivery_snapshot_hash
            ),
        )
    )

    delivery_store.put(
        observation=observation
    )

    with pytest.raises(
        Exception,
        match="report_id",
    ):
        bridge.capture(
            commercial_client_acknowledgment=(
                commercial_result
            )
        )


def test_bridge_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    bridge, _, _ = build_bridge(
        tmp_path
    )

    _, commercial_result = (
        build_fixture(
            tmp_path / "fixture"
        )
    )

    result = bridge.capture(
        commercial_client_acknowledgment=(
            commercial_result
        )
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "bridge_observes_existing_pa006_receipt"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_create_client_receipt"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_record_client_response"
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