from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_release_backup_integrity import (
    GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME,
    GovernanceReleaseBackupIntegrityManifest,
    verify_governance_release_backup_integrity,
)


GOVERNANCE_RELEASE_BACKUP_RECOVERY_TYPE = (
    "governance-release-backup-recovery"
)

GOVERNANCE_RELEASE_BACKUP_RECOVERY_VERSION = "0.1.0"


class GovernanceReleaseBackupRecoveryError(RuntimeError):
    pass


class GovernanceReleaseBackupRecoveryDestinationError(
    GovernanceReleaseBackupRecoveryError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseBackupRecoveryReceipt:
    backup_id: str
    release_environment: str
    backup_root: Path
    restore_root: Path
    recovered_file_count: int
    verified_package_sha256: str

    receipt_type: str = (
        GOVERNANCE_RELEASE_BACKUP_RECOVERY_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_BACKUP_RECOVERY_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "receipt_type":
                self.receipt_type,

            "version":
                self.version,

            "backup_id":
                self.backup_id,

            "release_environment":
                self.release_environment,

            "backup_root":
                str(
                    self.backup_root
                ),

            "restore_root":
                str(
                    self.restore_root
                ),

            "recovered_file_count":
                self.recovered_file_count,

            "verified_package_sha256":
                self.verified_package_sha256,

            "boundaries": {
                "recovery_is_not_production_activation":
                    True,

                "recovery_is_not_trial_authorization":
                    True,

                "recovery_is_not_storage_migration":
                    True,

                "recovery_does_not_mutate_backup":
                    True,

                "integrity_verification_precedes_restore":
                    True,
            },
        }


def recover_governance_release_backup(
    *,
    backup_root: Path,
    restore_root: Path,
) -> GovernanceReleaseBackupRecoveryReceipt:
    resolved_backup_root = (
        Path(
            backup_root
        )
        .expanduser()
        .resolve()
    )

    resolved_restore_root = (
        Path(
            restore_root
        )
        .expanduser()
        .resolve()
    )

    if not resolved_backup_root.is_dir():
        raise GovernanceReleaseBackupRecoveryError(
            "backup root does not exist"
        )

    if resolved_restore_root.exists():
        raise GovernanceReleaseBackupRecoveryDestinationError(
            "restore destination already exists"
        )

    if (
        resolved_restore_root
        == resolved_backup_root
        or resolved_backup_root
        in resolved_restore_root.parents
    ):
        raise GovernanceReleaseBackupRecoveryDestinationError(
            "restore destination must not be inside "
            "the backup root"
        )

    #
    # Constitutional recovery gate:
    # verification MUST succeed before restore storage
    # is created or mutated.
    #
    manifest = (
        verify_governance_release_backup_integrity(
            backup_root=resolved_backup_root
        )
    )

    _validate_manifest_paths(
        manifest=manifest
    )

    resolved_restore_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    recovered_file_count = 0

    try:
        for manifest_file in manifest.files:
            relative_path = Path(
                manifest_file.relative_path
            )

            source = (
                resolved_backup_root
                / relative_path
            )

            destination = (
                resolved_restore_root
                / relative_path
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if source.suffix.lower() == ".sqlite3":
                _recover_sqlite_database(
                    source=source,
                    destination=destination,
                )

            else:
                shutil.copy2(
                    source,
                    destination,
                )

            recovered_file_count += 1

    except Exception:
        shutil.rmtree(
            resolved_restore_root,
            ignore_errors=True,
        )
        raise

    return (
        GovernanceReleaseBackupRecoveryReceipt(
            backup_id=(
                manifest.backup_id
            ),
            release_environment=(
                manifest.release_environment
            ),
            backup_root=(
                resolved_backup_root
            ),
            restore_root=(
                resolved_restore_root
            ),
            recovered_file_count=(
                recovered_file_count
            ),
            verified_package_sha256=(
                manifest.package_sha256
            ),
        )
    )


def _validate_manifest_paths(
    *,
    manifest:
        GovernanceReleaseBackupIntegrityManifest,
) -> None:
    for manifest_file in manifest.files:
        relative_path = Path(
            manifest_file.relative_path
        )

        if relative_path.is_absolute():
            raise GovernanceReleaseBackupRecoveryError(
                "backup manifest contains absolute path"
            )

        if ".." in relative_path.parts:
            raise GovernanceReleaseBackupRecoveryError(
                "backup manifest contains path traversal"
            )

        if (
            manifest_file.relative_path
            == GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME
        ):
            raise GovernanceReleaseBackupRecoveryError(
                "backup manifest must not list itself "
                "as recoverable state"
            )


def _recover_sqlite_database(
    *,
    source: Path,
    destination: Path,
) -> None:
    source_uri = (
        source.resolve()
        .as_uri()
        + "?mode=ro"
    )

    source_connection = sqlite3.connect(
        source_uri,
        uri=True,
    )

    try:
        destination_connection = (
            sqlite3.connect(
                destination
            )
        )

        try:
            source_connection.backup(
                destination_connection
            )

            destination_connection.commit()

        finally:
            destination_connection.close()

    finally:
        source_connection.close()