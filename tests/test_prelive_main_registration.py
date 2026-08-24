from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def test_main_registers_prelive_api():
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

    assert (
        validate_response.status_code
        == 200
    )

    assert (
        validate_response.json()[
            "result"
        ]["valid"]
        is True
    )

    assert (
        prepare_response.status_code
        == 200
    )

    assert (
        prepare_response.json()[
            "result"
        ]["status"]
        == "prepared"
    )


def test_main_exposes_no_prelive_execute_route():
    client = TestClient(app)

    response = client.post(
        "/api/v1/prelive/execute",
        json={
            "scenario": build_scenario(),
        },
    )

    assert response.status_code == 404