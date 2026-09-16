from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    CustomerTrialClientReceiptObservationReceipt,
)
from backend.app.gagf.governance_customer_trial_client_response_observation import (
    CLIENT_RESPONSE_OBSERVED,
    CustomerTrialClientResponseObservationIdentityError,
    CustomerTrialClientResponseObservationLineageError,
    CustomerTrialClientResponseObservationStateError,
    GovernanceCustomerTrialClientResponseObservationService,
)

from tests.test_governance_commercial_paid_assessment_client_response import (
    HIERARCHY,
    build_response_payload,
    prepare_delivered_and_acknowledged,
)
from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    GovernanceCommercialPaidAssessmentClientResponseService,
)


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64


def hierarchy_key() -> str:
    return "/".join(
        (
            HIERARCHY["tenant_id"],
            HIERARCHY["client_id"],
            HIERARCHY["engagement_id"],
            HIERARCHY["assessment_id"],
        )
    )


def build_fixture(
    tmp_path: Path,
):
    execution_service, _ = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    commercial_result = (
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        )
        .record(
            **HIERARCHY,
            response_payload=(
                build_response_payload()
            ),
        )
    )

    receipt = (
        CustomerTrialClientReceiptObservationReceipt(
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
            hierarchy_key=(
                hierarchy_key()
            ),

            observation_status=(
                "client_receipt_observed"
            ),

            delivery_observation_receipt_hash=
                HEX_A,
            delivery_observation_hash=
                HEX_B,

            report_id=(
                commercial_result.report_id
            ),

            acknowledgment_id=(
                "client-ack-001"
            ),
            acknowledged_by=(
                "ACME Client Representative"
            ),
            acknowledged_at=(
                "2026-09-03T20:15:00+00:00"
            ),
            acknowledgment_method=(
                "email_reply"
            ),
            acknowledgment_reference=(
                "mail-reply-001"
            ),
            acknowledgment_status=(
                "client_receipt_acknowledged"
            ),

            acknowledgment_artifact_id=(
                "ack-artifact-001"
            ),
            acknowledgment_artifact_hash=
                HEX_C,
            acknowledgment_sequence_number=
                12,
            acknowledgment_chain_hash=
                HEX_D,

            observation_hash=
                HEX_E,
            receipt_hash=
                HEX_F,
        )
    )

    return (
        receipt,
        commercial_result,
    )


def test_observe_authoritative_client_response(
    tmp_path: Path,
) -> None:
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    result = (
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

    assert (
        result.observation_status
        == CLIENT_RESPONSE_OBSERVED
    )

    assert (
        result.hierarchy_key
        == receipt.hierarchy_key
    )

    assert (
        result.client_receipt_observation_receipt_hash
        == receipt.receipt_hash
    )

    assert (
        result.client_receipt_observation_hash
        == receipt.observation_hash
    )

    assert (
        result.report_id
        == commercial_result.report_id
    )

    assert (
        result.response_id
        == commercial_result.response_id
    )

    assert (
        result.findings_disposition
        == commercial_result.findings_disposition
    )

    assert (
        result.recommendations_disposition
        == commercial_result.recommendations_disposition
    )


def test_observe_rejects_hierarchy_mismatch(
    tmp_path: Path,
) -> None:
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        receipt,
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
        CustomerTrialClientResponseObservationIdentityError,
        match="hierarchy",
    ):
        (
            GovernanceCustomerTrialClientResponseObservationService()
            .observe(
                client_receipt_observation_receipt=wrong,
                commercial_client_response=(
                    commercial_result
                ),
            )
        )


def test_observe_rejects_report_mismatch(
    tmp_path: Path,
) -> None:
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        receipt,
        report_id="other-report",
    )

    with pytest.raises(
        CustomerTrialClientResponseObservationLineageError,
        match="report_id",
    ):
        (
            GovernanceCustomerTrialClientResponseObservationService()
            .observe(
                client_receipt_observation_receipt=wrong,
                commercial_client_response=(
                    commercial_result
                ),
            )
        )


def test_observe_requires_client_receipt_observed(
    tmp_path: Path,
) -> None:
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    wrong = replace(
        receipt,
        observation_status=(
            "client_receipt_not_observed"
        ),
    )

    with pytest.raises(
        CustomerTrialClientResponseObservationStateError,
        match="client receipt must be observed",
    ):
        (
            GovernanceCustomerTrialClientResponseObservationService()
            .observe(
                client_receipt_observation_receipt=wrong,
                commercial_client_response=(
                    commercial_result
                ),
            )
        )


def test_observation_preserves_response_semantics(
    tmp_path: Path,
) -> None:
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    payload = (
        GovernanceCustomerTrialClientResponseObservationService()
        .observe(
            client_receipt_observation_receipt=(
                receipt
            ),
            commercial_client_response=(
                commercial_result
            ),
        )
        .to_dict()
    )

    response = payload[
        "client_response"
    ]

    assert (
        response["response_id"]
        == commercial_result.response_id
    )

    assert (
        response["responded_by"]
        == commercial_result.responded_by
    )

    assert (
        response["findings_disposition"]
        == commercial_result.findings_disposition
    )

    assert (
        response["recommendations_disposition"]
        == commercial_result.recommendations_disposition
    )

    assert (
        response["response_status"]
        == "client_response_recorded"
    )


def test_observation_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    receipt, commercial_result = (
        build_fixture(
            tmp_path
        )
    )

    boundaries = (
        GovernanceCustomerTrialClientResponseObservationService()
        .observe(
            client_receipt_observation_receipt=(
                receipt
            ),
            commercial_client_response=(
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
            "observation_does_not_create_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_does_not_validate_findings"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_does_not_implement_recommendations"
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
            "observation_is_not_roi_verification"
        ]
        is True
    )

    assert (
        boundaries[
            "observation_is_not_customer_outcome_verification"
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