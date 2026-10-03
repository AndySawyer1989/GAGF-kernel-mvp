from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from fastapi import HTTPException
from starlette.requests import Request

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    ASSESSMENT_AUTH_VERSION,
    ASSESSMENT_EXECUTOR_ROLE,
    ASSESSMENT_READER_ROLE,
    AssessmentActorContext,
    require_assessment_actor,
)


GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE = (
    "governance-release-identity-tenant-boundary-preflight"
)

GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION = (
    "0.1.0"
)

SUPPORTED_RELEASE_ENVIRONMENTS = frozenset(
    {
        "prelive",
        "paid_trial",
    }
)

REQUIRED_IDENTITY_HEADERS = (
    "X-Tenant-ID",
    "X-Actor-ID",
    "X-Actor-Roles",
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseIdentityTenantBoundaryPreflightResult:
    release_environment: str
    assessment_auth_version: str

    tenant_identity_required: bool
    actor_identity_required: bool
    actor_roles_required: bool

    missing_identity_fails_closed: bool
    deterministic_role_parsing: bool
    tenant_scope_binding_enforced: bool
    insufficient_role_fails_closed: bool
    valid_identity_accepted: bool

    passed: bool
    failure_reasons: tuple[str, ...]

    preflight_type: str = (
        GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION
    )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "preflight_type":
                self.preflight_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "assessment_auth_version":
                self.assessment_auth_version,

            "required_identity_headers":
                list(
                    REQUIRED_IDENTITY_HEADERS
                ),

            "tenant_identity_required":
                self.tenant_identity_required,

            "actor_identity_required":
                self.actor_identity_required,

            "actor_roles_required":
                self.actor_roles_required,

            "missing_identity_fails_closed":
                self.missing_identity_fails_closed,

            "deterministic_role_parsing":
                self.deterministic_role_parsing,

            "tenant_scope_binding_enforced":
                self.tenant_scope_binding_enforced,

            "insufficient_role_fails_closed":
                self.insufficient_role_fails_closed,

            "valid_identity_accepted":
                self.valid_identity_accepted,

            "passed":
                self.passed,

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "preflight_is_read_only":
                    True,

                "preflight_uses_existing_assessment_auth_authority":
                    True,

                "preflight_does_not_create_identity":
                    True,

                "preflight_does_not_grant_roles":
                    True,

                "preflight_does_not_grant_access":
                    True,

                "identity_preflight_is_not_authentication":
                    True,

                "identity_preflight_is_not_authorization":
                    True,

                "identity_preflight_is_not_deployment_activation":
                    True,

                "identity_preflight_is_not_trial_authorization":
                    True,
            },
        }


async def evaluate_governance_release_identity_tenant_boundary_preflight(
    *,
    release_environment: str,
) -> GovernanceReleaseIdentityTenantBoundaryPreflightResult:
    normalized_environment = (
        _normalize_release_environment(
            release_environment
        )
    )

    tenant_identity_required = await _missing_header_fails_closed(
        missing_header="tenant"
    )

    actor_identity_required = await _missing_header_fails_closed(
        missing_header="actor"
    )

    actor_roles_required = await _missing_header_fails_closed(
        missing_header="roles"
    )

    missing_identity_fails_closed = all(
        (
            tenant_identity_required,
            actor_identity_required,
            actor_roles_required,
        )
    )

    deterministic_role_parsing = (
        await _prove_deterministic_role_parsing()
    )

    tenant_scope_binding_enforced = all(
        (
            await _tenant_mismatch_is_denied(
                tenant_source="path"
            ),
            await _tenant_mismatch_is_denied(
                tenant_source="query"
            ),
            await _tenant_mismatch_is_denied(
                tenant_source="body"
            ),
        )
    )

    insufficient_role_fails_closed = (
        await _insufficient_role_is_denied()
    )

    valid_identity_accepted = (
        await _valid_identity_is_accepted()
    )

    checks = {
        "tenant_identity_required":
            tenant_identity_required,

        "actor_identity_required":
            actor_identity_required,

        "actor_roles_required":
            actor_roles_required,

        "missing_identity_fails_closed":
            missing_identity_fails_closed,

        "deterministic_role_parsing":
            deterministic_role_parsing,

        "tenant_scope_binding_enforced":
            tenant_scope_binding_enforced,

        "insufficient_role_fails_closed":
            insufficient_role_fails_closed,

        "valid_identity_accepted":
            valid_identity_accepted,
    }

    failure_reasons = tuple(
        check_name
        for check_name, passed
        in checks.items()
        if not passed
    )

    return (
        GovernanceReleaseIdentityTenantBoundaryPreflightResult(
            release_environment=normalized_environment,
            assessment_auth_version=ASSESSMENT_AUTH_VERSION,
            tenant_identity_required=tenant_identity_required,
            actor_identity_required=actor_identity_required,
            actor_roles_required=actor_roles_required,
            missing_identity_fails_closed=(
                missing_identity_fails_closed
            ),
            deterministic_role_parsing=(
                deterministic_role_parsing
            ),
            tenant_scope_binding_enforced=(
                tenant_scope_binding_enforced
            ),
            insufficient_role_fails_closed=(
                insufficient_role_fails_closed
            ),
            valid_identity_accepted=(
                valid_identity_accepted
            ),
            passed=not failure_reasons,
            failure_reasons=failure_reasons,
        )
    )


async def _missing_header_fails_closed(
    *,
    missing_header: str,
) -> bool:
    request = _build_request(
        method="GET",
        query_tenant_id="tenant-alpha",
    )

    tenant_id = (
        None
        if missing_header == "tenant"
        else "tenant-alpha"
    )

    actor_id = (
        None
        if missing_header == "actor"
        else "release-preflight-actor"
    )

    actor_roles = (
        None
        if missing_header == "roles"
        else ASSESSMENT_READER_ROLE
    )

    try:
        await require_assessment_actor(
            request=request,
            x_tenant_id=tenant_id,
            x_actor_id=actor_id,
            x_actor_roles=actor_roles,
        )
    except HTTPException as exc:
        return (
            exc.status_code == 401
            and _exception_code(exc)
            == "ASSESSMENT_AUTH_REQUIRED"
        )

    return False


async def _prove_deterministic_role_parsing(
) -> bool:
    request = _build_request(
        method="GET",
        query_tenant_id="tenant-alpha",
    )

    context = await require_assessment_actor(
        request=request,
        x_tenant_id="tenant-alpha",
        x_actor_id="release-preflight-actor",
        x_actor_roles=(
            " Assessment:Read, "
            "assessment:admin,"
            "assessment:read "
        ),
    )

    return (
        context.roles
        == (
            ASSESSMENT_ADMIN_ROLE,
            ASSESSMENT_READER_ROLE,
        )
    )


async def _tenant_mismatch_is_denied(
    *,
    tenant_source: str,
) -> bool:
    method = (
        "POST"
        if tenant_source == "body"
        else "GET"
    )

    request = _build_request(
        method=method,
        path_tenant_id=(
            "tenant-beta"
            if tenant_source == "path"
            else None
        ),
        query_tenant_id=(
            "tenant-beta"
            if tenant_source == "query"
            else None
        ),
        body_tenant_id=(
            "tenant-beta"
            if tenant_source == "body"
            else None
        ),
    )

    roles = (
        ASSESSMENT_EXECUTOR_ROLE
        if method == "POST"
        else ASSESSMENT_READER_ROLE
    )

    try:
        await require_assessment_actor(
            request=request,
            x_tenant_id="tenant-alpha",
            x_actor_id="release-preflight-actor",
            x_actor_roles=roles,
        )
    except HTTPException as exc:
        return (
            exc.status_code == 403
            and _exception_code(exc)
            == "ASSESSMENT_TENANT_MISMATCH"
        )

    return False


async def _insufficient_role_is_denied(
) -> bool:
    request = _build_request(
        method="GET",
        query_tenant_id="tenant-alpha",
    )

    try:
        await require_assessment_actor(
            request=request,
            x_tenant_id="tenant-alpha",
            x_actor_id="release-preflight-actor",
            x_actor_roles=ASSESSMENT_EXECUTOR_ROLE,
        )
    except HTTPException as exc:
        return (
            exc.status_code == 403
            and _exception_code(exc)
            == "ASSESSMENT_ROLE_FORBIDDEN"
        )

    return False


async def _valid_identity_is_accepted(
) -> bool:
    request = _build_request(
        method="GET",
        query_tenant_id="tenant-alpha",
    )

    context = await require_assessment_actor(
        request=request,
        x_tenant_id="tenant-alpha",
        x_actor_id="release-preflight-actor",
        x_actor_roles=ASSESSMENT_READER_ROLE,
    )

    return (
        isinstance(
            context,
            AssessmentActorContext,
        )
        and context.tenant_id
        == "tenant-alpha"
        and context.actor_id
        == "release-preflight-actor"
        and context.roles
        == (
            ASSESSMENT_READER_ROLE,
        )
        and getattr(
            request.state,
            "assessment_actor",
            None,
        )
        == context
    )


def _build_request(
    *,
    method: str,
    path_tenant_id: str | None = None,
    query_tenant_id: str | None = None,
    body_tenant_id: str | None = None,
) -> Request:
    query_string = b""

    if query_tenant_id is not None:
        query_string = urlencode(
            {
                "tenant_id":
                    query_tenant_id,
            }
        ).encode(
            "utf-8"
        )

    body_payload: dict[str, str] = {}

    if body_tenant_id is not None:
        body_payload[
            "tenant_id"
        ] = body_tenant_id

    body_bytes = (
        json.dumps(
            body_payload
        ).encode(
            "utf-8"
        )
        if body_payload
        else b""
    )

    headers: list[
        tuple[bytes, bytes]
    ] = []

    if body_payload:
        headers.append(
            (
                b"content-type",
                b"application/json",
            )
        )

    scope: dict[str, Any] = {
        "type":
            "http",

        "http_version":
            "1.1",

        "method":
            method,

        "scheme":
            "https",

        "path":
            "/release-identity-preflight",

        "raw_path":
            b"/release-identity-preflight",

        "query_string":
            query_string,

        "headers":
            headers,

        "client":
            (
                "127.0.0.1",
                0,
            ),

        "server":
            (
                "release-preflight",
                443,
            ),

        "path_params":
            {},
    }

    if path_tenant_id is not None:
        scope[
            "path_params"
        ][
            "tenant_id"
        ] = path_tenant_id

    body_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal body_sent

        if not body_sent:
            body_sent = True

            return {
                "type":
                    "http.request",

                "body":
                    body_bytes,

                "more_body":
                    False,
            }

        return {
            "type":
                "http.disconnect",
        }

    return Request(
        scope,
        receive,
    )


def _exception_code(
    exc: HTTPException,
) -> str | None:
    detail = exc.detail

    if not isinstance(
        detail,
        dict,
    ):
        return None

    value = detail.get(
        "code"
    )

    if value is None:
        return None

    return str(
        value
    )


def _normalize_release_environment(
    value: str,
) -> str:
    normalized = str(
        value
    ).strip().lower()

    if (
        normalized
        not in SUPPORTED_RELEASE_ENVIRONMENTS
    ):
        raise ValueError(
            "identity/tenant boundary preflight requires "
            "release environment prelive or paid_trial"
        )

    return normalized