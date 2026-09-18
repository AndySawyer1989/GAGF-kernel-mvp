from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_release_durable_storage_inventory import (
    GovernanceReleaseDurableStorageInventory,
    GovernanceReleaseDurableStorageItem,
)


GOVERNANCE_RELEASE_BACKUP_PACKAGE_TYPE = (
    "governance-release-backup-package"
)

GOVERNANCE_RELEASE_BACKUP_PACKAGE_VERSION = "0.1.0"


class GovernanceReleaseBackupError(RuntimeError):
    pass


class GovernanceReleaseBackupSourceMissingError(
    GovernanceReleaseBackupError
):
    pass


class GovernanceReleaseBackupDestinationError(
    GovernanceReleaseBackupError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseBackupItemReceipt:
    name: str
    storage_kind: str
    source_path: Path
    backup_path: Path

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "storage_kind": self.storage_kind,
            "source_path": str(
                self.source_path
            ),
            "backup_path": str(
                self.backup_path
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseBackupPackageReceipt:
    backup_id: str
    release_environment: str
    source_root: Path
    backup_root: Path
    items: tuple[
        GovernanceReleaseBackupItemReceipt,
        ...,
    ]

    receipt_type: str = (
        GOVERNANCE_RELEASE_BACKUP_PACKAGE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_BACKUP_PACKAGE_VERSION
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

            "source_root":
                str(
                    self.source_root
                ),

            "backup_root":
                str(
                    self.backup_root
                ),

            "items": [
                item.to_dict()
                for item in self.items
            ],

            "boundaries": {
                "backup_is_not_restore":
                    True,

                "backup_is_not_trial_authorization":
                    True,

                "backup_is_not_storage_migration":
                    True,

                "backup_does_not_mutate_source":
                    True,
            },
        }


def create_governance_release_backup_package(
    *,
    inventory:
        GovernanceReleaseDurableStorageInventory,
    backup_parent: Path,
    backup_id: str,
) -> GovernanceReleaseBackupPackageReceipt:
    if not isinstance(
        inventory,
        GovernanceReleaseDurableStorageInventory,
    ):
        raise TypeError(
            "inventory must be a "
            "GovernanceReleaseDurableStorageInventory"
        )

    resolved_backup_parent = (
        Path(
            backup_parent
        )
        .expanduser()
        .resolve()
    )

    normalized_backup_id = (
        backup_id.strip()
    )

    if not normalized_backup_id:
        raise GovernanceReleaseBackupDestinationError(
            "backup_id must not be empty"
        )

    if (
        Path(
            normalized_backup_id
        ).name
        != normalized_backup_id
    ):
        raise GovernanceReleaseBackupDestinationError(
            "backup_id must be a single path component"
        )

    source_root = (
        inventory.effective_data_root.resolve()
    )

    backup_root = (
        resolved_backup_parent
        / normalized_backup_id
    )

    if (
        backup_root == source_root
        or source_root in backup_root.parents
    ):
        raise GovernanceReleaseBackupDestinationError(
            "backup destination must not be inside "
            "the release data root"
        )

    if backup_root.exists():
        raise GovernanceReleaseBackupDestinationError(
            "backup destination already exists"
        )

    missing = tuple(
        item
        for item in inventory.required_items
        if not item.path.exists()
    )

    if missing:
        names = ", ".join(
            item.name
            for item in missing
        )

        raise GovernanceReleaseBackupSourceMissingError(
            "required release backup source missing: "
            f"{names}"
        )

    backup_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    receipts: list[
        GovernanceReleaseBackupItemReceipt
    ] = []

    try:
        for item in inventory.items:
            if not item.path.exists():
                continue

            relative_path = (
                item.path.resolve()
                .relative_to(
                    source_root
                )
            )

            backup_path = (
                backup_root
                / relative_path
            )

            _backup_item(
                item=item,
                backup_path=backup_path,
            )

            receipts.append(
                GovernanceReleaseBackupItemReceipt(
                    name=item.name,
                    storage_kind=(
                        item.storage_kind
                    ),
                    source_path=(
                        item.path.resolve()
                    ),
                    backup_path=(
                        backup_path.resolve()
                    ),
                )
            )

    except Exception:
        shutil.rmtree(
            backup_root,
            ignore_errors=True,
        )
        raise

    return (
        GovernanceReleaseBackupPackageReceipt(
            backup_id=normalized_backup_id,
            release_environment=(
                inventory.release_environment
            ),
            source_root=source_root,
            backup_root=backup_root,
            items=tuple(
                receipts
            ),
        )
    )


def _backup_item(
    *,
    item: GovernanceReleaseDurableStorageItem,
    backup_path: Path,
) -> None:
    if item.storage_kind == "sqlite":
        _backup_sqlite_database(
            source=item.path,
            destination=backup_path,
        )
        return

    if item.storage_kind == "directory":
        _backup_directory(
            source=item.path,
            destination=backup_path,
        )
        return

    raise GovernanceReleaseBackupError(
        "unsupported release backup storage kind: "
        f"{item.storage_kind}"
    )


def _backup_sqlite_database(
    *,
    source: Path,
    destination: Path,
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def _backup_directory(
    *,
    source: Path,
    destination: Path,
) -> None:
    destination.mkdir(
        parents=True,
        exist_ok=False,
    )

    entries = sorted(
        source.rglob("*"),
        key=lambda path: (
            path.relative_to(
                source
            ).as_posix()
        ),
    )

    for source_entry in entries:
        relative_path = (
            source_entry.relative_to(
                source
            )
        )

        destination_entry = (
            destination
            / relative_path
        )

        if source_entry.is_dir():
            destination_entry.mkdir(
                parents=True,
                exist_ok=True,
            )
            continue

        if not source_entry.is_file():
            raise GovernanceReleaseBackupError(
                "unsupported non-file release "
                "backup directory entry: "
                f"{source_entry}"
            )

        destination_entry.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source_entry,
            destination_entry,
        )