from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_closeout import (
    GovernanceCommercialPaidAssessmentCloseoutService,
)
from backend.app.gagf.governance_commercial_paid_assessment_closeout_status import (
    GovernanceCommercialPaidAssessmentCloseoutStatusService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationService,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_api import (
    create_customer_trial_administrative_closeout_observation_router,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_recording_bridge import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_service import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService,
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
    build_observation as build_client_response_observation,
)


class UnusedService:
    pass


def administrative_closeout_url() -> str:
    return (
        "/api/v1/governance-paid-assessments/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "administrative-closeout"
    )


def controlled_trial_completion_url() -> str:
    return (
        "/api/v1/governance-customer-trials/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "controlled-trial-completion-status"
    )


def build_e2e_runtime(
    tmp_path: Path,
):
    #
    # Existing authoritative commercial lifecycle through PA-007.
    #
    (
        execution_service,
        _repository,
        commercial_response,
    ) = prepare_client_response(
        tmp_path / "commercial"
    )

    assert (
        commercial_response.response_status
        == "client_response_recorded"
    )

    #
    # Seed the already-proven controlled-trial 09B prerequisite.
    #
    response_observation_database_path = (
        tmp_path
        / "controlled-trial-client-response-observation.sqlite3"
    )

    response_observation_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            response_observation_database_path
        )
    )

    client_response_observation = (
        build_client_response_observation(
            tmp_path / "controlled-trial-response"
        )
    )

    client_response_receipt = (
        response_observation_store.put(
            observation=client_response_observation
        )
    )

    assert (
        client_response_receipt.observation_status
        == "client_response_observed"
    )

    assert (
        client_response_receipt.report_id
        == commercial_response.report_id
    )

    #
    # New 10B terminal completion receipt.
    #
    closeout_observation_database_path = (
        tmp_path
        / "controlled-trial-administrative-closeout-observation.sqlite3"
    )

    closeout_observation_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            closeout_observation_database_path
        )
    )

    closeout_projection = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationService()
    )

    closeout_bridge = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationRecordingBridge(
            client_response_observation_receipt_store=(
                response_observation_store
            ),
            observation_service=(
                closeout_projection
            ),
            observation_receipt_store=(
                closeout_observation_store
            ),
        )
    )

    #
    # Real PA-010 commercial service.
    #
    administrative_closeout_service = (
        GovernanceCommercialPaidAssessmentCloseoutService(
            execution_service=execution_service
        )
    )

    administrative_closeout_service.configure_customer_trial_administrative_closeout_observation_recorder(
        recorder=closeout_bridge
    )

    closeout_status_service = (
        GovernanceCommercialPaidAssessmentCloseoutStatusService(
            execution_service=execution_service
        )
    )

    completion_status_service = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=(
                closeout_observation_store
            )
        )
    )

    #
    # HTTP application:
    # - real commercial PA-010 POST
    # - controlled-trial READ_ONLY completion GET
    #
    app = FastAPI()

    unused = UnusedService()

    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=unused,
            approval_service=unused,
            recording_service=unused,
            status_service=unused,
            lifecycle_status_service=unused,
            client_acknowledgment_service=unused,
            client_response_service=unused,
            closeout_status_service=(
                closeout_status_service
            ),
            administrative_closeout_service=(
                administrative_closeout_service
            ),
        )
    )

    app.include_router(
        create_customer_trial_administrative_closeout_observation_router(
            service=completion_status_service
        )
    )

    return {
        "client":
            TestClient(app),

        "client_response_receipt":
            client_response_receipt,

        "closeout_store":
            closeout_observation_store,

        "closeout_database_path":
            closeout_observation_database_path,
    }


def test_controlled_trial_administrative_closeout_true_e2e(
    tmp_path: Path,
) -> None:
    runtime = build_e2e_runtime(
        tmp_path
    )

    client = runtime[
        "client"
    ]

    client_response_receipt = runtime[
        "client_response_receipt"
    ]

    closeout_store = runtime[
        "closeout_store"
    ]

    closeout_database_path = runtime[
        "closeout_database_path"
    ]

    #
    # 1. PA-007 and 09B exist, but PA-010 has not yet occurred.
    #
    before = client.get(
        controlled_trial_completion_url()
    )

    assert before.status_code == 200

    before_payload = before.json()

    assert (
        before_payload["authority"]
        == "READ_ONLY"
    )

    assert (
        before_payload[
            "result"
        ][
            "receipt_found"
        ]
        is False
    )

    assert (
        before_payload[
            "result"
        ][
            "controlled_trial_complete"
        ]
        is False
    )

    #
    # 2. Invoke the REAL commercial PA-010 HTTP endpoint.
    #
    closeout_payload = (
        build_closeout_payload()
    )

    response = client.post(
        administrative_closeout_url(),
        json=closeout_payload,
    )

    assert response.status_code == 200

    commercial_closeout = (
        response.json()
    )

    assert (
        commercial_closeout[
            "administrative_closeout_recorded"
        ]
        is True
    )

    assert (
        commercial_closeout[
            "closeout_status"
        ]
        == "assessment_closed"
    )

    assert (
        commercial_closeout[
            "report_id"
        ]
        == "report-001"
    )

    assert (
        commercial_closeout[
            "repository_chain_valid"
        ]
        is True
    )

    assert (
        commercial_closeout[
            "closeout_artifact_id"
        ]
    )

    assert (
        commercial_closeout[
            "closeout_artifact_hash"
        ]
    )

    #
    # 3. Preserve commercial PA-010 authority boundaries.
    #
    commercial_boundaries = (
        commercial_closeout[
            "boundaries"
        ]
    )

    assert (
        commercial_boundaries[
            "closeout_requires_explicit_human_confirmation"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "response_is_not_closeout"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_recommendation_implementation"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_intervention_authorization"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_execution_authority"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_causation"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_roi_verification"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_remediation_success"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "closeout_is_not_customer_outcome"
        ]
        is True
    )

    #
    # 4. 10D automatically observes PA-010.
    #
    after = client.get(
        controlled_trial_completion_url()
    )

    assert after.status_code == 200

    after_payload = after.json()

    assert (
        after_payload[
            "authority"
        ]
        == "READ_ONLY"
    )

    result = after_payload[
        "result"
    ]

    assert (
        result[
            "receipt_found"
        ]
        is True
    )

    assert (
        result[
            "controlled_trial_complete"
        ]
        is True
    )

    assert (
        result[
            "controlled_trial_status"
        ]
        == "controlled_trial_complete"
    )

    receipt = result[
        "receipt"
    ]

    assert receipt is not None

    assert (
        receipt[
            "observation_status"
        ]
        == "administrative_closeout_observed"
    )

    assert (
        receipt[
            "trial_completion"
        ][
            "controlled_trial_complete"
        ]
        is True
    )

    #
    # 5. Exact 09 -> 10 controlled-trial lineage.
    #
    lineage = receipt[
        "controlled_trial_lineage"
    ]

    assert (
        lineage[
            "client_response_observation_receipt_hash"
        ]
        == client_response_receipt.receipt_hash
    )

    assert (
        lineage[
            "client_response_observation_hash"
        ]
        == client_response_receipt.observation_hash
    )

    #
    # 6. Exact PA-010 artifact lineage.
    #
    observed_closeout = receipt[
        "administrative_closeout"
    ]

    assert (
        observed_closeout[
            "closeout_status"
        ]
        == "assessment_closed"
    )

    assert (
        observed_closeout[
            "closed_by"
        ]
        == commercial_closeout[
            "closed_by"
        ]
    )

    assert (
        observed_closeout[
            "closeout_reason"
        ]
        == commercial_closeout[
            "closeout_reason"
        ]
    )

    assert (
        observed_closeout[
            "closeout_artifact_id"
        ]
        == commercial_closeout[
            "closeout_artifact_id"
        ]
    )

    assert (
        observed_closeout[
            "closeout_artifact_hash"
        ]
        == commercial_closeout[
            "closeout_artifact_hash"
        ]
    )

    assert (
        observed_closeout[
            "repository_chain_valid"
        ]
        is True
    )

    #
    # 7. Completion remains administrative only.
    #
    boundaries = receipt[
        "boundaries"
    ]

    assert (
        boundaries[
            "receipt_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_does_not_create_closeout"
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

    #
    # 8. Exact durable 10B receipt is present.
    #
    stored = closeout_store.get(
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
    )

    assert stored is not None

    assert (
        stored.receipt_hash
        == receipt[
            "receipt_hash"
        ]
    )

    original_receipt_hash = (
        stored.receipt_hash
    )

    original_observation_hash = (
        stored.observation_hash
    )

    #
    # 9. Restart proof:
    # rebuild only 10B store + 10C READ_ONLY API from SQLite.
    #
    restarted_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            closeout_database_path
        )
    )

    restarted_service = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=restarted_store
        )
    )

    restarted_app = FastAPI()

    restarted_app.include_router(
        create_customer_trial_administrative_closeout_observation_router(
            service=restarted_service
        )
    )

    restarted_client = (
        TestClient(
            restarted_app
        )
    )

    restarted_response = (
        restarted_client.get(
            controlled_trial_completion_url()
        )
    )

    assert (
        restarted_response.status_code
        == 200
    )

    restarted_payload = (
        restarted_response.json()
    )

    assert (
        restarted_payload[
            "result"
        ][
            "controlled_trial_complete"
        ]
        is True
    )

    restarted_receipt = (
        restarted_payload[
            "result"
        ][
            "receipt"
        ]
    )

    assert (
        restarted_receipt[
            "receipt_hash"
        ]
        == original_receipt_hash
    )

    assert (
        restarted_receipt[
            "observation_hash"
        ]
        == original_observation_hash
    )

    assert (
        restarted_receipt[
            "administrative_closeout"
        ][
            "closeout_artifact_hash"
        ]
        == commercial_closeout[
            "closeout_artifact_hash"
        ]
    )

    #
    # 10. Controlled-trial namespace stays READ_ONLY.
    #
    openapi = (
        client.get(
            "/openapi.json"
        )
        .json()
    )

    completion_path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "controlled-trial-completion-status"
    )

    assert (
        completion_path
        in openapi[
            "paths"
        ]
    )

    assert set(
        openapi[
            "paths"
        ][
            completion_path
        ].keys()
    ) == {
        "get"
    }

    controlled_trial_paths = [
        path
        for path
        in openapi[
            "paths"
        ]
        if (
            "governance-customer-trials"
            in path
        )
    ]

    assert not any(
        path.endswith(
            "/administrative-closeout"
        )
        or path.endswith(
            "/closeout"
        )
        or path.endswith(
            "/intervene"
        )
        or path.endswith(
            "/execute"
        )
        for path in controlled_trial_paths
    )