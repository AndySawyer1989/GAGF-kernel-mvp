from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_client_acknowledgment import (
    GovernanceCommercialPaidAssessmentClientAcknowledgmentService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    GovernanceCustomerTrialClientReceiptObservationService,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_api import (
    create_customer_trial_client_receipt_observation_router,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_recording_bridge import (
    GovernanceCustomerTrialClientReceiptObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_service import (
    GovernanceCustomerTrialClientReceiptObservationStatusService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    CustomerTrialDeliveryObservation,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)

from tests.test_governance_commercial_paid_assessment_client_acknowledgment import (
    HIERARCHY,
    build_acknowledgment_payload,
    build_delivery_event,
    build_execution_service,
    build_repository,
    persist_delivery,
)


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64


class UnusedService:
    """
    Placeholder for unrelated commercial lifecycle routes.

    04J-08E exercises only the real PA-006 HTTP endpoint.
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


def paid_client_acknowledgment_url() -> str:
    return (
        "/api/v1/governance-paid-assessments/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "client-acknowledgment"
    )


def controlled_trial_receipt_observation_url() -> str:
    return (
        "/api/v1/governance-customer-trials/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "client-receipt-observation-status"
    )


def seed_delivery_observation(
    *,
    store:
        GovernanceCustomerTrialDeliveryObservationReceiptStore,
    delivery_event,
):
    observation = CustomerTrialDeliveryObservation(
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
            "delivery_observed",

        delivery_readiness_receipt_hash=
            HEX_D,
        delivery_readiness_hash=
            HEX_E,

        delivery_event_id=
            delivery_event.delivery_event_id,
        delivery_event_hash=
            delivery_event.delivery_event_hash,

        report_id=
            delivery_event.report_id,

        delivered_by=
            delivery_event.delivered_by,
        delivered_at=
            delivery_event.delivered_at,
        delivery_method=
            delivery_event.delivery_method,
        delivery_reference=
            delivery_event.delivery_reference,

        human_delivery_confirmation_hash=(
            delivery_event
            .human_delivery_confirmation_hash
        ),

        approved_delivery_snapshot_hash=
            HEX_A,
    )

    return store.put(
        observation=observation
    )


def build_e2e_runtime(
    tmp_path: Path,
):
    #
    # Existing authoritative paid lifecycle:
    #
    # governed delivery already persisted
    #     ↓
    # PA-006 explicit client receipt acknowledgment
    #
    execution_service = (
        build_execution_service(
            tmp_path / "commercial"
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

    client_acknowledgment_service = (
        GovernanceCommercialPaidAssessmentClientAcknowledgmentService(
            execution_service=execution_service
        )
    )

    #
    # Existing 04J-07 controlled-trial delivery observation.
    #
    delivery_observation_database_path = (
        tmp_path
        / "controlled-trial-delivery-observation.sqlite3"
    )

    delivery_observation_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            delivery_observation_database_path
        )
    )

    delivery_observation_receipt = (
        seed_delivery_observation(
            store=delivery_observation_store,
            delivery_event=delivery_event,
        )
    )

    #
    # 04J-08 controlled-trial client-receipt observation.
    #
    client_receipt_database_path = (
        tmp_path
        / "controlled-trial-client-receipt-observation.sqlite3"
    )

    client_receipt_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            client_receipt_database_path
        )
    )

    client_receipt_projection = (
        GovernanceCustomerTrialClientReceiptObservationService()
    )

    client_receipt_bridge = (
        GovernanceCustomerTrialClientReceiptObservationRecordingBridge(
            delivery_observation_receipt_store=(
                delivery_observation_store
            ),
            observation_service=(
                client_receipt_projection
            ),
            observation_receipt_store=(
                client_receipt_store
            ),
        )
    )

    client_acknowledgment_service.configure_customer_trial_client_receipt_observation_recorder(
        recorder=client_receipt_bridge
    )

    client_receipt_status_service = (
        GovernanceCustomerTrialClientReceiptObservationStatusService(
            receipt_store=client_receipt_store
        )
    )

    #
    # HTTP application using the actual PA-006 commercial route.
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
            client_acknowledgment_service=(
                client_acknowledgment_service
            ),
            client_response_service=unused,
            closeout_status_service=unused,
            administrative_closeout_service=unused,
        )
    )

    app.include_router(
        create_customer_trial_client_receipt_observation_router(
            service=(
                client_receipt_status_service
            )
        )
    )

    return {
        "client":
            TestClient(app),

        "delivery_event":
            delivery_event,

        "delivery_observation_receipt":
            delivery_observation_receipt,

        "client_receipt_store":
            client_receipt_store,

        "client_receipt_database_path":
            client_receipt_database_path,
    }


def test_controlled_trial_client_receipt_observation_true_e2e(
    tmp_path: Path,
) -> None:
    runtime = build_e2e_runtime(
        tmp_path
    )

    client = runtime["client"]

    delivery_event = runtime[
        "delivery_event"
    ]

    delivery_observation_receipt = runtime[
        "delivery_observation_receipt"
    ]

    client_receipt_store = runtime[
        "client_receipt_store"
    ]

    client_receipt_database_path = runtime[
        "client_receipt_database_path"
    ]

    #
    # 1. Governed delivery has occurred and 04J-07 evidence exists,
    #    but PA-006 client receipt has NOT occurred yet.
    #
    before = client.get(
        controlled_trial_receipt_observation_url()
    )

    assert before.status_code == 200

    before_payload = (
        before.json()
    )

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
            "receipt"
        ]
        is None
    )

    #
    # 2. Submit REAL PA-006 HTTP client acknowledgment.
    #
    acknowledgment_payload = (
        build_acknowledgment_payload()
    )

    acknowledgment_response = (
        client.post(
            paid_client_acknowledgment_url(),
            json=acknowledgment_payload,
        )
    )

    assert (
        acknowledgment_response.status_code
        == 200
    )

    commercial_payload = (
        acknowledgment_response.json()
    )

    assert (
        commercial_payload[
            "client_receipt_acknowledged"
        ]
        is True
    )

    assert (
        commercial_payload[
            "acknowledgment_status"
        ]
        == "client_receipt_acknowledged"
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
        == delivery_event.report_id
    )

    assert (
        commercial_payload[
            "acknowledgment_id"
        ]
        == acknowledgment_payload[
            "acknowledgment_id"
        ]
    )

    assert (
        commercial_payload[
            "acknowledged_by"
        ]
        == acknowledgment_payload[
            "acknowledged_by"
        ]
    )

    persistence = (
        commercial_payload[
            "persistence_result"
        ]
    )

    assert persistence[
        "artifact_id"
    ]

    assert persistence[
        "artifact_hash"
    ]

    assert persistence[
        "chain_hash"
    ]

    assert (
        persistence[
            "repository_chain_valid"
        ]
        is True
    )

    #
    # Existing commercial PA-006 boundaries remain authoritative.
    #
    commercial_boundaries = (
        commercial_payload[
            "boundaries"
        ]
    )

    assert (
        commercial_boundaries[
            "receipt_is_not_findings_acceptance"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "receipt_is_not_recommendation_acceptance"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "receipt_is_not_client_response"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "receipt_is_not_closeout"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )

    #
    # 3. 08D must have automatically captured PA-006.
    #
    after = client.get(
        controlled_trial_receipt_observation_url()
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
        == "client_receipt_observed"
    )

    assert (
        receipt[
            "hierarchy_key"
        ]
        == hierarchy_key()
    )

    #
    # 4. Exact controlled-trial lineage:
    #    04J-07 receipt -> 04J-08 receipt.
    #
    controlled_lineage = (
        receipt[
            "controlled_trial_lineage"
        ]
    )

    assert (
        controlled_lineage[
            "delivery_observation_receipt_hash"
        ]
        == delivery_observation_receipt.receipt_hash
    )

    assert (
        controlled_lineage[
            "delivery_observation_hash"
        ]
        == delivery_observation_receipt.observation_hash
    )

    assert (
        receipt[
            "report"
        ][
            "report_id"
        ]
        == delivery_event.report_id
    )

    #
    # 5. Exact PA-006 / PA-012 persistence lineage.
    #
    receipt_persistence = (
        receipt[
            "persistence_lineage"
        ]
    )

    assert (
        receipt_persistence[
            "acknowledgment_artifact_id"
        ]
        == persistence[
            "artifact_id"
        ]
    )

    assert (
        receipt_persistence[
            "acknowledgment_artifact_hash"
        ]
        == persistence[
            "artifact_hash"
        ]
    )

    assert (
        receipt_persistence[
            "acknowledgment_sequence_number"
        ]
        == persistence[
            "sequence_number"
        ]
    )

    assert (
        receipt_persistence[
            "acknowledgment_chain_hash"
        ]
        == persistence[
            "chain_hash"
        ]
    )

    assert (
        receipt_persistence[
            "repository_chain_valid"
        ]
        is True
    )

    #
    # 6. Controlled-trial receipt observation stays evidence-only.
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
            "receipt_is_not_client_response"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_findings_acceptance"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_recommendation_acceptance"
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
            "pa006_remains_client_receipt_authority"
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
    # 7. Store contains the exact same durable receipt.
    #
    stored = (
        client_receipt_store.get(
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
    # 8. Restart proof:
    #    rebuild the 08B store + 08C read surface from SQLite.
    #
    restarted_store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            client_receipt_database_path
        )
    )

    restarted_service = (
        GovernanceCustomerTrialClientReceiptObservationStatusService(
            receipt_store=(
                restarted_store
            )
        )
    )

    restarted_app = FastAPI()

    restarted_app.include_router(
        create_customer_trial_client_receipt_observation_router(
            service=(
                restarted_service
            )
        )
    )

    restarted_client = (
        TestClient(
            restarted_app
        )
    )

    restarted_response = (
        restarted_client.get(
            controlled_trial_receipt_observation_url()
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
            "persistence_lineage"
        ][
            "acknowledgment_artifact_hash"
        ]
        == persistence[
            "artifact_hash"
        ]
    )

    #
    # 9. Controlled-trial namespace remains observation-only.
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
        "client-receipt-observation-status"
    )

    assert (
        observation_path
        in openapi["paths"]
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
        for path in openapi[
            "paths"
        ]
        if (
            "governance-customer-trials"
            in path
        )
    ]

    assert not any(
        path.endswith(
            "/client-acknowledgment"
        )
        or path.endswith(
            "/client-receipt"
        )
        or path.endswith(
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