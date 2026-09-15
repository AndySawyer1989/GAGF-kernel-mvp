from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_customer_trial_execution_observation_api import (
    create_customer_trial_execution_observation_router,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_observation_service import (
    GovernanceCustomerTrialExecutionObservationStatusService,
)


CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_STATE_KEY = (
    "governance_customer_trial_execution_observation_service"
)

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_STORE_STATE_KEY = (
    "governance_customer_trial_execution_observation_receipt_store"
)


def register_customer_trial_execution_observation_api(
    *,
    app: FastAPI,
    database_path: str | Path,
) -> None:
    """
    Register the read-only controlled-customer-trial
    execution-observation API.

    Registration creates infrastructure only.

    It does not:
    - create an execution observation,
    - infer execution from a handoff,
    - execute an assessment,
    - establish recovery authority,
    - approve delivery,
    - record delivery,
    - establish administrative closeout authority,
    - establish intervention authority.

    PA015 remains execution/recovery authority.
    """

    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=store
        )
    )

    router = (
        create_customer_trial_execution_observation_router(
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
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_STORE_STATE_KEY,
        store,
    )