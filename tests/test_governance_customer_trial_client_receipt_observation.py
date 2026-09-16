from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    CLIENT_RECEIPT_OBSERVED,
    CustomerTrialClientReceiptObservationIdentityError,
    CustomerTrialClientReceiptObservationLineageError,
    CustomerTrialClientReceiptObservationStateError,
    GovernanceCustomerTrialClientReceiptObservationService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    CustomerTrialDeliveryObservationReceipt,
)

from tests.test_governance_commercial_paid_assessment_client_acknowledgment import (
    HIERARCHY,
    build_acknowledgment_payload,
    build_delivery_event,
    build_execution_service,
    build_repository,
    build_service,
    persist_delivery,
)


HEX_D = "d" * 64
HEX_E = "e" * 64


def build_fixture(
    tmp_path: Path,
):
    execution_service = (
        build_execution_service(
            tmp_path
        )
    )

    repository = build_repository(
        execution_service
    )

    delivery_event = (
        build_delivery_event()
    )

    persist_delivery(
        repository,
        delivery_event,
    )

    commercial_result = (
        build_service(
            execution_service
        )
        .record(
            **HIERARCHY,
            acknowledgment_payload=(
                build_acknowledgment_payload()
            ),
        )
    )

    delivery_observation_receipt = (
        CustomerTrialDeliveryObservationReceipt(
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
            hierarchy_key="/".join(
                (
                    HIERARCHY["tenant_id"],
                    HIERARCHY["client_id"],
                    HIERARCHY["engagement_id"],
                    HIERARCHY["assessment_id"],
                )
            ),

            observation_status=(
                "delivery_observed"
            ),

            delivery_readiness_receipt_hash=HEX_D,
            delivery_readiness_hash=HEX_E,

            delivery_event_id=(
                delivery_event.delivery_event_id
            ),
            delivery_event_hash=(
                delivery_event.delivery_event_hash
            ),

            report_id=(
                delivery_event.report_id
            ),

            delivered_by=(
                delivery_event.delivered_by
            ),
            delivered_at=(
                delivery_event.delivered_at
            ),
            delivery_method=(
                delivery_event.delivery_method
            ),
            delivery_reference=(
                delivery_event.delivery_reference
            ),

            human_delivery_confirmation_hash=(
                delivery_event
                .human_delivery_confirmation_hash
            ),
            approved_delivery_snapshot_hash=(
                "a" * 64
            ),

            observation_hash=(
                "b" * 64
            ),
            receipt_hash=(
                "c" * 64
            ),
        )
    )

    return (
        delivery_observation_receipt,
        commercial_result,
    )


def test_observe_authoritative_client_receipt(
    tmp_path: Path,
) -> None:
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    result = (
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

    assert (
        result.observation_status
        == CLIENT_RECEIPT_OBSERVED
    )

    assert (
        result.hierarchy_key
        == delivery_receipt.hierarchy_key
    )

    assert (
        result.delivery_observation_receipt_hash
        == delivery_receipt.receipt_hash
    )

    assert (
        result.delivery_observation_hash
        == delivery_receipt.observation_hash
    )

    assert (
        result.report_id
        == delivery_receipt.report_id
    )

    assert (
        result.acknowledgment_id
        == commercial_result.acknowledgment_id
    )

    assert (
        result.acknowledgment_artifact_hash
        == (
            commercial_result
            .persistence_result
            .artifact_hash
        )
    )

    assert (
        result.acknowledgment_chain_hash
        == (
            commercial_result
            .persistence_result
            .chain_hash
        )
    )


def test_observe_rejects_hierarchy_mismatch(
    tmp_path: Path,
) -> None:
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        delivery_receipt,
        assessment_id="other-assessment",
        hierarchy_key=(
            HIERARCHY["tenant_id"]
            + "/"
            + HIERARCHY["client_id"]
            + "/"
            + HIERARCHY["engagement_id"]
            + "/other-assessment"
        ),
    )

    with pytest.raises(
        CustomerTrialClientReceiptObservationIdentityError,
        match="hierarchy",
    ):
        (
            GovernanceCustomerTrialClientReceiptObservationService()
            .observe(
                delivery_observation_receipt=wrong,
                commercial_client_acknowledgment=(
                    commercial_result
                ),
            )
        )


def test_observe_rejects_report_mismatch(
    tmp_path: Path,
) -> None:
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        delivery_receipt,
        report_id="other-report",
    )

    with pytest.raises(
        CustomerTrialClientReceiptObservationLineageError,
        match="report_id",
    ):
        (
            GovernanceCustomerTrialClientReceiptObservationService()
            .observe(
                delivery_observation_receipt=wrong,
                commercial_client_acknowledgment=(
                    commercial_result
                ),
            )
        )


def test_observe_requires_delivery_observed(
    tmp_path: Path,
) -> None:
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        delivery_receipt,
        observation_status="delivery_not_observed",
    )

    with pytest.raises(
        CustomerTrialClientReceiptObservationStateError,
        match="delivery must be observed",
    ):
        (
            GovernanceCustomerTrialClientReceiptObservationService()
            .observe(
                delivery_observation_receipt=wrong,
                commercial_client_acknowledgment=(
                    commercial_result
                ),
            )
        )


def test_observation_uses_pa012_persistence_lineage(
    tmp_path: Path,
) -> None:
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    payload = (
        GovernanceCustomerTrialClientReceiptObservationService()
        .observe(
            delivery_observation_receipt=(
                delivery_receipt
            ),
            commercial_client_acknowledgment=(
                commercial_result
            ),
        )
        .to_dict()
    )

    persistence = payload[
        "persistence_lineage"
    ]

    assert (
        persistence["artifact_id"]
        == commercial_result
        .persistence_result
        .artifact_id
    )

    assert (
        persistence["artifact_hash"]
        == commercial_result
        .persistence_result
        .artifact_hash
    )

    assert (
        persistence["chain_hash"]
        == commercial_result
        .persistence_result
        .chain_hash
    )

    assert (
        persistence["repository_chain_valid"]
        is True
    )


def test_observation_preserves_receipt_boundaries(
    tmp_path: Path,
) -> None:
    delivery_receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    boundaries = (
        GovernanceCustomerTrialClientReceiptObservationService()
        .observe(
            delivery_observation_receipt=(
                delivery_receipt
            ),
            commercial_client_acknowledgment=(
                commercial_result
            ),
        )
        .to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "observation_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_does_not_create_client_receipt"
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
            "observation_is_not_findings_acceptance"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_is_not_recommendation_acceptance"
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