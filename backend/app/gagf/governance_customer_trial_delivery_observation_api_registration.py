from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_customer_trial_delivery_observation_api import (
    create_customer_trial_delivery_observation_router,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_service import (
    GovernanceCustomerTrialDeliveryObservationStatusService,
)


CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_STATE_KEY = (
    "governance_customer_trial_delivery_observation_service"
)

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_STORE_STATE_KEY = (
    "governance_customer_trial_delivery_observation_receipt_store"
)


def register_customer_trial_delivery_observation_api(
    *,
    app: FastAPI,
    database_path: str | Path,
) -> None:
    """
    Register the read-only controlled-trial delivery-observation API.

    Registration creates observation-read infrastructure only.
    It does not approve, perform, or infer delivery.
    """

    store = (
        GovernanceCustomerTrialDeliveryObservationReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryObservationStatusService(
            receipt_store=store
        )
    )

    router = (
        create_customer_trial_delivery_observation_router(
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
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_STORE_STATE_KEY,
        store,
    )