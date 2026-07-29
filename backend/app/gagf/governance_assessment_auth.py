from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Header, HTTPException, Request, status


ASSESSMENT_AUTH_VERSION = "1.0.0"
ASSESSMENT_READER_ROLE = "assessment:read"
ASSESSMENT_EXECUTOR_ROLE = "assessment:execute"
ASSESSMENT_ADMIN_ROLE = "assessment:admin"


@dataclass(frozen=True)
class AssessmentActorContext:
    tenant_id: str
    actor_id: str
    roles: tuple[str, ...]

    def has_any_role(self, *required_roles: str) -> bool:
        return bool(set(self.roles).intersection(required_roles))


def normalize_required_header(
    *,
    value: str | None,
    header_name: str,
) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ASSESSMENT_AUTH_REQUIRED",
                "message": f"{header_name} is required",
            },
        )
    return normalized


def parse_roles(value: str | None) -> tuple[str, ...]:
    normalized = normalize_required_header(
        value=value,
        header_name="X-Actor-Roles",
    )
    roles = tuple(
        sorted(
            {
                role.strip().lower()
                for role in normalized.split(",")
                if role.strip()
            }
        )
    )
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ASSESSMENT_AUTH_REQUIRED",
                "message": "X-Actor-Roles is required",
            },
        )
    return roles


async def read_json_body(request: Request) -> dict[str, Any]:
    if request.method.upper() not in {"POST", "PUT", "PATCH"}:
        return {}

    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type.lower():
        return {}

    try:
        payload = await request.json()
    except Exception:
        return {}

    return payload if isinstance(payload, dict) else {}


async def require_assessment_actor(
    request: Request,
    x_tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID",
    ),
    x_actor_id: str | None = Header(
        default=None,
        alias="X-Actor-ID",
    ),
    x_actor_roles: str | None = Header(
        default=None,
        alias="X-Actor-Roles",
    ),
) -> AssessmentActorContext:
    context = AssessmentActorContext(
        tenant_id=normalize_required_header(
            value=x_tenant_id,
            header_name="X-Tenant-ID",
        ),
        actor_id=normalize_required_header(
            value=x_actor_id,
            header_name="X-Actor-ID",
        ),
        roles=parse_roles(x_actor_roles),
    )

    body = await read_json_body(request)
    candidate_tenants = {
        str(value).strip()
        for value in (
            request.path_params.get("tenant_id"),
            request.query_params.get("tenant_id"),
            body.get("tenant_id"),
        )
        if value is not None and str(value).strip()
    }

    if candidate_tenants and candidate_tenants != {context.tenant_id}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_TENANT_MISMATCH",
                "message": (
                    "authenticated tenant does not match "
                    "the requested assessment tenant"
                ),
                "authenticated_tenant_id": context.tenant_id,
                "requested_tenant_ids": sorted(candidate_tenants),
            },
        )

    required_roles = (
        (ASSESSMENT_EXECUTOR_ROLE, ASSESSMENT_ADMIN_ROLE)
        if request.method.upper() == "POST"
        else (ASSESSMENT_READER_ROLE, ASSESSMENT_ADMIN_ROLE)
    )

    if not context.has_any_role(*required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_ROLE_FORBIDDEN",
                "message": "actor lacks the required assessment role",
                "required_roles": list(required_roles),
                "actor_roles": list(context.roles),
            },
        )

    request.state.assessment_actor = context
    return context
