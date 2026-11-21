from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_AUTH_VERSION,
)


GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE = (
    "governance-release-identity-tenant-boundary-preflight"
)

GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION = (
    "0.2.0"
)

SUPPORTED_RELEASE_ENVIRONMENTS = frozenset(
    {
        "prelive",
        "paid_trial",
    }
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseIdentityTenantBoundaryPreflightResult:
    release_environment: str
    assessment_auth_version: str

    identity_provider_configured: bool
    deployment_identity_evidence_present: bool
    provider_claim_mapping_verified: bool
    tenant_boundary_evidence_verified: bool
    role_mapping_evidence_verified: bool

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
    ) -> dict[str, object]:
        return {
            "preflight_type":
                self.preflight_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "assessment_auth_version":
                self.assessment_auth_version,

            "identity_provider_configured":
                self.identity_provider_configured,

            "deployment_identity_evidence_present":
                self.deployment_identity_evidence_present,

            "provider_claim_mapping_verified":
                self.provider_claim_mapping_verified,

            "tenant_boundary_evidence_verified":
                self.tenant_boundary_evidence_verified,

            "role_mapping_evidence_verified":
                self.role_mapping_evidence_verified,

            "passed":
                self.passed,

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "preflight_is_read_only":
                    True,

                "preflight_does_not_create_identity":
                    True,

                "preflight_does_not_verify_identity_by_simulation":
                    True,

                "preflight_does_not_grant_roles":
                    True,

                "preflight_does_not_grant_access":
                    True,

                "preflight_is_not_authentication":
                    True,

                "preflight_is_not_authorization":
                    True,

                "preflight_is_not_deployment_activation":
                    True,

                "preflight_is_not_trial_authorization":
                    True,

                "unverified_identity_evidence_fails_closed":
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

    # No production identity provider has been selected or configured.
    # No independently verifiable deployment identity evidence is
    # currently available. These are intentionally not inferred from
    # synthetic requests, test verifiers, or caller-supplied booleans.
    identity_provider_configured = False
    deployment_identity_evidence_present = False
    provider_claim_mapping_verified = False
    tenant_boundary_evidence_verified = False
    role_mapping_evidence_verified = False

    failure_reasons = (
        "production_identity_provider_not_configured",
        "deployment_identity_evidence_unavailable",
        "provider_claim_mapping_unverified",
        "tenant_boundary_evidence_unverified",
        "role_mapping_evidence_unverified",
    )

    return GovernanceReleaseIdentityTenantBoundaryPreflightResult(
        release_environment=normalized_environment,
        assessment_auth_version=ASSESSMENT_AUTH_VERSION,
        identity_provider_configured=identity_provider_configured,
        deployment_identity_evidence_present=(
            deployment_identity_evidence_present
        ),
        provider_claim_mapping_verified=(
            provider_claim_mapping_verified
        ),
        tenant_boundary_evidence_verified=(
            tenant_boundary_evidence_verified
        ),
        role_mapping_evidence_verified=(
            role_mapping_evidence_verified
        ),
        passed=False,
        failure_reasons=failure_reasons,
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
