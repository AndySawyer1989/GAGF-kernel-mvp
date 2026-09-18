from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_release_storage_configuration import (
    GovernanceReleaseStorageConfiguration,
)


GOVERNANCE_RELEASE_DURABLE_STORAGE_INVENTORY_TYPE = (
    "governance-release-durable-storage-inventory"
)

GOVERNANCE_RELEASE_DURABLE_STORAGE_INVENTORY_VERSION = (
    "0.1.0"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseDurableStorageItem:
    name: str
    path: Path
    storage_kind: str
    required_for_backup: bool

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "name":
                self.name,

            "path":
                str(
                    self.path
                ),

            "storage_kind":
                self.storage_kind,

            "required_for_backup":
                self.required_for_backup,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseDurableStorageInventory:
    release_environment: str
    effective_data_root: Path
    items: tuple[
        GovernanceReleaseDurableStorageItem,
        ...,
    ]

    inventory_type: str = (
        GOVERNANCE_RELEASE_DURABLE_STORAGE_INVENTORY_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_DURABLE_STORAGE_INVENTORY_VERSION
    )

    @property
    def required_items(
        self,
    ) -> tuple[
        GovernanceReleaseDurableStorageItem,
        ...,
    ]:
        return tuple(
            item
            for item in self.items
            if item.required_for_backup
        )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "inventory_type":
                self.inventory_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "effective_data_root":
                str(
                    self.effective_data_root
                ),

            "items": [
                item.to_dict()
                for item in self.items
            ],

            "boundaries": {
                "inventory_is_not_backup_execution":
                    True,

                "inventory_is_not_restore_execution":
                    True,

                "inventory_is_not_trial_authorization":
                    True,

                "inventory_does_not_mutate_storage":
                    True,
            },
        }


def build_governance_release_durable_storage_inventory(
    *,
    configuration:
        GovernanceReleaseStorageConfiguration,
) -> GovernanceReleaseDurableStorageInventory:
    if not isinstance(
        configuration,
        GovernanceReleaseStorageConfiguration,
    ):
        raise TypeError(
            "configuration must be a "
            "GovernanceReleaseStorageConfiguration"
        )

    root = (
        configuration.effective_data_root
    )

    assessment_database_path = (
        configuration.assessment_database_path
    )

    items = (
        GovernanceReleaseDurableStorageItem(
            name="assessment_database",
            path=assessment_database_path,
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="assessment_audit_database",
            path=assessment_database_path.with_name(
                "governance_assessment_audit.sqlite3"
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="assessment_audit_checkpoint_database",
            path=assessment_database_path.with_name(
                "governance_assessment_audit_checkpoints.sqlite3"
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="assessment_signed_checkpoint_database",
            path=assessment_database_path.with_name(
                "governance_assessment_signed_checkpoints.sqlite3"
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="assessment_checkpoint_key_audit_database",
            path=assessment_database_path.with_name(
                "governance_assessment_checkpoint_key_audit.sqlite3"
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="assessment_checkpoint_key_database",
            path=assessment_database_path.with_name(
                "governance_assessment_checkpoint_keys.sqlite3"
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="paid_assessment_execution_inputs",
            path=(
                root
                / "governance_paid_assessment_execution_inputs"
            ),
            storage_kind="directory",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="paid_assessment_executions",
            path=(
                root
                / "governance_paid_assessment_executions"
            ),
            storage_kind="directory",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_preflight_database",
            path=(
                configuration
                .customer_trial_preflight_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_execution_handoff_database",
            path=(
                configuration
                .customer_trial_execution_handoff_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_execution_observation_database",
            path=(
                configuration
                .customer_trial_execution_observation_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_delivery_readiness_database",
            path=(
                configuration
                .customer_trial_delivery_readiness_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_delivery_observation_database",
            path=(
                configuration
                .customer_trial_delivery_observation_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_client_receipt_observation_database",
            path=(
                configuration
                .customer_trial_client_receipt_observation_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name="customer_trial_client_response_observation_database",
            path=(
                configuration
                .customer_trial_client_response_observation_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),

        GovernanceReleaseDurableStorageItem(
            name=(
                "customer_trial_"
                "administrative_closeout_observation_database"
            ),
            path=(
                configuration
                .customer_trial_administrative_closeout_observation_database_path
            ),
            storage_kind="sqlite",
            required_for_backup=True,
        ),
    )

    for item in items:
        try:
            item.path.relative_to(
                root
            )
        except ValueError as exc:
            raise ValueError(
                "release durable storage item escaped "
                "effective release data root: "
                f"{item.name}"
            ) from exc

    paths = [
        item.path
        for item in items
    ]

    if len(paths) != len(set(paths)):
        raise ValueError(
            "release durable storage inventory "
            "contains duplicate paths"
        )

    return (
        GovernanceReleaseDurableStorageInventory(
            release_environment=(
                configuration.release_environment
            ),
            effective_data_root=root,
            items=items,
        )
    )