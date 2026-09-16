from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.app.gagf.governance_release_storage_configuration import (
    GovernanceReleaseStorageConfiguration,
)


GOVERNANCE_RELEASE_STORAGE_STATUS_API_VERSION = "1.0.0"

GOVERNANCE_RELEASE_STORAGE_STATUS_API_PREFIX = (
    "/api/v1/governance-release"
)

GOVERNANCE_RELEASE_STORAGE_STATUS_API_TAG = (
    "governance-release-storage"
)


def create_governance_release_storage_status_router(
    *,
    configuration:
        GovernanceReleaseStorageConfiguration,
) -> APIRouter:
    if not isinstance(
        configuration,
        GovernanceReleaseStorageConfiguration,
    ):
        raise TypeError(
            "configuration must be a "
            "GovernanceReleaseStorageConfiguration"
        )

    router = APIRouter(
        prefix=(
            GOVERNANCE_RELEASE_STORAGE_STATUS_API_PREFIX
        ),
        tags=[
            GOVERNANCE_RELEASE_STORAGE_STATUS_API_TAG
        ],
    )

    @router.get(
        "/storage-status"
    )
    def get_release_storage_status(
    ) -> dict[str, Any]:
        return {
            "status":
                "ok",

            "api_version":
                GOVERNANCE_RELEASE_STORAGE_STATUS_API_VERSION,

            "authority":
                "READ_ONLY",

            "release_storage":
                configuration.to_public_status_dict(),

            "boundaries": {
                "api_is_observability_only":
                    True,

                "api_is_read_only":
                    True,

                "api_does_not_authorize_trial":
                    True,

                "api_does_not_authorize_execution":
                    True,

                "api_does_not_migrate_storage":
                    True,

                "api_does_not_expose_filesystem_paths":
                    True,
            },
        }

    return router