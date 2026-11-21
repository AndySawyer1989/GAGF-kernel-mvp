from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import HTTPException, Request, status


ASSESSMENT_AUTH_VERSION = "2.0.0"

ASSESSMENT_READER_ROLE = "assessment:read"
ASSESSMENT_EXECUTOR_ROLE = "assessment:execute"
ASSESSMENT_ADMIN_ROLE = "assessment:admin"

ALLOWED_ASSESSMENT_ROLES = frozenset(
    {
        ASSESSMENT_READER_ROLE,
        ASSESSMENT_EXECUTOR_ROLE,
        ASSESSMENT_ADMIN_ROLE,
    }
)


@dataclass(frozen=True)
class AssessmentActorContext:
    tenant_id: str
    actor_id: str
    roles: tuple[str, ...]

    def has_any_role(self, *required_roles: str) -> bool:
        return bool(set(self.roles).intersection(required_roles))


class AssessmentIdentityVerifier(Protocol):
    async def __call__(
        self,
        request: Request,
    ) -> AssessmentActorContext:
        """
        Authenticate the request using a deployment-approved
        identity mechanism and return verified identity claims.

        Implementations must not treat caller-supplied identity
        headers as trusted claims unless those claims have been
        cryptographically or otherwise authoritatively verified.
        """
        ...


def _authentication_required() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "ASSESSMENT_AUTH_REQUIRED",
            "message": "valid assessment identity credentials are required",
        },
    )


def _identity_verifier_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "ASSESSMENT_IDENTITY_VERIFIER_UNAVAILABLE",
            "message": (
                "assessment identity verification is not configured"
            ),
        },
    )


def _validate_verified_context(
    value: Any,
) -> AssessmentActorContext:
    if not isinstance(value, AssessmentActorContext):
        raise _identity_verifier_unavailable()

    tenant_id = value.tenant_id.strip()
    actor_id = value.actor_id.strip()

    if not tenant_id or not actor_id:
        raise _authentication_required()

    roles = tuple(
        sorted(
            {
                str(role).strip().lower()
                for role in value.roles
                if str(role).strip()
            }
        )
    )

    if not roles:
        raise _authentication_required()

    if not set(roles).issubset(ALLOWED_ASSESSMENT_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ASSESSMENT_ROLE_CLAIM_INVALID",
                "message": (
                    "identity verifier returned an unsupported "
                    "assessment role"
                ),
            },
        )

    return AssessmentActorContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        roles=roles,
    )


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
) -> AssessmentActorContext:
    verifier = getattr(
        request.app.state,
        "assessment_identity_verifier",
        None,
    )

    if verifier is None or not callable(verifier):
        raise _identity_verifier_unavailable()

    try:
        verified_value = await verifier(request)
    except HTTPException:
        raise
    except Exception:
        # Do not expose provider internals or fail open.
        raise _identity_verifier_unavailable() from None

    context = _validate_verified_context(verified_value)

    # Attach verified identity before authorization checks.
    # This allows audit middleware to attribute denied requests
    # to the authenticated actor without trusting request headers.
    request.state.assessment_actor = context

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

    return context
