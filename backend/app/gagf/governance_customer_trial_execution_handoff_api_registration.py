from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_api import (
    create_customer_trial_execution_handoff_router,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_bridge import (
    GovernanceCustomerTrialExecutionHandoffBridge,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_service import (
    GovernanceCustomerTrialExecutionHandoffService,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY = (
    "governance_customer_trial_execution_handoff_service"
)

CUSTOMER_TRIAL_EXECUTION_HANDOFF_STORE_STATE_KEY = (
    "governance_customer_trial_execution_handoff_receipt_store"
)

CUSTOMER_TRIAL_EXECUTION_HANDOFF_BINDING_SERVICE_STATE_KEY = (
    "governance_customer_trial_execution_handoff_binding_service"
)


def register_customer_trial_execution_handoff_api(
    *,
    app: FastAPI,
    database_path: str | Path,
    preflight_service:
        GovernanceCustomerTrialPreflightService,
    execution_input_binding_service:
        GovernanceCommercialPaidAssessmentExecutionInputBindingService,
) -> None:
    """
    Register the controlled customer-trial
    execution-handoff API.

    Registration creates infrastructure only.

    It does not:
    - establish trial readiness,
    - establish contract execution,
    - create paid-work authorization,
    - execute an assessment,
    - establish recovery authority,
    - approve delivery,
    - record delivery,
    - establish administrative closeout authority,
    - establish intervention authority.

    The repository's existing paid-assessment
    execution path remains authoritative.
    """

    store = (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            database_path
        )
    )

    bridge = (
        GovernanceCustomerTrialExecutionHandoffBridge(
            preflight_service=preflight_service
        )
    )

    service = (
        GovernanceCustomerTrialExecutionHandoffService(
            bridge=bridge,
            receipt_store=store,
        )
    )

    router = (
        create_customer_trial_execution_handoff_router(
            service=service,
            execution_input_binding_service=(
                execution_input_binding_service
            ),
        )
    )

    for route in router.routes:
        app.router.routes.append(
            route
        )

    app.openapi_schema = None

    setattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_STORE_STATE_KEY,
        store,
    )

    setattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_BINDING_SERVICE_STATE_KEY,
        execution_input_binding_service,
    )
