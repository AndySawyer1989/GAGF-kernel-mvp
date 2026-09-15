from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_execution_observation import (
    CustomerTrialExecutionObservation,
    EXECUTION_OBSERVED,
)
from backend.app.gagf.governance_customer_trial_execution_observation_api import (
    create_customer_trial_execution_observation_router,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_observation_service import (
    GovernanceCustomerTrialExecutionObservationStatusService,
)


def build_client(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=store
        )
    )

    app = FastAPI()

    router = (
        create_customer_trial_execution_observation_router(
            service=service
        )
    )

    for route in router.routes:
        app.router.routes.append(
            route
        )

    app.openapi_schema = None

    return (
        TestClient(app),
        store,
    )


def build_observation(
) -> CustomerTrialExecutionObservation:
    return CustomerTrialExecutionObservation(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
        hierarchy_key=(
            "tenant-controlled/"
            "client-controlled/"
            "engagement-controlled/"
            "assessment-controlled"
        ),
        observation_status=
            EXECUTION_OBSERVED,
        handoff_receipt_hash=
            "handoff-receipt-hash",
        handoff_lineage_hash=
            "handoff-lineage-hash",
        handoff_hash=
            "handoff-hash",
        assessment_execution_request_hash=
            "execution-request-hash",
        execution_result_hash=
            "execution-result-hash",
        application_hash=
            "application-hash",
        persistence_hash=
            "persistence-hash",
        report_id=
            "report-controlled",
        report_package_hash=
            "report-package-hash",
        application_completed=True,
        repository_chain_valid=True,
    )


def observation_status_url(
) -> str:
    return (
        "/api/v1/governance-customer-trials/"
        "tenant-controlled/"
        "client-controlled/"
        "engagement-controlled/"
        "assessment-controlled/"
        "execution-observation-status"
    )


def test_get_observation_status_returns_not_found(
    tmp_path,
):
    client, _ = build_client(
        tmp_path
    )

    response = client.get(
        observation_status_url()
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "status"
    ] == "ok"

    assert payload[
        "authority"
    ] == "READ_ONLY"

    assert payload[
        "result"
    ][
        "receipt_found"
    ] is False

    assert payload[
        "result"
    ][
        "receipt"
    ] is None


def test_get_observation_status_returns_durable_receipt(
    tmp_path,
):
    client, store = build_client(
        tmp_path
    )

    receipt = store.put(
        observation=
            build_observation()
    )

    response = client.get(
        observation_status_url()
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "result"
    ][
        "receipt_found"
    ] is True

    assert payload[
        "result"
    ][
        "receipt"
    ][
        "receipt_hash"
    ] == receipt.receipt_hash


def test_observation_status_api_is_read_only(
    tmp_path,
):
    client, _ = build_client(
        tmp_path
    )

    payload = client.get(
        observation_status_url()
    ).json()

    boundaries = payload[
        "boundaries"
    ]

    assert boundaries[
        "api_is_read_only"
    ] is True

    assert boundaries[
        "api_does_not_execute_assessment"
    ] is True

    assert boundaries[
        "api_does_not_create_execution_observation"
    ] is True

    assert boundaries[
        "api_does_not_infer_execution_from_handoff"
    ] is True

    assert boundaries[
        "api_does_not_authorize_recovery"
    ] is True

    assert boundaries[
        "api_does_not_authorize_delivery"
    ] is True

    assert boundaries[
        "api_does_not_authorize_closeout"
    ] is True

    assert boundaries[
        "api_does_not_authorize_intervention"
    ] is True


def test_observation_router_has_no_mutating_routes(
    tmp_path,
):
    client, _ = build_client(
        tmp_path
    )

    openapi = client.get(
        "/openapi.json"
    ).json()

    paths = openapi[
        "paths"
    ]

    observation_path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "execution-observation-status"
    )

    assert observation_path in paths

    assert set(
        paths[
            observation_path
        ].keys()
    ) == {
        "get"
    }

    assert not any(
        path.endswith(
            "/execute"
        )
        or path.endswith(
            "/recover"
        )
        or path.endswith(
            "/deliver"
        )
        or path.endswith(
            "/closeout"
        )
        or path.endswith(
            "/intervene"
        )
        for path in paths
        if "governance-customer-trials" in path
    )