from __future__ import annotations

import os
from collections.abc import Mapping


ASSESSMENT_CHECKPOINT_ENVIRONMENT_RESOLVER_VERSION = "1.0.0"
ASSESSMENT_CHECKPOINT_ENVIRONMENT_SCHEME = "env://"


class EnvironmentAssessmentCheckpointSecretResolver:
    def __init__(
        self,
        *,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._environment = (
            environment
            if environment is not None
            else os.environ
        )

    def resolve_secret(
        self,
        *,
        secret_reference: str,
    ) -> bytes:
        normalized_reference = secret_reference.strip()

        if not normalized_reference.startswith(
            ASSESSMENT_CHECKPOINT_ENVIRONMENT_SCHEME
        ):
            raise ValueError(
                "unsupported checkpoint secret reference scheme"
            )

        variable_name = normalized_reference.removeprefix(
            ASSESSMENT_CHECKPOINT_ENVIRONMENT_SCHEME
        ).strip()

        if not variable_name:
            raise ValueError(
                "checkpoint environment variable name is required"
            )

        value = self._environment.get(variable_name)

        if value is None:
            raise KeyError(
                "checkpoint signing secret was not found"
            )

        if not value:
            raise ValueError(
                "checkpoint signing secret is empty"
            )

        return value.encode("utf-8")
