from __future__ import annotations

from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    GovernanceCustomerTrialDeliveryReadinessService,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_recording_bridge import (
    CustomerTrialDeliveryReadinessRecordingBridgeError,
    GovernanceCustomerTrialDeliveryReadinessRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)

from tests.test_governance_customer_trial_delivery_readiness import (
    StubCommercialReadinessService,
)
from tests.test_governance_customer_trial_execution_observation_receipt_store import (
    build_observation,
)

import pytest


def build_bridge(
    tmp_path,
):
    execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                tmp_path / "paid-assessments"
            )
        )
    )

    commercial_readiness_service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    projection_service = (
        GovernanceCustomerTrialDeliveryReadinessService(
            commercial_readiness_service=(
                commercial_readiness_service
            )
        )
    )

    observation_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    readiness_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    bridge = (
        GovernanceCustomerTrialDeliveryReadinessRecordingBridge(
            observation_receipt_store=(
                observation_store
            ),
            readiness_projection_service=(
                projection_service
            ),
            readiness_receipt_store=(
                readiness_store
            ),
        )
    )

    return (
        bridge,
        observation_store,
        readiness_store,
    )


def build_commercial_readiness():
    return (
        StubCommercialReadinessService()
        .result
    )


def test_capture_is_not_applicable_without_controlled_trial_observation(
    tmp_path,
):
    bridge, _, readiness_store = (
        build_bridge(
            tmp_path
        )
    )

    commercial_readiness = (
        build_commercial_readiness()
    )

    result = bridge.capture(
        commercial_readiness=(
            commercial_readiness
        )
    )

    assert result.applicable is False
    assert result.receipt is None

    stored = readiness_store.get(
        tenant_id=(
            commercial_readiness.tenant_id
        ),
        client_id=(
            commercial_readiness.client_id
        ),
        engagement_id=(
            commercial_readiness.engagement_id
        ),
        assessment_id=(
            commercial_readiness.assessment_id
        ),
    )

    assert stored is None


def test_capture_persists_controlled_trial_readiness(
    tmp_path,
):
    (
        bridge,
        observation_store,
        readiness_store,
    ) = build_bridge(
        tmp_path
    )

    observation_store.put(
        observation=build_observation()
    )

    commercial_readiness = (
        build_commercial_readiness()
    )

    result = bridge.capture(
        commercial_readiness=(
            commercial_readiness
        )
    )

    assert result.applicable is True
    assert result.receipt is not None

    assert (
        result.receipt.readiness_status
        == "controlled_trial_delivery_ready"
    )

    restored = readiness_store.get(
        tenant_id=(
            commercial_readiness.tenant_id
        ),
        client_id=(
            commercial_readiness.client_id
        ),
        engagement_id=(
            commercial_readiness.engagement_id
        ),
        assessment_id=(
            commercial_readiness.assessment_id
        ),
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == result.receipt.receipt_hash
    )


def test_capture_is_idempotent(
    tmp_path,
):
    bridge, observation_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    observation_store.put(
        observation=build_observation()
    )

    commercial_readiness = (
        build_commercial_readiness()
    )

    first = bridge.capture(
        commercial_readiness=(
            commercial_readiness
        )
    )

    second = bridge.capture(
        commercial_readiness=(
            commercial_readiness
        )
    )

    assert first.receipt is not None
    assert second.receipt is not None

    assert (
        second.receipt.receipt_hash
        == first.receipt.receipt_hash
    )


def test_capture_rejects_wrong_commercial_readiness_type(
    tmp_path,
):
    bridge, _, _ = build_bridge(
        tmp_path
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessRecordingBridgeError,
        match="commercial_readiness",
    ):
        bridge.capture(
            commercial_readiness=object(),
        )


def test_capture_fails_closed_on_controlled_trial_lineage_mismatch(
    tmp_path,
):
    bridge, observation_store, _ = (
        build_bridge(
            tmp_path
        )
    )

    observation_store.put(
        observation=build_observation()
    )

    mismatched = (
        StubCommercialReadinessService(
            report_id="different-report"
        )
        .result
    )

    with pytest.raises(
        Exception,
        match="report_id",
    ):
        bridge.capture(
            commercial_readiness=mismatched
        )


def test_recording_result_boundaries_preserve_authority(
    tmp_path,
):
    bridge, _, _ = build_bridge(
        tmp_path
    )

    result = bridge.capture(
        commercial_readiness=(
            build_commercial_readiness()
        )
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "bridge_observes_existing_commercial_readiness"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_does_not_compute_pa003_readiness"
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
            "bridge_does_not_record_delivery"
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
            "pa003_remains_delivery_readiness_authority"
        ]
        is True
    )