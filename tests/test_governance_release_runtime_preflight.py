from pathlib import Path

import pytest

from backend.app.gagf.governance_release_runtime_preflight import (
    evaluate_governance_release_runtime_preflight,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    GovernanceReleaseDataRootError,
)


def test_paid_trial_runtime_preflight_passes(
    tmp_path: Path,
) -> None:
    root = (
        tmp_path
        / "release"
    ).resolve()

    result = (
        evaluate_governance_release_runtime_preflight(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        root
                    ),
            },
        )
    )

    assert result.passed is True

    assert (
        result.release_environment
        == "paid_trial"
    )

    assert (
        result.effective_data_root
        == root
        / "paid_trial"
    )

    assert all(
        result.checks.values()
    )


def test_prelive_does_not_pass_paid_trial_preflight(
    tmp_path: Path,
) -> None:
    root = (
        tmp_path
        / "release"
    ).resolve()

    result = (
        evaluate_governance_release_runtime_preflight(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "prelive",

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        root
                    ),
            },
        )
    )

    assert result.passed is False

    assert (
        "paid_trial_environment"
        in result.failure_reasons
    )


def test_paid_trial_missing_data_root_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GovernanceReleaseDataRootError,
        match=(
            "paid_trial requires "
            "GAGF_RELEASE_DATA_ROOT"
        ),
    ):
        evaluate_governance_release_runtime_preflight(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",
            },
        )


def test_runtime_preflight_does_not_create_storage(
    tmp_path: Path,
) -> None:
    root = (
        tmp_path
        / "release"
    ).resolve()

    effective_root = (
        root
        / "paid_trial"
    )

    assert (
        effective_root.exists()
        is False
    )

    evaluate_governance_release_runtime_preflight(
        application_data_root=(
            tmp_path
            / "development"
        ),
        environment={
            GAGF_RELEASE_ENVIRONMENT_ENV:
                "paid_trial",

            GAGF_RELEASE_DATA_ROOT_ENV:
                str(
                    root
                ),
        },
    )

    assert (
        effective_root.exists()
        is False
    )


def test_runtime_preflight_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    root = (
        tmp_path
        / "release"
    ).resolve()

    result = (
        evaluate_governance_release_runtime_preflight(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    "paid_trial",

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        root
                    ),
            },
        )
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "preflight_is_not_process_start"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_mutate_storage"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_bind_network_port"
        ]
        is True
    )