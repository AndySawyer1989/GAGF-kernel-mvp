from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
    ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
    ASSESSMENT_CHECKPOINT_TENANT_ENV,
)
from backend.app.gagf.governance_release_secret_preflight import (
    evaluate_governance_release_secret_preflight,
)


SECRET_VARIABLE = (
    "GAGF_PAID_TRIAL_CHECKPOINT_SECRET"
)


def valid_environment() -> dict[str, str]:
    return {
        ASSESSMENT_CHECKPOINT_TENANT_ENV:
            "tenant-alpha",

        ASSESSMENT_CHECKPOINT_KEY_ID_ENV:
            "checkpoint-key-001",

        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV:
            f"env://{SECRET_VARIABLE}",

        SECRET_VARIABLE:
            "test-signing-secret",
    }


def evaluate(
    tmp_path: Path,
    environment: dict[str, str],
):
    return (
        evaluate_governance_release_secret_preflight(
            release_environment="paid_trial",
            assessment_database_path=(
                tmp_path
                / "governance_assessments.sqlite3"
            ),
            environment=environment,
        )
    )


def test_valid_release_secret_configuration_passes(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path,
        valid_environment(),
    )

    assert result.passed is True

    assert (
        result.signing_configuration_enabled
        is True
    )

    assert (
        result.environment_secret_reference
        is True
    )

    assert (
        result.secret_resolved
        is True
    )

    assert (
        result.failure_reasons
        == ()
    )


def test_missing_signing_configuration_fails(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path,
        {},
    )

    assert result.passed is False

    assert (
        "signing_configuration_required"
        in result.failure_reasons
    )


def test_partial_signing_configuration_fails(
    tmp_path: Path,
) -> None:
    environment = {
        ASSESSMENT_CHECKPOINT_TENANT_ENV:
            "tenant-alpha",

        ASSESSMENT_CHECKPOINT_KEY_ID_ENV:
            "checkpoint-key-001",
    }

    result = evaluate(
        tmp_path,
        environment,
    )

    assert result.passed is False

    assert (
        "signing_configuration_invalid"
        in result.failure_reasons
    )


def test_missing_referenced_secret_fails(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment()
    )

    environment.pop(
        SECRET_VARIABLE
    )

    result = evaluate(
        tmp_path,
        environment,
    )

    assert result.passed is False

    assert (
        "checkpoint_signing_secret_unavailable"
        in result.failure_reasons
    )


def test_empty_referenced_secret_fails(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment()
    )

    environment[
        SECRET_VARIABLE
    ] = ""

    result = evaluate(
        tmp_path,
        environment,
    )

    assert result.passed is False

    assert (
        "checkpoint_signing_secret_unavailable"
        in result.failure_reasons
    )


def test_non_environment_secret_reference_fails(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment()
    )

    environment[
        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV
    ] = (
        "secret://tenant-alpha/key-001"
    )

    result = evaluate(
        tmp_path,
        environment,
    )

    assert result.passed is False

    assert (
        "environment_secret_reference_required"
        in result.failure_reasons
    )

    assert (
        result.secret_resolved
        is False
    )


def test_public_result_exposes_no_secret_material(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment()
    )

    result = evaluate(
        tmp_path,
        environment,
    )

    payload = json.dumps(
        result.to_public_dict(),
        sort_keys=True,
    )

    assert (
        "test-signing-secret"
        not in payload
    )

    assert (
        SECRET_VARIABLE
        not in payload
    )

    assert (
        "checkpoint-key-001"
        not in payload
    )


def test_preflight_does_not_mutate_environment(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment()
    )

    before = dict(
        environment
    )

    evaluate(
        tmp_path,
        environment,
    )

    assert environment == before


def test_preflight_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path,
        valid_environment(),
    )

    boundaries = (
        result.to_public_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "preflight_does_not_return_secret_material"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_create_credentials"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_rotate_keys"
        ]
        is True
    )

    assert (
        boundaries[
            "secret_presence_is_not_credential_validity"
        ]
        is True
    )

    assert (
        boundaries[
            "secret_resolution_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "secret_resolution_is_not_trial_authorization"
        ]
        is True
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "development",
        "test",
        "",
    ),
)
def test_non_release_environment_is_rejected(
    tmp_path: Path,
    release_environment: str,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        evaluate_governance_release_secret_preflight(
            release_environment=(
                release_environment
            ),
            assessment_database_path=(
                tmp_path
                / "governance_assessments.sqlite3"
            ),
            environment=(
                valid_environment()
            ),
        )