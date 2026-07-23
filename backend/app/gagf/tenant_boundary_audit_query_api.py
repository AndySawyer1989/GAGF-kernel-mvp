from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status

from backend.app.gagf.tenant_boundary_audit_query import (
    TenantBoundaryAuditEvidenceQueryService,
)
from backend.app.gagf.tenant_public_response_gate import (
    TenantPublicResponseRejectedError,
)
from backend.app.gagf.tenant_recorded_public_response_gate import (
    TenantRecordedPublicResponseGate,
)


TENANT_BOUNDARY_AUDIT_QUERY_API_ID = (
    "tenant-boundary-audit-evidence-query-api"
)
TENANT_BOUNDARY_AUDIT_QUERY_API_VERSION = "0.2.0"

TENANT_BOUNDARY_AUDIT_READ_SCOPE = (
    "boundary-audit:read"
)

_ALLOWED_ROLES = frozenset(
    {
        "scientific-reviewer",
        "tenant-auditor",
    }
)


def _parse_boolean_header(
    *,
    value: str,
    header_name: str,
) -> bool:
    normalized = value.strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"{header_name} must be either true or false."
        ),
    )


def create_tenant_boundary_audit_query_router(
    *,
    database_path: str | Path,
) -> APIRouter:
    router = APIRouter(
        prefix="/tenant-boundary-audit",
        tags=["tenant-boundary-audit"],
    )

    query_service = (
        TenantBoundaryAuditEvidenceQueryService(
            database_path=database_path
        )
    )
    response_gate = TenantRecordedPublicResponseGate(
        database_path=database_path
    )

    def authorize(
        *,
        tenant_id: str,
        role_id: str,
        policy_scope: str,
        credential_verified: str,
        session_verified: str,
        device_trusted: str,
        tenant_membership_verified: str,
    ) -> dict:
        normalized_tenant_id = tenant_id.strip()
        normalized_role_id = role_id.strip()
        normalized_scope = policy_scope.strip()

        if not normalized_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="x-tenant-id must not be empty.",
            )

        checks = {
            "role_permitted": (
                normalized_role_id in _ALLOWED_ROLES
            ),
            "scope_permitted": (
                normalized_scope
                == TENANT_BOUNDARY_AUDIT_READ_SCOPE
            ),
            "credential_verified": (
                _parse_boolean_header(
                    value=credential_verified,
                    header_name=(
                        "x-credential-verified"
                    ),
                )
            ),
            "session_verified": (
                _parse_boolean_header(
                    value=session_verified,
                    header_name=(
                        "x-session-verified"
                    ),
                )
            ),
            "device_trusted": (
                _parse_boolean_header(
                    value=device_trusted,
                    header_name="x-device-trusted",
                )
            ),
            "tenant_membership_verified": (
                _parse_boolean_header(
                    value=tenant_membership_verified,
                    header_name=(
                        "x-tenant-membership-verified"
                    ),
                )
            ),
        }

        allowed = all(checks.values())

        decision = {
            "view_id": (
                "tenant-public-boundary-audit-"
                "authorization-view"
            ),
            "view_version": "0.1.0",
            "tenant_id": normalized_tenant_id,
            "role_id": normalized_role_id,
            "scope": normalized_scope,
            "allowed": allowed,
            "checks": checks,
            "reasons": [
                reason
                for condition, reason in (
                    (
                        checks["role_permitted"],
                        "Role is not permitted.",
                    ),
                    (
                        checks["scope_permitted"],
                        "Policy scope is not permitted.",
                    ),
                    (
                        checks["credential_verified"],
                        "Credential is not verified.",
                    ),
                    (
                        checks["session_verified"],
                        "Session is not verified.",
                    ),
                    (
                        checks["device_trusted"],
                        "Device is not trusted.",
                    ),
                    (
                        checks[
                            "tenant_membership_verified"
                        ],
                        (
                            "Tenant membership is not "
                            "verified."
                        ),
                    ),
                )
                if not condition
            ],
        }

        if not allowed:
            try:
                detail = response_gate.release_error_detail(
                    tenant_id=normalized_tenant_id,
                    response_kind=(
                        "boundary-audit-query-denial"
                    ),
                    detail={
                        "message": (
                            "Tenant boundary-audit query "
                            "was denied."
                        ),
                        "authorization": decision,
                    }
                )
            except TenantPublicResponseRejectedError as exc:
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Authorization denial failed "
                        "public-boundary validation."
                    ),
                ) from exc

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

        return decision

    def release_response(
        *,
        tenant_id: str,
        response_kind: str,
        response: dict,
    ) -> dict:
        try:
            return response_gate.release(
                tenant_id=tenant_id,
                response_kind=response_kind,
                response=response,
            )
        except TenantPublicResponseRejectedError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Tenant boundary-audit response failed "
                    "public-boundary validation."
                ),
            ) from exc
    @router.get("/records")
    def list_records(
        x_tenant_id: str = Header(
            ...,
            alias="x-tenant-id",
        ),
        x_role_id: str = Header(
            ...,
            alias="x-role-id",
        ),
        x_policy_scope: str = Header(
            ...,
            alias="x-policy-scope",
        ),
        x_credential_verified: str = Header(
            ...,
            alias="x-credential-verified",
        ),
        x_session_verified: str = Header(
            ...,
            alias="x-session-verified",
        ),
        x_device_trusted: str = Header(
            ...,
            alias="x-device-trusted",
        ),
        x_tenant_membership_verified: str = Header(
            ...,
            alias="x-tenant-membership-verified",
        ),
    ) -> dict:
        authorization = authorize(
            tenant_id=x_tenant_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            credential_verified=(
                x_credential_verified
            ),
            session_verified=x_session_verified,
            device_trusted=x_device_trusted,
            tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        result = query_service.list_for_tenant(
            tenant_id=x_tenant_id
        )

        return release_response(
            tenant_id=x_tenant_id,
            response_kind="boundary-audit-list",
            response={
                "api_id": (
                    TENANT_BOUNDARY_AUDIT_QUERY_API_ID
                ),
                "api_version": (
                    TENANT_BOUNDARY_AUDIT_QUERY_API_VERSION
                ),
                "authorization": authorization,
                "result": result.to_dict(),
            }
        )

    @router.get(
        "/records/{public_record_id}"
    )
    def get_record(
        public_record_id: str,
        x_tenant_id: str = Header(
            ...,
            alias="x-tenant-id",
        ),
        x_role_id: str = Header(
            ...,
            alias="x-role-id",
        ),
        x_policy_scope: str = Header(
            ...,
            alias="x-policy-scope",
        ),
        x_credential_verified: str = Header(
            ...,
            alias="x-credential-verified",
        ),
        x_session_verified: str = Header(
            ...,
            alias="x-session-verified",
        ),
        x_device_trusted: str = Header(
            ...,
            alias="x-device-trusted",
        ),
        x_tenant_membership_verified: str = Header(
            ...,
            alias="x-tenant-membership-verified",
        ),
    ) -> dict:
        authorization = authorize(
            tenant_id=x_tenant_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            credential_verified=(
                x_credential_verified
            ),
            session_verified=x_session_verified,
            device_trusted=x_device_trusted,
            tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        record = query_service.get_for_tenant(
            tenant_id=x_tenant_id,
            public_record_id=public_record_id,
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Tenant boundary-audit record was "
                    "not found."
                ),
            )

        return release_response(
            tenant_id=x_tenant_id,
            response_kind="boundary-audit-record-read",
            response={
                "api_id": (
                    TENANT_BOUNDARY_AUDIT_QUERY_API_ID
                ),
                "api_version": (
                    TENANT_BOUNDARY_AUDIT_QUERY_API_VERSION
                ),
                "authorization": authorization,
                "record": record.to_dict(),
            }
        )

    return router






