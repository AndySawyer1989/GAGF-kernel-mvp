from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    CustomerTrialDeliveryReadinessReceiptError,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_service import (
    GovernanceCustomerTrialDeliveryReadinessStatusService,
)


CUSTOMER_TRIAL_DELIVERY_READINESS_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_DELIVERY_READINESS_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_DELIVERY_READINESS_API_TAG = (
    "governance-customer-trial-delivery-readiness"
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


def create_customer_trial_delivery_readiness_router(
    *,
    service:
        GovernanceCustomerTrialDeliveryReadinessStatusService,
) -> APIRouter:
    """
    Expose read-only controlled-customer-trial
    delivery-readiness status.

    This API does not:
    - create delivery readiness,
    - rerun PA-003 readiness,
    - infer readiness from execution observation,
    - execute an assessment,
    - recover an execution,
    - approve delivery,
    - create approved_for_human_delivery,
    - record delivery,
    - record client receipt or response,
    - close an assessment,
    - authorize intervention.

    Only a previously persisted governed delivery-readiness
    receipt can produce receipt_found=True.
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_DELIVERY_READINESS_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_DELIVERY_READINESS_API_TAG
        ],
    )

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "delivery-readiness-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_delivery_readiness_status(
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
                    CUSTOMER_TRIAL_DELIVERY_READINESS_API_VERSION
                ),
                "authority": "READ_ONLY",
                "result":
                    result.to_dict(),
                "boundaries": {
                    "api_is_read_only":
                        True,
                    "api_does_not_create_delivery_readiness":
                        True,
                    "api_does_not_recompute_pa003_readiness":
                        True,
                    "api_does_not_infer_readiness_from_execution_observation":
                        True,
                    "api_does_not_execute_assessment":
                        True,
                    "api_does_not_authorize_recovery":
                        True,
                    "api_does_not_approve_delivery":
                        True,
                    "api_does_not_create_approved_for_human_delivery":
                        True,
                    "api_does_not_record_delivery":
                        True,
                    "api_does_not_record_client_receipt":
                        True,
                    "api_does_not_record_client_response":
                        True,
                    "api_does_not_authorize_closeout":
                        True,
                    "api_does_not_authorize_intervention":
                        True,
                    "pa003_remains_delivery_readiness_authority":
                        True,
                },
            }

        except (
            CustomerTrialDeliveryReadinessReceiptError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "DELIVERY_READINESS_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router