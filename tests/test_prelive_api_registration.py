from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.prelive_api_registration import (
    PRELIVE_API_REGISTERED_STATE_KEY,
    PRELIVE_SERVICE_STATE_KEY,
    register_prelive_api,
)
from backend.app.gagf.prelive_blind_assessment_service import (
    PreliveBlindAssessmentService,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def test_registration_adds_prelive_routes():
    app = FastAPI()

    register_prelive_api(
        app=app
    )

    client = TestClient(app)

    validate_response = client.post(
        "/api/v1/prelive/validate",
        json={
            "scenario": build_scenario(),
        },
    )

    prepare_response = client.post(
        "/api/v1/prelive/prepare",
        json={
            "scenario": build_scenario(),
        },
    )

    execute_response = client.post(
        "/api/v1/prelive/execute",
        json={
            "scenario": build_scenario(),
        },
    )

    assert (
        validate_response.status_code
        == 200
    )

    assert (
        prepare_response.status_code
        == 200
    )

    assert (
        execute_response.status_code
        == 404
    )


def test_registration_stores_prelive_service():
    app = FastAPI()

    service = register_prelive_api(
        app=app
    )

    assert isinstance(
        service,
        PreliveBlindAssessmentService,
    )

    assert (
        getattr(
            app.state,
            PRELIVE_SERVICE_STATE_KEY,
        )
        is service
    )


def test_registration_sets_registered_flag():
    app = FastAPI()

    register_prelive_api(
        app=app
    )

    assert (
        getattr(
            app.state,
            PRELIVE_API_REGISTERED_STATE_KEY,
        )
        is True
    )


def test_registration_is_idempotent():
    app = FastAPI()

    first = register_prelive_api(
        app=app
    )

    second = register_prelive_api(
        app=app
    )

    assert second is first

    client = TestClient(app)

    response = client.post(
        "/api/v1/prelive/validate",
        json={
            "scenario": build_scenario(),
        },
    )

    assert response.status_code == 200