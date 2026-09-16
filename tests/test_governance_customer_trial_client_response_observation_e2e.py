from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    GovernanceCommercialPaidAssessmentClientResponseService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    CustomerTrialClientReceiptObservation,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation import (
    GovernanceCustomerTrialClientResponseObservationService,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_api import (
    create_customer_trial_client_response_observation_router,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_recording_bridge import (
    GovernanceCustomerTrialClientResponseObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_service import (
    GovernanceCustomerTrialClientResponseObservationStatusService,
)

from tests.test_governance_commercial_paid_assessment_client_response import (
    HIERARCHY,
    build_response_payload,
    prepare_delivered_and_acknowledged,
)


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64


class UnusedService:
    """
    Placeholder for commercial lifecycle routes not exercised by 09E.
    """

    pass


def hierarchy_key() -> str:
    return "/".join(
        (
            HIERARCHY["tenant_id"],
            HIERARCHY["client_id"],
            HIERARCHY["engagement_id"],
            HIERARCHY["assessment_id"],
        )
    )


def paid_client_response_url() -> str:
    return (
        "/api/v1/governance-paid-assessments/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "client-response"
    )


def controlled_trial_response_observation_url() -> str:
    return (
        "/api/v1/governance-customer-trials/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "client-response-observation-status"
    )


def seed_client_receipt_observation(
    *,
    store:
        GovernanceCustomerTrialClientReceiptObservationReceiptStore,
) -> object:
    """
    Seed the already-proven 04J-08 durable prerequisite.

    09E is intentionally about:
        existing 08B receipt
            -> real HTTP PA-007
            -> automatic 09D observation

    It does not retest the PA-006 HTTP path already proven by 08E.
    """

    observation = CustomerTrialClientReceiptObservation(
        tenant_id=
            HIERARCHY["tenant_id"],
        client_id=
            HIERARCHY["client_id"],
        engagement_id=
            HIERARCHY["engagement_id"],
        assessment_id=
            HIERARCHY["assessment_id"],
        hierarchy_key=
            hierarchy_key(),

        observation_status=
            "client_receipt_observed",

        delivery_observation_receipt_hash=
            HEX_A,
        delivery_observation_hash=
            HEX_B,

        report_id=
            "report-001",

        acknowledgment_id=
            "client-ack-001",
        acknowledged_by=
            "ACME Client Representative",
        acknowledged_at=
            "2026-09-03T20:15:00+00:00",
        acknowledgment_method=
            "email_reply",
        acknowledgment_reference=
            "mail-reply-001",
        acknowledgment_status=
            "client_receipt_acknowledged",

        acknowledgment_artifact_id=
            "ack-artifact-001",
        acknowledgment_artifact_hash=
            HEX_C,
        acknowledgment_sequence_number=
            12,
        acknowledgment_chain_hash=
            HEX_D,
    )

    return store.put(
        observation=observation
    )


def build_e2e_runtime(
    tmp_path: Path,
):
    #
    # Authoritative paid lifecycle:
    #
    # delivery
    #   -> persisted PA-006 receipt
    #   -> PA-007 may now execute
    #
    execution_service, repository = (
        prepare_delivered_and_acknowledged(
            tmp_path / "commercial"
        )
    )

    client_response_service = (
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        )
    )

    #
    # Existing 04J-08 controlled-trial receipt evidence.
    #
    receipt_database_path = (
        tmp_path
        / "controlled-trial-client-receipt-observation.sqlite3"
    )

    receipt_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            receipt_database_path
        )
    )

    client_receipt_observation_receipt = (
        seed_client_receipt_observation(
            store=receipt_store
        )
    )

    #
    # New 04J-09 response observation persistence.
    #
    response_database_path = (
        tmp_path
        / "controlled-trial-client-response-observation.sqlite3"
    )

    response_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            response_database_path
        )
    )

    response_projection = (
        GovernanceCustomerTrialClientResponseObservationService()
    )

    response_bridge = (
        GovernanceCustomerTrialClientResponseObservationRecordingBridge(
            client_receipt_observation_receipt_store=(
                receipt_store
            ),
            observation_service=(
                response_projection
            ),
            observation_receipt_store=(
                response_store
            ),
        )
    )

    client_response_service.configure_customer_trial_client_response_observation_recorder(
        recorder=response_bridge
    )

    response_status_service = (
        GovernanceCustomerTrialClientResponseObservationStatusService(
            receipt_store=response_store
        )
    )

    #
    # HTTP app:
    # - actual paid PA-007 route
    # - controlled-trial READ_ONLY observation route
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
            client_response_service=(
                client_response_service
            ),
            closeout_status_service=unused,
            administrative_closeout_service=unused,
        )
    )

    app.include_router(
        create_customer_trial_client_response_observation_router(
            service=(
                response_status_service
            )
        )
    )

    return {
        "client":
            TestClient(app),

        "repository":
            repository,

        "client_receipt_observation_receipt":
            client_receipt_observation_receipt,

        "response_store":
            response_store,

        "response_database_path":
            response_database_path,
    }


def test_controlled_trial_client_response_observation_true_e2e(
    tmp_path: Path,
) -> None:
    runtime = build_e2e_runtime(
        tmp_path
    )

    client = runtime[
        "client"
    ]

    client_receipt_observation_receipt = runtime[
        "client_receipt_observation_receipt"
    ]

    response_store = runtime[
        "response_store"
    ]

    response_database_path = runtime[
        "response_database_path"
    ]

    #
    # 1. PA-006 and 04J-08 have occurred,
    #    but no PA-007 response exists yet.
    #
    before = client.get(
        controlled_trial_response_observation_url()
    )

    assert before.status_code == 200

    before_payload = (
        before.json()
    )

    assert (
        before_payload[
            "authority"
        ]
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
            "receipt"
        ]
        is None
    )

    #
    # 2. Submit the REAL PA-007 HTTP client response.
    #
    response_payload = (
        build_response_payload()
    )

    response = client.post(
        paid_client_response_url(),
        json=response_payload,
    )

    assert response.status_code == 200

    commercial_payload = (
        response.json()
    )

    assert (
        commercial_payload[
            "client_response_recorded"
        ]
        is True
    )

    assert (
        commercial_payload[
            "response_status"
        ]
        == "client_response_recorded"
    )

    assert (
        commercial_payload[
            "hierarchy_key"
        ]
        == hierarchy_key()
    )

    assert (
        commercial_payload[
            "report_id"
        ]
        == "report-001"
    )

    assert (
        commercial_payload[
            "response_id"
        ]
        == response_payload[
            "response_id"
        ]
    )

    assert (
        commercial_payload[
            "responded_by"
        ]
        == response_payload[
            "responded_by"
        ]
    )

    assert (
        commercial_payload[
            "responded_at"
        ]
        == response_payload[
            "responded_at"
        ]
    )

    assert (
        commercial_payload[
            "response_method"
        ]
        == response_payload[
            "response_method"
        ]
    )

    assert (
        commercial_payload[
            "response_reference"
        ]
        == response_payload[
            "response_reference"
        ]
    )

    assert (
        commercial_payload[
            "findings_disposition"
        ]
        == response_payload[
            "findings_disposition"
        ]
    )

    assert (
        commercial_payload[
            "recommendations_disposition"
        ]
        == response_payload[
            "recommendations_disposition"
        ]
    )

    #
    # 3. Commercial PA-007 boundaries remain intact.
    #
    commercial_boundaries = (
        commercial_payload[
            "boundaries"
        ]
    )

    assert (
        commercial_boundaries[
            "response_requires_prior_receipt"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "response_is_not_inferred_from_receipt"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "findings_acknowledgment_is_not_validation"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "recommendation_acceptance_is_not_implementation"
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
            "response_is_not_intervention_authorization"
        ]
        is True
    )

    #
    # 4. 09D automatically captures the already-authoritative PA-007
    #    result. No controlled-trial response action was called.
    #
    after = client.get(
        controlled_trial_response_observation_url()
    )

    assert after.status_code == 200

    after_payload = (
        after.json()
    )

    assert (
        after_payload[
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        after_payload[
            "result"
        ][
            "receipt_found"
        ]
        is True
    )

    receipt = (
        after_payload[
            "result"
        ][
            "receipt"
        ]
    )

    assert receipt is not None

    assert (
        receipt[
            "observation_status"
        ]
        == "client_response_observed"
    )

    assert (
        receipt[
            "hierarchy_key"
        ]
        == hierarchy_key()
    )

    #
    # 5. Exact 08 -> 09 controlled-trial lineage.
    #
    controlled_lineage = (
        receipt[
            "controlled_trial_lineage"
        ]
    )

    assert (
        controlled_lineage[
            "client_receipt_observation_receipt_hash"
        ]
        == client_receipt_observation_receipt.receipt_hash
    )

    assert (
        controlled_lineage[
            "client_receipt_observation_hash"
        ]
        == client_receipt_observation_receipt.observation_hash
    )

    assert (
        receipt[
            "report"
        ][
            "report_id"
        ]
        == commercial_payload[
            "report_id"
        ]
    )

    #
    # 6. Exact PA-007 semantics are projected into the durable
    #    controlled-trial observation.
    #
    observed_response = (
        receipt[
            "client_response"
        ]
    )

    assert (
        observed_response[
            "response_id"
        ]
        == commercial_payload[
            "response_id"
        ]
    )

    assert (
        observed_response[
            "responded_by"
        ]
        == commercial_payload[
            "responded_by"
        ]
    )

    assert (
        observed_response[
            "responded_at"
        ]
        == commercial_payload[
            "responded_at"
        ]
    )

    assert (
        observed_response[
            "response_method"
        ]
        == commercial_payload[
            "response_method"
        ]
    )

    assert (
        observed_response[
            "response_reference"
        ]
        == commercial_payload[
            "response_reference"
        ]
    )

    assert (
        observed_response[
            "findings_disposition"
        ]
        == commercial_payload[
            "findings_disposition"
        ]
    )

    assert (
        observed_response[
            "recommendations_disposition"
        ]
        == commercial_payload[
            "recommendations_disposition"
        ]
    )

    assert (
        observed_response[
            "response_status"
        ]
        == "client_response_recorded"
    )

    #
    # 7. 09B durable boundaries remain evidence-only.
    #
    receipt_boundaries = (
        receipt[
            "boundaries"
        ]
    )

    assert (
        receipt_boundaries[
            "receipt_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_does_not_create_client_response"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_does_not_validate_findings"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_does_not_implement_recommendations"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_roi_verification"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_customer_outcome_verification"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "pa007_remains_client_response_authority"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "pa012_remains_lifecycle_persistence_authority"
        ]
        is True
    )

    #
    # 8. The exact same receipt is durable in 09B storage.
    #
    stored = response_store.get(
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
        receipt[
            "receipt_hash"
        ]
    )

    original_observation_hash = (
        receipt[
            "observation_hash"
        ]
    )

    #
    # 9. Restart proof:
    #    rebuild only the 09B store + 09C GET surface from SQLite.
    #
    restarted_store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            response_database_path
        )
    )

    restarted_service = (
        GovernanceCustomerTrialClientResponseObservationStatusService(
            receipt_store=restarted_store
        )
    )

    restarted_app = FastAPI()

    restarted_app.include_router(
        create_customer_trial_client_response_observation_router(
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
            controlled_trial_response_observation_url()
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
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        restarted_payload[
            "result"
        ][
            "receipt_found"
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
            "client_response"
        ][
            "response_id"
        ]
        == commercial_payload[
            "response_id"
        ]
    )

    #
    # 10. Controlled-trial namespace remains observation-only.
    #
    openapi = (
        client.get(
            "/openapi.json"
        )
        .json()
    )

    observation_path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "client-response-observation-status"
    )

    assert (
        observation_path
        in openapi[
            "paths"
        ]
    )

    assert set(
        openapi[
            "paths"
        ][
            observation_path
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
            "/client-response"
        )
        or path.endswith(
            "/closeout"
        )
        or path.endswith(
            "/intervene"
        )
        for path in controlled_trial_paths
    )