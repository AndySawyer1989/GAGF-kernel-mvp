from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_api import (
    create_customer_trial_administrative_closeout_observation_router,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_service import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService,
)

from tests.test_governance_customer_trial_administrative_closeout_observation_receipt_store import (
    build_observation,
)


def build_client(
    tmp_path: Path,
):
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=store
        )
    )

    app = FastAPI()

    app.include_router(
        create_customer_trial_administrative_closeout_observation_router(
            service=service
        )
    )

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
        "controlled-trial-completion-status"
    )


def test_get_returns_incomplete_without_receipt(
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

    assert (
        payload["result"]["controlled_trial_complete"]
        is False
    )


def test_get_returns_controlled_trial_complete(
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
        payload["result"]["controlled_trial_complete"]
        is True
    )

    assert (
        payload["result"]["controlled_trial_status"]
        == "controlled_trial_complete"
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
            "api_does_not_recompute_pa010_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_infer_closeout_from_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_authorize_intervention"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_verify_roi"
        ]
        is True
    )


def test_router_is_get_only(
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
        "controlled-trial-completion-status"
    )

    assert path in openapi["paths"]

    assert set(
        openapi["paths"][path].keys()
    ) == {
        "get"
    }

    assert not any(
        candidate.endswith(
            "/closeout"
        )
        or candidate.endswith(
            "/intervene"
        )
        or candidate.endswith(
            "/execute"
        )
        for candidate in openapi["paths"]
        if (
            "governance-customer-trials"
            in candidate
        )
    )