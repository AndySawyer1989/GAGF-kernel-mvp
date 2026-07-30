import pytest

from backend.app.gagf.governance_assessment_checkpoint_composite_secret_resolver import (
    CompositeAssessmentCheckpointSecretResolver,
)
from backend.app.gagf.governance_assessment_checkpoint_environment_secret_resolver import (
    EnvironmentAssessmentCheckpointSecretResolver,
)
from backend.app.gagf.governance_assessment_checkpoint_secret_resolver import (
    InMemoryAssessmentCheckpointSecretResolver,
)


def test_environment_secret_is_resolved():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={
            "GAGF_CHECKPOINT_KEY": "private-secret"
        }
    )

    secret = resolver.resolve_secret(
        secret_reference="env://GAGF_CHECKPOINT_KEY"
    )

    assert secret == b"private-secret"


def test_environment_reference_is_trimmed():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={
            "GAGF_CHECKPOINT_KEY": "private-secret"
        }
    )

    secret = resolver.resolve_secret(
        secret_reference="  env://GAGF_CHECKPOINT_KEY  "
    )

    assert secret == b"private-secret"


def test_missing_environment_variable_is_rejected():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={}
    )

    with pytest.raises(
        KeyError,
        match="signing secret was not found",
    ):
        resolver.resolve_secret(
            secret_reference="env://MISSING_KEY"
        )


def test_empty_environment_secret_is_rejected():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={"EMPTY_KEY": ""}
    )

    with pytest.raises(
        ValueError,
        match="signing secret is empty",
    ):
        resolver.resolve_secret(
            secret_reference="env://EMPTY_KEY"
        )


def test_unsupported_reference_scheme_is_rejected():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={}
    )

    with pytest.raises(
        ValueError,
        match="unsupported checkpoint secret reference scheme",
    ):
        resolver.resolve_secret(
            secret_reference="vault://checkpoint-key"
        )


def test_missing_variable_name_is_rejected():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={}
    )

    with pytest.raises(
        ValueError,
        match="environment variable name is required",
    ):
        resolver.resolve_secret(
            secret_reference="env://"
        )


def test_error_does_not_expose_environment_values():
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment={
            "OTHER_KEY": "do-not-expose-this"
        }
    )

    try:
        resolver.resolve_secret(
            secret_reference="env://MISSING_KEY"
        )
    except KeyError as error:
        assert "do-not-expose-this" not in str(error)
    else:
        raise AssertionError("missing secret was accepted")


def test_composite_resolver_uses_environment_provider():
    memory = InMemoryAssessmentCheckpointSecretResolver()
    environment = EnvironmentAssessmentCheckpointSecretResolver(
        environment={
            "GAGF_CHECKPOINT_KEY": "environment-secret"
        }
    )
    resolver = CompositeAssessmentCheckpointSecretResolver(
        resolvers=(memory, environment)
    )

    secret = resolver.resolve_secret(
        secret_reference="env://GAGF_CHECKPOINT_KEY"
    )

    assert secret == b"environment-secret"


def test_composite_resolver_uses_in_memory_provider():
    memory = InMemoryAssessmentCheckpointSecretResolver()
    memory.register_secret(
        secret_reference="secret://tenant-alpha/key-001",
        secret=b"memory-secret",
    )
    environment = EnvironmentAssessmentCheckpointSecretResolver(
        environment={}
    )
    resolver = CompositeAssessmentCheckpointSecretResolver(
        resolvers=(environment, memory)
    )

    secret = resolver.resolve_secret(
        secret_reference="secret://tenant-alpha/key-001"
    )

    assert secret == b"memory-secret"


def test_composite_resolver_rejects_unresolved_reference():
    resolver = CompositeAssessmentCheckpointSecretResolver(
        resolvers=(
            EnvironmentAssessmentCheckpointSecretResolver(
                environment={}
            ),
            InMemoryAssessmentCheckpointSecretResolver(),
        )
    )

    with pytest.raises(
        KeyError,
        match="could not be resolved",
    ):
        resolver.resolve_secret(
            secret_reference="env://MISSING_KEY"
        )


def test_composite_resolver_requires_provider():
    with pytest.raises(
        ValueError,
        match="at least one checkpoint secret resolver",
    ):
        CompositeAssessmentCheckpointSecretResolver(
            resolvers=()
        )
