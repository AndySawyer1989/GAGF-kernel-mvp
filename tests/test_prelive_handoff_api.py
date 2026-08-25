from __future__ import annotations

from copy import deepcopy

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.prelive_api import (
    create_prelive_router,
)
from backend.app.gagf.prelive_blind_assessment_service import (
    PreliveBlindAssessmentService,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)
from tests.test_prelive_execution_handoff_bridge import (
    build_contract_event,
)


def build_client() -> TestClient:
    app = FastAPI()

    router = create_prelive_router(
        service=PreliveBlindAssessmentService()
    )

    for route in router.routes:
        app.router.routes.append(route)

    return TestClient(app)


def build_paid_work_authorization() -> dict:
    return {
        "authorization_id":
            "paid-work-auth-prelive-001",
        "tenant_id":
            "synthetic-tenant",
        "client_id":
            "prelive-client",
        "engagement_id":
            "prelive-engagement",
        "assessment_id":
            "prelive-assessment",
        "contract_execution_event_id":
            "contract-event-prelive-001",
        "authorized_by":
            "PRELIVE Human Operator",
        "authorized_at":
            "2026-08-24T18:35:00+00:00",
        "paid_assessment_authorized":
            True,
    }


def build_payload() -> dict:
    return {
        "scenario":
            build_scenario(),
        "tenant_id":
            "synthetic-tenant",
        "client_id":
            "prelive-client",
        "engagement_id":
            "prelive-engagement",
        "assessment_id":
            "prelive-assessment",
        "assessment_name":
            "PRELIVE Blind Governance Assessment",
        "workflow_names": [
            "Synthetic Workflow",
        ],
        "organizational_units": [
            "Synthetic Operations",
        ],
        "objectives": [
            "Evaluate governance friction detection.",
        ],
        "expected_outcomes": [
            (
                "Produce deterministic FIP "
                "assessment output."
            ),
        ],
        "client_display_name":
            "Synthetic Test Organization",
        "prepared_by":
            "PRELIVE Test Operator",
        "exclusions": [
            "Production actions",
        ],
        "maximum_priorities":
            3,
        "contract_execution_event":
            build_contract_event(),
        "paid_work_authorization":
            build_paid_work_authorization(),
    }


def test_prepare_handoff_endpoint_returns_ready_handoff():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=build_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["api_version"] == "1.0.0"

    assert (
        payload["operation"]
        == "prepare-handoff"
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
        payload["result"]["handoff"]["status"]
        == "ready_for_assessment_execution"
    )


def test_prepare_handoff_preserves_hierarchy():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=build_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["result"]["handoff"][
            "hierarchy_key"
        ]
        == (
            "synthetic-tenant/"
            "prelive-client/"
            "prelive-engagement/"
            "prelive-assessment"
        )
    )


def test_prepare_handoff_binds_request_authorization_and_contract():
    client = build_client()

    request_payload = build_payload()

    authorization = PaidAssessmentWorkAuthorization(
        **request_payload[
            "paid_work_authorization"
        ]
    )

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=request_payload,
    )

    assert response.status_code == 200

    payload = response.json()

    handoff = payload["result"]["handoff"]

    assert (
        handoff["paid_work_authorization_id"]
        == "paid-work-auth-prelive-001"
    )

    assert (
        handoff["paid_work_authorization_hash"]
        == authorization.authorization_hash
    )

    assert (
        handoff["contract_execution_event_id"]
        == "contract-event-prelive-001"
    )

    assert (
        len(
            handoff[
                "contract_execution_event_hash"
            ]
        )
        == 64
    )

    assert (
        len(
            handoff[
                "assessment_execution_request_hash"
            ]
        )
        == 64
    )

    assert (
        len(
            handoff["handoff_hash"]
        )
        == 64
    )


def test_prepare_handoff_rejects_cross_tenant_authorization():
    client = build_client()

    request_payload = build_payload()

    request_payload[
        "paid_work_authorization"
    ][
        "tenant_id"
    ] = "different-tenant"

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=request_payload,
    )

    assert response.status_code == 422

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == "PRELIVE_EXECUTION_HANDOFF_FAILED"
    )


def test_prepare_handoff_rejects_contract_event_mismatch():
    client = build_client()

    request_payload = build_payload()

    request_payload[
        "paid_work_authorization"
    ][
        "contract_execution_event_id"
    ] = "different-contract-event"

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=request_payload,
    )

    assert response.status_code == 422

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == "PRELIVE_EXECUTION_HANDOFF_FAILED"
    )


def test_prepare_handoff_requires_human_contract_confirmation():
    client = build_client()

    request_payload = build_payload()

    contract_event = deepcopy(
        request_payload[
            "contract_execution_event"
        ]
    )

    contract_event[
        "event_checklist"
    ][
        "human_operator_confirmed_execution"
    ] = False

    request_payload[
        "contract_execution_event"
    ] = contract_event

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=request_payload,
    )

    assert response.status_code == 422

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == "PRELIVE_EXECUTION_HANDOFF_FAILED"
    )


def test_prepare_handoff_requires_executed_contract():
    client = build_client()

    request_payload = build_payload()

    contract_event = deepcopy(
        request_payload[
            "contract_execution_event"
        ]
    )

    contract_event[
        "commercial_boundary"
    ][
        "contract_executed"
    ] = False

    request_payload[
        "contract_execution_event"
    ] = contract_event

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=request_payload,
    )

    assert response.status_code == 422

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == "PRELIVE_EXECUTION_HANDOFF_FAILED"
    )


def test_prepare_handoff_does_not_claim_execution():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/prepare-handoff",
        json=build_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["assessment_executed"]
        is False
    )

    assert (
        payload["execution_authorized"]
        is False
    )

    assert (
        "execution_result"
        not in payload
    )

    assert (
        "customer_outcome_verified"
        not in payload
    )

    assert (
        "production_onboarding_authorized"
        not in payload
    )


def test_prelive_execute_endpoint_remains_absent():
    client = build_client()

    response = client.post(
        "/api/v1/prelive/execute",
        json=build_payload(),
    )

    assert response.status_code == 404