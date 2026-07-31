from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    AssessmentActorContext,
    require_assessment_actor,
)
from backend.app.gagf.governance_assessment_checkpoint_durable_key_service import (
    AssessmentCheckpointDurableKeyService,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)


ASSESSMENT_CHECKPOINT_KEY_ADMIN_API_VERSION = "1.0.0"


def require_checkpoint_key_admin(
    request: Request,
    context: AssessmentActorContext = Depends(
        require_assessment_actor
    ),
) -> AssessmentActorContext:
    if ASSESSMENT_ADMIN_ROLE not in context.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_CHECKPOINT_KEY_ROLE_FORBIDDEN",
                "message": (
                    "assessment:admin is required to manage "
                    "checkpoint signing keys"
                ),
                "required_roles": [ASSESSMENT_ADMIN_ROLE],
                "actor_roles": list(context.roles),
            },
        )

    request.state.assessment_actor = context
    return context


def enforce_checkpoint_key_tenant_match(
    *,
    requested_tenant_id: str,
    context: AssessmentActorContext,
) -> None:
    if requested_tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_CHECKPOINT_KEY_TENANT_MISMATCH",
                "message": (
                    "authenticated tenant does not match "
                    "the requested signing-key tenant"
                ),
                "authenticated_tenant_id": context.tenant_id,
                "requested_tenant_id": requested_tenant_id,
            },
        )


def create_assessment_checkpoint_key_admin_router(
    *,
    metadata_store: AssessmentCheckpointSigningKeyMetadataStore,
    key_service: AssessmentCheckpointDurableKeyService,
) -> APIRouter:
    router = APIRouter(
        prefix=(
            "/api/v1/governance-assessments"
            "/checkpoint-signing-keys"
        ),
        tags=["governance-assessment-checkpoint-keys"],
    )

    @router.get("")
    def list_checkpoint_signing_keys(
        tenant_id: str,
        context: AssessmentActorContext = Depends(
            require_checkpoint_key_admin
        ),
    ) -> dict[str, Any]:
        enforce_checkpoint_key_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        keys = metadata_store.list_keys(
            tenant_id=context.tenant_id
        )

        return {
            "tenant_id": context.tenant_id,
            "items": [item.to_dict() for item in keys],
            "count": len(keys),
        }

    @router.get("/active")
    def get_active_checkpoint_signing_key(
        tenant_id: str,
        context: AssessmentActorContext = Depends(
            require_checkpoint_key_admin
        ),
    ) -> dict[str, Any]:
        enforce_checkpoint_key_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        try:
            active = metadata_store.get_active_key(
                tenant_id=context.tenant_id
            )
        except KeyError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": (
                        "ASSESSMENT_CHECKPOINT_ACTIVE_KEY_NOT_FOUND"
                    ),
                    "message": (
                        "no active checkpoint signing key was found"
                    ),
                    "tenant_id": context.tenant_id,
                },
            ) from error

        return active.to_dict()

    @router.post(
        "/{key_id}/activate",
        status_code=status.HTTP_200_OK,
    )
    def activate_checkpoint_signing_key(
        key_id: str,
        tenant_id: str,
        context: AssessmentActorContext = Depends(
            require_checkpoint_key_admin
        ),
    ) -> dict[str, Any]:
        enforce_checkpoint_key_tenant_match(
            requested_tenant_id=tenant_id,
            context=context,
        )

        try:
            activated = key_service.activate_key(
                tenant_id=context.tenant_id,
                key_id=key_id,
            )
        except KeyError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": (
                        "ASSESSMENT_CHECKPOINT_SIGNING_KEY_NOT_FOUND"
                    ),
                    "message": (
                        "checkpoint signing key or secret "
                        "could not be resolved"
                    ),
                    "tenant_id": context.tenant_id,
                    "key_id": key_id,
                },
            ) from error

        return {
            "tenant_id": context.tenant_id,
            "key_id": activated.key_id,
            "active": activated.active,
            "retired_at": activated.retired_at,
        }

    return router
