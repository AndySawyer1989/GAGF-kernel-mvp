from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    CustomerTrialDeliveryObservationReceiptError,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_service import (
    GovernanceCustomerTrialDeliveryObservationStatusService,
)


CUSTOMER_TRIAL_DELIVERY_OBSERVATION_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_API_TAG = (
    "governance-customer-trial-delivery-observation"
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


def create_customer_trial_delivery_observation_router(
    *,
    service:
        GovernanceCustomerTrialDeliveryObservationStatusService,
) -> APIRouter:
    """
    Expose read-only controlled-customer-trial delivery observation.

    This API does not:
    - create delivery observation,
    - rerun PA-005 delivery,
    - infer observation from delivery-status,
    - approve delivery,
    - create approved_for_human_delivery,
    - record delivery,
    - acknowledge client receipt,
    - record client response,
    - close an assessment,
    - authorize intervention.
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_DELIVERY_OBSERVATION_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_DELIVERY_OBSERVATION_API_TAG
        ],
    )

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "delivery-observation-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_delivery_observation_status(
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
                    CUSTOMER_TRIAL_DELIVERY_OBSERVATION_API_VERSION
                ),
                "authority": "READ_ONLY",
                "result":
                    result.to_dict(),
                "boundaries": {
                    "api_is_read_only":
                        True,
                    "api_does_not_create_delivery_observation":
                        True,
                    "api_does_not_recompute_pa005_delivery":
                        True,
                    "api_does_not_infer_observation_from_delivery_status":
                        True,
                    "api_does_not_approve_delivery":
                        True,
                    "api_does_not_create_approved_for_human_delivery":
                        True,
                    "api_does_not_record_delivery":
                        True,
                    "api_does_not_record_client_receipt":
                        True,
                    "api_does_not_record_client_acknowledgment":
                        True,
                    "api_does_not_record_client_response":
                        True,
                    "api_does_not_authorize_closeout":
                        True,
                    "api_does_not_authorize_intervention":
                        True,
                    "pa005_remains_delivery_event_authority":
                        True,
                    "pa012_remains_lifecycle_persistence_authority":
                        True,
                },
            }

        except (
            CustomerTrialDeliveryObservationReceiptError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "DELIVERY_OBSERVATION_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router