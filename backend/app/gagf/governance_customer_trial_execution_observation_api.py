from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    CustomerTrialExecutionObservationReceiptError,
)
from backend.app.gagf.governance_customer_trial_execution_observation_service import (
    GovernanceCustomerTrialExecutionObservationStatusService,
)


CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_TAG = (
    "governance-customer-trial-execution-observation"
)


def _error_detail(
    *,
    code: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
    }


def create_customer_trial_execution_observation_router(
    *,
    service:
        GovernanceCustomerTrialExecutionObservationStatusService,
) -> APIRouter:
    """
    Expose read-only controlled-customer-trial
    execution-observation status.

    This API does not:
    - execute an assessment,
    - create an execution observation,
    - infer execution from a handoff,
    - recover an execution,
    - authorize delivery,
    - record delivery,
    - close an assessment,
    - authorize intervention.

    Only a previously persisted governed observation
    receipt can produce observation_found=True.
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_TAG
        ],
    )

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "execution-observation-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_execution_observation_status(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        try:
            result = service.status(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )

            return {
                "status": "ok",
                "api_version": (
                    CUSTOMER_TRIAL_EXECUTION_OBSERVATION_API_VERSION
                ),
                "authority": "READ_ONLY",
                "result":
                    result.to_dict(),
                "boundaries": {
                    "api_is_read_only":
                        True,
                    "api_does_not_execute_assessment":
                        True,
                    "api_does_not_create_execution_observation":
                        True,
                    "api_does_not_infer_execution_from_handoff":
                        True,
                    "api_does_not_authorize_recovery":
                        True,
                    "api_does_not_authorize_delivery":
                        True,
                    "api_does_not_authorize_closeout":
                        True,
                    "api_does_not_authorize_intervention":
                        True,
                },
            }

        except (
            CustomerTrialExecutionObservationReceiptError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "EXECUTION_OBSERVATION_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router