from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    AssessmentActorContext,
    require_assessment_actor,
)
from backend.app.gagf.governance_paid_work_prerequisite_producer_service import (
    GovernancePaidWorkPrerequisiteProducerError,
    GovernancePaidWorkPrerequisiteProducerService,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    GovernancePaidWorkPrerequisiteRecordError,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStoreError,
)


PAID_WORK_PREREQUISITE_PRODUCER_API_VERSION = "0.2.0"
PAID_WORK_PREREQUISITE_PRODUCER_API_PREFIX = (
    "/api/v1/governance-paid-work-prerequisites"
)


class PaidWorkPrerequisiteProductionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    engagement_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)

    evidence: dict[str, Any] = Field(default_factory=dict)


FORBIDDEN_BROWSER_TERMINAL_FIELDS = frozenset(
    {
        "authorization_id",
        "prepared_at",
        "authorization_package_ready",
        "human_operator_authorized_package",
        "paid_assessment_authorized",
        "package_status",
        "contract_execution_event_id",
        "recorded_at",
        "contract_execution_confirmed",
        "contract_executed",
        "event_status",
        "payment_confirmation_event_id",
        "payment_confirmed",
        "human_operator_confirmed_payment",
    }
)


def _find_forbidden_browser_claim(
    value: Any,
    *,
    path: str = "evidence",
) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_BROWSER_TERMINAL_FIELDS:
                return child_path
            found = _find_forbidden_browser_claim(
                child,
                path=child_path,
            )
            if found is not None:
                return found
        return None

    if isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_forbidden_browser_claim(
                child,
                path=f"{path}[{index}]",
            )
            if found is not None:
                return found

    return None


def create_governance_paid_work_prerequisite_producer_router(
    *,
    producer_service: GovernancePaidWorkPrerequisiteProducerService,
) -> APIRouter:
    if not isinstance(
        producer_service,
        GovernancePaidWorkPrerequisiteProducerService,
    ):
        raise TypeError(
            "producer_service must be a "
            "GovernancePaidWorkPrerequisiteProducerService"
        )

    router = APIRouter(
        prefix=PAID_WORK_PREREQUISITE_PRODUCER_API_PREFIX,
        tags=["governance-paid-work-prerequisites"],
    )

    def require_admin(
        actor: AssessmentActorContext,
    ) -> None:
        if not actor.has_any_role(
            ASSESSMENT_ADMIN_ROLE
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ASSESSMENT_ADMIN_REQUIRED",
                    "message": (
                        "assessment:admin role is required"
                    ),
                },
            )

    def produce(
        *,
        kind: str,
        request: PaidWorkPrerequisiteProductionRequest,
        actor: AssessmentActorContext,
    ) -> dict[str, Any]:
        require_admin(actor)

        if actor.tenant_id != request.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ASSESSMENT_TENANT_MISMATCH",
                    "message": (
                        "actor tenant does not match request tenant"
                    ),
                },
            )

        forbidden_claim = _find_forbidden_browser_claim(
            request.evidence
        )
        if forbidden_claim is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PREREQUISITE_TERMINAL_CLAIM_FORBIDDEN",
                    "message": (
                        "browser evidence may not assert terminal prerequisite state"
                    ),
                    "field": forbidden_claim,
                },
            )

        hierarchy = {
            "tenant_id": request.tenant_id,
            "client_id": request.client_id,
            "engagement_id": request.engagement_id,
            "assessment_id": request.assessment_id,
        }

        try:
            if kind == "authorization_package":
                result = (
                    producer_service.produce_authorization_package(
                        source=request.evidence,
                        actor=actor,
                        **hierarchy,
                    )
                )
            elif kind == "contract_execution_event":
                result = (
                    producer_service.produce_contract_execution_event(
                        source=request.evidence,
                        actor=actor,
                        **hierarchy,
                    )
                )
            elif kind == "payment_confirmation_event":
                result = (
                    producer_service.produce_payment_confirmation_event(
                        source=request.evidence,
                        actor=actor,
                        **hierarchy,
                    )
                )
            else:
                raise RuntimeError(
                    "unsupported prerequisite producer kind"
                )

        except (
            GovernancePaidWorkPrerequisiteProducerError,
            GovernancePaidWorkPrerequisiteRecordError,
            GovernancePaidWorkPrerequisiteRecordStoreError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": (
                        "PA001_PREREQUISITE_PRODUCTION_BLOCKED"
                    ),
                    "message": str(exc),
                },
            ) from exc

        return {
            "status": "ok",
            "api_version": (
                PAID_WORK_PREREQUISITE_PRODUCER_API_VERSION
            ),
            "prerequisite": result.to_dict(),
            "boundaries": {
                "admin_action_required": True,
                "server_owns_prerequisite_identity": True,
                "server_owns_prerequisite_timestamp": True,
                "browser_evidence_cannot_assert_terminal_state": True,
                "producer_actor_context_is_bound": True,
                "server_creates_evidence_instance_identity": True,
                "producer_does_not_issue_pa001": True,
                "producer_does_not_authorize_execution": True,
                "producer_does_not_approve_delivery": True,
                "producer_does_not_grant_intervention_authority": True,
            },
        }

    @router.post(
        "/authorization-package",
        status_code=status.HTTP_201_CREATED,
    )
    def produce_authorization_package(
        request: PaidWorkPrerequisiteProductionRequest,
        actor: AssessmentActorContext = Depends(
            require_assessment_actor
        ),
    ) -> dict[str, Any]:
        return produce(
            kind="authorization_package",
            request=request,
            actor=actor,
        )

    @router.post(
        "/contract-execution-event",
        status_code=status.HTTP_201_CREATED,
    )
    def produce_contract_execution_event(
        request: PaidWorkPrerequisiteProductionRequest,
        actor: AssessmentActorContext = Depends(
            require_assessment_actor
        ),
    ) -> dict[str, Any]:
        return produce(
            kind="contract_execution_event",
            request=request,
            actor=actor,
        )

    @router.post(
        "/payment-confirmation-event",
        status_code=status.HTTP_201_CREATED,
    )
    def produce_payment_confirmation_event(
        request: PaidWorkPrerequisiteProductionRequest,
        actor: AssessmentActorContext = Depends(
            require_assessment_actor
        ),
    ) -> dict[str, Any]:
        return produce(
            kind="payment_confirmation_event",
            request=request,
            actor=actor,
        )

    return router
