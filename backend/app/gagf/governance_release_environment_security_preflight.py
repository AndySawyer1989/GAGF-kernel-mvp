from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_release_cors_configuration import (
    GovernanceReleaseCorsConfiguration,
    REQUIRED_ASSESSMENT_IDENTITY_HEADERS,
)
from backend.app.gagf.governance_release_storage_configuration import (
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    RELEASE_ENVIRONMENT_PRELIVE,
)


GOVERNANCE_RELEASE_ENVIRONMENT_SECURITY_PREFLIGHT_TYPE = (
    "governance-release-environment-security-preflight"
)

GOVERNANCE_RELEASE_ENVIRONMENT_SECURITY_PREFLIGHT_VERSION = (
    "0.2.0"
)

SUPPORTED_SECURITY_PREFLIGHT_ENVIRONMENTS = (
    RELEASE_ENVIRONMENT_PRELIVE,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseEnvironmentSecurityPreflightResult:
    release_environment: str

    explicit_origins: bool
    wildcard_origin_absent: bool
    credentialed_cors_enabled: bool
    assessment_identity_headers_allowed: bool
    origin_count: int

    passed: bool
    failure_reasons: tuple[str, ...]

    preflight_type: str = (
        GOVERNANCE_RELEASE_ENVIRONMENT_SECURITY_PREFLIGHT_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_ENVIRONMENT_SECURITY_PREFLIGHT_VERSION
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

            "explicit_origins":
                self.explicit_origins,

            "wildcard_origin_absent":
                self.wildcard_origin_absent,

            "credentialed_cors_enabled":
                self.credentialed_cors_enabled,

            "assessment_identity_headers_allowed":
                self.assessment_identity_headers_allowed,

            "origin_count":
                self.origin_count,

            "passed":
                self.passed,

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "preflight_is_read_only":
                    True,

                "preflight_does_not_modify_cors":
                    True,

                "cors_configuration_is_not_authentication":
                    True,

                "cors_configuration_is_not_authorization":
                    True,

                "cors_pass_is_not_deployment_activation":
                    True,

                "cors_pass_is_not_trial_authorization":
                    True,
            },
        }


def evaluate_governance_release_environment_security_preflight(
    *,
    configuration: GovernanceReleaseCorsConfiguration,
) -> GovernanceReleaseEnvironmentSecurityPreflightResult:
    _validate_release_configuration(
        configuration
    )

    explicit_origins = (
        configuration.explicit_origins
        is True
    )

    wildcard_origin_absent = (
        "*"
        not in configuration.allow_origins
    )

    credentialed_cors_enabled = (
        configuration.allow_credentials
        is True
    )

    assessment_identity_headers_allowed = (
        _assessment_identity_headers_allowed(
            configuration.allow_headers
        )
    )

    checks = {
        "explicit_origins_required":
            explicit_origins,

        "wildcard_origin_forbidden":
            wildcard_origin_absent,

        "credentialed_cors_required":
            credentialed_cors_enabled,

        "assessment_identity_headers_required":
            assessment_identity_headers_allowed,
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    return (
        GovernanceReleaseEnvironmentSecurityPreflightResult(
            release_environment=(
                configuration.release_environment
            ),

            explicit_origins=(
                explicit_origins
            ),

            wildcard_origin_absent=(
                wildcard_origin_absent
            ),

            credentialed_cors_enabled=(
                credentialed_cors_enabled
            ),

            assessment_identity_headers_allowed=(
                assessment_identity_headers_allowed
            ),

            origin_count=len(
                configuration.allow_origins
            ),

            passed=(
                not failure_reasons
            ),

            failure_reasons=(
                failure_reasons
            ),
        )
    )


def _validate_release_configuration(
    configuration: GovernanceReleaseCorsConfiguration,
) -> None:
    if not isinstance(
        configuration,
        GovernanceReleaseCorsConfiguration,
    ):
        raise TypeError(
            "configuration must be a "
            "GovernanceReleaseCorsConfiguration"
        )

    if (
        configuration.release_environment
        not in SUPPORTED_SECURITY_PREFLIGHT_ENVIRONMENTS
    ):
        raise ValueError(
            "environment security preflight supports "
            "only prelive and paid_trial"
        )


def _assessment_identity_headers_allowed(
    allow_headers: tuple[str, ...],
) -> bool:
    normalized_headers = {
        header.lower()
        for header
        in allow_headers
    }

    required_headers = {
        header.lower()
        for header
        in REQUIRED_ASSESSMENT_IDENTITY_HEADERS
    }

    return required_headers.issubset(
        normalized_headers
    )