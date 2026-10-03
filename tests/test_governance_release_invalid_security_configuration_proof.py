from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.gagf.governance_release_invalid_security_configuration_proof import (
    FAILURE_SCENARIOS,
    GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_TYPE,
    GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_VERSION,
    evaluate_governance_release_invalid_security_configuration_proof,
)


SECRET_VARIABLE = (
    "GAGF_04K04F_TEST_SECRET"
)


def valid_environment(
    tmp_path: Path,
) -> dict[str, str]:
    return {
        "GAGF_RELEASE_ENVIRONMENT":
            "paid_trial",

        "GAGF_RELEASE_DATA_ROOT":
            str(
                (
                    tmp_path
                    / "release-data"
                ).resolve()
            ),

        "GAGF_RELEASE_CORS_ORIGINS":
            "https://operator.example.com",

        "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID":
            "tenant-04k04f",

        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID":
            "key-04k04f",

        "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE":
            f"env://{SECRET_VARIABLE}",

        SECRET_VARIABLE:
            "secret-04k04f-value",
    }


def evaluate(
    tmp_path: Path,
    *,
    release_environment: str = "paid_trial",
    environment: dict[str, str] | None = None,
):
    selected_environment = (
        valid_environment(
            tmp_path
        )
        if environment is None
        else environment
    )

    return (
        evaluate_governance_release_invalid_security_configuration_proof(
            release_environment=(
                release_environment
            ),
            application_data_root=(
                tmp_path
                / "application-data"
            ),
            assessment_database_path=(
                tmp_path
                / "governance_assessments.sqlite3"
            ),
            environment=(
                selected_environment
            ),
        )
    )


def test_all_invalid_security_scenarios_are_rejected(
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
        result.scenario_count
        == 7
    )

    assert (
        result.rejected_scenario_count
        == 7
    )

    assert (
        result.all_invalid_configurations_rejected
        is True
    )


def test_failure_scenario_contract_is_exact(
) -> None:
    assert (
        FAILURE_SCENARIOS
        == (
            "unsupported_release_environment",
            "missing_release_data_root",
            "missing_cors_origins",
            "wildcard_cors_origin",
            "partial_signing_configuration",
            "missing_signing_secret",
            "invalid_secret_reference",
        )
    )


def test_every_scenario_reports_rejection_authority(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path
    )

    for scenario in result.scenarios:
        assert (
            scenario.rejected
            is True
        )

        assert (
            scenario.rejection_authority
            in {
                "release_storage_configuration",
                "release_cors_configuration",
                "release_secret_preflight",
            }
        )

        assert (
            scenario.failure_code
            != "invalid_configuration_was_not_rejected"
        )


def test_expected_failure_codes_are_preserved(
    tmp_path: Path,
) -> None:
    result = evaluate(
        tmp_path
    )

    by_scenario = {
        item.scenario:
            item.failure_code
        for item
        in result.scenarios
    }

    assert (
        by_scenario[
            "unsupported_release_environment"
        ]
        == "unsupported_release_environment"
    )

    assert (
        by_scenario[
            "missing_release_data_root"
        ]
        == "explicit_release_data_root_required"
    )

    assert (
        by_scenario[
            "missing_cors_origins"
        ]
        == "explicit_cors_origins_required"
    )

    assert (
        by_scenario[
            "wildcard_cors_origin"
        ]
        == "wildcard_cors_origin_forbidden"
    )

    assert (
        by_scenario[
            "partial_signing_configuration"
        ]
        == "signing_configuration_invalid"
    )

    assert (
        by_scenario[
            "missing_signing_secret"
        ]
        == "checkpoint_signing_secret_unavailable"
    )

    assert (
        by_scenario[
            "invalid_secret_reference"
        ]
        == "environment_secret_reference_required"
    )


def test_prelive_uses_same_failure_proof(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment(
            tmp_path
        )
    )

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "prelive"

    result = evaluate(
        tmp_path,
        release_environment="prelive",
        environment=environment,
    )

    assert (
        result.release_environment
        == "prelive"
    )

    assert result.passed is True

    assert (
        result.rejected_scenario_count
        == 7
    )


def test_failure_proof_does_not_mutate_environment(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment(
            tmp_path
        )
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


def test_public_result_exposes_no_secret_material(
    tmp_path: Path,
) -> None:
    environment = (
        valid_environment(
            tmp_path
        )
    )

    result = evaluate(
        tmp_path,
        environment=environment,
    )

    payload = json.dumps(
        result.to_public_dict(),
        sort_keys=True,
    )

    sensitive_values = (
        "tenant-04k04f",
        "key-04k04f",
        SECRET_VARIABLE,
        f"env://{SECRET_VARIABLE}",
        "secret-04k04f-value",
    )

    for value in sensitive_values:
        assert (
            value
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
        == GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_TYPE
    )

    assert (
        public["version"]
        == GOVERNANCE_RELEASE_INVALID_SECURITY_CONFIGURATION_PROOF_VERSION
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
            "proof_uses_existing_validation_authorities"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_weaken_fail_closed_behavior"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_create_credentials"
        ]
        is True
    )

    assert (
        boundaries[
            "proof_does_not_modify_runtime_configuration"
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
            "failure_proof_is_not_deployment_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "failure_proof_is_not_trial_authorization"
        ]
        is True
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "",
        "development",
        "test",
        "production",
    ),
)
def test_failure_proof_rejects_unsupported_proof_environment(
    tmp_path: Path,
    release_environment: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "invalid security configuration proof supports "
            "only prelive and paid_trial"
        ),
    ):
        evaluate_governance_release_invalid_security_configuration_proof(
            release_environment=(
                release_environment
            ),
            application_data_root=(
                tmp_path
                / "application-data"
            ),
            assessment_database_path=(
                tmp_path
                / "governance_assessments.sqlite3"
            ),
            environment=(
                valid_environment(
                    tmp_path
                )
            ),
        )