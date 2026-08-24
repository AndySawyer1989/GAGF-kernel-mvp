from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.prelive_api import (
    PRELIVE_API_VERSION,
    create_prelive_router,
)
from backend.app.gagf.prelive_blind_assessment_service import (
    PreliveBlindAssessmentService,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def build_client() -> TestClient:
    app = FastAPI()

    app.include_router(
        create_prelive_router(
            service=PreliveBlindAssessmentService()
        )
    )

    return TestClient(app)


def test_validate_endpoint_accepts_valid_blind_scenario():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/validate",
        json={
            "scenario": build_scenario(),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["api_version"]
        == PRELIVE_API_VERSION
    )

    assert (
        payload["operation"]
        == "validate"
    )

    assert (
        payload["authority"]
        == "GAGF_FIP_ONLY"
    )

    assert (
        payload["assessment_executed"]
        is False
    )

    assert (
        payload["result"]["valid"]
        is True
    )

    assert (
        payload["result"]["summary"]["event_count"]
        == 100
    )


def test_validate_endpoint_reports_invalid_scenario():
    client = build_client()

    scenario = build_scenario()

    scenario["expected_conditions"] = [
        {
            "condition": "hidden answer",
        }
    ]

    response = client.post(
        "/api/v1/prelive/validate",
        json={
            "scenario": scenario,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["result"]["valid"]
        is False
    )

    issue_codes = {
        issue["code"]
        for issue in payload["result"]["issues"]
    }

    assert (
        "ORACLE_LEAKAGE"
        in issue_codes
    )


def test_prepare_endpoint_prepares_valid_scenario():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/prepare",
        json={
            "scenario": build_scenario(),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["operation"]
        == "prepare"
    )

    assert (
        payload["authority"]
        == "GAGF_FIP_ONLY"
    )

    assert (
        payload["assessment_executed"]
        is False
    )

    assert (
        payload["execution_authorized"]
        is False
    )

    assert (
        payload["human_execution_required"]
        is True
    )

    assert (
        payload["result"]["status"]
        == "prepared"
    )

    assert (
        payload["result"]["manifest"]["oracle_status"]
        == "SEALED"
    )


def test_prepare_endpoint_returns_governed_evidence():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/prepare",
        json={
            "scenario": build_scenario(),
        },
    )

    assert response.status_code == 200

    result = response.json()["result"]

    assert (
        result["csv_text"].startswith(
            "event_id,event_type,"
            "occurred_at,work_item_id,"
        )
    )

    assert (
        result["manifest"]["event_count"]
        == 100
    )

    assert (
        len(
            result["manifest"]["scenario_sha256"]
        )
        == 64
    )


def test_prepare_endpoint_rejects_oracle_leakage():
    client = build_client()

    scenario = build_scenario()

    scenario["events"][0][
        "kernel_decision"
    ] = "approve"

    response = client.post(
        "/api/v1/prelive/prepare",
        json={
            "scenario": scenario,
        },
    )

    assert response.status_code == 422

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == "PRELIVE_VALIDATION_FAILED"
    )


def test_prelive_router_exposes_no_execute_route():
    client = build_client()

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