from pathlib import Path

import pytest

from backend.app.gagf.governance_release_durable_storage_inventory import (
    build_governance_release_durable_storage_inventory,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    RELEASE_ENVIRONMENT_PRELIVE,
    load_governance_release_storage_configuration,
)


def build_configuration(
    *,
    tmp_path: Path,
    environment_name: str,
):
    base_root = (
        tmp_path
        / "release-data"
    ).resolve()

    return (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    environment_name,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        base_root
                    ),
            },
        )
    )


def test_inventory_contains_release_critical_storage(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PAID_TRIAL
        ),
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    names = {
        item.name
        for item in inventory.items
    }

    assert "assessment_database" in names

    assert (
        "assessment_audit_database"
        in names
    )

    assert (
        "assessment_signed_checkpoint_database"
        in names
    )

    assert (
        "paid_assessment_execution_inputs"
        in names
    )

    assert (
        "paid_assessment_executions"
        in names
    )

    assert (
        "customer_trial_preflight_database"
        in names
    )

    assert (
        "customer_trial_administrative_closeout_observation_database"
        in names
    )


def test_all_inventory_paths_are_under_effective_root(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PAID_TRIAL
        ),
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    for item in inventory.items:
        item.path.relative_to(
            configuration.effective_data_root
        )


def test_inventory_contains_no_duplicate_paths(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PAID_TRIAL
        ),
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    paths = [
        item.path
        for item in inventory.items
    ]

    assert len(paths) == len(
        set(paths)
    )


def test_prelive_and_paid_trial_inventories_are_isolated(
    tmp_path: Path,
) -> None:
    prelive = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PRELIVE
        ),
    )

    paid_trial = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PAID_TRIAL
        ),
    )

    prelive_inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=prelive
        )
    )

    paid_inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=paid_trial
        )
    )

    prelive_paths = {
        item.path
        for item in prelive_inventory.items
    }

    paid_paths = {
        item.path
        for item in paid_inventory.items
    }

    assert prelive_paths.isdisjoint(
        paid_paths
    )


def test_inventory_does_not_create_storage(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PAID_TRIAL
        ),
    )

    assert (
        configuration.effective_data_root.exists()
        is False
    )

    build_governance_release_durable_storage_inventory(
        configuration=configuration
    )

    assert (
        configuration.effective_data_root.exists()
        is False
    )


def test_inventory_boundary_metadata(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path=tmp_path,
        environment_name=(
            RELEASE_ENVIRONMENT_PAID_TRIAL
        ),
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    boundaries = (
        inventory.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "inventory_is_not_backup_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_is_not_restore_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_does_not_mutate_storage"
        ]
        is True
    )


def test_inventory_rejects_wrong_configuration_type() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "configuration must be a "
            "GovernanceReleaseStorageConfiguration"
        ),
    ):
        build_governance_release_durable_storage_inventory(
            configuration=object(),
        )