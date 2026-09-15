from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_api import (
    create_governance_commercial_paid_assessment_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
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


def observation_status_url() -> str:
    return (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_PREFIX
        + f"/{TENANT_ID}/"
        + f"{CLIENT_ID}/"
        + f"{ENGAGEMENT_ID}/"
        + f"{ASSESSMENT_ID}/"
        + "execution-observation-status"
    )


def handoff_status_url() -> str:
    return (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + f"/{TENANT_ID}/"
        + f"{CLIENT_ID}/"
        + f"{ENGAGEMENT_ID}/"
        + f"{ASSESSMENT_ID}/"
        + "execution-handoff-status"
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

    commercial_service = (
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

    commercial_service.configure_customer_trial_observation_recorder(
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

    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_router(
            service=(
                commercial_service
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

    return {
        "app":
            app,
        "client":
            TestClient(app),
        "commercial_service":
            commercial_service,
        "binding_service":
            binding_service,
        "handoff_store":
            handoff_store,
        "observation_store":
            observation_store,
        "observation_database_path":
            observation_database_path,
    }


def test_controlled_trial_execution_observation_true_e2e(
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

    handoff_store = runtime[
        "handoff_store"
    ]

    observation_database_path = runtime[
        "observation_database_path"
    ]

    #
    # 1. Persist the exact authoritative commercial execution
    #    request before either handoff or PA015 execution.
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

    assert (
        isinstance(
            binding.binding_hash,
            str,
        )
    )

    assert len(
        binding.binding_hash
    ) == 64

    assert (
        isinstance(
            binding.assessment_execution_request_hash,
            str,
        )
    )

    assert len(
        binding.assessment_execution_request_hash
    ) == 64

    #
    # 2. Use exactly the same governed contract event and paid
    #    work authorization for customer-trial handoff and the
    #    commercial PA015 execution.
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

    handoff_payload_result = (
        handoff_response.json()
    )

    assert (
        handoff_payload_result[
            "authority"
        ]
        == "HANDOFF_PREPARATION_ONLY"
    )

    handoff_receipt = (
        handoff_payload_result[
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

    execution_handoff_lineage = (
        handoff_receipt[
            "execution_handoff_lineage"
        ]
    )

    assert (
        execution_handoff_lineage[
            "assessment_execution_request_hash"
        ]
        == (
            binding
            .assessment_execution_request_hash
        )
    )

    original_handoff_receipt_hash = (
        handoff_receipt[
            "receipt_hash"
        ]
    )

    original_handoff_hash = (
        execution_handoff_lineage[
            "handoff_hash"
        ]
    )

    assert len(
        original_handoff_receipt_hash
    ) == 64

    assert len(
        original_handoff_hash
    ) == 64

    persisted_handoff = (
        handoff_store.get(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        )
    )

    assert persisted_handoff is not None

    assert (
        persisted_handoff.receipt_hash
        == original_handoff_receipt_hash
    )

    #
    # 4. Before PA015 executes, handoff exists but execution
    #    observation MUST NOT exist.
    #
    before_execution = client.get(
        observation_status_url()
    )

    assert (
        before_execution.status_code
        == 200
    )

    before_payload = (
        before_execution.json()
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

    assert (
        before_payload[
            "boundaries"
        ][
            "api_does_not_infer_execution_from_handoff"
        ]
        is True
    )

    #
    # 5. Execute through the real commercial API. This invokes
    #    the real commercial service, PA015 path, durable status,
    #    snapshot bridge, then the configured 04J-05D recorder.
    #
    execution_response = client.post(
        (
            "/api/v1/"
            "governance-paid-assessments/"
            "execute"
        ),
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
    # 6. PA015 success must have automatically produced the
    #    durable customer-trial execution observation.
    #
    after_execution = client.get(
        observation_status_url()
    )

    assert (
        after_execution.status_code
        == 200
    )

    after_payload = (
        after_execution.json()
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

    observation_receipt = (
        after_payload[
            "result"
        ][
            "receipt"
        ]
    )

    assert observation_receipt is not None

    assert (
        observation_receipt[
            "hierarchy_key"
        ]
        == HIERARCHY_KEY
    )

    assert (
        observation_receipt[
            "observation_status"
        ]
        == "execution_observed"
    )

    #
    # Exact controlled-trial and PA015 execution lineage.
    #
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
        == (
            binding
            .assessment_execution_request_hash
        )
    )

    #
    # Exact authoritative PA015 result evidence must be carried
    # into the observation receipt.
    #
    assert (
        isinstance(
            observation_execution_lineage[
                "execution_result_hash"
            ],
            str,
        )
    )

    assert len(
        observation_execution_lineage[
            "execution_result_hash"
        ]
    ) == 64

    assert (
        isinstance(
            observation_execution_lineage[
                "application_hash"
            ],
            str,
        )
    )

    assert len(
        observation_execution_lineage[
            "application_hash"
        ]
    ) == 64

    assert (
        isinstance(
            observation_execution_lineage[
                "persistence_hash"
            ],
            str,
        )
    )

    assert len(
        observation_execution_lineage[
            "persistence_hash"
        ]
    ) == 64

    observation_report = (
        observation_receipt[
            "report"
        ]
    )

    assert (
        isinstance(
            observation_report[
                "report_id"
            ],
            str,
        )
    )

    assert (
        observation_report[
            "report_id"
        ]
    )

    assert (
        isinstance(
            observation_report[
                "report_package_hash"
            ],
            str,
        )
    )

    assert len(
        observation_report[
            "report_package_hash"
        ]
    ) == 64

    original_observation_receipt_hash = (
        observation_receipt[
            "receipt_hash"
        ]
    )

    assert len(
        original_observation_receipt_hash
    ) == 64

    #
    # 7. Observation remains evidence only.
    #
    receipt_boundaries = (
        observation_receipt[
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
            "receipt_is_not_execution_authority"
        ]
        is True
    )

    assert (
        receipt_boundaries[
            "receipt_is_not_recovery_authority"
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

    #
    # 8. Recreate the observation store/service/router against
    #    the same SQLite file. This is the restart/recovery proof
    #    for the read-only observation boundary.
    #
    restarted_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            observation_database_path
        )
    )

    restarted_service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=(
                restarted_store
            )
        )
    )

    restarted_app = FastAPI()

    restarted_app.include_router(
        create_customer_trial_execution_observation_router(
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
            observation_status_url()
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
        == original_observation_receipt_hash
    )

    assert (
        restarted_receipt[
            "handoff_receipt_hash"
        ]
        == original_handoff_receipt_hash
    )

    restarted_execution_lineage = (
        restarted_receipt[
            "execution_lineage"
        ]
    )

    assert (
        restarted_execution_lineage[
            "handoff_hash"
        ]
        == original_handoff_hash
    )

    assert (
        restarted_execution_lineage[
            "assessment_execution_request_hash"
        ]
        == (
            binding
            .assessment_execution_request_hash
        )
    )

    #
    # 9. Handoff itself remains durable and READ_ONLY through
    #    its status endpoint.
    #
    handoff_status_response = (
        client.get(
            handoff_status_url()
        )
    )

    assert (
        handoff_status_response.status_code
        == 200
    )

    assert (
        handoff_status_response.json()[
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        handoff_status_response.json()[
            "result"
        ][
            "receipt_found"
        ]
        is True
    )

    #
    # 10. Controlled-trial namespace never becomes another
    #     execution authority.
    #
    forbidden_execute = (
        client.post(
            (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
                + "/execute"
            ),
            json={},
        )
    )

    assert (
        forbidden_execute.status_code
        == 404
    )
