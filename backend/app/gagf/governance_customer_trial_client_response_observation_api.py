from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    CustomerTrialClientResponseObservationReceiptError,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_service import (
    GovernanceCustomerTrialClientResponseObservationStatusService,
)


CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_API_TAG = (
    "governance-customer-trial-client-response-observation"
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


def create_customer_trial_client_response_observation_router(
    *,
    service:
        GovernanceCustomerTrialClientResponseObservationStatusService,
) -> APIRouter:
    """
    Read-only controlled-trial response-observation surface.
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_API_TAG
        ],
    )

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "client-response-observation-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_client_response_observation_status(
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
                    CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_API_VERSION
                ),
                "authority": "READ_ONLY",
                "result":
                    result.to_dict(),
                "boundaries": {
                    "api_is_read_only":
                        True,
                    "api_does_not_create_client_response_observation":
                        True,
                    "api_does_not_recompute_pa007_response":
                        True,
                    "api_does_not_infer_response_from_receipt":
                        True,
                    "api_does_not_record_client_response":
                        True,
                    "api_does_not_validate_findings":
                        True,
                    "api_does_not_implement_recommendations":
                        True,
                    "api_does_not_authorize_closeout":
                        True,
                    "api_does_not_authorize_intervention":
                        True,
                    "pa007_remains_client_response_authority":
                        True,
                    "pa012_remains_lifecycle_persistence_authority":
                        True,
                },
            }

        except (
            CustomerTrialClientResponseObservationReceiptError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "CLIENT_RESPONSE_OBSERVATION_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router