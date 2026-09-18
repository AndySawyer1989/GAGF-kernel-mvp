from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_release_backup_package import (
    GovernanceReleaseBackupPackageReceipt,
)


GOVERNANCE_RELEASE_BACKUP_MANIFEST_TYPE = (
    "governance-release-backup-integrity-manifest"
)

GOVERNANCE_RELEASE_BACKUP_MANIFEST_VERSION = "0.1.0"

GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME = (
    "governance_release_backup_manifest.json"
)


class GovernanceReleaseBackupIntegrityError(RuntimeError):
    pass


class GovernanceReleaseBackupIntegrityMismatchError(
    GovernanceReleaseBackupIntegrityError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseBackupManifestFile:
    relative_path: str
    size_bytes: int
    sha256: str

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "relative_path":
                self.relative_path,

            "size_bytes":
                self.size_bytes,

            "sha256":
                self.sha256,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseBackupIntegrityManifest:
    backup_id: str
    release_environment: str
    files: tuple[
        GovernanceReleaseBackupManifestFile,
        ...,
    ]
    package_sha256: str

    manifest_type: str = (
        GOVERNANCE_RELEASE_BACKUP_MANIFEST_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_BACKUP_MANIFEST_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "manifest_type":
                self.manifest_type,

            "version":
                self.version,

            "backup_id":
                self.backup_id,

            "release_environment":
                self.release_environment,

            "file_count":
                len(
                    self.files
                ),

            "files": [
                item.to_dict()
                for item in self.files
            ],

            "package_sha256":
                self.package_sha256,

            "boundaries": {
                "integrity_is_not_restore":
                    True,

                "integrity_is_not_trial_authorization":
                    True,

                "integrity_is_not_backup_creation":
                    True,

                "hash_match_is_not_semantic_validation":
                    True,
            },
        }


def create_governance_release_backup_integrity_manifest(
    *,
    backup_receipt:
        GovernanceReleaseBackupPackageReceipt,
) -> GovernanceReleaseBackupIntegrityManifest:
    if not isinstance(
        backup_receipt,
        GovernanceReleaseBackupPackageReceipt,
    ):
        raise TypeError(
            "backup_receipt must be a "
            "GovernanceReleaseBackupPackageReceipt"
        )

    backup_root = (
        backup_receipt.backup_root.resolve()
    )

    if not backup_root.is_dir():
        raise GovernanceReleaseBackupIntegrityError(
            "backup root does not exist"
        )

    manifest_path = (
        backup_root
        / GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME
    )

    files = _collect_backup_files(
        backup_root=backup_root,
    )

    manifest_files = tuple(
        GovernanceReleaseBackupManifestFile(
            relative_path=(
                file_path
                .relative_to(
                    backup_root
                )
                .as_posix()
            ),
            size_bytes=(
                file_path.stat().st_size
            ),
            sha256=_sha256_file(
                file_path
            ),
        )
        for file_path in files
    )

    package_sha256 = (
        _calculate_package_sha256(
            files=manifest_files
        )
    )

    manifest = (
        GovernanceReleaseBackupIntegrityManifest(
            backup_id=(
                backup_receipt.backup_id
            ),
            release_environment=(
                backup_receipt.release_environment
            ),
            files=manifest_files,
            package_sha256=package_sha256,
        )
    )

    manifest_path.write_text(
        _canonical_json(
            manifest.to_dict()
        )
        + "\n",
        encoding="utf-8",
    )

    return manifest


def load_governance_release_backup_integrity_manifest(
    *,
    backup_root: Path,
) -> GovernanceReleaseBackupIntegrityManifest:
    resolved_root = (
        Path(
            backup_root
        )
        .resolve()
    )

    manifest_path = (
        resolved_root
        / GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME
    )

    if not manifest_path.is_file():
        raise GovernanceReleaseBackupIntegrityError(
            "backup integrity manifest is missing"
        )

    try:
        payload = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise GovernanceReleaseBackupIntegrityError(
            "backup integrity manifest is unreadable"
        ) from exc

    if (
        payload.get(
            "manifest_type"
        )
        != GOVERNANCE_RELEASE_BACKUP_MANIFEST_TYPE
    ):
        raise GovernanceReleaseBackupIntegrityError(
            "unexpected backup integrity manifest type"
        )

    if (
        payload.get(
            "version"
        )
        != GOVERNANCE_RELEASE_BACKUP_MANIFEST_VERSION
    ):
        raise GovernanceReleaseBackupIntegrityError(
            "unsupported backup integrity manifest version"
        )

    raw_files = payload.get(
        "files"
    )

    if not isinstance(
        raw_files,
        list,
    ):
        raise GovernanceReleaseBackupIntegrityError(
            "backup integrity manifest files must be a list"
        )

    files = tuple(
        GovernanceReleaseBackupManifestFile(
            relative_path=(
                str(
                    item[
                        "relative_path"
                    ]
                )
            ),
            size_bytes=int(
                item[
                    "size_bytes"
                ]
            ),
            sha256=str(
                item[
                    "sha256"
                ]
            ),
        )
        for item in raw_files
    )

    return (
        GovernanceReleaseBackupIntegrityManifest(
            backup_id=str(
                payload[
                    "backup_id"
                ]
            ),
            release_environment=str(
                payload[
                    "release_environment"
                ]
            ),
            files=files,
            package_sha256=str(
                payload[
                    "package_sha256"
                ]
            ),
        )
    )


def verify_governance_release_backup_integrity(
    *,
    backup_root: Path,
) -> GovernanceReleaseBackupIntegrityManifest:
    resolved_root = (
        Path(
            backup_root
        )
        .resolve()
    )

    manifest = (
        load_governance_release_backup_integrity_manifest(
            backup_root=resolved_root
        )
    )

    actual_files = _collect_backup_files(
        backup_root=resolved_root,
    )

    actual_entries = tuple(
        GovernanceReleaseBackupManifestFile(
            relative_path=(
                file_path
                .relative_to(
                    resolved_root
                )
                .as_posix()
            ),
            size_bytes=(
                file_path.stat().st_size
            ),
            sha256=_sha256_file(
                file_path
            ),
        )
        for file_path in actual_files
    )

    expected_paths = tuple(
        item.relative_path
        for item in manifest.files
    )

    actual_paths = tuple(
        item.relative_path
        for item in actual_entries
    )

    if actual_paths != expected_paths:
        raise GovernanceReleaseBackupIntegrityMismatchError(
            "backup file inventory does not match manifest"
        )

    for expected, actual in zip(
        manifest.files,
        actual_entries,
        strict=True,
    ):
        if (
            expected.size_bytes
            != actual.size_bytes
        ):
            raise GovernanceReleaseBackupIntegrityMismatchError(
                "backup file size mismatch: "
                f"{expected.relative_path}"
            )

        if (
            expected.sha256
            != actual.sha256
        ):
            raise GovernanceReleaseBackupIntegrityMismatchError(
                "backup file hash mismatch: "
                f"{expected.relative_path}"
            )

    actual_package_sha256 = (
        _calculate_package_sha256(
            files=actual_entries
        )
    )

    if (
        manifest.package_sha256
        != actual_package_sha256
    ):
        raise GovernanceReleaseBackupIntegrityMismatchError(
            "backup package hash mismatch"
        )

    return manifest


def _collect_backup_files(
    *,
    backup_root: Path,
) -> tuple[
    Path,
    ...,
]:
    manifest_path = (
        backup_root
        / GOVERNANCE_RELEASE_BACKUP_MANIFEST_FILENAME
    )

    files = tuple(
        sorted(
            (
                path
                for path in backup_root.rglob("*")
                if (
                    path.is_file()
                    and path
                    != manifest_path
                )
            ),
            key=lambda path: (
                path.relative_to(
                    backup_root
                ).as_posix()
            ),
        )
    )

    return files


def _calculate_package_sha256(
    *,
    files: tuple[
        GovernanceReleaseBackupManifestFile,
        ...,
    ],
) -> str:
    canonical_entries = [
        item.to_dict()
        for item in files
    ]

    payload = _canonical_json(
        canonical_entries
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


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


def _canonical_json(
    value: object,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    )