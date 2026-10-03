from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_environment_security_preflight import (
    GovernanceReleaseEnvironmentSecurityPreflightResult,
)
from backend.app.gagf.governance_release_identity_tenant_boundary_preflight import (
    GovernanceReleaseIdentityTenantBoundaryPreflightResult,
)
from backend.app.gagf.governance_release_invalid_security_configuration_proof import (
    GovernanceReleaseInvalidSecurityConfigurationProofResult,
)
from backend.app.gagf.governance_release_secret_preflight import (
    GovernanceReleaseSecretPreflightResult,
)
from backend.app.gagf.governance_release_secret_redaction_proof import (
    GovernanceReleaseSecretRedactionProofResult,
)


GOVERNANCE_RELEASE_SECURITY_GATE_TYPE = (
    "governance-release-security-gate"
)

GOVERNANCE_RELEASE_SECURITY_GATE_VERSION = (
    "0.1.0"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseSecurityGateResult:
    release_environment: str
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    gate_type: str = (
        GOVERNANCE_RELEASE_SECURITY_GATE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_SECURITY_GATE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "gate_type":
                self.gate_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "passed":
                self.passed,

            "checks":
                dict(
                    self.checks
                ),

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "gate_is_read_only":
                    True,

                "gate_evaluates_existing_evidence_only":
                    True,

                "gate_does_not_resolve_secret_material":
                    True,

                "gate_does_not_create_credentials":
                    True,

                "gate_does_not_rotate_credentials":
                    True,

                "gate_does_not_authenticate_actor":
                    True,

                "gate_does_not_authorize_actor":
                    True,

                "gate_is_not_deployment_activation":
                    True,

                "gate_is_not_trial_authorization":
                    True,

                "gate_is_not_production_activation":
                    True,

                "gate_is_not_intervention_authority":
                    True,

                "security_readiness_is_not_customer_trial_authority":
                    True,
            },
        }


def evaluate_governance_release_security_gate(
    *,
    secret_preflight:
        GovernanceReleaseSecretPreflightResult,
    environment_preflight:
        GovernanceReleaseEnvironmentSecurityPreflightResult,
    identity_preflight:
        GovernanceReleaseIdentityTenantBoundaryPreflightResult,
    redaction_proof:
        GovernanceReleaseSecretRedactionProofResult,
    invalid_configuration_proof:
        GovernanceReleaseInvalidSecurityConfigurationProofResult,
) -> GovernanceReleaseSecurityGateResult:
    _require_types(
        secret_preflight=secret_preflight,
        environment_preflight=environment_preflight,
        identity_preflight=identity_preflight,
        redaction_proof=redaction_proof,
        invalid_configuration_proof=(
            invalid_configuration_proof
        ),
    )

    release_environment = (
        secret_preflight.release_environment
    )

    checks = {
        "paid_trial_environment":
            release_environment
            == "paid_trial",

        "secret_preflight_passed":
            secret_preflight.passed
            is True,

        "environment_security_preflight_passed":
            environment_preflight.passed
            is True,

        "identity_tenant_boundary_preflight_passed":
            identity_preflight.passed
            is True,

        "secret_redaction_proof_passed":
            redaction_proof.passed
            is True,

        "invalid_security_configuration_proof_passed":
            invalid_configuration_proof.passed
            is True,

        "environment_preflight_matches_gate_environment":
            environment_preflight.release_environment
            == release_environment,

        "identity_preflight_matches_gate_environment":
            identity_preflight.release_environment
            == release_environment,

        "redaction_proof_matches_gate_environment":
            redaction_proof.release_environment
            == release_environment,

        "invalid_configuration_proof_matches_gate_environment":
            invalid_configuration_proof.release_environment
            == release_environment,
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    return GovernanceReleaseSecurityGateResult(
        release_environment=(
            release_environment
        ),
        passed=(
            not failure_reasons
        ),
        checks=checks,
        failure_reasons=(
            failure_reasons
        ),
    )


def _require_types(
    *,
    secret_preflight: object,
    environment_preflight: object,
    identity_preflight: object,
    redaction_proof: object,
    invalid_configuration_proof: object,
) -> None:
    expected = (
        (
            "secret_preflight",
            secret_preflight,
            GovernanceReleaseSecretPreflightResult,
        ),
        (
            "environment_preflight",
            environment_preflight,
            GovernanceReleaseEnvironmentSecurityPreflightResult,
        ),
        (
            "identity_preflight",
            identity_preflight,
            GovernanceReleaseIdentityTenantBoundaryPreflightResult,
        ),
        (
            "redaction_proof",
            redaction_proof,
            GovernanceReleaseSecretRedactionProofResult,
        ),
        (
            "invalid_configuration_proof",
            invalid_configuration_proof,
            GovernanceReleaseInvalidSecurityConfigurationProofResult,
        ),
    )

    for (
        name,
        value,
        expected_type,
    ) in expected:
        if not isinstance(
            value,
            expected_type,
        ):
            raise TypeError(
                f"{name} must be a "
                f"{expected_type.__name__}"
            )