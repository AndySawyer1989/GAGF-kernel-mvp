from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_customer_trial_client_receipt_observation_api import (
    create_customer_trial_client_receipt_observation_router,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_service import (
    GovernanceCustomerTrialClientReceiptObservationStatusService,
)


CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SERVICE_STATE_KEY = (
    "governance_customer_trial_client_receipt_observation_service"
)

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_STORE_STATE_KEY = (
    "governance_customer_trial_client_receipt_observation_receipt_store"
)


def register_customer_trial_client_receipt_observation_api(
    *,
    app: FastAPI,
    database_path: str | Path,
) -> None:
    """
    Register read-only controlled-trial client-receipt observation.

    Registration creates no PA-006 or lifecycle authority.
    """

    store = (
        GovernanceCustomerTrialClientReceiptObservationReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialClientReceiptObservationStatusService(
            receipt_store=store
        )
    )

    router = (
        create_customer_trial_client_receipt_observation_router(
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
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_STORE_STATE_KEY,
        store,
    )