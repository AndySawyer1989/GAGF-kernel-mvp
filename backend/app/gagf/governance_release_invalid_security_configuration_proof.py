from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
    ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
    ASSESSMENT_CHECKPOINT_TENANT_ENV,
)
from backend.app.gagf.governance_release_cors_configuration import (
    GAGF_RELEASE_CORS_ORIGINS_ENV,
    GovernanceReleaseCorsConfigurationError,
    load_governance_release_cors_configuration,
)
from backend.app.gagf.governance_release_secret_preflight import (
    evaluate_governance_release_secret_preflight,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    GovernanceReleaseStorageConfigurationError,
    load_governance_release_storage_configuration,
)


GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_TYPE = (
    "governance-release-invalid-security-configuration-proof"
)

GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_VERSION = (
    "0.1.0"
)

SUPPORTED_PROOF_ENVIRONMENTS = (
    "prelive",
    "paid_trial",
)

FAILURE_SCENARIOS = (
    "unsupported_release_environment",
    "missing_release_data_root",
    "missing_cors_origins",
    "wildcard_cors_origin",
    "partial_signing_configuration",
    "missing_signing_secret",
    "invalid_secret_reference",
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseSecurityFailureScenarioResult:
    scenario: str
    rejected: bool
    rejection_authority: str
    failure_code: str


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseInvalidSecurityConfigurationProofResult:
    release_environment: str

    scenarios: tuple[
        GovernanceReleaseSecurityFailureScenarioResult,
        ...
    ]

    scenario_count: int
    rejected_scenario_count: int

    all_invalid_configurations_rejected: bool

    passed: bool
    failure_reasons: tuple[str, ...]

    proof_type: str = (
        GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_VERSION
    )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "proof_type":
                self.proof_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "scenario_count":
                self.scenario_count,

            "rejected_scenario_count":
                self.rejected_scenario_count,

            "all_invalid_configurations_rejected":
                self.all_invalid_configurations_rejected,

            "passed":
                self.passed,

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "scenarios": [
                {
                    "scenario":
                        result.scenario,

                    "rejected":
                        result.rejected,

                    "rejection_authority":
                        result.rejection_authority,

                    "failure_code":
                        result.failure_code,
                }
                for result
                in self.scenarios
            ],

            "boundaries": {
                "proof_is_read_only":
                    True,

                "proof_uses_existing_validation_authorities":
                    True,

                "proof_does_not_weaken_fail_closed_behavior":
                    True,

                "proof_does_not_create_credentials":
                    True,

                "proof_does_not_modify_runtime_configuration":
                    True,

                "proof_does_not_return_secret_material":
                    True,

                "failure_proof_is_not_deployment_activation":
                    True,

                "failure_proof_is_not_trial_authorization":
                    True,
            },
        }


def evaluate_governance_release_invalid_security_configuration_proof(
    *,
    release_environment: str,
    application_data_root: str | Path,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseInvalidSecurityConfigurationProofResult:
    normalized_environment = (
        _normalize_release_environment(
            release_environment
        )
    )

    baseline_environment = dict(
        environment
    )

    baseline_environment[
        GAGF_RELEASE_ENVIRONMENT_ENV
    ] = normalized_environment

    scenario_results = (
        _prove_unsupported_release_environment_rejected(
            application_data_root=application_data_root,
            environment=baseline_environment,
        ),
        _prove_missing_release_data_root_rejected(
            application_data_root=application_data_root,
            environment=baseline_environment,
        ),
        _prove_missing_cors_origins_rejected(
            environment=baseline_environment,
        ),
        _prove_wildcard_cors_origin_rejected(
            environment=baseline_environment,
        ),
        _prove_partial_signing_configuration_rejected(
            release_environment=normalized_environment,
            assessment_database_path=assessment_database_path,
            environment=baseline_environment,
        ),
        _prove_missing_signing_secret_rejected(
            release_environment=normalized_environment,
            assessment_database_path=assessment_database_path,
            environment=baseline_environment,
        ),
        _prove_invalid_secret_reference_rejected(
            release_environment=normalized_environment,
            assessment_database_path=assessment_database_path,
            environment=baseline_environment,
        ),
    )

    rejected_scenario_count = sum(
        1
        for result
        in scenario_results
        if result.rejected
    )

    all_invalid_configurations_rejected = (
        rejected_scenario_count
        == len(
            scenario_results
        )
    )

    failure_reasons = tuple(
        (
            f"{result.scenario}_not_rejected"
        )
        for result
        in scenario_results
        if not result.rejected
    )

    return (
        GovernanceReleaseInvalidSecurityConfigurationProofResult(
            release_environment=normalized_environment,
            scenarios=scenario_results,
            scenario_count=len(
                scenario_results
            ),
            rejected_scenario_count=(
                rejected_scenario_count
            ),
            all_invalid_configurations_rejected=(
                all_invalid_configurations_rejected
            ),
            passed=(
                not failure_reasons
            ),
            failure_reasons=(
                failure_reasons
            ),
        )
    )


def _prove_unsupported_release_environment_rejected(
    *,
    application_data_root: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    invalid_environment[
        GAGF_RELEASE_ENVIRONMENT_ENV
    ] = "production-ish"

    try:
        load_governance_release_storage_configuration(
            application_data_root=(
                application_data_root
            ),
            environment=(
                invalid_environment
            ),
        )
    except GovernanceReleaseStorageConfigurationError:
        return _rejected(
            scenario="unsupported_release_environment",
            authority="release_storage_configuration",
            failure_code="unsupported_release_environment",
        )

    return _not_rejected(
        scenario="unsupported_release_environment",
        authority="release_storage_configuration",
    )


def _prove_missing_release_data_root_rejected(
    *,
    application_data_root: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    invalid_environment.pop(
        GAGF_RELEASE_DATA_ROOT_ENV,
        None,
    )

    try:
        load_governance_release_storage_configuration(
            application_data_root=(
                application_data_root
            ),
            environment=(
                invalid_environment
            ),
        )
    except GovernanceReleaseStorageConfigurationError:
        return _rejected(
            scenario="missing_release_data_root",
            authority="release_storage_configuration",
            failure_code="explicit_release_data_root_required",
        )

    return _not_rejected(
        scenario="missing_release_data_root",
        authority="release_storage_configuration",
    )


def _prove_missing_cors_origins_rejected(
    *,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    invalid_environment.pop(
        GAGF_RELEASE_CORS_ORIGINS_ENV,
        None,
    )

    try:
        load_governance_release_cors_configuration(
            environment=(
                invalid_environment
            ),
        )
    except GovernanceReleaseCorsConfigurationError:
        return _rejected(
            scenario="missing_cors_origins",
            authority="release_cors_configuration",
            failure_code="explicit_cors_origins_required",
        )

    return _not_rejected(
        scenario="missing_cors_origins",
        authority="release_cors_configuration",
    )


def _prove_wildcard_cors_origin_rejected(
    *,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    invalid_environment[
        GAGF_RELEASE_CORS_ORIGINS_ENV
    ] = "*"

    try:
        load_governance_release_cors_configuration(
            environment=(
                invalid_environment
            ),
        )
    except GovernanceReleaseCorsConfigurationError:
        return _rejected(
            scenario="wildcard_cors_origin",
            authority="release_cors_configuration",
            failure_code="wildcard_cors_origin_forbidden",
        )

    return _not_rejected(
        scenario="wildcard_cors_origin",
        authority="release_cors_configuration",
    )


def _prove_partial_signing_configuration_rejected(
    *,
    release_environment: str,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    invalid_environment.pop(
        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
        None,
    )

    result = (
        evaluate_governance_release_secret_preflight(
            release_environment=(
                release_environment
            ),
            assessment_database_path=(
                assessment_database_path
            ),
            environment=(
                invalid_environment
            ),
        )
    )

    rejected = (
        result.passed is False
        and "signing_configuration_invalid"
        in result.failure_reasons
    )

    if rejected:
        return _rejected(
            scenario="partial_signing_configuration",
            authority="release_secret_preflight",
            failure_code="signing_configuration_invalid",
        )

    return _not_rejected(
        scenario="partial_signing_configuration",
        authority="release_secret_preflight",
    )


def _prove_missing_signing_secret_rejected(
    *,
    release_environment: str,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    secret_reference = (
        invalid_environment.get(
            ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV
        )
    )

    secret_variable = (
        _environment_secret_variable(
            secret_reference
        )
    )

    if secret_variable is not None:
        invalid_environment.pop(
            secret_variable,
            None,
        )

    result = (
        evaluate_governance_release_secret_preflight(
            release_environment=(
                release_environment
            ),
            assessment_database_path=(
                assessment_database_path
            ),
            environment=(
                invalid_environment
            ),
        )
    )

    rejected = (
        result.passed is False
        and "checkpoint_signing_secret_unavailable"
        in result.failure_reasons
    )

    if rejected:
        return _rejected(
            scenario="missing_signing_secret",
            authority="release_secret_preflight",
            failure_code="checkpoint_signing_secret_unavailable",
        )

    return _not_rejected(
        scenario="missing_signing_secret",
        authority="release_secret_preflight",
    )


def _prove_invalid_secret_reference_rejected(
    *,
    release_environment: str,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecurityFailureScenarioResult:
    invalid_environment = dict(
        environment
    )

    invalid_environment[
        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV
    ] = "secret://invalid-reference"

    result = (
        evaluate_governance_release_secret_preflight(
            release_environment=(
                release_environment
            ),
            assessment_database_path=(
                assessment_database_path
            ),
            environment=(
                invalid_environment
            ),
        )
    )

    rejected = (
        result.passed is False
        and "environment_secret_reference_required"
        in result.failure_reasons
    )

    if rejected:
        return _rejected(
            scenario="invalid_secret_reference",
            authority="release_secret_preflight",
            failure_code="environment_secret_reference_required",
        )

    return _not_rejected(
        scenario="invalid_secret_reference",
        authority="release_secret_preflight",
    )


def _environment_secret_variable(
    secret_reference: object,
) -> str | None:
    if not isinstance(
        secret_reference,
        str,
    ):
        return None

    prefix = "env://"

    if not secret_reference.startswith(
        prefix
    ):
        return None

    variable_name = (
        secret_reference[
            len(prefix):
        ]
        .strip()
    )

    if not variable_name:
        return None

    return variable_name


def _rejected(
    *,
    scenario: str,
    authority: str,
    failure_code: str,
) -> GovernanceReleaseSecurityFailureScenarioResult:
    return (
        GovernanceReleaseSecurityFailureScenarioResult(
            scenario=scenario,
            rejected=True,
            rejection_authority=authority,
            failure_code=failure_code,
        )
    )


def _not_rejected(
    *,
    scenario: str,
    authority: str,
) -> GovernanceReleaseSecurityFailureScenarioResult:
    return (
        GovernanceReleaseSecurityFailureScenarioResult(
            scenario=scenario,
            rejected=False,
            rejection_authority=authority,
            failure_code="invalid_configuration_was_not_rejected",
        )
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
        value.strip().lower()
    )

    if (
        normalized
        not in SUPPORTED_PROOF_ENVIRONMENTS
    ):
        raise ValueError(
            "invalid security configuration proof supports "
            "only prelive and paid_trial"
        )

    return normalized