from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_release_cors_configuration import (
    GAGF_RELEASE_CORS_ORIGINS_ENV,
    GovernanceReleaseCorsConfiguration,
    GovernanceReleaseCorsOriginsError,
    load_governance_release_cors_configuration,
)
from backend.app.gagf.governance_release_environment_security_preflight import (
    evaluate_governance_release_environment_security_preflight,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_ENVIRONMENT_ENV,
)


PAID_TRIAL_ENVIRONMENT = {
    GAGF_RELEASE_ENVIRONMENT_ENV:
        "paid_trial",

    GAGF_RELEASE_CORS_ORIGINS_ENV:
        (
            "https://operator.example.com,"
            "https://customer.example.com"
        ),
}

PRELIVE_ENVIRONMENT = {
    GAGF_RELEASE_ENVIRONMENT_ENV:
        "prelive",

    GAGF_RELEASE_CORS_ORIGINS_ENV:
        "https://prelive.example.com",
}


def build_paid_trial_configuration(
) -> GovernanceReleaseCorsConfiguration:
    return (
        load_governance_release_cors_configuration(
            environment=PAID_TRIAL_ENVIRONMENT
        )
    )


def evaluate_paid_trial():
    configuration = (
        build_paid_trial_configuration()
    )

    return (
        evaluate_governance_release_environment_security_preflight(
            configuration=configuration
        )
    )


def test_paid_trial_release_cors_contract_passes() -> None:
    result = (
        evaluate_paid_trial()
    )

    assert result.passed is True

    assert (
        result.release_environment
        == "paid_trial"
    )

    assert (
        result.explicit_origins
        is True
    )

    assert (
        result.wildcard_origin_absent
        is True
    )

    assert (
        result.credentialed_cors_enabled
        is True
    )

    assert (
        result.assessment_identity_headers_allowed
        is True
    )

    assert (
        result.origin_count
        == 2
    )

    assert (
        result.failure_reasons
        == ()
    )


def test_prelive_release_cors_contract_passes() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment=PRELIVE_ENVIRONMENT
        )
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=configuration
        )
    )

    assert result.passed is True
    assert (
        result.release_environment
        == "prelive"
    )
    assert (
        result.explicit_origins
        is True
    )
    assert (
        result.origin_count
        == 1
    )


def test_release_configuration_requires_explicit_origins() -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",
            }
        )


def test_preflight_detects_missing_explicit_origin_evidence() -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    modified = replace(
        configuration,
        explicit_origins=False,
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=modified
        )
    )

    assert result.passed is False

    assert (
        "explicit_origins_required"
        in result.failure_reasons
    )


def test_preflight_detects_wildcard_origin() -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    modified = replace(
        configuration,
        allow_origins=(
            "https://operator.example.com",
            "*",
        ),
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=modified
        )
    )

    assert result.passed is False

    assert (
        "wildcard_origin_forbidden"
        in result.failure_reasons
    )


def test_preflight_detects_disabled_credentials() -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    modified = replace(
        configuration,
        allow_credentials=False,
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=modified
        )
    )

    assert result.passed is False

    assert (
        "credentialed_cors_required"
        in result.failure_reasons
    )


@pytest.mark.parametrize(
    "missing_header",
    (
        "X-Tenant-ID",
        "X-Actor-ID",
        "X-Actor-Roles",
    ),
)
def test_each_assessment_identity_header_is_required(
    missing_header: str,
) -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    headers = tuple(
        header
        for header
        in configuration.allow_headers
        if (
            header.lower()
            != missing_header.lower()
        )
    )

    modified = replace(
        configuration,
        allow_headers=headers,
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=modified
        )
    )

    assert result.passed is False

    assert (
        "assessment_identity_headers_required"
        in result.failure_reasons
    )


def test_header_matching_is_case_insensitive() -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    modified = replace(
        configuration,
        allow_headers=tuple(
            header.lower()
            for header
            in configuration.allow_headers
        ),
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=modified
        )
    )

    assert result.passed is True


def test_preflight_preserves_authority_boundaries() -> None:
    result = (
        evaluate_paid_trial()
    )

    public_result = (
        result.to_public_dict()
    )

    boundaries = (
        public_result[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "preflight_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_modify_cors"
        ]
        is True
    )

    assert (
        boundaries[
            "cors_configuration_is_not_authentication"
        ]
        is True
    )

    assert (
        boundaries[
            "cors_configuration_is_not_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "cors_pass_is_not_deployment_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "cors_pass_is_not_trial_authorization"
        ]
        is True
    )


def test_public_preflight_result_does_not_expose_origin_values() -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    result = (
        evaluate_governance_release_environment_security_preflight(
            configuration=configuration
        )
    )

    public_result = (
        result.to_public_dict()
    )

    assert (
        public_result[
            "origin_count"
        ]
        == 2
    )

    for origin in configuration.allow_origins:
        assert (
            origin
            not in repr(
                public_result
            )
        )


@pytest.mark.parametrize(
    "release_environment",
    (
        "development",
        "test",
    ),
)
def test_non_release_configuration_is_rejected(
    release_environment: str,
) -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    release_environment,
            }
        )
    )

    with pytest.raises(
        ValueError,
        match="only prelive and paid_trial",
    ):
        evaluate_governance_release_environment_security_preflight(
            configuration=configuration
        )


def test_non_configuration_input_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="GovernanceReleaseCorsConfiguration",
    ):
        evaluate_governance_release_environment_security_preflight(
            configuration=None,  # type: ignore[arg-type]
        )


def test_input_configuration_is_not_mutated() -> None:
    configuration = (
        build_paid_trial_configuration()
    )

    original = configuration

    evaluate_governance_release_environment_security_preflight(
        configuration=configuration
    )

    assert (
        configuration
        == original
    )