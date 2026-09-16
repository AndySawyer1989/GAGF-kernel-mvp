from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_closeout import (
    GovernanceCommercialPaidAssessmentCloseoutService,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation import (
    ADMINISTRATIVE_CLOSEOUT_OBSERVED,
    CONTROLLED_TRIAL_COMPLETE,
    CustomerTrialAdministrativeCloseoutObservationIdentityError,
    CustomerTrialAdministrativeCloseoutObservationLineageError,
    CustomerTrialAdministrativeCloseoutObservationStateError,
    GovernanceCustomerTrialAdministrativeCloseoutObservationService,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)

from tests.test_governance_commercial_paid_assessment_closeout import (
    HIERARCHY,
    build_closeout_payload,
    prepare_client_response,
)
from tests.test_governance_customer_trial_client_response_observation_receipt_store import (
    build_observation,
)


def build_fixture(
    tmp_path: Path,
):
    #
    # Existing controlled-trial 09B prerequisite.
    #
    response_observation_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            tmp_path
            / "controlled-trial-client-response-observation.sqlite3"
        )
    )

    response_observation_receipt = (
        response_observation_store.put(
            observation=build_observation(
                tmp_path / "response-observation"
            )
        )
    )

    #
    # Real authoritative commercial PA-010 closeout.
    #
    (
        execution_service,
        _repository,
        _response_result,
    ) = prepare_client_response(
        tmp_path / "commercial-closeout"
    )

    commercial_closeout = (
        GovernanceCommercialPaidAssessmentCloseoutService(
            execution_service=execution_service
        )
        .record(
            **HIERARCHY,
            closeout_payload=(
                build_closeout_payload()
            ),
        )
    )

    return (
        response_observation_receipt,
        commercial_closeout,
    )


def test_observe_authoritative_administrative_closeout(
    tmp_path: Path,
) -> None:
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    result = (
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

    assert (
        result.observation_status
        == ADMINISTRATIVE_CLOSEOUT_OBSERVED
    )

    assert (
        result.controlled_trial_status
        == CONTROLLED_TRIAL_COMPLETE
    )

    assert (
        result.controlled_trial_complete
        is True
    )

    assert (
        result.hierarchy_key
        == response_receipt.hierarchy_key
    )

    assert (
        result.client_response_observation_receipt_hash
        == response_receipt.receipt_hash
    )

    assert (
        result.client_response_observation_hash
        == response_receipt.observation_hash
    )

    assert (
        result.closeout_artifact_id
        == commercial_closeout.closeout_artifact_id
    )

    assert (
        result.closeout_artifact_hash
        == commercial_closeout.closeout_artifact_hash
    )

    assert (
        result.repository_chain_valid
        is True
    )


def test_observe_rejects_hierarchy_mismatch(
    tmp_path: Path,
) -> None:
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    wrong = replace(
        response_receipt,
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
        CustomerTrialAdministrativeCloseoutObservationIdentityError,
        match="hierarchy",
    ):
        (
            GovernanceCustomerTrialAdministrativeCloseoutObservationService()
            .observe(
                client_response_observation_receipt=wrong,
                commercial_closeout=(
                    commercial_closeout
                ),
            )
        )


def test_observe_rejects_report_mismatch(
    tmp_path: Path,
) -> None:
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    wrong = replace(
        response_receipt,
        report_id="different-report",
    )

    with pytest.raises(
        CustomerTrialAdministrativeCloseoutObservationLineageError,
        match="report_id",
    ):
        (
            GovernanceCustomerTrialAdministrativeCloseoutObservationService()
            .observe(
                client_response_observation_receipt=wrong,
                commercial_closeout=(
                    commercial_closeout
                ),
            )
        )


def test_observe_requires_client_response_observed(
    tmp_path: Path,
) -> None:
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    wrong = replace(
        response_receipt,
        observation_status=(
            "client_response_not_observed"
        ),
    )

    with pytest.raises(
        CustomerTrialAdministrativeCloseoutObservationStateError,
        match="client response must be observed",
    ):
        (
            GovernanceCustomerTrialAdministrativeCloseoutObservationService()
            .observe(
                client_response_observation_receipt=wrong,
                commercial_closeout=(
                    commercial_closeout
                ),
            )
        )


def test_observation_preserves_authoritative_closeout_artifact(
    tmp_path: Path,
) -> None:
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    payload = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationService()
        .observe(
            client_response_observation_receipt=(
                response_receipt
            ),
            commercial_closeout=(
                commercial_closeout
            ),
        )
        .to_dict()
    )

    closeout = payload[
        "administrative_closeout"
    ]

    assert (
        closeout[
            "closeout_status"
        ]
        == "assessment_closed"
    )

    assert (
        closeout[
            "closeout_artifact_id"
        ]
        == commercial_closeout.closeout_artifact_id
    )

    assert (
        closeout[
            "closeout_artifact_hash"
        ]
        == commercial_closeout.closeout_artifact_hash
    )

    assert (
        closeout[
            "repository_chain_valid"
        ]
        is True
    )


def test_observation_preserves_completion_boundaries(
    tmp_path: Path,
) -> None:
    (
        response_receipt,
        commercial_closeout,
    ) = build_fixture(
        tmp_path
    )

    payload = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationService()
        .observe(
            client_response_observation_receipt=(
                response_receipt
            ),
            commercial_closeout=(
                commercial_closeout
            ),
        )
        .to_dict()
    )

    completion = payload[
        "trial_completion"
    ]

    assert (
        completion["status"]
        == "controlled_trial_complete"
    )

    assert (
        completion[
            "controlled_trial_complete"
        ]
        is True
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
            "observation_does_not_create_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "response_observed_is_not_closeout"
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
            "trial_complete_is_not_findings_validation"
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
            "trial_complete_is_not_remediation_success"
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