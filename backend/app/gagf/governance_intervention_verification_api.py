from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status

from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationLedgerError,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleError,
)
from backend.app.gagf.governance_intervention_verification_query import (
    GovernanceInterventionVerificationQueryService,
)


GOVERNANCE_INTERVENTION_VERIFICATION_API_ID = (
    "governance-intervention-verification-api"
)
GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION = "0.2.0"

GOVERNANCE_INTERVENTION_VERIFICATION_READ_SCOPE = (
    "intervention-verification:read"
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


def create_governance_intervention_verification_router(
    *,
    database_path: str | Path,
) -> APIRouter:
    router = APIRouter(
        prefix="/tenant-intervention-verification",
        tags=["tenant-intervention-verification"],
    )

    query_service = (
        GovernanceInterventionVerificationQueryService(
            database_path=database_path
        )
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
                == (
                    GOVERNANCE_INTERVENTION_VERIFICATION_READ_SCOPE
                )
            ),
            "credential_verified": _parse_boolean_header(
                value=credential_verified,
                header_name="x-credential-verified",
            ),
            "session_verified": _parse_boolean_header(
                value=session_verified,
                header_name="x-session-verified",
            ),
            "device_trusted": _parse_boolean_header(
                value=device_trusted,
                header_name="x-device-trusted",
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
                "tenant-intervention-verification-"
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": (
                        "Tenant intervention-verification "
                        "query was denied."
                    ),
                    "authorization": decision,
                },
            )

        return decision

    def common_authorization(
        *,
        x_tenant_id: str,
        x_role_id: str,
        x_policy_scope: str,
        x_credential_verified: str,
        x_session_verified: str,
        x_device_trusted: str,
        x_tenant_membership_verified: str,
    ) -> dict:
        return authorize(
            tenant_id=x_tenant_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            credential_verified=x_credential_verified,
            session_verified=x_session_verified,
            device_trusted=x_device_trusted,
            tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

    @router.get(
        "/interventions/{intervention_id}"
    )
    def get_intervention_history(
        intervention_id: str,
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
        authorization = common_authorization(
            x_tenant_id=x_tenant_id,
            x_role_id=x_role_id,
            x_policy_scope=x_policy_scope,
            x_credential_verified=(
                x_credential_verified
            ),
            x_session_verified=x_session_verified,
            x_device_trusted=x_device_trusted,
            x_tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        try:
            records = query_service.list_for_intervention(
                tenant_id=x_tenant_id,
                intervention_id=intervention_id,
            )
        except GovernanceInterventionVerificationLedgerError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return {
            "api_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
            ),
            "api_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION
            ),
            "authorization": authorization,
            "tenant_id": x_tenant_id,
            "intervention_id": intervention_id,
            "record_count": len(records),
            "records": [
                record.to_dict()
                for record in records
            ],
        }

    @router.get(
        "/summaries/{verification_summary_hash}"
    )
    def get_summary_record(
        verification_summary_hash: str,
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
        authorization = common_authorization(
            x_tenant_id=x_tenant_id,
            x_role_id=x_role_id,
            x_policy_scope=x_policy_scope,
            x_credential_verified=(
                x_credential_verified
            ),
            x_session_verified=x_session_verified,
            x_device_trusted=x_device_trusted,
            x_tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        try:
            record = query_service.get_by_summary_hash(
                tenant_id=x_tenant_id,
                verification_summary_hash=(
                    verification_summary_hash
                ),
            )
        except GovernanceInterventionVerificationLedgerError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Governed intervention verification "
                    "record was not found."
                ),
            )

        return {
            "api_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
            ),
            "api_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION
            ),
            "authorization": authorization,
            "record": record.to_dict(),
        }

    @router.get("/ledger/integrity")
    def get_ledger_integrity(
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
        authorization = common_authorization(
            x_tenant_id=x_tenant_id,
            x_role_id=x_role_id,
            x_policy_scope=x_policy_scope,
            x_credential_verified=(
                x_credential_verified
            ),
            x_session_verified=x_session_verified,
            x_device_trusted=x_device_trusted,
            x_tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        try:
            verification = (
                query_service.verify_tenant_ledger(
                    tenant_id=x_tenant_id
                )
            )
        except GovernanceInterventionVerificationLedgerError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return {
            "api_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
            ),
            "api_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION
            ),
            "authorization": authorization,
            "integrity": {
                "tenant_id": verification.tenant_id,
                "record_count": verification.record_count,
                "valid": verification.valid,
                "last_chain_hash": (
                    verification.last_chain_hash
                ),
            },
        }

    @router.get(
        "/records/{verification_record_hash}/lifecycle"
    )
    def get_verification_lifecycle_state(
        verification_record_hash: str,
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
        authorization = common_authorization(
            x_tenant_id=x_tenant_id,
            x_role_id=x_role_id,
            x_policy_scope=x_policy_scope,
            x_credential_verified=(
                x_credential_verified
            ),
            x_session_verified=x_session_verified,
            x_device_trusted=x_device_trusted,
            x_tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        try:
            lifecycle = (
                query_service.get_lifecycle_state(
                    tenant_id=x_tenant_id,
                    verification_record_hash=(
                        verification_record_hash
                    ),
                )
            )
        except GovernanceInterventionVerificationLifecycleError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        if lifecycle is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Governed intervention verification "
                    "lifecycle state was not found."
                ),
            )

        return {
            "api_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
            ),
            "api_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION
            ),
            "authorization": authorization,
            "lifecycle": lifecycle.to_dict(),
        }

    @router.get(
        "/records/{verification_record_hash}/lifecycle/history"
    )
    def get_verification_lifecycle_history(
        verification_record_hash: str,
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
        authorization = common_authorization(
            x_tenant_id=x_tenant_id,
            x_role_id=x_role_id,
            x_policy_scope=x_policy_scope,
            x_credential_verified=(
                x_credential_verified
            ),
            x_session_verified=x_session_verified,
            x_device_trusted=x_device_trusted,
            x_tenant_membership_verified=(
                x_tenant_membership_verified
            ),
        )

        try:
            history = (
                query_service.list_lifecycle_history(
                    tenant_id=x_tenant_id,
                    verification_record_hash=(
                        verification_record_hash
                    ),
                )
            )
        except GovernanceInterventionVerificationLifecycleError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return {
            "api_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
            ),
            "api_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION
            ),
            "authorization": authorization,
            "tenant_id": x_tenant_id,
            "verification_record_hash": (
                verification_record_hash
            ),
            "event_count": len(history),
            "events": [
                event.to_dict()
                for event in history
            ],
        }

    return router