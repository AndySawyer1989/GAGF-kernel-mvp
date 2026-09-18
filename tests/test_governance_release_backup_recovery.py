from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_release_backup_integrity import (
    GovernanceReleaseBackupIntegrityMismatchError,
    create_governance_release_backup_integrity_manifest,
)
from backend.app.gagf.governance_release_backup_package import (
    create_governance_release_backup_package,
)
from backend.app.gagf.governance_release_backup_recovery import (
    GovernanceReleaseBackupRecoveryDestinationError,
    recover_governance_release_backup,
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


def build_verified_backup(
    tmp_path: Path,
):
    configuration = (
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
                        (
                            tmp_path
                            / "release-data"
                        ).resolve()
                    ),
            },
        )
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    for item in inventory.required_items:
        if item.storage_kind == "sqlite":
            item.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            connection = sqlite3.connect(
                item.path
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
                        item.name,
                    ),
                )

                connection.commit()

            finally:
                connection.close()

        elif item.storage_kind == "directory":
            item.path.mkdir(
                parents=True,
                exist_ok=True,
            )

            nested = (
                item.path
                / "nested"
            )

            nested.mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                nested
                / "evidence.txt"
            ).write_text(
                item.name,
                encoding="utf-8",
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

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    return (
        configuration,
        inventory,
        receipt,
        manifest,
    )


def test_recovery_materializes_verified_backup(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        manifest,
    ) = build_verified_backup(
        tmp_path
    )

    restore_root = (
        tmp_path
        / "restore"
    )

    receipt = (
        recover_governance_release_backup(
            backup_root=(
                backup.backup_root
            ),
            restore_root=restore_root,
        )
    )

    assert restore_root.is_dir()

    assert (
        receipt.recovered_file_count
        == len(
            manifest.files
        )
    )

    for manifest_file in manifest.files:
        assert (
            restore_root
            / manifest_file.relative_path
        ).is_file()


def test_recovered_sqlite_database_contains_data(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        _,
    ) = build_verified_backup(
        tmp_path
    )

    restore_root = (
        tmp_path
        / "restore"
    )

    recover_governance_release_backup(
        backup_root=(
            backup.backup_root
        ),
        restore_root=restore_root,
    )

    database = (
        restore_root
        / "governance_assessments.sqlite3"
    )

    connection = sqlite3.connect(
        database
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


def test_recovery_preserves_nested_directory_files(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        _,
    ) = build_verified_backup(
        tmp_path
    )

    restore_root = (
        tmp_path
        / "restore"
    )

    recover_governance_release_backup(
        backup_root=(
            backup.backup_root
        ),
        restore_root=restore_root,
    )

    restored_file = (
        restore_root
        / "governance_paid_assessment_execution_inputs"
        / "nested"
        / "evidence.txt"
    )

    assert restored_file.read_text(
        encoding="utf-8"
    ) == (
        "paid_assessment_execution_inputs"
    )


def test_corrupted_backup_fails_before_restore_root_created(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        manifest,
    ) = build_verified_backup(
        tmp_path
    )

    target = (
        backup.backup_root
        / manifest.files[0].relative_path
    )

    with target.open(
        "ab"
    ) as handle:
        handle.write(
            b"corruption"
        )

    restore_root = (
        tmp_path
        / "restore"
    )

    with pytest.raises(
        GovernanceReleaseBackupIntegrityMismatchError,
    ):
        recover_governance_release_backup(
            backup_root=(
                backup.backup_root
            ),
            restore_root=restore_root,
        )

    assert (
        restore_root.exists()
        is False
    )


def test_recovery_refuses_existing_destination(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        _,
    ) = build_verified_backup(
        tmp_path
    )

    restore_root = (
        tmp_path
        / "restore"
    )

    restore_root.mkdir()

    sentinel = (
        restore_root
        / "sentinel.txt"
    )

    sentinel.write_text(
        "preserve",
        encoding="utf-8",
    )

    with pytest.raises(
        GovernanceReleaseBackupRecoveryDestinationError,
        match=(
            "restore destination already exists"
        ),
    ):
        recover_governance_release_backup(
            backup_root=(
                backup.backup_root
            ),
            restore_root=restore_root,
        )

    assert sentinel.read_text(
        encoding="utf-8"
    ) == "preserve"


def test_recovery_refuses_destination_inside_backup(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        _,
    ) = build_verified_backup(
        tmp_path
    )

    with pytest.raises(
        GovernanceReleaseBackupRecoveryDestinationError,
        match=(
            "restore destination must not be inside "
            "the backup root"
        ),
    ):
        recover_governance_release_backup(
            backup_root=(
                backup.backup_root
            ),
            restore_root=(
                backup.backup_root
                / "restore"
            ),
        )


def test_recovery_does_not_copy_manifest_as_application_state(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        _,
    ) = build_verified_backup(
        tmp_path
    )

    restore_root = (
        tmp_path
        / "restore"
    )

    recover_governance_release_backup(
        backup_root=(
            backup.backup_root
        ),
        restore_root=restore_root,
    )

    assert (
        restore_root
        / "governance_release_backup_manifest.json"
    ).exists() is False


def test_recovery_receipt_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        backup,
        manifest,
    ) = build_verified_backup(
        tmp_path
    )

    receipt = (
        recover_governance_release_backup(
            backup_root=(
                backup.backup_root
            ),
            restore_root=(
                tmp_path
                / "restore"
            ),
        )
    )

    payload = receipt.to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        receipt.verified_package_sha256
        == manifest.package_sha256
    )

    assert (
        boundaries[
            "recovery_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "recovery_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "recovery_is_not_storage_migration"
        ]
        is True
    )

    assert (
        boundaries[
            "recovery_does_not_mutate_backup"
        ]
        is True
    )

    assert (
        boundaries[
            "integrity_verification_precedes_restore"
        ]
        is True
    )