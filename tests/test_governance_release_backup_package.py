from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_release_backup_package import (
    GovernanceReleaseBackupDestinationError,
    GovernanceReleaseBackupSourceMissingError,
    create_governance_release_backup_package,
)
from backend.app.gagf.governance_release_durable_storage_inventory import (
    build_governance_release_durable_storage_inventory,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    load_governance_release_storage_configuration,
)


def build_configuration(
    tmp_path: Path,
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
                    RELEASE_ENVIRONMENT_PAID_TRIAL,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        base_root
                    ),
            },
        )
    )


def create_sqlite_database(
    path: Path,
    *,
    value: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        path
    )

    try:
        connection.execute(
            """
            CREATE TABLE evidence (
                value TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT INTO evidence (
                value
            )
            VALUES (?)
            """,
            (
                value,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def populate_required_storage(
    inventory,
) -> None:
    for item in inventory.required_items:
        if item.storage_kind == "sqlite":
            create_sqlite_database(
                item.path,
                value=item.name,
            )

        elif item.storage_kind == "directory":
            item.path.mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                item.path
                / "evidence.txt"
            ).write_text(
                item.name,
                encoding="utf-8",
            )

        else:
            raise AssertionError(
                item.storage_kind
            )


def test_backup_copies_all_required_inventory_items(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    populate_required_storage(
        inventory
    )

    receipt = (
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )
    )

    assert receipt.backup_root.exists()

    assert len(
        receipt.items
    ) == len(
        inventory.required_items
    )

    for item in receipt.items:
        assert item.backup_path.exists()


def test_sqlite_backup_contains_committed_data(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    populate_required_storage(
        inventory
    )

    receipt = (
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )
    )

    assessment = next(
        item
        for item in receipt.items
        if item.name
        == "assessment_database"
    )

    connection = sqlite3.connect(
        assessment.backup_path
    )

    try:
        row = connection.execute(
            """
            SELECT value
            FROM evidence
            """
        ).fetchone()

    finally:
        connection.close()

    assert row == (
        "assessment_database",
    )


def test_directory_backup_preserves_files(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    populate_required_storage(
        inventory
    )

    receipt = (
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )
    )

    execution_inputs = next(
        item
        for item in receipt.items
        if item.name
        == "paid_assessment_execution_inputs"
    )

    assert (
        execution_inputs.backup_path
        / "evidence.txt"
    ).read_text(
        encoding="utf-8"
    ) == "paid_assessment_execution_inputs"


def test_backup_fails_closed_when_required_source_missing(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    with pytest.raises(
        GovernanceReleaseBackupSourceMissingError,
        match=(
            "required release backup source missing"
        ),
    ):
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )

    assert (
        tmp_path
        / "backups"
        / "backup-001"
    ).exists() is False


def test_backup_refuses_existing_destination(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    populate_required_storage(
        inventory
    )

    backup_parent = (
        tmp_path
        / "backups"
    )

    create_governance_release_backup_package(
        inventory=inventory,
        backup_parent=backup_parent,
        backup_id="backup-001",
    )

    with pytest.raises(
        GovernanceReleaseBackupDestinationError,
        match=(
            "backup destination already exists"
        ),
    ):
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=backup_parent,
            backup_id="backup-001",
        )


def test_backup_refuses_destination_inside_release_root(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    populate_required_storage(
        inventory
    )

    with pytest.raises(
        GovernanceReleaseBackupDestinationError,
        match=(
            "must not be inside "
            "the release data root"
        ),
    ):
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                configuration.effective_data_root
                / "backups"
            ),
            backup_id="backup-001",
        )


def test_backup_receipt_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    configuration = build_configuration(
        tmp_path
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    populate_required_storage(
        inventory
    )

    receipt = (
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )
    )

    boundaries = (
        receipt.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "backup_is_not_restore"
        ]
        is True
    )

    assert (
        boundaries[
            "backup_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "backup_is_not_storage_migration"
        ]
        is True
    )

    assert (
        boundaries[
            "backup_does_not_mutate_source"
        ]
        is True
    )