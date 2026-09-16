from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    GovernanceCommercialPaidAssessmentDeliveryRecordingService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    GovernanceCustomerTrialDeliveryObservationService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_recording_bridge import (
    CustomerTrialDeliveryObservationRecordingBridgeError,
    GovernanceCustomerTrialDeliveryObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)

from tests.test_governance_commercial_paid_assessment_delivery_recording import (
    HIERARCHY,
    build_approved_assessment,
    valid_human_confirmation,
)
from tests.test_governance_customer_trial_delivery_readiness_receipt_store import (
    build_readiness,
)


def build_controlled_trial_fixture(
    tmp_path: Path,
):
    execution_service = (
        build_approved_assessment(
            tmp_path
        )
    )

    recording = (
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        )
        .record(
            **HIERARCHY,
            human_confirmation_payload=(
                valid_human_confirmation(
                    execution_service
                )
            ),
        )
    )

    hierarchy_key = "/".join(
        (
            HIERARCHY["tenant_id"],
            HIERARCHY["client_id"],
            HIERARCHY["engagement_id"],
            HIERARCHY["assessment_id"],
        )
    )

    readiness = replace(
        build_readiness(),
        tenant_id=HIERARCHY[
            "tenant_id"
        ],
        client_id=HIERARCHY[
            "client_id"
        ],
        engagement_id=HIERARCHY[
            "engagement_id"
        ],
        assessment_id=HIERARCHY[
            "assessment_id"
        ],
        hierarchy_key=hierarchy_key,
        report_id=(
            recording
            .recording
            .delivery_event
            .report_id
        ),
    )

    return (
        readiness,
        recording,
    )


def build_bridge(
    tmp_path: Path,
):
    readiness_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "readiness.sqlite3"
        )
    )

    observation_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    bridge = (
        GovernanceCustomerTrialDeliveryObservationRecordingBridge(
            readiness_receipt_store=readiness_store,
            observation_service=(
                GovernanceCustomerTrialDeliveryObservationService()
            ),
            observation_receipt_store=observation_store,
        )
    )

    return (
        bridge,
        readiness_store,
        observation_store,
    )


def test_capture_not_applicable_without_controlled_trial_readiness(
    tmp_path: Path,
) -> None:
    bridge, _, observation_store = (
        build_bridge(
            tmp_path
        )
    )

    _, recording = (
        build_controlled_trial_fixture(
            tmp_path / "fixture"
        )
    )

    result = bridge.capture(
        commercial_delivery_recording=recording
    )

    assert result.applicable is False
    assert result.receipt is None

    assert (
        observation_store.get(
            tenant_id=recording.tenant_id,
            client_id=recording.client_id,
            engagement_id=recording.engagement_id,
            assessment_id=recording.assessment_id,
        )
        is None
    )


def test_capture_persists_controlled_trial_delivery_observation(
    tmp_path: Path,
) -> None:
    (
        bridge,
        readiness_store,
        observation_store,
    ) = build_bridge(
        tmp_path
    )

    readiness, recording = (
        build_controlled_trial_fixture(
            tmp_path / "fixture"
        )
    )

    readiness_receipt = (
        readiness_store.put(
            readiness=readiness
        )
    )

    result = bridge.capture(
        commercial_delivery_recording=recording
    )

    assert result.applicable is True
    assert result.receipt is not None

    assert (
        result.receipt.observation_status
        == "delivery_observed"
    )

    assert (
        result.receipt.delivery_readiness_receipt_hash
        == readiness_receipt.receipt_hash
    )

    assert (
        result.receipt.delivery_readiness_hash
        == readiness_receipt.readiness_hash
    )

    restored = observation_store.get(
        tenant_id=recording.tenant_id,
        client_id=recording.client_id,
        engagement_id=recording.engagement_id,
        assessment_id=recording.assessment_id,
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == result.receipt.receipt_hash
    )


def test_capture_is_idempotent_for_same_delivery(
    tmp_path: Path,
) -> None:
    bridge, readiness_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    readiness, recording = (
        build_controlled_trial_fixture(
            tmp_path / "fixture"
        )
    )

    readiness_store.put(
        readiness=readiness
    )

    first = bridge.capture(
        commercial_delivery_recording=recording
    )

    second = bridge.capture(
        commercial_delivery_recording=recording
    )

    assert first.receipt is not None
    assert second.receipt is not None

    assert (
        second.receipt.receipt_hash
        == first.receipt.receipt_hash
    )

    assert (
        second.receipt.delivery_event_hash
        == first.receipt.delivery_event_hash
    )


def test_capture_rejects_wrong_recording_type(
    tmp_path: Path,
) -> None:
    bridge, _, _ = build_bridge(
        tmp_path
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationRecordingBridgeError,
        match="commercial_delivery_recording",
    ):
        bridge.capture(
            commercial_delivery_recording=object()
        )


def test_capture_fails_closed_on_report_lineage_mismatch(
    tmp_path: Path,
) -> None:
    bridge, readiness_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    readiness, recording = (
        build_controlled_trial_fixture(
            tmp_path / "fixture"
        )
    )

    mismatched = replace(
        readiness,
        report_id="different-report",
    )

    readiness_store.put(
        readiness=mismatched
    )

    with pytest.raises(
        Exception,
        match="report_id",
    ):
        bridge.capture(
            commercial_delivery_recording=recording
        )


def test_recording_result_boundaries_preserve_authority(
    tmp_path: Path,
) -> None:
    bridge, _, _ = build_bridge(
        tmp_path
    )

    _, recording = (
        build_controlled_trial_fixture(
            tmp_path / "fixture"
        )
    )

    result = bridge.capture(
        commercial_delivery_recording=recording
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "bridge_observes_existing_pa005_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_approve_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_deliver"
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
            "bridge_does_not_create_client_response"
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
            "pa005_remains_delivery_event_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa012_remains_lifecycle_persistence_authority"
        ]
        is True
    )