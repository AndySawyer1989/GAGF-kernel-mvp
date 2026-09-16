from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_api_registration import (
    CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_STORE_STATE_KEY,
    register_customer_trial_administrative_closeout_observation_api,
)


def test_registration_exposes_completion_status_route(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_administrative_closeout_observation_api(
        app=app,
        database_path=(
            tmp_path / "administrative-closeout-observation.sqlite3"
        ),
    )

    client = TestClient(app)

    response = client.get(
        (
            "/api/v1/governance-customer-trials/"
            "tenant/client/engagement/assessment/"
            "controlled-trial-completion-status"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authority"] == "READ_ONLY"

    assert (
        payload["result"]["controlled_trial_complete"]
        is False
    )


def test_registration_exposes_service_state(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_administrative_closeout_observation_api(
        app=app,
        database_path=(
            tmp_path / "administrative-closeout-observation.sqlite3"
        ),
    )

    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SERVICE_STATE_KEY,
    )


def test_registration_exposes_store_state(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_administrative_closeout_observation_api(
        app=app,
        database_path=(
            tmp_path / "administrative-closeout-observation.sqlite3"
        ),
    )

    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_STORE_STATE_KEY,
    )


def test_registration_adds_no_action_route(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_administrative_closeout_observation_api(
        app=app,
        database_path=(
            tmp_path / "administrative-closeout-observation.sqlite3"
        ),
    )

    matching = [
        route
        for route in app.routes
        if getattr(
            route,
            "path",
            "",
        ).endswith(
            "/controlled-trial-completion-status"
        )
    ]

    assert len(matching) == 1

    assert matching[0].methods == {
        "GET"
    }