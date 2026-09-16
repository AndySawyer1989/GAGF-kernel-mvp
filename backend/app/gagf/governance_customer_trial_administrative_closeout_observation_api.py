from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    CustomerTrialAdministrativeCloseoutObservationReceiptError,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_service import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService,
)


CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_API_TAG = (
    "governance-customer-trial-administrative-closeout-observation"
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


def create_customer_trial_administrative_closeout_observation_router(
    *,
    service:
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService,
) -> APIRouter:
    """
    Read-only controlled-trial completion surface.
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_API_TAG
        ],
    )

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "controlled-trial-completion-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_controlled_trial_completion_status(
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
                    CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_API_VERSION
                ),

                "authority":
                    "READ_ONLY",

                "result":
                    result.to_dict(),

                "boundaries": {
                    "api_is_read_only":
                        True,

                    "api_does_not_create_closeout":
                        True,

                    "api_does_not_recompute_pa010_closeout":
                        True,

                    "api_does_not_infer_closeout_from_client_response":
                        True,

                    "controlled_trial_complete_is_administrative_only":
                        True,

                    "api_does_not_validate_findings":
                        True,

                    "api_does_not_implement_recommendations":
                        True,

                    "api_does_not_request_intervention":
                        True,

                    "api_does_not_authorize_intervention":
                        True,

                    "api_does_not_authorize_execution":
                        True,

                    "api_does_not_verify_causation":
                        True,

                    "api_does_not_verify_roi":
                        True,

                    "api_does_not_verify_remediation_success":
                        True,

                    "api_does_not_verify_customer_outcome":
                        True,

                    "pa010_remains_administrative_closeout_authority":
                        True,

                    "pa012_remains_lifecycle_persistence_authority":
                        True,

                    "pa013_remains_operator_coordination_authority":
                        True,
                },
            }

        except (
            CustomerTrialAdministrativeCloseoutObservationReceiptError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "ADMINISTRATIVE_CLOSEOUT_OBSERVATION_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router