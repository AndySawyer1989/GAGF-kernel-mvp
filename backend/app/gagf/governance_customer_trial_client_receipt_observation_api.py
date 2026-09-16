from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    CustomerTrialClientReceiptObservationReceiptError,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_service import (
    GovernanceCustomerTrialClientReceiptObservationStatusService,
)


CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_API_TAG = (
    "governance-customer-trial-client-receipt-observation"
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


def create_customer_trial_client_receipt_observation_router(
    *,
    service:
        GovernanceCustomerTrialClientReceiptObservationStatusService,
) -> APIRouter:
    """
    Expose read-only controlled-trial client-receipt observation.

    This API does not:
    - create a client receipt,
    - rerun PA-006,
    - infer receipt from delivery,
    - record a client response,
    - accept findings or recommendations,
    - close the assessment,
    - authorize intervention.
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_API_TAG
        ],
    )

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "client-receipt-observation-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_client_receipt_observation_status(
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
                    CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_API_VERSION
                ),
                "authority": "READ_ONLY",
                "result":
                    result.to_dict(),
                "boundaries": {
                    "api_is_read_only":
                        True,
                    "api_does_not_create_client_receipt_observation":
                        True,
                    "api_does_not_recompute_pa006_receipt":
                        True,
                    "api_does_not_infer_receipt_from_delivery":
                        True,
                    "api_does_not_record_client_acknowledgment":
                        True,
                    "api_does_not_record_client_response":
                        True,
                    "api_does_not_accept_findings":
                        True,
                    "api_does_not_accept_recommendations":
                        True,
                    "api_does_not_authorize_closeout":
                        True,
                    "api_does_not_authorize_intervention":
                        True,
                    "pa006_remains_client_receipt_authority":
                        True,
                    "pa012_remains_lifecycle_persistence_authority":
                        True,
                },
            }

        except (
            CustomerTrialClientReceiptObservationReceiptError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "CLIENT_RECEIPT_OBSERVATION_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router