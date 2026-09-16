from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_delivery_observation_api_registration import (
    CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_DELIVERY_OBSERVATION_STORE_STATE_KEY,
    register_customer_trial_delivery_observation_api,
)


def test_registration_exposes_status_route(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_delivery_observation_api(
        app=app,
        database_path=(
            tmp_path / "delivery-observation.sqlite3"
        ),
    )

    client = TestClient(app)

    response = client.get(
        (
            "/api/v1/governance-customer-trials/"
            "tenant/client/engagement/assessment/"
            "delivery-observation-status"
        )
    )

    assert response.status_code == 200
    assert response.json()["authority"] == "READ_ONLY"


def test_registration_exposes_service_state(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_delivery_observation_api(
        app=app,
        database_path=(
            tmp_path / "delivery-observation.sqlite3"
        ),
    )

    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_STATE_KEY,
    )


def test_registration_exposes_store_state(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_delivery_observation_api(
        app=app,
        database_path=(
            tmp_path / "delivery-observation.sqlite3"
        ),
    )

    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_STORE_STATE_KEY,
    )


def test_registration_adds_no_post_route(
    tmp_path: Path,
) -> None:
    app = FastAPI()

    register_customer_trial_delivery_observation_api(
        app=app,
        database_path=(
            tmp_path / "delivery-observation.sqlite3"
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
            "/delivery-observation-status"
        )
    ]

    assert len(matching) == 1

    assert matching[0].methods == {
        "GET"
    }