from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
    create_assessment_audit_checkpoint,
)
from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    AssessmentActorContext,
    require_assessment_actor,
)


ASSESSMENT_AUDIT_API_VERSION = "1.2.0"


def require_assessment_audit_admin(
    request: Request,
    context: AssessmentActorContext = Depends(
        require_assessment_actor
    ),
) -> AssessmentActorContext:
    if ASSESSMENT_ADMIN_ROLE not in context.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_AUDIT_ROLE_FORBIDDEN",
                "message": (
                    "assessment:admin is required to access "
                    "assessment audit evidence"
                ),
                "required_roles": [ASSESSMENT_ADMIN_ROLE],
                "actor_roles": list(context.roles),
            },
        )

    request.state.assessment_actor = context
    return context


def enforce_audit_tenant_match(
    *,
    requested_tenant_id: str,
    context: AssessmentActorContext,
) -> None:
    if requested_tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_TENANT_MISMATCH",
                "message": (
                    "authenticated tenant does not match "
                    "the requested audit tenant"
                ),
                "authenticated_tenant_id": context.tenant_id,
                "requested_tenant_id": requested_tenant_id,
            },
        )


def create_governance_assessment_audit_router(
    *,
    ledger: AssessmentAuditLedger,
    checkpoint_store: AssessmentAuditCheckpointStore | None = None,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/governance-assessments",
        tags=["governance-assessment-audit"],
    )

    @router.get("/audit-events")
    def list_audit_events(
        tenant_id: str,
        limit: int = Query(default=100, ge=1, le=500),
        context: AssessmentActorContext = Depends(
            require_assessment_audit_admin
        ),
    ) -> dict[str, Any]:
        enforce_audit_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        events = ledger.list_events(
            tenant_id=context.tenant_id,
            limit=limit,
        )

        return {
            "tenant_id": context.tenant_id,
            "items": [event.to_dict() for event in events],
            "count": len(events),
            "limit": limit,
        }

    @router.get("/audit-integrity")
    def verify_audit_integrity(
        tenant_id: str,
        context: AssessmentActorContext = Depends(
            require_assessment_audit_admin
        ),
    ) -> dict[str, Any]:
        enforce_audit_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        verification = ledger.verify_tenant_chain(
            tenant_id=context.tenant_id
        )

        return {
            "tenant_id": context.tenant_id,
            "valid": verification.valid,
            "checked_count": verification.checked_count,
            "failure_index": verification.failure_index,
            "failure_event_id": verification.failure_event_id,
            "reason_code": verification.reason_code,
        }

    @router.post(
        "/audit-checkpoints",
        status_code=status.HTTP_201_CREATED,
    )
    def create_audit_checkpoint(
        tenant_id: str,
        context: AssessmentActorContext = Depends(
            require_assessment_audit_admin
        ),
    ) -> dict[str, Any]:
        enforce_audit_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        if checkpoint_store is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ASSESSMENT_CHECKPOINT_STORE_UNAVAILABLE",
                    "message": (
                        "assessment audit checkpoint storage "
                        "is unavailable"
                    ),
                },
            )

        checkpoint = create_assessment_audit_checkpoint(
            tenant_id=context.tenant_id,
            ledger=ledger,
        )
        checkpoint_store.append(checkpoint)

        return checkpoint.to_dict()

    @router.get("/audit-checkpoints")
    def list_audit_checkpoints(
        tenant_id: str,
        limit: int = Query(default=100, ge=1, le=500),
        context: AssessmentActorContext = Depends(
            require_assessment_audit_admin
        ),
    ) -> dict[str, Any]:
        enforce_audit_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        if checkpoint_store is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ASSESSMENT_CHECKPOINT_STORE_UNAVAILABLE",
                    "message": (
                        "assessment audit checkpoint storage "
                        "is unavailable"
                    ),
                },
            )

        checkpoints = checkpoint_store.list_checkpoints(
            tenant_id=context.tenant_id,
            limit=limit,
        )

        return {
            "tenant_id": context.tenant_id,
            "items": [
                checkpoint.to_dict()
                for checkpoint in checkpoints
            ],
            "count": len(checkpoints),
            "limit": limit,
        }

    return router
