from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_preflight_api import (
    CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX,
)
from backend.app.gagf.governance_customer_trial_preflight_api_registration import (
    CUSTOMER_TRIAL_PREFLIGHT_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_PREFLIGHT_STORE_STATE_KEY,
    register_customer_trial_preflight_api,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    GovernanceCustomerTrialPreflightReceiptStore,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


def test_registers_customer_trial_preflight_routes(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_preflight_api(
        app=app,
        database_path=(
            tmp_path / "preflight.sqlite3"
        ),
    )

    paths = {
        route.path
        for route in app.routes
    }

    assert (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/preflight"
        in paths
    )

    assert (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "preflight-status"
        in paths
    )


def test_registration_exposes_service_state(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_preflight_api(
        app=app,
        database_path=(
            tmp_path / "preflight.sqlite3"
        ),
    )

    service = getattr(
        app.state,
        CUSTOMER_TRIAL_PREFLIGHT_SERVICE_STATE_KEY,
    )

    store = getattr(
        app.state,
        CUSTOMER_TRIAL_PREFLIGHT_STORE_STATE_KEY,
    )

    assert isinstance(
        service,
        GovernanceCustomerTrialPreflightService,
    )

    assert isinstance(
        store,
        GovernanceCustomerTrialPreflightReceiptStore,
    )


def test_registration_invalidates_openapi_cache(
    tmp_path,
):
    app = FastAPI()

    app.openapi()

    assert app.openapi_schema is not None

    register_customer_trial_preflight_api(
        app=app,
        database_path=(
            tmp_path / "preflight.sqlite3"
        ),
    )

    assert app.openapi_schema is None

    rebuilt = app.openapi()

    paths = rebuilt["paths"]

    assert (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/preflight"
        in paths
    )


def test_registered_api_is_callable(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_preflight_api(
        app=app,
        database_path=(
            tmp_path / "preflight.sqlite3"
        ),
    )

    client = TestClient(
        app
    )

    response = client.get(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/tenant-alpha/"
            "client-customer-001/"
            "engagement-trial-001/"
            "assessment-trial-001/"
            "preflight-status"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["authority"]
        == "READ_ONLY"
    )

    assert (
        payload["result"][
            "receipt_found"
        ]
        is False
    )


def test_registration_does_not_add_execution_route(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_preflight_api(
        app=app,
        database_path=(
            tmp_path / "preflight.sqlite3"
        ),
    )

    client = TestClient(
        app
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/execute"
        ),
        json={},
    )

    assert response.status_code == 404