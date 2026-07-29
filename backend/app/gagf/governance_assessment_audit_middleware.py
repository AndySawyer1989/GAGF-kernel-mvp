from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import Request, Response

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
    build_assessment_audit_event,
)


ASSESSMENT_API_PREFIX = "/api/v1/governance-assessments"


def extract_reason_code(
    response: Response,
) -> str | None:
    return getattr(
        response,
        "assessment_reason_code",
        None,
    )


def actor_context_from_request(
    request: Request,
) -> tuple[str | None, str | None, tuple[str, ...]]:
    context = getattr(
        request.state,
        "assessment_actor",
        None,
    )

    if context is not None:
        return (
            context.tenant_id,
            context.actor_id,
            tuple(context.roles),
        )

    tenant_id = request.headers.get("X-Tenant-ID")
    actor_id = request.headers.get("X-Actor-ID")
    roles_header = request.headers.get(
        "X-Actor-Roles",
        "",
    )
    roles = tuple(
        sorted(
            {
                role.strip().lower()
                for role in roles_header.split(",")
                if role.strip()
            }
        )
    )

    return tenant_id, actor_id, roles


def install_assessment_audit_middleware(
    *,
    app: Any,
    ledger: AssessmentAuditLedger,
) -> None:
    if getattr(
        app.state,
        "governance_assessment_audit_middleware_installed",
        False,
    ):
        return

    @app.middleware("http")
    async def assessment_audit_middleware(
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        if not request.url.path.startswith(
            ASSESSMENT_API_PREFIX
        ):
            return await call_next(request)

        request_id = request.headers.get(
            "X-Request-ID"
        ) or str(uuid4())

        try:
            response = await call_next(request)
        except Exception:
            tenant_id, actor_id, roles = (
                actor_context_from_request(request)
            )
            ledger.append(
                build_assessment_audit_event(
                    request_id=request_id,
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    actor_roles=roles,
                    method=request.method,
                    route=request.url.path,
                    outcome="error",
                    status_code=500,
                    reason_code="ASSESSMENT_INTERNAL_ERROR",
                )
            )
            raise

        tenant_id, actor_id, roles = (
            actor_context_from_request(request)
        )

        outcome = (
            "allowed"
            if response.status_code < 400
            else "denied"
        )

        reason_code = extract_reason_code(response)

        if reason_code is None:
            reason_code = {
                401: "ASSESSMENT_AUTH_REQUIRED",
                403: "ASSESSMENT_ACCESS_FORBIDDEN",
                404: "ASSESSMENT_NOT_FOUND",
                422: "ASSESSMENT_VALIDATION_ERROR",
            }.get(response.status_code)

        ledger.append(
            build_assessment_audit_event(
                request_id=request_id,
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_roles=roles,
                method=request.method,
                route=request.url.path,
                outcome=outcome,
                status_code=response.status_code,
                reason_code=reason_code,
            )
        )

        response.headers["X-Request-ID"] = request_id
        return response

    app.state.governance_assessment_audit_ledger = (
        ledger
    )
    app.state.governance_assessment_audit_middleware_installed = (
        True
    )
