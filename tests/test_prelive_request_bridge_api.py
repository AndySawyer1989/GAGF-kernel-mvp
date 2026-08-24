from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.prelive_api import (
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

    router = create_prelive_router(
        service=PreliveBlindAssessmentService()
    )

    for route in router.routes:
        app.router.routes.append(route)

    return TestClient(app)


def build_payload(
    *,
    tenant_id: str = "synthetic-tenant",
) -> dict:
    return {
        "scenario":
            build_scenario(),
        "tenant_id":
            tenant_id,
        "client_id":
            "prelive-client",
        "engagement_id":
            "prelive-engagement",
        "assessment_id":
            "prelive-assessment",
        "assessment_name":
            "PRELIVE Blind Governance Assessment",
        "workflow_names": [
            "Synthetic Workflow"
        ],
        "organizational_units": [
            "Synthetic Operations"
        ],
        "objectives": [
            "Evaluate governance friction detection."
        ],
        "expected_outcomes": [
            "Produce deterministic FIP assessment output."
        ],
        "client_display_name":
            "Synthetic Test Organization",
        "prepared_by":
            "PRELIVE Test Operator",
        "exclusions": [
            "Production actions"
        ],
        "maximum_priorities":
            3,
    }


def test_build_request_endpoint_constructs_real_handoff():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/build-request",
        json=build_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["operation"]
        == "build-request"
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
        payload["result"]["event_count"]
        == 100
    )

    assert (
        len(
            payload["result"][
                "scenario_sha256"
            ]
        )
        == 64
    )


def test_build_request_endpoint_preserves_hierarchy():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/build-request",
        json=build_payload(),
    )

    assert response.status_code == 200

    request = response.json()[
        "result"
    ]["request"]

    assert (
        request["hierarchy_key"]
        == (
            "synthetic-tenant/"
            "prelive-client/"
            "prelive-engagement/"
            "prelive-assessment"
        )
    )


def test_build_request_endpoint_rejects_cross_tenant():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/build-request",
        json=build_payload(
            tenant_id="different-tenant"
        ),
    )

    assert response.status_code == 422

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == "PRELIVE_REQUEST_BRIDGE_FAILED"
    )


def test_build_request_endpoint_remains_non_executing():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/build-request",
        json=build_payload(),
    )

    assert response.status_code == 200

    result = response.json()[
        "result"
    ]

    assert (
        result["execution_authorized"]
        is False
    )

    assert (
        result["assessment_executed"]
        is False
    )

    assert (
        result["paid_work_authorized"]
        is False
    )

    assert (
        result[
            "production_onboarding_authorized"
        ]
        is False
    )


def test_build_request_endpoint_preserves_gagf_authority():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/build-request",
        json=build_payload(),
    )

    assert response.status_code == 200

    assert (
        response.json()["result"][
            "authority"
        ]
        == "GAGF_FIP_ONLY"
    )


def test_prelive_execute_endpoint_still_does_not_exist():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/execute",
        json=build_payload(),
    )

    assert response.status_code == 404