from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_release_backup_integrity import (
    GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME,
    GovernanceReleaseBackupIntegrityMismatchError,
    create_governance_release_backup_integrity_manifest,
    verify_governance_release_backup_integrity,
)
from backend.app.gagf.governance_release_backup_package import (
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


def build_backup(
    tmp_path: Path,
):
    base_root = (
        tmp_path
        / "release-data"
    ).resolve()

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
                        base_root
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

    return (
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )
    )


def test_manifest_is_created_with_sha256_entries(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    manifest_path = (
        receipt.backup_root
        / GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME
    )

    assert manifest_path.is_file()

    assert manifest.files

    assert len(
        manifest.package_sha256
    ) == 64

    assert all(
        len(
            item.sha256
        )
        == 64
        for item in manifest.files
    )


def test_manifest_file_order_is_deterministic(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    paths = [
        item.relative_path
        for item in manifest.files
    ]

    assert paths == sorted(
        paths
    )


def test_untouched_backup_verifies(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    created = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    verified = (
        verify_governance_release_backup_integrity(
            backup_root=(
                receipt.backup_root
            )
        )
    )

    assert (
        verified.package_sha256
        == created.package_sha256
    )


def test_modified_backup_file_fails_verification(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    target = (
        receipt.backup_root
        / manifest.files[0].relative_path
    )

    with target.open(
        "ab"
    ) as handle:
        handle.write(
            b"tampered"
        )

    with pytest.raises(
        GovernanceReleaseBackupIntegrityMismatchError,
    ):
        verify_governance_release_backup_integrity(
            backup_root=(
                receipt.backup_root
            )
        )


def test_deleted_backup_file_fails_verification(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    target = (
        receipt.backup_root
        / manifest.files[0].relative_path
    )

    target.unlink()

    with pytest.raises(
        GovernanceReleaseBackupIntegrityMismatchError,
        match=(
            "backup file inventory "
            "does not match manifest"
        ),
    ):
        verify_governance_release_backup_integrity(
            backup_root=(
                receipt.backup_root
            )
        )


def test_unexpected_backup_file_fails_verification(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    create_governance_release_backup_integrity_manifest(
        backup_receipt=receipt
    )

    (
        receipt.backup_root
        / "unexpected.txt"
    ).write_text(
        "unexpected",
        encoding="utf-8",
    )

    with pytest.raises(
        GovernanceReleaseBackupIntegrityMismatchError,
        match=(
            "backup file inventory "
            "does not match manifest"
        ),
    ):
        verify_governance_release_backup_integrity(
            backup_root=(
                receipt.backup_root
            )
        )


def test_manifest_tampering_fails_package_verification(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    create_governance_release_backup_integrity_manifest(
        backup_receipt=receipt
    )

    manifest_path = (
        receipt.backup_root
        / GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME
    )

    payload = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "package_sha256"
    ] = "0" * 64

    manifest_path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        GovernanceReleaseBackupIntegrityMismatchError,
        match=(
            "backup package hash mismatch"
        ),
    ):
        verify_governance_release_backup_integrity(
            backup_root=(
                receipt.backup_root
            )
        )


def test_manifest_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    receipt = build_backup(
        tmp_path
    )

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=receipt
        )
    )

    boundaries = (
        manifest.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "integrity_is_not_restore"
        ]
        is True
    )

    assert (
        boundaries[
            "integrity_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "integrity_is_not_backup_creation"
        ]
        is True
    )

    assert (
        boundaries[
            "hash_match_is_not_semantic_validation"
        ]
        is True
    )