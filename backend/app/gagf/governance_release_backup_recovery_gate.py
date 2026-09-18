from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_backup_integrity import (
    GovernanceReleaseBackupIntegrityManifest,
)
from backend.app.gagf.governance_release_backup_package import (
    GovernanceReleaseBackupPackageReceipt,
)
from backend.app.gagf.governance_release_backup_recovery import (
    GovernanceReleaseBackupRecoveryReceipt,
)
from backend.app.gagf.governance_release_durable_storage_inventory import (
    GovernanceReleaseDurableStorageInventory,
)
from backend.app.gagf.governance_release_recovery_validation import (
    GovernanceReleaseRecoveryValidationReceipt,
)


GOVERNANCE_RELEASE_BACKUP_RECOVERY_GATE_TYPE = (
    "governance-release-backup-recovery-gate"
)

GOVERNANCE_RELEASE_BACKUP_RECOVERY_GATE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseBackupRecoveryGateResult:
    release_environment: str
    backup_id: str
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    gate_type: str = (
        GOVERNANCE_RELEASE_BACKUP_RECOVERY_GATE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_BACKUP_RECOVERY_GATE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "gate_type":
                self.gate_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "backup_id":
                self.backup_id,

            "passed":
                self.passed,

            "checks":
                dict(
                    self.checks
                ),

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "gate_is_not_deployment_authority":
                    True,

                "gate_is_not_trial_authorization":
                    True,

                "gate_is_not_production_activation":
                    True,

                "gate_is_not_restore_execution":
                    True,

                "gate_is_not_backup_execution":
                    True,

                "gate_only_evaluates_existing_evidence":
                    True,
            },
        }


def evaluate_governance_release_backup_recovery_gate(
    *,
    inventory:
        GovernanceReleaseDurableStorageInventory,
    backup_receipt:
        GovernanceReleaseBackupPackageReceipt,
    manifest:
        GovernanceReleaseBackupIntegrityManifest,
    recovery_receipt:
        GovernanceReleaseBackupRecoveryReceipt,
    validation_receipt:
        GovernanceReleaseRecoveryValidationReceipt,
) -> GovernanceReleaseBackupRecoveryGateResult:
    _require_types(
        inventory=inventory,
        backup_receipt=backup_receipt,
        manifest=manifest,
        recovery_receipt=recovery_receipt,
        validation_receipt=validation_receipt,
    )

    required_inventory_names = {
        item.name
        for item in inventory.required_items
    }

    backed_up_names = {
        item.name
        for item in backup_receipt.items
    }

    environments = {
        inventory.release_environment,
        backup_receipt.release_environment,
        manifest.release_environment,
        recovery_receipt.release_environment,
        validation_receipt.release_environment,
    }

    backup_ids = {
        backup_receipt.backup_id,
        manifest.backup_id,
        recovery_receipt.backup_id,
        validation_receipt.backup_id,
    }

    checks = {
        "single_release_environment":
            len(
                environments
            ) == 1,

        "single_backup_identity":
            len(
                backup_ids
            ) == 1,

        "backup_source_matches_inventory_root":
            (
                backup_receipt.source_root.resolve()
                == inventory.effective_data_root.resolve()
            ),

        "all_required_inventory_items_backed_up":
            (
                required_inventory_names
                == backed_up_names
            ),

        "backup_contains_files":
            len(
                manifest.files
            ) > 0,

        "recovery_file_count_matches_manifest":
            (
                recovery_receipt.recovered_file_count
                == len(
                    manifest.files
                )
            ),

        "validation_file_count_matches_manifest":
            (
                validation_receipt.validated_file_count
                == len(
                    manifest.files
                )
            ),

        "recovery_hash_matches_manifest":
            (
                recovery_receipt.verified_package_sha256
                == manifest.package_sha256
            ),

        "validation_hash_matches_manifest":
            (
                validation_receipt.source_package_sha256
                == manifest.package_sha256
            ),

        "recovery_root_matches_validation_root":
            (
                recovery_receipt.restore_root.resolve()
                == validation_receipt.restore_root.resolve()
            ),

        "recovery_origin_matches_backup":
            (
                recovery_receipt.backup_root.resolve()
                == backup_receipt.backup_root.resolve()
            ),
    }

    failure_reasons = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    passed = not failure_reasons

    return (
        GovernanceReleaseBackupRecoveryGateResult(
            release_environment=(
                inventory.release_environment
            ),
            backup_id=(
                backup_receipt.backup_id
            ),
            passed=passed,
            checks=checks,
            failure_reasons=failure_reasons,
        )
    )


def _require_types(
    *,
    inventory: object,
    backup_receipt: object,
    manifest: object,
    recovery_receipt: object,
    validation_receipt: object,
) -> None:
    expected = (
        (
            "inventory",
            inventory,
            GovernanceReleaseDurableStorageInventory,
        ),
        (
            "backup_receipt",
            backup_receipt,
            GovernanceReleaseBackupPackageReceipt,
        ),
        (
            "manifest",
            manifest,
            GovernanceReleaseBackupIntegrityManifest,
        ),
        (
            "recovery_receipt",
            recovery_receipt,
            GovernanceReleaseBackupRecoveryReceipt,
        ),
        (
            "validation_receipt",
            validation_receipt,
            GovernanceReleaseRecoveryValidationReceipt,
        ),
    )

    for name, value, expected_type in expected:
        if not isinstance(
            value,
            expected_type,
        ):
            raise TypeError(
                f"{name} must be a "
                f"{expected_type.__name__}"
            )