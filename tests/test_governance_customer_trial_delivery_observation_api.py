from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_delivery_observation_api import (
    create_customer_trial_delivery_observation_router,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_service import (
    GovernanceCustomerTrialDeliveryObservationStatusService,
)

from tests.test_governance_customer_trial_delivery_observation_receipt_store import (
    build_observation,
)


def build_client(
    tmp_path: Path,
):
    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            tmp_path / "delivery-observation.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=store
        )
    )

    app = FastAPI()

    router = (
        create_customer_trial_delivery_observation_router(
            service=service
        )
    )

    for route in router.routes:
        app.router.routes.append(route)

    app.openapi_schema = None

    return TestClient(app), store


def status_url(
    *,
    tenant_id: str,
    client_id: str,
    engagement_id: str,
    assessment_id: str,
) -> str:
    return (
        "/api/v1/governance-customer-trials/"
        f"{tenant_id}/"
        f"{client_id}/"
        f"{engagement_id}/"
        f"{assessment_id}/"
        "delivery-observation-status"
    )


def test_get_returns_not_found_without_receipt(
    tmp_path: Path,
) -> None:
    client, _ = build_client(
        tmp_path
    )

    response = client.get(
        status_url(
            tenant_id="tenant",
            client_id="client",
            engagement_id="engagement",
            assessment_id="assessment",
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authority"] == "READ_ONLY"

    assert (
        payload["result"]["receipt_found"]
        is False
    )

    assert payload["result"]["receipt"] is None


def test_get_returns_persisted_receipt(
    tmp_path: Path,
) -> None:
    client, store = build_client(
        tmp_path
    )

    written = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    response = client.get(
        status_url(
            tenant_id=written.tenant_id,
            client_id=written.client_id,
            engagement_id=written.engagement_id,
            assessment_id=written.assessment_id,
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["result"]["receipt_found"]
        is True
    )

    assert (
        payload["result"]["receipt"]["receipt_hash"]
        == written.receipt_hash
    )


def test_api_boundaries_are_read_only(
    tmp_path: Path,
) -> None:
    client, _ = build_client(
        tmp_path
    )

    payload = client.get(
        status_url(
            tenant_id="tenant",
            client_id="client",
            engagement_id="engagement",
            assessment_id="assessment",
        )
    ).json()

    boundaries = payload["boundaries"]

    assert boundaries["api_is_read_only"] is True
    assert (
        boundaries[
            "api_does_not_create_delivery_observation"
        ]
        is True
    )
    assert (
        boundaries[
            "api_does_not_recompute_pa005_delivery"
        ]
        is True
    )
    assert (
        boundaries[
            "api_does_not_infer_observation_from_delivery_status"
        ]
        is True
    )
    assert (
        boundaries[
            "api_does_not_record_delivery"
        ]
        is True
    )
    assert (
        boundaries[
            "api_does_not_record_client_response"
        ]
        is True
    )
    assert (
        boundaries[
            "api_does_not_authorize_closeout"
        ]
        is True
    )


def test_router_exposes_get_only(
    tmp_path: Path,
) -> None:
    client, _ = build_client(
        tmp_path
    )

    openapi = client.get(
        "/openapi.json"
    ).json()

    path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "delivery-observation-status"
    )

    assert path in openapi["paths"]

    assert set(
        openapi["paths"][path].keys()
    ) == {
        "get"
    }

    assert not any(
        candidate.endswith(
            "/delivery-recording"
        )
        or candidate.endswith(
            "/deliver"
        )
        or candidate.endswith(
            "/client-acknowledgment"
        )
        or candidate.endswith(
            "/client-response"
        )
        or candidate.endswith(
            "/closeout"
        )
        or candidate.endswith(
            "/intervene"
        )
        for candidate in openapi["paths"]
        if "governance-customer-trials" in candidate
    )