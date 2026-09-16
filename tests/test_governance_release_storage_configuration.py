from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_DEVELOPMENT,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    RELEASE_ENVIRONMENT_PRELIVE,
    RELEASE_ENVIRONMENT_TEST,
    GovernanceReleaseDataRootError,
    GovernanceReleaseEnvironmentError,
    load_governance_release_storage_configuration,
)


def test_default_configuration_preserves_development_fallback(
    tmp_path: Path,
) -> None:
    default_root = (
        tmp_path
        / "backend"
        / "app"
        / "data"
    )

    config = (
        load_governance_release_storage_configuration(
            application_data_root=(
                default_root
            ),
            environment={},
        )
    )

    assert (
        config.release_environment
        == RELEASE_ENVIRONMENT_DEVELOPMENT
    )

    assert (
        config.data_root
        == default_root
    )

    assert (
        config.explicit_data_root
        is False
    )

    assert config.is_development is True
    assert config.is_paid_trial is False


def test_test_environment_may_use_injected_root(
    tmp_path: Path,
) -> None:
    test_root = (
        tmp_path
        / "test-data"
    )

    config = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "default"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_TEST,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        test_root
                    ),
            },
        )
    )

    assert config.is_test is True

    assert (
        config.data_root
        == test_root
    )

    assert (
        config.explicit_data_root
        is True
    )


def test_prelive_requires_explicit_data_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GovernanceReleaseDataRootError,
        match="prelive requires GAGF_RELEASE_DATA_ROOT",
    ):
        (
            load_governance_release_storage_configuration(
                application_data_root=(
                    tmp_path
                    / "default"
                ),
                environment={
                    GAGF_RELEASE_ENVIRONMENT_ENV:
                        RELEASE_ENVIRONMENT_PRELIVE,
                },
            )
        )


def test_paid_trial_requires_explicit_data_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GovernanceReleaseDataRootError,
        match="paid_trial requires GAGF_RELEASE_DATA_ROOT",
    ):
        (
            load_governance_release_storage_configuration(
                application_data_root=(
                    tmp_path
                    / "default"
                ),
                environment={
                    GAGF_RELEASE_ENVIRONMENT_ENV:
                        RELEASE_ENVIRONMENT_PAID_TRIAL,
                },
            )
        )


def test_prelive_requires_absolute_data_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GovernanceReleaseDataRootError,
        match="absolute",
    ):
        (
            load_governance_release_storage_configuration(
                application_data_root=(
                    tmp_path
                    / "default"
                ),
                environment={
                    GAGF_RELEASE_ENVIRONMENT_ENV:
                        RELEASE_ENVIRONMENT_PRELIVE,

                    GAGF_RELEASE_DATA_ROOT_ENV:
                        "relative/prelive-data",
                },
            )
        )


def test_paid_trial_requires_absolute_data_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GovernanceReleaseDataRootError,
        match="absolute",
    ):
        (
            load_governance_release_storage_configuration(
                application_data_root=(
                    tmp_path
                    / "default"
                ),
                environment={
                    GAGF_RELEASE_ENVIRONMENT_ENV:
                        RELEASE_ENVIRONMENT_PAID_TRIAL,

                    GAGF_RELEASE_DATA_ROOT_ENV:
                        "relative/paid-trial-data",
                },
            )
        )


def test_unknown_environment_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GovernanceReleaseEnvironmentError,
        match="unsupported",
    ):
        (
            load_governance_release_storage_configuration(
                application_data_root=(
                    tmp_path
                    / "default"
                ),
                environment={
                    GAGF_RELEASE_ENVIRONMENT_ENV:
                        "production-ish",
                },
            )
        )


def test_paid_trial_resolves_absolute_isolated_paths(
    tmp_path: Path,
) -> None:
    root = (
        tmp_path
        / "paid-trial"
    ).resolve()

    config = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "default"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_PAID_TRIAL,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        root
                    ),
            },
        )
    )

    assert config.is_paid_trial is True

    assert (
        config.effective_data_root
        == root
        / "paid_trial"
    )

    assert (
        config.assessment_database_path
        == root
        / "paid_trial"
        / "governance_assessments.sqlite3"
    )

    assert (
        config.controlled_trial_root
        == root
        / "paid_trial"
        / "controlled_trial"
    )

    assert (
        config.customer_trial_preflight_database_path
        == root
        / "paid_trial"
        / "controlled_trial"
        / "preflight.sqlite3"
    )

    assert (
        config.customer_trial_execution_handoff_database_path
        == root
        / "paid_trial"
        / "controlled_trial"
        / "execution_handoff.sqlite3"
    )

    assert (
        config.customer_trial_administrative_closeout_observation_database_path
        == root
        / "paid_trial"
        / "controlled_trial"
        / "administrative_closeout_observation.sqlite3"
    )


def test_environment_storage_roots_can_be_isolated(
    tmp_path: Path,
) -> None:
    development_root = (
        tmp_path
        / "development"
    ).resolve()

    test_root = (
        tmp_path
        / "test"
    ).resolve()

    prelive_root = (
        tmp_path
        / "prelive"
    ).resolve()

    paid_trial_root = (
        tmp_path
        / "paid-trial"
    ).resolve()

    development = (
        load_governance_release_storage_configuration(
            application_data_root=(
                development_root
            ),
            environment={},
        )
    )

    test = (
        load_governance_release_storage_configuration(
            application_data_root=(
                development_root
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_TEST,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        test_root
                    ),
            },
        )
    )

    prelive = (
        load_governance_release_storage_configuration(
            application_data_root=(
                development_root
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_PRELIVE,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        prelive_root
                    ),
            },
        )
    )

    paid_trial = (
        load_governance_release_storage_configuration(
            application_data_root=(
                development_root
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_PAID_TRIAL,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        paid_trial_root
                    ),
            },
        )
    )

    roots = {
        development.data_root,
        test.data_root,
        prelive.data_root,
        paid_trial.data_root,
    }

    assert len(
        roots
    ) == 4


def test_configuration_boundaries_do_not_create_trial_authority(
    tmp_path: Path,
) -> None:
    config = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={},
        )
    )

    boundaries = (
        config.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "configuration_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "configuration_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "configuration_is_not_customer_data_migration"
        ]
        is True
    )

    assert (
        boundaries[
            "development_fallback_is_not_paid_trial_storage"
        ]
        is True
    )

    assert (
        boundaries[
            "prelive_storage_is_not_paid_trial_storage"
        ]
        is True
    )

    assert (
        boundaries[
            "paid_trial_requires_explicit_absolute_data_root"
        ]
        is True
    )

    assert (
        boundaries[
            "explicit_release_roots_are_environment_namespaced"
        ]
        is True
    )

    assert (
        boundaries[
            "prelive_and_paid_trial_cannot_share_effective_root"
        ]
        is True
    )

def test_implicit_development_preserves_legacy_effective_root(
    tmp_path: Path,
) -> None:
    legacy_root = (
        tmp_path
        / "backend"
        / "app"
        / "data"
    )

    config = (
        load_governance_release_storage_configuration(
            application_data_root=legacy_root,
            environment={},
        )
    )

    assert (
        config.effective_data_root
        == legacy_root
    )

    assert (
        config.assessment_database_path
        == legacy_root
        / "governance_assessments.sqlite3"
    )


def test_prelive_and_paid_trial_same_base_root_do_not_collide(
    tmp_path: Path,
) -> None:
    shared_base_root = (
        tmp_path
        / "release-data"
    ).resolve()

    prelive = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_PRELIVE,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        shared_base_root
                    ),
            },
        )
    )

    paid_trial = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_PAID_TRIAL,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        shared_base_root
                    ),
            },
        )
    )

    assert (
        prelive.data_root
        == paid_trial.data_root
        == shared_base_root
    )

    assert (
        prelive.effective_data_root
        == shared_base_root
        / "prelive"
    )

    assert (
        paid_trial.effective_data_root
        == shared_base_root
        / "paid_trial"
    )

    assert (
        prelive.effective_data_root
        != paid_trial.effective_data_root
    )

    assert (
        prelive.assessment_database_path
        != paid_trial.assessment_database_path
    )

    assert (
        prelive.controlled_trial_root
        != paid_trial.controlled_trial_root
    )
