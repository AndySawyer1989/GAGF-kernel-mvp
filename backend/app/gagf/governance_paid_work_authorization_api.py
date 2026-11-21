from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    AssessmentActorContext,
    require_assessment_actor,
)
from backend.app.gagf.governance_paid_work_authorization_issuance_service import (
    GovernancePaidWorkAuthorizationIssuanceError,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GovernancePaidWorkAuthorizationRecordStoreError,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStoreError,
)
from backend.app.gagf.governance_paid_work_prerequisite_resolver import (
    GovernancePaidWorkPrerequisiteResolver,
)


PAID_WORK_AUTHORIZATION_API_VERSION = "0.2.0"
PAID_WORK_AUTHORIZATION_API_PREFIX = (
    "/api/v1/governance-paid-work-authorizations"
)


class PaidWorkAuthorizationIssuanceApiRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    authorization_package_id: str
    contract_execution_event_id: str
    payment_confirmation_event_id: str


def create_governance_paid_work_authorization_router(
    *,
    prerequisite_resolver: GovernancePaidWorkPrerequisiteResolver,
) -> APIRouter:
    router = APIRouter(
        prefix=PAID_WORK_AUTHORIZATION_API_PREFIX,
        tags=["governance-paid-work-authorizations"],
    )

    @router.post(
        "/issue",
        status_code=status.HTTP_201_CREATED,
    )
    def issue_paid_work_authorization(
        request: PaidWorkAuthorizationIssuanceApiRequest,
        actor: AssessmentActorContext = Depends(
            require_assessment_actor
        ),
    ) -> dict[str, Any]:
        if not actor.has_any_role(
            ASSESSMENT_ADMIN_ROLE
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PA001_ISSUANCE_ROLE_FORBIDDEN",
                    "message": (
                        "PA-001 issuance requires assessment:admin"
                    ),
                    "required_role": ASSESSMENT_ADMIN_ROLE,
                    "actor_roles": list(actor.roles),
                },
            )

        try:
            result = prerequisite_resolver.issue_from_ids(
                tenant_id=request.tenant_id,
                client_id=request.client_id,
                engagement_id=request.engagement_id,
                assessment_id=request.assessment_id,
                authorization_package_id=(
                    request.authorization_package_id
                ),
                contract_execution_event_id=(
                    request.contract_execution_event_id
                ),
                payment_confirmation_event_id=(
                    request.payment_confirmation_event_id
                ),
                actor=actor,
            )
        except GovernancePaidWorkPrerequisiteRecordStoreError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PA001_PREREQUISITE_RESOLUTION_BLOCKED",
                    "message": str(exc),
                },
            ) from exc
        except GovernancePaidWorkAuthorizationIssuanceError as exc:
            message = str(exc)

            if "actor tenant" in message:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "PA001_ISSUANCE_TENANT_FORBIDDEN",
                        "message": message,
                    },
                ) from exc

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PA001_ISSUANCE_BLOCKED",
                    "message": message,
                },
            ) from exc
        except GovernancePaidWorkAuthorizationRecordStoreError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PA001_STORE_CONFLICT",
                    "message": str(exc),
                },
            ) from exc

        authorization = result.issuance.authorization

        return {
            "status": "issued",
            "api_version": PAID_WORK_AUTHORIZATION_API_VERSION,
            "authorization_id": authorization.authorization_id,
            "hierarchy_key": "/".join(
                (
                    authorization.tenant_id,
                    authorization.client_id,
                    authorization.engagement_id,
                    authorization.assessment_id,
                )
            ),
            "paid_assessment_authorized": True,
            "prerequisite_resolution": (
                result.resolution.to_dict()
            ),
            "issuance": result.issuance.to_dict(),
            "boundaries": {
                "browser_supplies_prerequisite_ids_only": True,
                "browser_does_not_supply_prerequisite_artifacts": True,
                "prerequisites_resolved_server_side": True,
                "browser_does_not_supply_authorized_by": True,
                "browser_does_not_supply_authorized_at": True,
                "browser_does_not_supply_authorization_id": True,
                "browser_does_not_self_authorize": True,
                "admin_issuance_required": True,
                "pa001_is_not_execution": True,
                "pa001_is_not_delivery": True,
                "pa001_is_not_production_onboarding": True,
                "pa001_is_not_intervention_authority": True,
            },
        }

    return router


ROUTER_FACTORY = create_governance_paid_work_authorization_router
