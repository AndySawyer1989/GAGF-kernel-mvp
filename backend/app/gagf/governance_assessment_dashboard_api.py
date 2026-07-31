from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.gagf.governance_assessment_auth import (
    AssessmentActorContext,
    require_assessment_actor,
)
from backend.app.gagf.governance_assessment_dashboard import (
    GovernanceAssessmentDashboardService,
)


GOVERNANCE_ASSESSMENT_DASHBOARD_API_VERSION = "1.0.0"


def enforce_dashboard_tenant_match(
    *,
    requested_tenant_id: str,
    context: AssessmentActorContext,
) -> None:
    if requested_tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_DASHBOARD_TENANT_MISMATCH",
                "message": (
                    "authenticated tenant does not match "
                    "the requested dashboard tenant"
                ),
                "authenticated_tenant_id": context.tenant_id,
                "requested_tenant_id": requested_tenant_id,
            },
        )


def create_governance_assessment_dashboard_router(
    *,
    dashboard_service: GovernanceAssessmentDashboardService,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/governance-assessments",
        tags=["governance-assessment-dashboard"],
    )

    @router.get("/dashboard-summary")
    def get_dashboard_summary(
        tenant_id: str,
        context: AssessmentActorContext = Depends(
            require_assessment_actor
        ),
    ) -> dict[str, Any]:
        enforce_dashboard_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        summary = dashboard_service.build_summary(
            tenant_id=context.tenant_id
        )

        return summary.to_dict()

    return router
