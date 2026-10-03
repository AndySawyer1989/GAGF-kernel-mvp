from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
    ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
    ASSESSMENT_CHECKPOINT_TENANT_ENV,
)
from backend.app.gagf.governance_release_secret_redaction_proof import (
    GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_TYPE,
    GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_VERSION,
    evaluate_governance_release_secret_redaction_proof,
)


SECRET_VARIABLE = (
    "GAGF_04K04E_REDACTION_SECRET"
)

TENANT_IDENTIFIER = (
    "tenant-04k04e-sensitive-7f31"
)

KEY_IDENTIFIER = (
    "key-04k04e-sensitive-9a52"
)

SECRET_VALUE = (
    "secret-04k04e-sensitive-b84d"
)

SECRET_REFERENCE = (
    f"env://{SECRET_VARIABLE}"
)


def valid_environment(
) -> dict[str, str]:
    return {
        ASSESSMENT_CHECKPOINT_TENANT_ENV:
            TENANT_IDENTIFIER,

        ASSESSMENT_CHECKPOINT_KEY_ID_ENV:
            KEY_IDENTIFIER,

        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV:
            SECRET_REFERENCE,

        SECRET_VARIABLE:
            SECRET_VALUE,
    }


def evaluate(
    tmp_path: Path,
    *,
    release_environment: str = "paid_trial",
    environment: dict[str, str] | None = None,
):
    return (
        evaluate_governance_release_secret_redaction_proof(
            release_environment=release_environment,
            assessment_database_path=(
                tmp_path
                / "governance_assessments.sqlite3"
            ),
            environment=(
                valid_environment()
                if environment is None
                else environment
            ),
        )
    )


def test_valid_paid_trial_redaction_proof_passes(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path
    )

    assert result.passed is True

    assert (
        result.failure_reasons
        == ()
    )

    assert (
        result.public_status_available
        is True
    )

    assert (
        result.redaction_verified
        is True
    )


def test_prelive_uses_same_redaction_proof(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path,
        release_environment="prelive",
    )

    assert result.passed is True

    assert (
        result.release_environment
        == "prelive"
    )

    assert (
        result.redaction_verified
        is True
    )


def test_each_sensitive_source_value_is_redacted(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path
    )

    assert (
        result.secret_value_redacted
        is True
    )

    assert (
        result.secret_variable_name_redacted
        is True
    )

    assert (
        result.secret_reference_redacted
        is True
    )

    assert (
        result.tenant_identifier_redacted
        is True
    )

    assert (
        result.key_identifier_redacted
        is True
    )


def test_public_result_contains_no_sensitive_source_material(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path
    )

    payload = json.dumps(
        result.to_public_dict(),
        sort_keys=True,
    )

    for sensitive_value in (
        TENANT_IDENTIFIER,
        KEY_IDENTIFIER,
        SECRET_VARIABLE,
        SECRET_REFERENCE,
        SECRET_VALUE,
    ):
        assert (
            sensitive_value
            not in payload
        )


def test_public_result_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path
    )

    public = (
        result.to_public_dict()
    )

    assert (
        public["proof_type"]
        == GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_TYPE
    )

    assert (
        public["version"]
        == GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_VERSION
    )

    boundaries = (
        public[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "proof_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_uses_existing_secret_preflight"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_return_secret_material"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_return_secret_reference"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_return_secret_variable_name"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_return_signing_tenant_identifier"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_return_signing_key_identifier"
        ]
        is True
    )

    assert (
        boundaries[
            "redaction_proof_is_not_credential_validity"
        ]
        is True
    )

    assert (
        boundaries[
            "redaction_proof_is_not_deployment_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "redaction_proof_is_not_trial_authorization"
        ]
        is True
    )


def test_redaction_proof_does_not_mutate_environment(
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
        environment=environment,
    )

    assert (
        environment
        == before
    )


def test_distinct_adversarial_values_remain_absent(
    tmp_path: Path,
) -> None:
    environment = {
        ASSESSMENT_CHECKPOINT_TENANT_ENV:
            "TENANT_VALUE_9D731C",

        ASSESSMENT_CHECKPOINT_KEY_ID_ENV:
            "KEY_VALUE_3A825E",

        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV:
            "env://SECRET_VARIABLE_7F416B",

        "SECRET_VARIABLE_7F416B":
            "SECRET_VALUE_5C902D",
    }

    result = evaluate(
        tmp_path,
        environment=environment,
    )

    payload = json.dumps(
        result.to_public_dict(),
        sort_keys=True,
    )

    for sensitive_value in (
        "TENANT_VALUE_9D731C",
        "KEY_VALUE_3A825E",
        "env://SECRET_VARIABLE_7F416B",
        "SECRET_VARIABLE_7F416B",
        "SECRET_VALUE_5C902D",
    ):
        assert (
            sensitive_value
            not in payload
        )

    assert (
        result.redaction_verified
        is True
    )

    assert (
        result.passed
        is True
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "",
        "development",
        "test",
    ),
)
def test_non_release_environment_is_rejected(
    tmp_path: Path,
    release_environment: str,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        evaluate_governance_release_secret_redaction_proof(
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