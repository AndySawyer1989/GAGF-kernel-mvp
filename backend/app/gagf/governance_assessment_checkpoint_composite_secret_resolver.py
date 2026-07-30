from __future__ import annotations

from collections.abc import Sequence

from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    AssessmentCheckpointSecretResolver,
)


ASSESSMENT_CHECKPOINT_COMPOSITE_RESOLVER_VERSION = "1.0.0"


class CompositeAssessmentCheckpointSecretResolver:
    def __init__(
        self,
        *,
        resolvers: Sequence[
            AssessmentCheckpointSecretResolver
        ],
    ) -> None:
        self._resolvers = tuple(resolvers)

        if not self._resolvers:
            raise ValueError(
                "at least one checkpoint secret resolver is required"
            )

    def resolve_secret(
        self,
        *,
        secret_reference: str,
    ) -> bytes:
        failures: list[Exception] = []

        for resolver in self._resolvers:
            try:
                return resolver.resolve_secret(
                    secret_reference=secret_reference
                )
            except (KeyError, ValueError) as error:
                failures.append(error)

        raise KeyError(
            "checkpoint signing secret could not be resolved"
        ) from failures[-1]
