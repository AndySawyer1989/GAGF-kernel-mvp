from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_customer_trial_delivery_readiness_api import (
    create_customer_trial_delivery_readiness_router,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_service import (
    GovernanceCustomerTrialDeliveryReadinessStatusService,
)


CUSTOMER_TRIAL_DELIVERY_READINESS_SERVICE_STATE_KEY = (
    "governance_customer_trial_delivery_readiness_service"
)

CUSTOMER_TRIAL_DELIVERY_READINESS_STORE_STATE_KEY = (
    "governance_customer_trial_delivery_readiness_receipt_store"
)


def register_customer_trial_delivery_readiness_api(
    *,
    app: FastAPI,
    database_path: str | Path,
) -> None:
    """
    Register the read-only controlled-customer-trial
    delivery-readiness API.

    Registration creates infrastructure only.

    It does not:
    - create delivery readiness,
    - rerun PA-003,
    - infer readiness from execution observation,
    - execute or recover an assessment,
    - approve delivery,
    - record delivery,
    - record client receipt/response,
    - establish administrative closeout authority,
    - establish intervention authority.

    PA-003 remains delivery-readiness authority.
    """

    store = (
        GovernanceCustomerTrialDeliveryReadinessReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialDeliveryReadinessStatusService(
            receipt_store=store
        )
    )

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

    setattr(
        app.state,
        CUSTOMER_TRIAL_DELIVERY_READINESS_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_DELIVERY_READINESS_STORE_STATE_KEY,
        store,
    )