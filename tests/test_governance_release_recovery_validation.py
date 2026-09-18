from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_release_backup_integrity import (
    create_governance_release_backup_integrity_manifest,
)
from backend.app.gagf.governance_release_backup_package import (
    create_governance_release_backup_package,
)
from backend.app.gagf.governance_release_backup_recovery import (
    recover_governance_release_backup,
)
from backend.app.gagf.governance_release_durable_storage_inventory import (
    build_governance_release_durable_storage_inventory,
)
from backend.app.gagf.governance_release_recovery_validation import (
    GovernanceReleaseRecoveryFileIntegrityError,
    GovernanceReleaseRecoveryInventoryError,
    GovernanceReleaseRecoverySQLiteIntegrityError,
    validate_governance_release_recovery,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    load_governance_release_storage_configuration,
)


def build_recovered_candidate(
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

            (
                item.path
                / "evidence.txt"
            ).write_text(
                item.name,
                encoding="utf-8",
            )

    backup = (
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
            backup_receipt=backup
        )
    )

    restore_root = (
        tmp_path
        / "restore"
    )

    recovery = (
        recover_governance_release_backup(
            backup_root=(
                backup.backup_root
            ),
            restore_root=restore_root,
        )
    )

    return (
        inventory,
        backup,
        manifest,
        recovery,
    )


def test_valid_recovery_candidate_passes_validation(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    receipt = (
        validate_governance_release_recovery(
            restore_root=(
                recovery.restore_root
            ),
            manifest=manifest,
        )
    )

    assert (
        receipt.validated_file_count
        == len(
            manifest.files
        )
    )

    assert (
        receipt.validated_sqlite_count
        > 0
    )

    assert (
        receipt.validated_regular_file_count
        > 0
    )

    assert (
        receipt.source_package_sha256
        == manifest.package_sha256
    )


def test_missing_recovered_file_fails_validation(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    target = (
        recovery.restore_root
        / manifest.files[0].relative_path
    )

    target.unlink()

    with pytest.raises(
        GovernanceReleaseRecoveryInventoryError,
        match=(
            "recovered file inventory does not match"
        ),
    ):
        validate_governance_release_recovery(
            restore_root=(
                recovery.restore_root
            ),
            manifest=manifest,
        )


def test_unexpected_recovered_file_fails_validation(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    (
        recovery.restore_root
        / "unexpected.txt"
    ).write_text(
        "unexpected",
        encoding="utf-8",
    )

    with pytest.raises(
        GovernanceReleaseRecoveryInventoryError,
        match=(
            "recovered file inventory does not match"
        ),
    ):
        validate_governance_release_recovery(
            restore_root=(
                recovery.restore_root
            ),
            manifest=manifest,
        )


def test_modified_regular_file_fails_hash_validation(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    regular_file = next(
        item
        for item in manifest.files
        if not item.relative_path.endswith(
            ".sqlite3"
        )
    )

    target = (
        recovery.restore_root
        / regular_file.relative_path
    )

    target.write_text(
        "tampered",
        encoding="utf-8",
    )

    with pytest.raises(
        GovernanceReleaseRecoveryFileIntegrityError,
        match=(
            "recovered file hash mismatch"
        ),
    ):
        validate_governance_release_recovery(
            restore_root=(
                recovery.restore_root
            ),
            manifest=manifest,
        )


def test_corrupted_sqlite_fails_validation(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    sqlite_file = next(
        item
        for item in manifest.files
        if item.relative_path.endswith(
            ".sqlite3"
        )
    )

    target = (
        recovery.restore_root
        / sqlite_file.relative_path
    )

    target.write_bytes(
        b"not-a-sqlite-database"
    )

    with pytest.raises(
        GovernanceReleaseRecoverySQLiteIntegrityError,
        match=(
            "recovered SQLite database is unreadable"
        ),
    ):
        validate_governance_release_recovery(
            restore_root=(
                recovery.restore_root
            ),
            manifest=manifest,
        )


def test_recovered_sqlite_integrity_check_is_ok(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    validate_governance_release_recovery(
        restore_root=(
            recovery.restore_root
        ),
        manifest=manifest,
    )

    assessment_database = (
        recovery.restore_root
        / "governance_assessments.sqlite3"
    )

    connection = sqlite3.connect(
        assessment_database
    )

    try:
        row = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

    finally:
        connection.close()

    assert row == (
        "ok",
    )


def test_validation_receipt_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        manifest,
        recovery,
    ) = build_recovered_candidate(
        tmp_path
    )

    receipt = (
        validate_governance_release_recovery(
            restore_root=(
                recovery.restore_root
            ),
            manifest=manifest,
        )
    )

    boundaries = (
        receipt.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "validation_is_not_restore"
        ]
        is True
    )

    assert (
        boundaries[
            "validation_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "validation_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "sqlite_integrity_is_not_business_semantic_validation"
        ]
        is True
    )

    assert (
        boundaries[
            "source_package_hash_is_lineage_not_activation_authority"
        ]
        is True
    )