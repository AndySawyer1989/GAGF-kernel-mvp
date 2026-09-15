from dataclasses import replace

import pytest

from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceipt,
)
from backend.app.gagf.governance_customer_trial_execution_observation import (
    EXECUTION_OBSERVED,
    CustomerTrialExecutionObservationIdentityError,
    CustomerTrialExecutionObservationLineageError,
    CustomerTrialExecutionObservationStateError,
    GovernanceCustomerTrialExecutionObservationService,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    REAL_EXECUTION_STATUS_COMPLETE,
    RealPaidAssessmentExecutionResult,
)


TENANT_ID = "tenant-controlled"
CLIENT_ID = "client-controlled"
ENGAGEMENT_ID = "engagement-controlled"
ASSESSMENT_ID = "assessment-controlled"

HIERARCHY_KEY = (
    f"{TENANT_ID}/"
    f"{CLIENT_ID}/"
    f"{ENGAGEMENT_ID}/"
    f"{ASSESSMENT_ID}"
)

HANDOFF_HASH = "handoff-hash-controlled"
REQUEST_HASH = "execution-request-hash-controlled"


def build_handoff_receipt(
) -> CustomerTrialExecutionHandoffReceipt:
    return CustomerTrialExecutionHandoffReceipt(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
        hierarchy_key=HIERARCHY_KEY,
        preflight_receipt_hash=
            "preflight-receipt-hash",
        preflight_decision_payload_hash=
            "preflight-decision-hash",
        preflight_package_hash=
            "preflight-package-hash",
        contract_execution_event_hash=
            "contract-event-hash",
        paid_work_authorization_hash=
            "paid-work-authorization-hash",
        assessment_execution_request_hash=
            REQUEST_HASH,
        handoff_hash=
            HANDOFF_HASH,
        lineage_hash=
            "customer-trial-handoff-lineage-hash",
        receipt_hash=
            "customer-trial-handoff-receipt-hash",
    )


def build_execution_result(
) -> RealPaidAssessmentExecutionResult:
    return RealPaidAssessmentExecutionResult(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
        execution_status=
            REAL_EXECUTION_STATUS_COMPLETE,
        handoff_hash=
            HANDOFF_HASH,
        assessment_execution_request_hash=
            REQUEST_HASH,
        application_request_hash=
            "application-request-hash",
        execution_result_hash=
            "execution-result-hash",
        application_hash=
            "application-hash",
        demonstration_hash=
            "demonstration-hash",
        persistence_hash=
            "persistence-hash",
        report_id=
            "report-controlled",
        report_package_hash=
            "report-package-hash",
        artifact_count=
            10,
        application_completed=
            True,
        repository_chain_valid=
            True,
    )


def test_observe_binds_customer_trial_handoff_to_real_execution():
    observation = (
        GovernanceCustomerTrialExecutionObservationService()
        .observe(
            handoff_receipt=
                build_handoff_receipt(),
            execution_result=
                build_execution_result(),
        )
    )

    assert observation.observation_status == (
        EXECUTION_OBSERVED
    )

    assert observation.hierarchy_key == (
        HIERARCHY_KEY
    )

    assert observation.handoff_hash == (
        HANDOFF_HASH
    )

    assert (
        observation.assessment_execution_request_hash
        == REQUEST_HASH
    )

    assert observation.handoff_receipt_hash == (
        "customer-trial-handoff-receipt-hash"
    )

    assert observation.handoff_lineage_hash == (
        "customer-trial-handoff-lineage-hash"
    )

    assert observation.execution_result_hash == (
        "execution-result-hash"
    )

    assert observation.application_completed is True
    assert observation.repository_chain_valid is True


def test_observation_is_explicitly_read_only():
    observation = (
        GovernanceCustomerTrialExecutionObservationService()
        .observe(
            handoff_receipt=
                build_handoff_receipt(),
            execution_result=
                build_execution_result(),
        )
    )

    boundaries = observation.boundaries

    assert boundaries[
        "observation_is_read_only"
    ] is True

    assert boundaries[
        "observation_is_not_execution_authority"
    ] is True

    assert boundaries[
        "observation_is_not_recovery_authority"
    ] is True

    assert boundaries[
        "observation_is_not_delivery_authority"
    ] is True

    assert boundaries[
        "observation_is_not_closeout_authority"
    ] is True

    assert boundaries[
        "observation_is_not_intervention_authority"
    ] is True


def test_observation_does_not_claim_customer_outcome_or_roi():
    observation = (
        GovernanceCustomerTrialExecutionObservationService()
        .observe(
            handoff_receipt=
                build_handoff_receipt(),
            execution_result=
                build_execution_result(),
        )
    )

    boundaries = observation.boundaries

    assert boundaries[
        "execution_complete_is_not_customer_outcome_verified"
    ] is True

    assert boundaries[
        "execution_complete_is_not_causal_proof"
    ] is True

    assert boundaries[
        "execution_complete_is_not_roi_verified"
    ] is True


def test_observe_rejects_identity_mismatch():
    execution = replace(
        build_execution_result(),
        assessment_id="different-assessment",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationIdentityError
    ):
        (
            GovernanceCustomerTrialExecutionObservationService()
            .observe(
                handoff_receipt=
                    build_handoff_receipt(),
                execution_result=
                    execution,
            )
        )


def test_observe_rejects_handoff_hash_mismatch():
    execution = replace(
        build_execution_result(),
        handoff_hash="different-handoff-hash",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationLineageError
    ):
        (
            GovernanceCustomerTrialExecutionObservationService()
            .observe(
                handoff_receipt=
                    build_handoff_receipt(),
                execution_result=
                    execution,
            )
        )


def test_observe_rejects_execution_request_hash_mismatch():
    execution = replace(
        build_execution_result(),
        assessment_execution_request_hash=
            "different-request-hash",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationLineageError
    ):
        (
            GovernanceCustomerTrialExecutionObservationService()
            .observe(
                handoff_receipt=
                    build_handoff_receipt(),
                execution_result=
                    execution,
            )
        )


def test_observe_rejects_incomplete_execution_status():
    execution = replace(
        build_execution_result(),
        execution_status="execution_incomplete",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationStateError
    ):
        (
            GovernanceCustomerTrialExecutionObservationService()
            .observe(
                handoff_receipt=
                    build_handoff_receipt(),
                execution_result=
                    execution,
            )
        )


def test_observe_rejects_incomplete_application():
    execution = replace(
        build_execution_result(),
        application_completed=False,
    )

    with pytest.raises(
        CustomerTrialExecutionObservationStateError
    ):
        (
            GovernanceCustomerTrialExecutionObservationService()
            .observe(
                handoff_receipt=
                    build_handoff_receipt(),
                execution_result=
                    execution,
            )
        )


def test_observe_rejects_invalid_repository_chain():
    execution = replace(
        build_execution_result(),
        repository_chain_valid=False,
    )

    with pytest.raises(
        CustomerTrialExecutionObservationStateError
    ):
        (
            GovernanceCustomerTrialExecutionObservationService()
            .observe(
                handoff_receipt=
                    build_handoff_receipt(),
                execution_result=
                    execution,
            )
        )


def test_observation_serialization_preserves_lineage():
    observation = (
        GovernanceCustomerTrialExecutionObservationService()
        .observe(
            handoff_receipt=
                build_handoff_receipt(),
            execution_result=
                build_execution_result(),
        )
    )

    payload = observation.to_dict()

    assert payload[
        "observation_status"
    ] == EXECUTION_OBSERVED

    lineage = payload[
        "execution_lineage"
    ]

    assert isinstance(
        lineage,
        dict,
    )

    assert lineage[
        "handoff_hash"
    ] == HANDOFF_HASH

    assert lineage[
        "assessment_execution_request_hash"
    ] == REQUEST_HASH

    assert lineage[
        "execution_result_hash"
    ] == "execution-result-hash"