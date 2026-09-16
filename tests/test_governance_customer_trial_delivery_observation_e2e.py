from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    GovernanceCommercialPaidAssessmentDeliveryRecordingService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    GovernanceCustomerTrialDeliveryObservationService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_api import (
    create_customer_trial_delivery_observation_router,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_recording_bridge import (
    GovernanceCustomerTrialDeliveryObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_service import (
    GovernanceCustomerTrialDeliveryObservationStatusService,
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


class UnusedService:
    """
    Placeholder for unrelated commercial delivery routes.

    This E2E exercises the real delivery-recording service only.
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


def commercial_delivery_recording_url() -> str:
    return (
        "/api/v1/governance-paid-assessments/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "delivery-recording"
    )


def controlled_trial_observation_url() -> str:
    return (
        "/api/v1/governance-customer-trials/"
        f"{HIERARCHY['tenant_id']}/"
        f"{HIERARCHY['client_id']}/"
        f"{HIERARCHY['engagement_id']}/"
        f"{HIERARCHY['assessment_id']}/"
        "delivery-observation-status"
    )


def build_e2e_runtime(
    tmp_path: Path,
):
    #
    # Existing commercial path:
    # completed assessment -> PA-003 readiness -> explicit approval.
    #
    execution_service = (
        build_approved_assessment(
            tmp_path / "commercial"
        )
    )

    recording_service = (
        GovernanceCommercialPaidAssessmentDeliveryRecordingService(
            execution_service=execution_service
        )
    )

    confirmation = valid_human_confirmation(
        execution_service
    )

    #
    # Controlled-trial 04J-06 durable readiness evidence.
    #
    readiness_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "controlled-trial-readiness.sqlite3"
        )
    )

    readiness = replace(
        build_readiness(),
        tenant_id=HIERARCHY["tenant_id"],
        client_id=HIERARCHY["client_id"],
        engagement_id=HIERARCHY["engagement_id"],
        assessment_id=HIERARCHY["assessment_id"],
        hierarchy_key=hierarchy_key(),
        report_id=confirmation["report_id"],
    )

    readiness_receipt = readiness_store.put(
        readiness=readiness
    )

    #
    # 04J-07 durable observation infrastructure.
    #
    observation_database_path = (
        tmp_path / "controlled-trial-delivery-observation.sqlite3"
    )

    observation_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            observation_database_path
        )
    )

    observation_projection = (
        GovernanceCustomerTrialDeliveryObservationService()
    )

    observation_bridge = (
        GovernanceCustomerTrialDeliveryObservationRecordingBridge(
            readiness_receipt_store=readiness_store,
            observation_service=observation_projection,
            observation_receipt_store=observation_store,
        )
    )

    recording_service.configure_customer_trial_delivery_observation_recorder(
        recorder=observation_bridge
    )

    observation_status_service = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=observation_store
        )
    )

    app = FastAPI()

    unused = UnusedService()

    #
    # Real commercial delivery HTTP route.
    #
    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=unused,
            approval_service=unused,
            recording_service=recording_service,
            status_service=unused,
            lifecycle_status_service=unused,
            client_acknowledgment_service=unused,
            client_response_service=unused,
            closeout_status_service=unused,
            administrative_closeout_service=unused,
        )
    )

    #
    # Real controlled-trial READ_ONLY observation route.
    #
    app.include_router(
        create_customer_trial_delivery_observation_router(
            service=observation_status_service
        )
    )

    return {
        "client":
            TestClient(app),

        "confirmation":
            confirmation,

        "readiness_receipt":
            readiness_receipt,

        "observation_store":
            observation_store,

        "observation_database_path":
            observation_database_path,
    }


def test_controlled_trial_delivery_observation_true_e2e(
    tmp_path: Path,
) -> None:
    runtime = build_e2e_runtime(
        tmp_path
    )

    client = runtime["client"]
    confirmation = runtime["confirmation"]
    readiness_receipt = runtime[
        "readiness_receipt"
    ]
    observation_store = runtime[
        "observation_store"
    ]
    observation_database_path = runtime[
        "observation_database_path"
    ]

    #
    # 1. 04J-06 controlled-trial readiness exists, but delivery
    #    has not yet occurred and therefore 04J-07 observation
    #    MUST NOT exist.
    #
    before = client.get(
        controlled_trial_observation_url()
    )

    assert before.status_code == 200

    before_payload = before.json()

    assert (
        before_payload["authority"]
        == "READ_ONLY"
    )

    assert (
        before_payload["result"]["receipt_found"]
        is False
    )

    assert (
        before_payload["result"]["receipt"]
        is None
    )

    #
    # 2. Perform actual governed delivery through the REAL
    #    commercial delivery-recording HTTP route.
    #
    delivery_response = client.post(
        commercial_delivery_recording_url(),
        json=confirmation,
    )

    assert (
        delivery_response.status_code
        == 200
    )

    delivery_payload = (
        delivery_response.json()
    )

    assert (
        delivery_payload["delivery_recorded"]
        is True
    )

    assert (
        delivery_payload["delivery_status"]
        == "delivered"
    )

    assert (
        delivery_payload["hierarchy_key"]
        == hierarchy_key()
    )

    assert (
        delivery_payload["report_id"]
        == confirmation["report_id"]
    )

    assert (
        delivery_payload["delivery_event_id"]
        == confirmation["delivery_event_id"]
    )

    assert delivery_payload[
        "delivery_event_hash"
    ]

    assert delivery_payload[
        "human_delivery_confirmation_hash"
    ]

    assert delivery_payload[
        "approved_delivery_snapshot_hash"
    ]

    #
    # The existing commercial result still declares PA-005
    # authoritative.
    #
    commercial_boundaries = (
        delivery_payload["boundaries"]
    )

    assert (
        commercial_boundaries[
            "pa005_remains_delivery_event_authority"
        ]
        is True
    )

    assert (
        commercial_boundaries[
            "delivery_is_not_client_receipt"
        ]
        is True
    )

    #
    # 3. 07D should have automatically captured the delivery.
    #
    after = client.get(
        controlled_trial_observation_url()
    )

    assert after.status_code == 200

    after_payload = after.json()

    assert (
        after_payload["authority"]
        == "READ_ONLY"
    )

    assert (
        after_payload["result"]["receipt_found"]
        is True
    )

    receipt = (
        after_payload["result"]["receipt"]
    )

    assert receipt is not None

    assert (
        receipt["hierarchy_key"]
        == hierarchy_key()
    )

    assert (
        receipt["observation_status"]
        == "delivery_observed"
    )

    #
    # 4. Exact 04J-06 -> 04J-07 lineage.
    #
    controlled_lineage = (
        receipt["controlled_trial_lineage"]
    )

    assert (
        controlled_lineage[
            "delivery_readiness_receipt_hash"
        ]
        == readiness_receipt.receipt_hash
    )

    assert (
        controlled_lineage[
            "delivery_readiness_hash"
        ]
        == readiness_receipt.readiness_hash
    )

    #
    # 5. Exact PA-005 delivery lineage.
    #
    delivery_lineage = (
        receipt["delivery_lineage"]
    )

    assert (
        delivery_lineage[
            "delivery_event_id"
        ]
        == delivery_payload[
            "delivery_event_id"
        ]
    )

    assert (
        delivery_lineage[
            "delivery_event_hash"
        ]
        == delivery_payload[
            "delivery_event_hash"
        ]
    )

    assert (
        delivery_lineage[
            "human_delivery_confirmation_hash"
        ]
        == delivery_payload[
            "human_delivery_confirmation_hash"
        ]
    )

    assert (
        delivery_lineage[
            "approved_delivery_snapshot_hash"
        ]
        == delivery_payload[
            "approved_delivery_snapshot_hash"
        ]
    )

    assert (
        receipt["report"]["report_id"]
        == delivery_payload["report_id"]
    )

    #
    # 6. Delivery observation remains evidence only.
    #
    receipt_boundaries = (
        receipt["boundaries"]
    )

    assert (
        receipt_boundaries[
            "receipt_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_delivery_authority"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_client_receipt"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_client_acknowledgment"
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
            "pa005_remains_delivery_event_authority"
        ]
        is True
    )

    #
    # 7. Durable store contains same receipt.
    #
    stored = observation_store.get(
        tenant_id=HIERARCHY["tenant_id"],
        client_id=HIERARCHY["client_id"],
        engagement_id=HIERARCHY["engagement_id"],
        assessment_id=HIERARCHY["assessment_id"],
    )

    assert stored is not None

    assert (
        stored.receipt_hash
        == receipt["receipt_hash"]
    )

    assert (
        stored.delivery_event_hash
        == delivery_payload[
            "delivery_event_hash"
        ]
    )

    original_receipt_hash = (
        receipt["receipt_hash"]
    )

    original_observation_hash = (
        receipt["observation_hash"]
    )

    #
    # 8. Restart proof:
    #    reconstruct store/service/API from same SQLite file.
    #
    restarted_store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            observation_database_path
        )
    )

    restarted_service = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=restarted_store
        )
    )

    restarted_app = FastAPI()

    restarted_app.include_router(
        create_customer_trial_delivery_observation_router(
            service=restarted_service
        )
    )

    restarted_client = TestClient(
        restarted_app
    )

    restarted_response = (
        restarted_client.get(
            controlled_trial_observation_url()
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
        restarted_payload["authority"]
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
            "delivery_lineage"
        ][
            "delivery_event_hash"
        ]
        == delivery_payload[
            "delivery_event_hash"
        ]
    )

    #
    # 9. Controlled-trial observation namespace must remain
    #    GET-only and must not invent lifecycle actions.
    #
    openapi = client.get(
        "/openapi.json"
    ).json()

    observation_path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "delivery-observation-status"
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
        for path in openapi["paths"]
        if (
            "governance-customer-trials"
            in path
        )
    ]

    assert not any(
        path.endswith(
            "/delivery-recording"
        )
        or path.endswith(
            "/deliver"
        )
        or path.endswith(
            "/client-acknowledgment"
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