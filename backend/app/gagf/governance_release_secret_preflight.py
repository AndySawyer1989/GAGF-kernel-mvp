from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_checkpoint_environment_secret_resolver import (
    ASSESSMENT_CHECKPOINT_ENVIRONMENT_SCHEME,
    EnvironmentAssessmentCheckpointSecretResolver,
)
from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
    ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
    ASSESSMENT_CHECKPOINT_TENANT_ENV,
    load_assessment_checkpoint_production_key_config,
)


GOVERNANCE_RELEASE_SECRET_PREFLIGHT_TYPE = (
    "governance-release-secret-preflight"
)

GOVERNANCE_RELEASE_SECRET_PREFLIGHT_VERSION = (
    "0.1.0"
)

SUPPORTED_RELEASE_ENVIRONMENTS = (
    "prelive",
    "paid_trial",
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseSecretPreflightResult:
    release_environment: str

    signing_configuration_enabled: bool
    tenant_configuration_present: bool
    key_id_configuration_present: bool
    secret_reference_present: bool
    environment_secret_reference: bool
    secret_resolved: bool

    passed: bool
    failure_reasons: tuple[str, ...]

    preflight_type: str = (
        GOVERNANCE_RELEASE_SECRET_PREFLIGHT_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_SECRET_PREFLIGHT_VERSION
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

            "signing_configuration_enabled":
                self.signing_configuration_enabled,

            "tenant_configuration_present":
                self.tenant_configuration_present,

            "key_id_configuration_present":
                self.key_id_configuration_present,

            "secret_reference_present":
                self.secret_reference_present,

            "environment_secret_reference":
                self.environment_secret_reference,

            "secret_resolved":
                self.secret_resolved,

            "passed":
                self.passed,

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "preflight_does_not_return_secret_material":
                    True,

                "preflight_does_not_create_credentials":
                    True,

                "preflight_does_not_rotate_keys":
                    True,

                "secret_presence_is_not_credential_validity":
                    True,

                "secret_resolution_is_not_deployment_authority":
                    True,

                "secret_resolution_is_not_trial_authorization":
                    True,
            },
        }


def evaluate_governance_release_secret_preflight(
    *,
    release_environment: str,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecretPreflightResult:
    normalized_environment = (
        _normalize_release_environment(
            release_environment
        )
    )

    tenant_configuration_present = (
        _has_nonblank_environment_value(
            environment,
            ASSESSMENT_CHECKPOINT_TENANT_ENV,
        )
    )

    key_id_configuration_present = (
        _has_nonblank_environment_value(
            environment,
            ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
        )
    )

    secret_reference_present = (
        _has_nonblank_environment_value(
            environment,
            ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
        )
    )

    signing_configuration_enabled = False
    environment_secret_reference = False
    secret_resolved = False

    failure_reasons: list[str] = []

    try:
        config = (
            load_assessment_checkpoint_production_key_config(
                assessment_database_path=(
                    assessment_database_path
                ),
                environment=environment,
            )
        )

    except ValueError:
        config = None

        failure_reasons.append(
            "signing_configuration_invalid"
        )

    if config is not None:
        signing_configuration_enabled = (
            config.enabled
            is True
        )

        if not signing_configuration_enabled:
            failure_reasons.append(
                "signing_configuration_required"
            )

        else:
            secret_reference = (
                config.secret_reference
            )

            if (
                isinstance(
                    secret_reference,
                    str,
                )
                and secret_reference.startswith(
                    ASSESSMENT_CHECKPOINT_ENVIRONMENT_SCHEME
                )
            ):
                environment_secret_reference = True

            else:
                failure_reasons.append(
                    "environment_secret_reference_required"
                )

            if environment_secret_reference:
                resolver = (
                    EnvironmentAssessmentCheckpointSecretResolver(
                        environment=environment
                    )
                )

                try:
                    resolved_secret = (
                        resolver.resolve_secret(
                            secret_reference=(
                                secret_reference
                            )
                        )
                    )

                    secret_resolved = (
                        isinstance(
                            resolved_secret,
                            bytes,
                        )
                        and bool(
                            resolved_secret
                        )
                    )

                except (
                    KeyError,
                    ValueError,
                ):
                    secret_resolved = False

                if not secret_resolved:
                    failure_reasons.append(
                        "checkpoint_signing_secret_unavailable"
                    )

    checks = (
        (
            "tenant_configuration_required",
            tenant_configuration_present,
        ),
        (
            "key_id_configuration_required",
            key_id_configuration_present,
        ),
        (
            "secret_reference_required",
            secret_reference_present,
        ),
    )

    for (
        failure_name,
        passed,
    ) in checks:
        if (
            not passed
            and failure_name
            not in failure_reasons
        ):
            failure_reasons.append(
                failure_name
            )

    normalized_failures = tuple(
        dict.fromkeys(
            failure_reasons
        )
    )

    return GovernanceReleaseSecretPreflightResult(
        release_environment=(
            normalized_environment
        ),
        signing_configuration_enabled=(
            signing_configuration_enabled
        ),
        tenant_configuration_present=(
            tenant_configuration_present
        ),
        key_id_configuration_present=(
            key_id_configuration_present
        ),
        secret_reference_present=(
            secret_reference_present
        ),
        environment_secret_reference=(
            environment_secret_reference
        ),
        secret_resolved=(
            secret_resolved
        ),
        passed=(
            not normalized_failures
        ),
        failure_reasons=(
            normalized_failures
        ),
    )


def _normalize_release_environment(
    value: object,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            "release_environment must be a string"
        )

    normalized = (
        value
        .strip()
        .lower()
    )

    if (
        normalized
        not in SUPPORTED_RELEASE_ENVIRONMENTS
    ):
        raise ValueError(
            "secret preflight supports only "
            "prelive and paid_trial"
        )

    return normalized


def _has_nonblank_environment_value(
    environment: Mapping[str, str],
    variable_name: str,
) -> bool:
    value = environment.get(
        variable_name
    )

    return (
        isinstance(
            value,
            str,
        )
        and bool(
            value.strip()
        )
    )