from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_DEVELOPMENT,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    RELEASE_ENVIRONMENT_PRELIVE,
    RELEASE_ENVIRONMENT_TEST,
    SUPPORTED_RELEASE_ENVIRONMENTS,
)


GOVERNANCE_RELEASE_CORS_CONFIGURATION_TYPE = (
    "governance-release-cors-configuration"
)

GOVERNANCE_RELEASE_CORS_CONFIGURATION_VERSION = "0.1.0"

GAGF_RELEASE_CORS_ORIGINS_ENV = (
    "GAGF_RELEASE_CORS_ORIGINS"
)

DEFAULT_DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

DEFAULT_TEST_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

REQUIRED_ASSESSMENT_IDENTITY_HEADERS = (
    "X-Tenant-ID",
    "X-Actor-ID",
    "X-Actor-Roles",
)

DEFAULT_ALLOWED_HEADERS = (
    "Accept",
    "Content-Type",
    *REQUIRED_ASSESSMENT_IDENTITY_HEADERS,
)

DEFAULT_ALLOWED_METHODS = (
    "*",
)


class GovernanceReleaseCorsConfigurationError(
    RuntimeError
):
    """Base release-CORS configuration error."""


class GovernanceReleaseCorsEnvironmentError(
    GovernanceReleaseCorsConfigurationError
):
    """Raised when the release environment is invalid."""


class GovernanceReleaseCorsOriginsError(
    GovernanceReleaseCorsConfigurationError
):
    """Raised when configured CORS origins are unsafe or incomplete."""


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseCorsConfiguration:
    release_environment: str
    allow_origins: tuple[str, ...]
    explicit_origins: bool

    allow_credentials: bool = True
    allow_methods: tuple[str, ...] = (
        DEFAULT_ALLOWED_METHODS
    )
    allow_headers: tuple[str, ...] = (
        DEFAULT_ALLOWED_HEADERS
    )

    configuration_type: str = (
        GOVERNANCE_RELEASE_CORS_CONFIGURATION_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_CORS_CONFIGURATION_VERSION
    )

    @property
    def is_development(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_DEVELOPMENT
        )

    @property
    def is_test(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_TEST
        )

    @property
    def is_prelive(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_PRELIVE
        )

    @property
    def is_paid_trial(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_PAID_TRIAL
        )

    @property
    def requires_explicit_origins(
        self,
    ) -> bool:
        return (
            self.is_prelive
            or self.is_paid_trial
        )

    def to_public_status_dict(
        self,
    ) -> dict[str, object]:
        """
        Return operator-safe CORS configuration metadata.

        Origin values are intentionally excluded.
        """

        return {
            "configuration_type":
                self.configuration_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "explicit_origins":
                self.explicit_origins,

            "origin_count":
                len(
                    self.allow_origins
                ),

            "allow_credentials":
                self.allow_credentials,

            "assessment_identity_headers_allowed":
                _assessment_identity_headers_allowed(
                    self.allow_headers
                ),

            "wildcard_origin_absent":
                (
                    "*"
                    not in self.allow_origins
                ),

            "origin_values_exposed":
                False,

            "configuration_grants_deployment_authority":
                False,

            "configuration_grants_trial_authority":
                False,
        }


def load_governance_release_cors_configuration(
    *,
    environment: Mapping[str, str] | None = None,
) -> GovernanceReleaseCorsConfiguration:
    resolved_environment = (
        environment
        if environment is not None
        else os.environ
    )

    release_environment = (
        _resolve_release_environment(
            resolved_environment
        )
    )

    raw_origins = (
        resolved_environment.get(
            GAGF_RELEASE_CORS_ORIGINS_ENV
        )
    )

    explicit_origins = (
        isinstance(
            raw_origins,
            str,
        )
        and bool(
            raw_origins.strip()
        )
    )

    if explicit_origins:
        allow_origins = (
            _parse_explicit_origins(
                raw_origins
            )
        )

    elif (
        release_environment
        == RELEASE_ENVIRONMENT_DEVELOPMENT
    ):
        allow_origins = (
            DEFAULT_DEVELOPMENT_CORS_ORIGINS
        )

    elif (
        release_environment
        == RELEASE_ENVIRONMENT_TEST
    ):
        allow_origins = (
            DEFAULT_TEST_CORS_ORIGINS
        )

    else:
        raise GovernanceReleaseCorsOriginsError(
            "prelive and paid_trial require explicit "
            f"{GAGF_RELEASE_CORS_ORIGINS_ENV}"
        )

    return GovernanceReleaseCorsConfiguration(
        release_environment=(
            release_environment
        ),
        allow_origins=(
            allow_origins
        ),
        explicit_origins=(
            explicit_origins
        ),
    )


def _resolve_release_environment(
    environment: Mapping[str, str],
) -> str:
    raw_environment = (
        environment.get(
            GAGF_RELEASE_ENVIRONMENT_ENV
        )
    )

    if raw_environment is None:
        return (
            RELEASE_ENVIRONMENT_DEVELOPMENT
        )

    if not isinstance(
        raw_environment,
        str,
    ):
        raise GovernanceReleaseCorsEnvironmentError(
            f"{GAGF_RELEASE_ENVIRONMENT_ENV} "
            "must be a string"
        )

    normalized_environment = (
        raw_environment
        .strip()
        .lower()
    )

    if not normalized_environment:
        raise GovernanceReleaseCorsEnvironmentError(
            f"{GAGF_RELEASE_ENVIRONMENT_ENV} "
            "must not be blank"
        )

    if (
        normalized_environment
        not in SUPPORTED_RELEASE_ENVIRONMENTS
    ):
        raise GovernanceReleaseCorsEnvironmentError(
            "unsupported release environment: "
            f"{normalized_environment}"
        )

    return normalized_environment


def _parse_explicit_origins(
    raw_origins: str,
) -> tuple[str, ...]:
    raw_parts = (
        raw_origins.split(",")
    )

    if not raw_parts:
        raise GovernanceReleaseCorsOriginsError(
            "CORS origins must not be empty"
        )

    normalized_origins: list[str] = []

    for raw_origin in raw_parts:
        origin = (
            raw_origin.strip()
        )

        if not origin:
            raise GovernanceReleaseCorsOriginsError(
                "CORS origin entries must not be blank"
            )

        if origin == "*":
            raise GovernanceReleaseCorsOriginsError(
                "wildcard CORS origins are forbidden"
            )

        _validate_origin(
            origin
        )

        if (
            origin
            not in normalized_origins
        ):
            normalized_origins.append(
                origin
            )

    if not normalized_origins:
        raise GovernanceReleaseCorsOriginsError(
            "at least one explicit CORS origin is required"
        )

    return tuple(
        normalized_origins
    )


def _validate_origin(
    origin: str,
) -> None:
    parsed = (
        urlsplit(
            origin
        )
    )

    if (
        parsed.scheme
        not in {
            "http",
            "https",
        }
    ):
        raise GovernanceReleaseCorsOriginsError(
            "CORS origins must use http or https"
        )

    if not parsed.netloc:
        raise GovernanceReleaseCorsOriginsError(
            "CORS origins must include a host"
        )

    if (
        parsed.path
        not in {
            "",
            "/",
        }
    ):
        raise GovernanceReleaseCorsOriginsError(
            "CORS origins must not include a path"
        )

    if (
        parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise GovernanceReleaseCorsOriginsError(
            "CORS origins must contain only scheme, host, and optional port"
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