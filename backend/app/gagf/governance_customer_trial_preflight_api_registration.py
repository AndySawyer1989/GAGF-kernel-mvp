from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_customer_trial_preflight_api import (
    create_customer_trial_preflight_router,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    GovernanceCustomerTrialPreflightReceiptStore,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


CUSTOMER_TRIAL_PREFLIGHT_SERVICE_STATE_KEY = (
    "governance_customer_trial_preflight_service"
)

CUSTOMER_TRIAL_PREFLIGHT_STORE_STATE_KEY = (
    "governance_customer_trial_preflight_receipt_store"
)


def register_customer_trial_preflight_api(
    *,
    app: FastAPI,
    database_path: str | Path,
) -> None:
    """
    Register controlled customer-trial preflight.

    Registration creates infrastructure only.

    It does not authorize:
    - paid execution
    - delivery
    - client acknowledgment
    - client response
    - administrative closeout
    - intervention
    """

    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialPreflightService(
            receipt_store=store
        )
    )

    router = (
        create_customer_trial_preflight_router(
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
        CUSTOMER_TRIAL_PREFLIGHT_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_PREFLIGHT_STORE_STATE_KEY,
        store,
    )