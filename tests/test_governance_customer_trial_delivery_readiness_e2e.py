from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_api import (
    create_governance_commercial_paid_assessment_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_api import (
    create_governance_commercial_paid_assessment_delivery_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    GovernanceCustomerTrialDeliveryReadinessService,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_api import (
    CUSTOMER_TRIAL_DELIVERY_READINESS_API_PREFIX,
    create_customer_trial_delivery_readiness_router,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_recording_bridge import (
    GovernanceCustomerTrialDeliveryReadinessRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_service import (
    GovernanceCustomerTrialDeliveryReadinessStatusService,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_api import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX,
    create_customer_trial_execution_handoff_router,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_service import (
    GovernanceCustomerTrialExecutionHandoffService,
)
from backend.app.gagf.governance_customer_trial_execution_observation_api import (
    CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_PREFIX,
    create_customer_trial_execution_observation_router,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_observation_recording_bridge import (
    GovernanceCustomerTrialExecutionObservationRecordingBridge,
)
from backend.app.gagf.governance_customer_trial_execution_observation_service import (
    GovernanceCustomerTrialExecutionObservationStatusService,
)

from tests.test_governance_commercial_paid_assessment_api import (
    bind_execution_input,
    build_payload as build_commercial_execution_payload,
)
from tests.test_governance_customer_trial_execution_handoff_api import (
    HIERARCHY_KEY,
    build_payload as build_customer_trial_handoff_payload,
)
from tests.test_governance_customer_trial_execution_handoff_bridge import (
    build_services,
    record_ready_preflight,
)


TENANT_ID = "tenant-alpha"
CLIENT_ID = "client-customer-001"
ENGAGEMENT_ID = "engagement-trial-001"
ASSESSMENT_ID = "assessment-trial-001"


class UnusedDeliveryService:
    """
    Inert dependency for commercial delivery routes that are not
    exercised by this readiness-only E2E.

    The actual readiness dependency is the production
    GovernanceCommercialPaidAssessmentDeliveryReadinessService.
    """

    pass


def observation_status_url() -> str:
    return (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_PREFIX
        + f"/{TENANT_ID}/"
        + f"{CLIENT_ID}/"
        + f"{ENGAGEMENT_ID}/"
        + f"{ASSESSMENT_ID}/"
        + "execution-observation-status"
    )


def customer_trial_readiness_status_url() -> str:
    return (
        CUSTOMER_TRIAL_DELIVERY_READINESS_API_PREFIX
        + f"/{TENANT_ID}/"
        + f"{CLIENT_ID}/"
        + f"{ENGAGEMENT_ID}/"
        + f"{ASSESSMENT_ID}/"
        + "delivery-readiness-status"
    )


def commercial_delivery_readiness_url() -> str:
    return (
        "/api/v1/governance-paid-assessments/"
        + f"{TENANT_ID}/"
        + f"{CLIENT_ID}/"
        + f"{ENGAGEMENT_ID}/"
        + f"{ASSESSMENT_ID}/"
        + "delivery-readiness"
    )


def build_e2e_app(
    tmp_path: Path,
):
    execution_directory = (
        tmp_path
        / "paid-assessments"
    )

    binding_directory = (
        tmp_path
        / "execution-input-bindings"
    )

    handoff_database_path = (
        tmp_path
        / "customer-trial-handoff.sqlite3"
    )

    observation_database_path = (
        tmp_path
        / "customer-trial-observation.sqlite3"
    )

    readiness_database_path = (
        tmp_path
        / "customer-trial-delivery-readiness.sqlite3"
    )

    commercial_execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                execution_directory
            )
        )
    )

    binding_service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=(
                binding_directory
            )
        )
    )

    preflight_service, handoff_bridge = (
        build_services(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    handoff_store = (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            handoff_database_path
        )
    )

    handoff_service = (
        GovernanceCustomerTrialExecutionHandoffService(
            bridge=handoff_bridge,
            receipt_store=handoff_store,
        )
    )

    observation_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            observation_database_path
        )
    )

    observation_recorder = (
        GovernanceCustomerTrialExecutionObservationRecordingBridge(
            handoff_receipt_store=(
                handoff_store
            ),
            observation_receipt_store=(
                observation_store
            ),
        )
    )

    commercial_execution_service.configure_customer_trial_observation_recorder(
        recorder=(
            observation_recorder
        )
    )

    observation_status_service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=(
                observation_store
            )
        )
    )

    commercial_readiness_service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=(
                commercial_execution_service
            )
        )
    )

    controlled_trial_readiness_projection_service = (
        GovernanceCustomerTrialDeliveryReadinessService(
            commercial_readiness_service=(
                commercial_readiness_service
            )
        )
    )

    readiness_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            readiness_database_path
        )
    )

    readiness_recorder = (
        GovernanceCustomerTrialDeliveryReadinessRecordingBridge(
            observation_receipt_store=(
                observation_store
            ),
            readiness_projection_service=(
                controlled_trial_readiness_projection_service
            ),
            readiness_receipt_store=(
                readiness_store
            ),
        )
    )

    commercial_readiness_service.configure_customer_trial_readiness_recorder(
        recorder=(
            readiness_recorder
        )
    )

    customer_trial_readiness_status_service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=(
                readiness_store
            )
        )
    )

    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_router(
            service=(
                commercial_execution_service
            ),
            execution_input_binding_service=(
                binding_service
            ),
        )
    )

    app.include_router(
        create_customer_trial_execution_handoff_router(
            service=(
                handoff_service
            ),
            execution_input_binding_service=(
                binding_service
            ),
        )
    )

    app.include_router(
        create_customer_trial_execution_observation_router(
            service=(
                observation_status_service
            )
        )
    )

    unused = UnusedDeliveryService()

    app.include_router(
        create_governance_commercial_paid_assessment_delivery_router(
            readiness_service=(
                commercial_readiness_service
            ),
            approval_service=unused,
            recording_service=unused,
            status_service=unused,
            lifecycle_status_service=unused,
            client_acknowledgment_service=unused,
            client_response_service=unused,
            closeout_status_service=unused,
            administrative_closeout_service=unused,
        )
    )

    app.include_router(
        create_customer_trial_delivery_readiness_router(
            service=(
                customer_trial_readiness_status_service
            )
        )
    )

    return {
        "app":
            app,
        "client":
            TestClient(app),
        "binding_service":
            binding_service,
        "handoff_store":
            handoff_store,
        "observation_store":
            observation_store,
        "readiness_store":
            readiness_store,
        "readiness_database_path":
            readiness_database_path,
    }


def test_controlled_trial_delivery_readiness_true_e2e(
    tmp_path: Path,
) -> None:
    runtime = build_e2e_app(
        tmp_path
    )

    client = runtime[
        "client"
    ]

    binding_service = runtime[
        "binding_service"
    ]

    readiness_store = runtime[
        "readiness_store"
    ]

    readiness_database_path = runtime[
        "readiness_database_path"
    ]

    #
    # 1. Bind the exact authoritative commercial execution input.
    #
    bind_execution_input(
        binding_service=(
            binding_service
        ),
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
    )

    binding = binding_service.get(
        hierarchy_key=(
            HIERARCHY_KEY
        )
    )

    assert (
        binding.hierarchy_key
        == HIERARCHY_KEY
    )

    assert len(
        binding.binding_hash
    ) == 64

    assert len(
        binding.assessment_execution_request_hash
    ) == 64

    #
    # 2. Build one governed contract/authorization payload and reuse
    #    it for both the trial handoff and PA015 execution.
    #
    commercial_payload = (
        build_commercial_execution_payload(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        )
    )

    handoff_payload = (
        build_customer_trial_handoff_payload(
            execution_input_binding_hash=(
                binding.binding_hash
            ),
            contract_execution_event=(
                commercial_payload[
                    "contract_execution_event"
                ]
            ),
            paid_work_authorization=(
                commercial_payload[
                    "paid_work_authorization"
                ]
            ),
        )
    )

    #
    # 3. Prepare the controlled-trial execution handoff.
    #
    handoff_response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=handoff_payload,
    )

    assert (
        handoff_response.status_code
        == 201
    )

    handoff_result = (
        handoff_response.json()
    )

    assert (
        handoff_result[
            "authority"
        ]
        == "HANDOFF_PREPARATION_ONLY"
    )

    handoff_receipt = (
        handoff_result[
            "result"
        ][
            "receipt"
        ]
    )

    assert (
        handoff_receipt[
            "hierarchy_key"
        ]
        == HIERARCHY_KEY
    )

    original_handoff_receipt_hash = (
        handoff_receipt[
            "receipt_hash"
        ]
    )

    handoff_lineage = (
        handoff_receipt[
            "execution_handoff_lineage"
        ]
    )

    original_handoff_hash = (
        handoff_lineage[
            "handoff_hash"
        ]
    )

    assert (
        handoff_lineage[
            "assessment_execution_request_hash"
        ]
        == binding.assessment_execution_request_hash
    )

    #
    # 4. Before PA015 execution there is no observation and no
    #    controlled-trial delivery-readiness receipt.
    #
    observation_before = client.get(
        observation_status_url()
    )

    assert (
        observation_before.status_code
        == 200
    )

    assert (
        observation_before.json()[
            "result"
        ][
            "receipt_found"
        ]
        is False
    )

    readiness_before_execution = (
        client.get(
            customer_trial_readiness_status_url()
        )
    )

    assert (
        readiness_before_execution.status_code
        == 200
    )

    assert (
        readiness_before_execution.json()[
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        readiness_before_execution.json()[
            "result"
        ][
            "receipt_found"
        ]
        is False
    )

    #
    # 5. Execute through the real commercial PA015 API.
    #
    execution_response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=commercial_payload,
    )

    assert (
        execution_response.status_code
        == 201
    )

    execution_payload = (
        execution_response.json()
    )

    assert (
        execution_payload[
            "operator_run_passed"
        ]
        is True
    )

    assert (
        execution_payload[
            "result"
        ][
            "disposition"
        ]
        == "executed"
    )

    assert (
        execution_payload[
            "result"
        ][
            "hierarchy_key"
        ]
        == HIERARCHY_KEY
    )

    assert (
        execution_payload[
            "result"
        ][
            "artifact_count_after"
        ]
        == 10
    )

    #
    # 6. PA015 automatically creates the 04J-05 observation.
    #
    observation_after = client.get(
        observation_status_url()
    )

    assert (
        observation_after.status_code
        == 200
    )

    observation_payload = (
        observation_after.json()
    )

    assert (
        observation_payload[
            "result"
        ][
            "receipt_found"
        ]
        is True
    )

    observation_receipt = (
        observation_payload[
            "result"
        ][
            "receipt"
        ]
    )

    assert (
        observation_receipt[
            "observation_status"
        ]
        == "execution_observed"
    )

    assert (
        observation_receipt[
            "handoff_receipt_hash"
        ]
        == original_handoff_receipt_hash
    )

    observation_execution_lineage = (
        observation_receipt[
            "execution_lineage"
        ]
    )

    assert (
        observation_execution_lineage[
            "handoff_hash"
        ]
        == original_handoff_hash
    )

    assert (
        observation_execution_lineage[
            "assessment_execution_request_hash"
        ]
        == binding.assessment_execution_request_hash
    )

    observation_report = (
        observation_receipt[
            "report"
        ]
    )

    #
    # 7. Critical constitutional proof:
    #
    #    execution_observed DOES NOT by itself imply
    #    controlled_trial_delivery_ready.
    #
    readiness_after_execution_before_pa003 = (
        client.get(
            customer_trial_readiness_status_url()
        )
    )

    assert (
        readiness_after_execution_before_pa003.status_code
        == 200
    )

    before_pa003_payload = (
        readiness_after_execution_before_pa003.json()
    )

    assert (
        before_pa003_payload[
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        before_pa003_payload[
            "result"
        ][
            "receipt_found"
        ]
        is False
    )

    assert (
        before_pa003_payload[
            "boundaries"
        ][
            "api_does_not_infer_readiness_from_execution_observation"
        ]
        is True
    )

    #
    # 8. Invoke the REAL commercial PA-003 readiness route.
    #
    #    This calls the existing authoritative commercial readiness
    #    service. Only AFTER its governed verification succeeds may
    #    the configured 06D recorder persist controlled-trial
    #    delivery-readiness evidence.
    #
    commercial_readiness_response = (
        client.get(
            commercial_delivery_readiness_url()
        )
    )

    assert (
        commercial_readiness_response.status_code
        == 200
    )

    commercial_readiness_payload = (
        commercial_readiness_response.json()
    )

    assert (
        commercial_readiness_payload[
            "delivery_readiness_status"
        ]
        == "ready_for_delivery_approval_review"
    )

    assert (
        commercial_readiness_payload[
            "repository_chain_valid"
        ]
        is True
    )

    assert (
        commercial_readiness_payload[
            "artifact_count"
        ]
        == 10
    )

    assert (
        commercial_readiness_payload[
            "report_id"
        ]
        == observation_report[
            "report_id"
        ]
    )

    #
    # 9. The PA-003 call must have automatically caused 06D to
    #    correlate and persist the 06B controlled-trial receipt.
    #
    readiness_after_pa003 = (
        client.get(
            customer_trial_readiness_status_url()
        )
    )

    assert (
        readiness_after_pa003.status_code
        == 200
    )

    controlled_trial_payload = (
        readiness_after_pa003.json()
    )

    assert (
        controlled_trial_payload[
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        controlled_trial_payload[
            "result"
        ][
            "receipt_found"
        ]
        is True
    )

    readiness_receipt = (
        controlled_trial_payload[
            "result"
        ][
            "receipt"
        ]
    )

    assert readiness_receipt is not None

    assert (
        readiness_receipt[
            "hierarchy_key"
        ]
        == HIERARCHY_KEY
    )

    assert (
        readiness_receipt[
            "readiness_status"
        ]
        == "controlled_trial_delivery_ready"
    )

    assert (
        readiness_receipt[
            "observation_receipt_hash"
        ]
        == observation_receipt[
            "receipt_hash"
        ]
    )

    readiness_controlled_trial_lineage = (
        readiness_receipt[
            "controlled_trial_lineage"
        ]
    )

    assert (
        readiness_controlled_trial_lineage[
            "handoff_receipt_hash"
        ]
        == original_handoff_receipt_hash
    )

    assert (
        readiness_controlled_trial_lineage[
            "handoff_hash"
        ]
        == original_handoff_hash
    )

    assert (
        readiness_controlled_trial_lineage[
            "assessment_execution_request_hash"
        ]
        == binding.assessment_execution_request_hash
    )

    readiness_execution_lineage = (
        readiness_receipt[
            "execution_lineage"
        ]
    )

    assert (
        readiness_execution_lineage[
            "execution_result_hash"
        ]
        == observation_execution_lineage[
            "execution_result_hash"
        ]
    )

    assert (
        readiness_execution_lineage[
            "application_hash"
        ]
        == observation_execution_lineage[
            "application_hash"
        ]
    )

    assert (
        readiness_execution_lineage[
            "persistence_hash"
        ]
        == observation_execution_lineage[
            "persistence_hash"
        ]
    )

    readiness_report = (
        readiness_receipt[
            "report"
        ]
    )

    assert (
        readiness_report[
            "report_id"
        ]
        == observation_report[
            "report_id"
        ]
    )

    assert (
        readiness_report[
            "report_package_hash"
        ]
        == observation_report[
            "report_package_hash"
        ]
    )

    commercial_lineage = (
        readiness_receipt[
            "commercial_readiness"
        ]
    )

    assert (
        commercial_lineage[
            "delivery_readiness_status"
        ]
        == "ready_for_delivery_approval_review"
    )

    assert (
        commercial_lineage[
            "repository_chain_valid"
        ]
        is True
    )

    assert (
        commercial_lineage[
            "artifact_count"
        ]
        == 10
    )

    original_readiness_receipt_hash = (
        readiness_receipt[
            "receipt_hash"
        ]
    )

    original_readiness_hash = (
        readiness_receipt[
            "readiness_hash"
        ]
    )

    assert len(
        original_readiness_receipt_hash
    ) == 64

    assert len(
        original_readiness_hash
    ) == 64

    #
    # 10. Verify the durable store contains exactly the same receipt.
    #
    stored_readiness = (
        readiness_store.get(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        )
    )

    assert stored_readiness is not None

    assert (
        stored_readiness.receipt_hash
        == original_readiness_receipt_hash
    )

    assert (
        stored_readiness.readiness_hash
        == original_readiness_hash
    )

    #
    # 11. Readiness evidence remains evidence/readiness only.
    #
    receipt_boundaries = (
        readiness_receipt[
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
            "receipt_is_not_delivery_approval"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_approved_for_human_delivery"
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
            "pa003_remains_delivery_readiness_authority"
        ]
        is True
    )

    #
    # 12. Restart proof.
    #
    # Recreate a fresh receipt store, status service, router, and
    # FastAPI application against the same readiness SQLite file.
    #
    restarted_store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            readiness_database_path
        )
    )

    restarted_service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=(
                restarted_store
            )
        )
    )

    restarted_app = FastAPI()

    restarted_app.include_router(
        create_customer_trial_delivery_readiness_router(
            service=(
                restarted_service
            )
        )
    )

    restarted_client = TestClient(
        restarted_app
    )

    restarted_response = (
        restarted_client.get(
            customer_trial_readiness_status_url()
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
        == original_readiness_receipt_hash
    )

    assert (
        restarted_receipt[
            "readiness_hash"
        ]
        == original_readiness_hash
    )

    assert (
        restarted_receipt[
            "observation_receipt_hash"
        ]
        == observation_receipt[
            "receipt_hash"
        ]
    )

    restarted_controlled_lineage = (
        restarted_receipt[
            "controlled_trial_lineage"
        ]
    )

    assert (
        restarted_controlled_lineage[
            "handoff_hash"
        ]
        == original_handoff_hash
    )

    assert (
        restarted_controlled_lineage[
            "assessment_execution_request_hash"
        ]
        == binding.assessment_execution_request_hash
    )

    #
    # 13. The customer-trial namespace still contains no delivery
    #     approval or delivery authority.
    #
    forbidden_approval = client.post(
        (
            CUSTOMER_TRIAL_DELIVERY_READINESS_API_PREFIX
            + f"/{TENANT_ID}/"
            + f"{CLIENT_ID}/"
            + f"{ENGAGEMENT_ID}/"
            + f"{ASSESSMENT_ID}/"
            + "delivery-approval"
        ),
        json={},
    )

    assert (
        forbidden_approval.status_code
        == 404
    )

    forbidden_delivery = client.post(
        (
            CUSTOMER_TRIAL_DELIVERY_READINESS_API_PREFIX
            + f"/{TENANT_ID}/"
            + f"{CLIENT_ID}/"
            + f"{ENGAGEMENT_ID}/"
            + f"{ASSESSMENT_ID}/"
            + "deliver"
        ),
        json={},
    )

    assert (
        forbidden_delivery.status_code
        == 404
    )

    #
    # 14. The controlled-trial readiness endpoint itself remains
    #     GET-only.
    #
    openapi = client.get(
        "/openapi.json"
    ).json()

    readiness_path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "delivery-readiness-status"
    )

    assert (
        readiness_path
        in openapi[
            "paths"
        ]
    )

    assert set(
        openapi[
            "paths"
        ][
            readiness_path
        ].keys()
    ) == {
        "get"
    }