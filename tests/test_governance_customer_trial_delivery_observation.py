from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    GovernanceCommercialPaidAssessmentDeliveryRecordingService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    DELIVERY_OBSERVED,
    CustomerTrialDeliveryObservationIdentityError,
    CustomerTrialDeliveryObservationLineageError,
    CustomerTrialDeliveryObservationStateError,
    GovernanceCustomerTrialDeliveryObservationService,
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


def build_fixture(
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

    readiness_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path
            / "customer-trial-delivery-readiness.sqlite3"
        )
    )

    readiness_receipt = (
        readiness_store.put(
            readiness=readiness
        )
    )

    return (
        readiness_receipt,
        recording,
    )


def test_observe_authoritative_paid_delivery(
    tmp_path: Path,
) -> None:
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    result = (
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

    assert (
        result.observation_status
        == DELIVERY_OBSERVED
    )

    assert (
        result.hierarchy_key
        == recording.hierarchy_key
    )

    assert (
        result.delivery_readiness_receipt_hash
        == readiness_receipt.receipt_hash
    )

    assert (
        result.delivery_readiness_hash
        == readiness_receipt.readiness_hash
    )

    assert (
        result.delivery_event_id
        == recording.recording.delivery_event.delivery_event_id
    )

    assert (
        result.delivery_event_hash
        == recording.recording.delivery_event.delivery_event_hash
    )

    assert (
        result.report_id
        == readiness_receipt.report_id
    )

    assert (
        result.human_delivery_confirmation_hash
        == (
            recording
            .recording
            .human_confirmation
            .confirmation_hash
        )
    )

    assert (
        result.approved_delivery_snapshot_hash
        == recording.approved_delivery_snapshot_hash
    )


def test_observe_rejects_readiness_hierarchy_mismatch(
    tmp_path: Path,
) -> None:
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        readiness_receipt,
        assessment_id="wrong-assessment",
        hierarchy_key=(
            HIERARCHY["tenant_id"]
            + "/"
            + HIERARCHY["client_id"]
            + "/"
            + HIERARCHY["engagement_id"]
            + "/wrong-assessment"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationIdentityError,
        match="hierarchy",
    ):
        (
            GovernanceCustomerTrialDeliveryObservationService()
            .observe(
                readiness_receipt=wrong,
                commercial_delivery_recording=recording,
            )
        )


def test_observe_rejects_report_mismatch(
    tmp_path: Path,
) -> None:
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        readiness_receipt,
        report_id="wrong-report",
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationLineageError,
        match="report_id",
    ):
        (
            GovernanceCustomerTrialDeliveryObservationService()
            .observe(
                readiness_receipt=wrong,
                commercial_delivery_recording=recording,
            )
        )


def test_observe_requires_controlled_trial_delivery_ready(
    tmp_path: Path,
) -> None:
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        readiness_receipt,
        readiness_status="trial_not_ready",
    )

    with pytest.raises(
        CustomerTrialDeliveryObservationStateError,
        match="delivery readiness",
    ):
        (
            GovernanceCustomerTrialDeliveryObservationService()
            .observe(
                readiness_receipt=wrong,
                commercial_delivery_recording=recording,
            )
        )


def test_observation_preserves_delivery_authority_boundaries(
    tmp_path: Path,
) -> None:
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    payload = (
        GovernanceCustomerTrialDeliveryObservationService()
        .observe(
            readiness_receipt=(
                readiness_receipt
            ),
            commercial_delivery_recording=(
                recording
            ),
        )
        .to_dict()
    )

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "observation_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_does_not_approve_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_does_not_deliver"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_is_not_client_receipt"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_is_not_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_is_not_intervention_authority"
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


def test_observation_serialization_binds_exact_delivery_lineage(
    tmp_path: Path,
) -> None:
    readiness_receipt, recording = (
        build_fixture(
            tmp_path
        )
    )

    payload = (
        GovernanceCustomerTrialDeliveryObservationService()
        .observe(
            readiness_receipt=(
                readiness_receipt
            ),
            commercial_delivery_recording=(
                recording
            ),
        )
        .to_dict()
    )

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
        == readiness_receipt.receipt_hash
    )

    assert (
        controlled[
            "delivery_readiness_hash"
        ]
        == readiness_receipt.readiness_hash
    )

    assert (
        delivery[
            "delivery_event_hash"
        ]
        == (
            recording
            .recording
            .delivery_event
            .delivery_event_hash
        )
    )

    assert (
        delivery[
            "human_delivery_confirmation_hash"
        ]
        == (
            recording
            .recording
            .human_confirmation
            .confirmation_hash
        )
    )

    assert (
        delivery[
            "approved_delivery_snapshot_hash"
        ]
        == recording.approved_delivery_snapshot_hash
    )