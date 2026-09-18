from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_release_backup_integrity import (
    GovernanceReleaseBackupIntegrityManifest,
)


GOVERNANCE_RELEASE_RECOVERY_VALIDATION_TYPE = (
    "governance-release-recovery-validation"
)

GOVERNANCE_RELEASE_RECOVERY_VALIDATION_VERSION = "0.1.0"


class GovernanceReleaseRecoveryValidationError(
    RuntimeError
):
    pass


class GovernanceReleaseRecoveryInventoryError(
    GovernanceReleaseRecoveryValidationError
):
    pass


class GovernanceReleaseRecoveryFileIntegrityError(
    GovernanceReleaseRecoveryValidationError
):
    pass


class GovernanceReleaseRecoverySQLiteIntegrityError(
    GovernanceReleaseRecoveryValidationError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseRecoveryValidationReceipt:
    backup_id: str
    release_environment: str
    restore_root: Path
    validated_file_count: int
    validated_sqlite_count: int
    validated_regular_file_count: int
    source_package_sha256: str

    validation_type: str = (
        GOVERNANCE_RELEASE_RECOVERY_VALIDATION_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_RECOVERY_VALIDATION_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "validation_type":
                self.validation_type,

            "version":
                self.version,

            "backup_id":
                self.backup_id,

            "release_environment":
                self.release_environment,

            "restore_root":
                str(
                    self.restore_root
                ),

            "validated_file_count":
                self.validated_file_count,

            "validated_sqlite_count":
                self.validated_sqlite_count,

            "validated_regular_file_count":
                self.validated_regular_file_count,

            "source_package_sha256":
                self.source_package_sha256,

            "boundaries": {
                "validation_is_not_restore":
                    True,

                "validation_is_not_production_activation":
                    True,

                "validation_is_not_trial_authorization":
                    True,

                "sqlite_integrity_is_not_business_semantic_validation":
                    True,

                "source_package_hash_is_lineage_not_activation_authority":
                    True,
            },
        }


def validate_governance_release_recovery(
    *,
    restore_root: Path,
    manifest:
        GovernanceReleaseBackupIntegrityManifest,
) -> GovernanceReleaseRecoveryValidationReceipt:
    if not isinstance(
        manifest,
        GovernanceReleaseBackupIntegrityManifest,
    ):
        raise TypeError(
            "manifest must be a "
            "GovernanceReleaseBackupIntegrityManifest"
        )

    resolved_restore_root = (
        Path(
            restore_root
        )
        .expanduser()
        .resolve()
    )

    if not resolved_restore_root.is_dir():
        raise GovernanceReleaseRecoveryValidationError(
            "restore root does not exist"
        )

    expected_paths = tuple(
        sorted(
            item.relative_path
            for item in manifest.files
        )
    )

    actual_files = tuple(
        sorted(
            (
                path
                for path in resolved_restore_root.rglob("*")
                if path.is_file()
            ),
            key=lambda path: (
                path.relative_to(
                    resolved_restore_root
                ).as_posix()
            ),
        )
    )

    actual_paths = tuple(
        path.relative_to(
            resolved_restore_root
        ).as_posix()
        for path in actual_files
    )

    if actual_paths != expected_paths:
        raise GovernanceReleaseRecoveryInventoryError(
            "recovered file inventory does not match "
            "verified backup manifest"
        )

    manifest_by_path = {
        item.relative_path:
            item
        for item in manifest.files
    }

    validated_sqlite_count = 0
    validated_regular_file_count = 0

    for file_path in actual_files:
        relative_path = (
            file_path.relative_to(
                resolved_restore_root
            ).as_posix()
        )

        manifest_file = (
            manifest_by_path[
                relative_path
            ]
        )

        if (
            file_path.suffix.lower()
            == ".sqlite3"
        ):
            _validate_sqlite_database(
                path=file_path
            )

            validated_sqlite_count += 1
            continue

        actual_sha256 = _sha256_file(
            file_path
        )

        if (
            actual_sha256
            != manifest_file.sha256
        ):
            raise GovernanceReleaseRecoveryFileIntegrityError(
                "recovered file hash mismatch: "
                f"{relative_path}"
            )

        if (
            file_path.stat().st_size
            != manifest_file.size_bytes
        ):
            raise GovernanceReleaseRecoveryFileIntegrityError(
                "recovered file size mismatch: "
                f"{relative_path}"
            )

        validated_regular_file_count += 1

    return (
        GovernanceReleaseRecoveryValidationReceipt(
            backup_id=(
                manifest.backup_id
            ),
            release_environment=(
                manifest.release_environment
            ),
            restore_root=(
                resolved_restore_root
            ),
            validated_file_count=(
                len(
                    actual_files
                )
            ),
            validated_sqlite_count=(
                validated_sqlite_count
            ),
            validated_regular_file_count=(
                validated_regular_file_count
            ),
            source_package_sha256=(
                manifest.package_sha256
            ),
        )
    )


def _validate_sqlite_database(
    *,
    path: Path,
) -> None:
    source_uri = (
        path.resolve()
        .as_uri()
        + "?mode=ro"
    )

    try:
        connection = sqlite3.connect(
            source_uri,
            uri=True,
        )

        try:
            row = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

        finally:
            connection.close()

    except sqlite3.DatabaseError as exc:
        raise GovernanceReleaseRecoverySQLiteIntegrityError(
            "recovered SQLite database is unreadable: "
            f"{path.name}"
        ) from exc

    if (
        row is None
        or len(row) != 1
        or row[0] != "ok"
    ):
        raise GovernanceReleaseRecoverySQLiteIntegrityError(
            "recovered SQLite integrity check failed: "
            f"{path.name}"
        )


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        while True:
            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()