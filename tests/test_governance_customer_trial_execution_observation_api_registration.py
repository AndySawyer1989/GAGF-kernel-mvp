from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_execution_observation_api_registration import (
    CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_EXECUTION_OBSERVATION_STORE_STATE_KEY,
    register_customer_trial_execution_observation_api,
)


def test_registration_exposes_read_only_status_route(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_execution_observation_api(
        app=app,
        database_path=(
            tmp_path / "observation.sqlite3"
        ),
    )

    client = TestClient(app)

    response = client.get(
        (
            "/api/v1/governance-customer-trials/"
            "tenant-controlled/"
            "client-controlled/"
            "engagement-controlled/"
            "assessment-controlled/"
            "execution-observation-status"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "authority"
    ] == "READ_ONLY"

    assert payload[
        "result"
    ][
        "receipt_found"
    ] is False


def test_registration_sets_service_state(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_execution_observation_api(
        app=app,
        database_path=(
            tmp_path / "observation.sqlite3"
        ),
    )

    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_STATE_KEY,
    )


def test_registration_sets_store_state(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_execution_observation_api(
        app=app,
        database_path=(
            tmp_path / "observation.sqlite3"
        ),
    )

    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_STORE_STATE_KEY,
    )


def test_registration_adds_no_post_route(
    tmp_path,
):
    app = FastAPI()

    register_customer_trial_execution_observation_api(
        app=app,
        database_path=(
            tmp_path / "observation.sqlite3"
        ),
    )

    matching_routes = [
        route
        for route in app.routes
        if (
            getattr(
                route,
                "path",
                "",
            ).endswith(
                "/execution-observation-status"
            )
        )
    ]

    assert len(
        matching_routes
    ) == 1

    assert matching_routes[
        0
    ].methods == {
        "GET"
    }