from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_delivery_readiness_api import (
    create_customer_trial_delivery_readiness_router,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_service import (
    GovernanceCustomerTrialDeliveryReadinessStatusService,
)

from tests.test_governance_customer_trial_delivery_readiness_receipt_store import (
    build_readiness,
)


def build_client(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            tmp_path / "delivery-readiness.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=store
        )
    )

    app = FastAPI()

    router = (
        create_customer_trial_delivery_readiness_router(
            service=service
        )
    )

    for route in router.routes:
        app.router.routes.append(
            route
        )

    app.openapi_schema = None

    return (
        TestClient(app),
        store,
    )


def delivery_readiness_status_url(
) -> str:
    return (
        "/api/v1/governance-customer-trials/"
        "tenant-controlled/"
        "client-controlled/"
        "engagement-controlled/"
        "assessment-controlled/"
        "delivery-readiness-status"
    )


def test_get_delivery_readiness_status_returns_not_found(
    tmp_path,
):
    client, _ = build_client(
        tmp_path
    )

    response = client.get(
        delivery_readiness_status_url()
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "status"
        ]
        == "ok"
    )

    assert (
        payload[
            "authority"
        ]
        == "READ_ONLY"
    )

    assert (
        payload[
            "result"
        ][
            "receipt_found"
        ]
        is False
    )

    assert (
        payload[
            "result"
        ][
            "receipt"
        ]
        is None
    )


def test_get_delivery_readiness_status_returns_durable_receipt(
    tmp_path,
):
    client, store = build_client(
        tmp_path
    )

    receipt = store.put(
        readiness=build_readiness()
    )

    response = client.get(
        delivery_readiness_status_url()
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "result"
        ][
            "receipt_found"
        ]
        is True
    )

    assert (
        payload[
            "result"
        ][
            "receipt"
        ][
            "receipt_hash"
        ]
        == receipt.receipt_hash
    )


def test_delivery_readiness_status_api_is_read_only(
    tmp_path,
):
    client, _ = build_client(
        tmp_path
    )

    payload = client.get(
        delivery_readiness_status_url()
    ).json()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "api_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_create_delivery_readiness"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_recompute_pa003_readiness"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_infer_readiness_from_execution_observation"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_approve_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_create_approved_for_human_delivery"
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
            "api_does_not_authorize_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "api_does_not_authorize_intervention"
        ]
        is True
    )


def test_delivery_readiness_router_has_no_mutating_routes(
    tmp_path,
):
    client, _ = build_client(
        tmp_path
    )

    openapi = client.get(
        "/openapi.json"
    ).json()

    paths = openapi[
        "paths"
    ]

    readiness_path = (
        "/api/v1/governance-customer-trials/"
        "{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "delivery-readiness-status"
    )

    assert readiness_path in paths

    assert set(
        paths[
            readiness_path
        ].keys()
    ) == {
        "get"
    }

    assert not any(
        path.endswith(
            "/execute"
        )
        or path.endswith(
            "/recover"
        )
        or path.endswith(
            "/delivery-approval"
        )
        or path.endswith(
            "/deliver"
        )
        or path.endswith(
            "/closeout"
        )
        or path.endswith(
            "/intervene"
        )
        for path in paths
        if "governance-customer-trials" in path
    )