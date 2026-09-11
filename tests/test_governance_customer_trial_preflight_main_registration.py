from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.gagf.governance_customer_trial_preflight_api import (
    CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX,
)
from backend.app.gagf.governance_customer_trial_preflight_api_registration import (
    CUSTOMER_TRIAL_PREFLIGHT_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_PREFLIGHT_STORE_STATE_KEY,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    GovernanceCustomerTrialPreflightReceiptStore,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


def test_main_registers_customer_trial_preflight_api():
    paths = {
        route.path
        for route in app.routes
    }

    assert (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/preflight"
        in paths
    )

    assert (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/{tenant_id}/{client_id}/"
        "{engagement_id}/{assessment_id}/"
        "preflight-status"
        in paths
    )


def test_main_exposes_preflight_service_state():
    service = getattr(
        app.state,
        CUSTOMER_TRIAL_PREFLIGHT_SERVICE_STATE_KEY,
    )

    store = getattr(
        app.state,
        CUSTOMER_TRIAL_PREFLIGHT_STORE_STATE_KEY,
    )

    assert isinstance(
        service,
        GovernanceCustomerTrialPreflightService,
    )

    assert isinstance(
        store,
        GovernanceCustomerTrialPreflightReceiptStore,
    )


def test_main_preflight_status_route_is_callable():
    client = TestClient(
        app
    )

    response = client.get(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/04i05c-test-tenant/"
            "04i05c-test-client/"
            "04i05c-test-engagement/"
            "04i05c-test-assessment/"
            "preflight-status"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["authority"]
        == "READ_ONLY"
    )

    assert (
        payload["result"][
            "receipt_found"
        ]
        is False
    )


def test_main_does_not_expose_customer_trial_execution():
    client = TestClient(
        app
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/execute"
        ),
        json={},
    )

    assert response.status_code == 404