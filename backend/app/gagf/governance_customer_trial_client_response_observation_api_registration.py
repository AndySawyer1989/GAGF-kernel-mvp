from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_customer_trial_client_response_observation_api import (
    create_customer_trial_client_response_observation_router,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_service import (
    GovernanceCustomerTrialClientResponseObservationStatusService,
)


CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SERVICE_STATE_KEY = (
    "governance_customer_trial_client_response_observation_service"
)

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_STORE_STATE_KEY = (
    "governance_customer_trial_client_response_observation_receipt_store"
)


def register_customer_trial_client_response_observation_api(
    *,
    app: FastAPI,
    database_path: str | Path,
) -> None:
    store = (
        GovernanceCustomerTrialClientResponseObservationReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialClientResponseObservationStatusService(
            receipt_store=store
        )
    )

    router = (
        create_customer_trial_client_response_observation_router(
            service=service
        )
    )

    for route in router.routes:
        app.router.routes.append(
            route
        )

    app.openapi_schema = None

    setattr(
        app.state,
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_STORE_STATE_KEY,
        store,
    )