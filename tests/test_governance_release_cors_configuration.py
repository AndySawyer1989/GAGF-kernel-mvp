from __future__ import annotations

import pytest

from backend.app.gagf.governance_release_cors_configuration import (
    DEFAULT_ALLOWED_HEADERS,
    DEFAULT_DEVELOPMENT_CORS_ORIGINS,
    DEFAULT_TEST_CORS_ORIGINS,
    GAGF_RELEASE_CORS_ORIGINS_ENV,
    GovernanceReleaseCorsEnvironmentError,
    GovernanceReleaseCorsOriginsError,
    load_governance_release_cors_configuration,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_ENVIRONMENT_ENV,
)


def test_development_uses_localhost_defaults_when_origins_absent() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "development",
            }
        )
    )

    assert (
        configuration.release_environment
        == "development"
    )
    assert (
        configuration.allow_origins
        == DEFAULT_DEVELOPMENT_CORS_ORIGINS
    )
    assert configuration.explicit_origins is False
    assert configuration.allow_credentials is True


def test_missing_release_environment_defaults_to_development() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={}
        )
    )

    assert (
        configuration.release_environment
        == "development"
    )
    assert (
        configuration.allow_origins
        == DEFAULT_DEVELOPMENT_CORS_ORIGINS
    )
    assert configuration.explicit_origins is False


def test_test_environment_uses_localhost_defaults_when_origins_absent() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "test",
            }
        )
    )

    assert (
        configuration.release_environment
        == "test"
    )
    assert (
        configuration.allow_origins
        == DEFAULT_TEST_CORS_ORIGINS
    )
    assert configuration.explicit_origins is False


@pytest.mark.parametrize(
    "release_environment",
    (
        "prelive",
        "paid_trial",
    ),
)
def test_release_environments_require_explicit_origins(
    release_environment: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError,
        match="require explicit",
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    release_environment,
            }
        )


@pytest.mark.parametrize(
    "release_environment",
    (
        "prelive",
        "paid_trial",
    ),
)
def test_release_environments_accept_explicit_origins(
    release_environment: str,
) -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    release_environment,

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    (
                        "https://operator.example.com,"
                        "https://customer.example.com"
                    ),
            }
        )
    )

    assert (
        configuration.release_environment
        == release_environment
    )
    assert (
        configuration.allow_origins
        == (
            "https://operator.example.com",
            "https://customer.example.com",
        )
    )
    assert configuration.explicit_origins is True


def test_explicit_origin_whitespace_is_normalized() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    (
                        "  https://operator.example.com  , "
                        "https://customer.example.com "
                    ),
            }
        )
    )

    assert (
        configuration.allow_origins
        == (
            "https://operator.example.com",
            "https://customer.example.com",
        )
    )


def test_duplicate_origins_are_removed_preserving_order() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    (
                        "https://operator.example.com,"
                        "https://customer.example.com,"
                        "https://operator.example.com"
                    ),
            }
        )
    )

    assert (
        configuration.allow_origins
        == (
            "https://operator.example.com",
            "https://customer.example.com",
        )
    )


def test_wildcard_origin_is_rejected() -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError,
        match="wildcard",
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    "*",
            }
        )


def test_wildcard_mixed_with_explicit_origin_is_rejected() -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError,
        match="wildcard",
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    (
                        "https://operator.example.com,*"
                    ),
            }
        )


@pytest.mark.parametrize(
    "raw_origins",
    (
        "https://operator.example.com,",
        ",https://operator.example.com",
        "https://operator.example.com,,https://customer.example.com",
    ),
)
def test_blank_origin_entry_is_rejected(
    raw_origins: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError,
        match="must not be blank",
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    raw_origins,
            }
        )


@pytest.mark.parametrize(
    "origin",
    (
        "ftp://operator.example.com",
        "operator.example.com",
        "file:///tmp/example",
    ),
)
def test_invalid_origin_scheme_or_host_is_rejected(
    origin: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    origin,
            }
        )


@pytest.mark.parametrize(
    "origin",
    (
        "https://operator.example.com/api",
        "https://operator.example.com/path/",
    ),
)
def test_origin_path_is_rejected(
    origin: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError,
        match="must not include a path",
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    origin,
            }
        )


@pytest.mark.parametrize(
    "origin",
    (
        "https://operator.example.com?tenant=one",
        "https://operator.example.com#fragment",
        "https://user@operator.example.com",
        "https://user:password@operator.example.com",
    ),
)
def test_origin_query_fragment_or_credentials_are_rejected(
    origin: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseCorsOriginsError,
        match="scheme, host, and optional port",
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    origin,
            }
        )


def test_origin_with_port_is_allowed() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "prelive",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    "https://prelive.example.com:8443",
            }
        )
    )

    assert (
        configuration.allow_origins
        == (
            "https://prelive.example.com:8443",
        )
    )


def test_required_assessment_identity_headers_are_present() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "development",
            }
        )
    )

    normalized_headers = {
        header.lower()
        for header
        in configuration.allow_headers
    }

    assert "x-tenant-id" in normalized_headers
    assert "x-actor-id" in normalized_headers
    assert "x-actor-roles" in normalized_headers

    assert (
        configuration.allow_headers
        == DEFAULT_ALLOWED_HEADERS
    )


def test_public_status_does_not_expose_origin_values() -> None:
    secret_customer_origin = (
        "https://private-customer.example.com"
    )

    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    secret_customer_origin,
            }
        )
    )

    public_status = (
        configuration.to_public_status_dict()
    )

    assert (
        public_status["release_environment"]
        == "paid_trial"
    )
    assert public_status["explicit_origins"] is True
    assert public_status["origin_count"] == 1
    assert (
        public_status["wildcard_origin_absent"]
        is True
    )
    assert (
        public_status[
            "assessment_identity_headers_allowed"
        ]
        is True
    )
    assert (
        public_status["origin_values_exposed"]
        is False
    )
    assert (
        public_status[
            "configuration_grants_deployment_authority"
        ]
        is False
    )
    assert (
        public_status[
            "configuration_grants_trial_authority"
        ]
        is False
    )

    assert (
        secret_customer_origin
        not in repr(
            public_status
        )
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "",
        "   ",
        "production",
        "production-ish",
        "customer",
    ),
)
def test_invalid_release_environment_is_rejected(
    release_environment: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseCorsEnvironmentError
    ):
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    release_environment,

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    "https://operator.example.com",
            }
        )


def test_release_environment_is_normalized() -> None:
    configuration = (
        load_governance_release_cors_configuration(
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "  PAID_TRIAL  ",

                GAGF_RELEASE_CORS_ORIGINS_ENV:
                    "https://operator.example.com",
            }
        )
    )

    assert (
        configuration.release_environment
        == "paid_trial"
    )


def test_input_environment_mapping_is_not_mutated() -> None:
    environment = {
        GAGF_RELEASE_ENVIRONMENT_ENV:
            "paid_trial",

        GAGF_RELEASE_CORS_ORIGINS_ENV:
            "https://operator.example.com",
    }

    original_environment = dict(
        environment
    )

    load_governance_release_cors_configuration(
        environment=environment
    )

    assert (
        environment
        == original_environment
    )