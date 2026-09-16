from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


GOVERNANCE_RELEASE_STORAGE_CONFIGURATION_ID = (
    "governance-release-storage-configuration"
)

GOVERNANCE_RELEASE_STORAGE_CONFIGURATION_VERSION = "0.1.0"

GAGF_RELEASE_ENVIRONMENT_ENV = (
    "GAGF_RELEASE_ENVIRONMENT"
)

GAGF_RELEASE_DATA_ROOT_ENV = (
    "GAGF_RELEASE_DATA_ROOT"
)


RELEASE_ENVIRONMENT_DEVELOPMENT = "development"
RELEASE_ENVIRONMENT_TEST = "test"
RELEASE_ENVIRONMENT_PRELIVE = "prelive"
RELEASE_ENVIRONMENT_PAID_TRIAL = "paid_trial"


SUPPORTED_RELEASE_ENVIRONMENTS = frozenset(
    {
        RELEASE_ENVIRONMENT_DEVELOPMENT,
        RELEASE_ENVIRONMENT_TEST,
        RELEASE_ENVIRONMENT_PRELIVE,
        RELEASE_ENVIRONMENT_PAID_TRIAL,
    }
)


class GovernanceReleaseStorageConfigurationError(
    RuntimeError
):
    """Base release-storage configuration error."""


class GovernanceReleaseEnvironmentError(
    GovernanceReleaseStorageConfigurationError
):
    """Raised when the release environment is invalid."""


class GovernanceReleaseDataRootError(
    GovernanceReleaseStorageConfigurationError
):
    """Raised when release storage cannot be resolved safely."""


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseStorageConfiguration:
    release_environment: str
    data_root: Path
    explicit_data_root: bool

    configuration_type: str = (
        GOVERNANCE_RELEASE_STORAGE_CONFIGURATION_ID
    )

    version: str = (
        GOVERNANCE_RELEASE_STORAGE_CONFIGURATION_VERSION
    )

    @property
    def is_development(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_DEVELOPMENT
        )

    @property
    def is_test(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_TEST
        )

    @property
    def is_prelive(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_PRELIVE
        )

    @property
    def is_paid_trial(
        self,
    ) -> bool:
        return (
            self.release_environment
            == RELEASE_ENVIRONMENT_PAID_TRIAL
        )

    @property
    def effective_data_root(
        self,
    ) -> Path:
        """
        Return the environment-isolated runtime storage root.

        Preserve the legacy implicit development location exactly.
        Every explicit release root is namespaced by environment so
        PRELIVE and PAID_TRIAL cannot collide even when configured
        with the same GAGF_RELEASE_DATA_ROOT.
        """

        if (
            self.is_development
            and not self.explicit_data_root
        ):
            return self.data_root

        return (
            self.data_root
            / self.release_environment
        )

    @property
    def assessment_database_path(
        self,
    ) -> Path:
        return (
            self.effective_data_root
            / "governance_assessments.sqlite3"
        )

    @property
    def controlled_trial_root(
        self,
    ) -> Path:
        return (
            self.effective_data_root
            / "controlled_trial"
        )

    @property
    def customer_trial_preflight_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "preflight.sqlite3"
        )

    @property
    def customer_trial_execution_handoff_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "execution_handoff.sqlite3"
        )

    @property
    def customer_trial_execution_observation_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "execution_observation.sqlite3"
        )

    @property
    def customer_trial_delivery_readiness_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "delivery_readiness.sqlite3"
        )

    @property
    def customer_trial_delivery_observation_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "delivery_observation.sqlite3"
        )

    @property
    def customer_trial_client_receipt_observation_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "client_receipt_observation.sqlite3"
        )

    @property
    def customer_trial_client_response_observation_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "client_response_observation.sqlite3"
        )

    @property
    def customer_trial_administrative_closeout_observation_database_path(
        self,
    ) -> Path:
        return (
            self.controlled_trial_root
            / "administrative_closeout_observation.sqlite3"
        )

    def to_public_status_dict(
        self,
    ) -> dict[str, object]:
        """
        Return operator-safe release configuration status.

        Filesystem paths are intentionally excluded.
        """

        return {
            "configuration_type":
                self.configuration_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "explicit_data_root":
                self.explicit_data_root,

            "environment_namespaced":
                (
                    self.explicit_data_root
                    is True
                ),

            "paid_trial_fail_closed":
                True,

            "prelive_fail_closed":
                True,

            "storage_paths_exposed":
                False,

            "boundaries": {
                "status_is_observability_only":
                    True,

                "status_is_not_trial_authorization":
                    True,

                "status_is_not_execution_authority":
                    True,

                "status_is_not_storage_migration":
                    True,

                "status_does_not_expose_filesystem_paths":
                    True,
            },
        }

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "configuration_type":
                self.configuration_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "data_root":
                str(
                    self.data_root
                ),

            "effective_data_root":
                str(
                    self.effective_data_root
                ),

            "explicit_data_root":
                self.explicit_data_root,

            "paths": {
                "assessment_database_path": str(
                    self.assessment_database_path
                ),

                "controlled_trial_root": str(
                    self.controlled_trial_root
                ),

                "customer_trial_preflight_database_path": str(
                    self.customer_trial_preflight_database_path
                ),

                "customer_trial_execution_handoff_database_path": str(
                    self.customer_trial_execution_handoff_database_path
                ),

                "customer_trial_execution_observation_database_path": str(
                    self.customer_trial_execution_observation_database_path
                ),

                "customer_trial_delivery_readiness_database_path": str(
                    self.customer_trial_delivery_readiness_database_path
                ),

                "customer_trial_delivery_observation_database_path": str(
                    self.customer_trial_delivery_observation_database_path
                ),

                "customer_trial_client_receipt_observation_database_path": str(
                    self.customer_trial_client_receipt_observation_database_path
                ),

                "customer_trial_client_response_observation_database_path": str(
                    self.customer_trial_client_response_observation_database_path
                ),

                "customer_trial_administrative_closeout_observation_database_path": str(
                    self.customer_trial_administrative_closeout_observation_database_path
                ),
            },

            "boundaries": {
                "configuration_is_not_trial_authorization":
                    True,

                "configuration_is_not_execution_authority":
                    True,

                "configuration_is_not_customer_data_migration":
                    True,

                "development_fallback_is_not_paid_trial_storage":
                    True,

                "prelive_storage_is_not_paid_trial_storage":
                    True,

                "paid_trial_requires_explicit_absolute_data_root":
                    True,

                "explicit_release_roots_are_environment_namespaced":
                    True,

                "prelive_and_paid_trial_cannot_share_effective_root":
                    True,
            },
        }


def load_governance_release_storage_configuration(
    *,
    application_data_root: str | Path,
    environment: Mapping[str, str] | None = None,
) -> GovernanceReleaseStorageConfiguration:
    resolved_environment = (
        environment
        if environment is not None
        else os.environ
    )

    release_environment = (
        resolved_environment.get(
            GAGF_RELEASE_ENVIRONMENT_ENV
        )
    )

    if release_environment is None:
        release_environment = (
            RELEASE_ENVIRONMENT_DEVELOPMENT
        )

    if not isinstance(
        release_environment,
        str,
    ):
        raise GovernanceReleaseEnvironmentError(
            "GAGF_RELEASE_ENVIRONMENT must be a string"
        )

    release_environment = (
        release_environment
        .strip()
        .lower()
    )

    if (
        release_environment
        not in SUPPORTED_RELEASE_ENVIRONMENTS
    ):
        raise GovernanceReleaseEnvironmentError(
            "unsupported GAGF_RELEASE_ENVIRONMENT: "
            f"{release_environment!r}"
        )

    configured_data_root = (
        resolved_environment.get(
            GAGF_RELEASE_DATA_ROOT_ENV
        )
    )

    explicit_data_root = (
        configured_data_root is not None
        and bool(
            configured_data_root.strip()
        )
    )

    if explicit_data_root:
        data_root = Path(
            configured_data_root.strip()
        )
    else:
        data_root = Path(
            application_data_root
        )

    if (
        release_environment
        in {
            RELEASE_ENVIRONMENT_PRELIVE,
            RELEASE_ENVIRONMENT_PAID_TRIAL,
        }
        and not explicit_data_root
    ):
        raise GovernanceReleaseDataRootError(
            f"{release_environment} requires "
            "GAGF_RELEASE_DATA_ROOT"
        )

    if (
        release_environment
        in {
            RELEASE_ENVIRONMENT_PRELIVE,
            RELEASE_ENVIRONMENT_PAID_TRIAL,
        }
        and not data_root.is_absolute()
    ):
        raise GovernanceReleaseDataRootError(
            f"{release_environment} requires an "
            "absolute GAGF_RELEASE_DATA_ROOT"
        )

    return (
        GovernanceReleaseStorageConfiguration(
            release_environment=(
                release_environment
            ),
            data_root=(
                data_root
            ),
            explicit_data_root=(
                explicit_data_root
            ),
        )
    )
