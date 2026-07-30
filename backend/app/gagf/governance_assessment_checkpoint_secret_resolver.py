from __future__ import annotations

from typing import Protocol


ASSESSMENT_CHECKPOINT_SECRET_RESOLVER_VERSION = "1.0.0"


class AssessmentCheckpointSecretResolver(Protocol):
    def resolve_secret(
        self,
        *,
        secret_reference: str,
    ) -> bytes:
        ...


class InMemoryAssessmentCheckpointSecretResolver:
    def __init__(
        self,
        secrets: dict[str, bytes] | None = None,
    ) -> None:
        self._secrets = dict(secrets or {})

    def register_secret(
        self,
        *,
        secret_reference: str,
        secret: bytes,
    ) -> None:
        normalized_reference = secret_reference.strip()

        if not normalized_reference:
            raise ValueError("secret_reference is required")

        if not secret:
            raise ValueError("signing secret is required")

        if normalized_reference in self._secrets:
            raise ValueError(
                "checkpoint signing secret reference already exists"
            )

        self._secrets[normalized_reference] = secret

    def resolve_secret(
        self,
        *,
        secret_reference: str,
    ) -> bytes:
        try:
            return self._secrets[secret_reference]
        except KeyError as error:
            raise KeyError(
                "checkpoint signing secret was not found"
            ) from error
