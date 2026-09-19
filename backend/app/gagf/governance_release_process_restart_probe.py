from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from backend.app.gagf.governance_release_process_start_probe import (
    GovernanceReleaseProcessStartReceipt,
    probe_governance_release_process_start,
)


GOVERNANCE_RELEASE_PROCESS_RESTART_PROBE_TYPE = (
    "governance-release-process-restart-probe"
)

GOVERNANCE_RELEASE_PROCESS_RESTART_PROBE_VERSION = "0.1.0"


class GovernanceReleaseProcessRestartError(RuntimeError):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseProcessRestartReceipt:
    host: str
    port: int
    first_start: GovernanceReleaseProcessStartReceipt
    second_start: GovernanceReleaseProcessStartReceipt
    same_release_environment: bool
    same_network_binding: bool
    restart_succeeded: bool

    probe_type: str = (
        GOVERNANCE_RELEASE_PROCESS_RESTART_PROBE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_PROCESS_RESTART_PROBE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "probe_type":
                self.probe_type,

            "version":
                self.version,

            "host":
                self.host,

            "port":
                self.port,

            "first_start":
                self.first_start.to_dict(),

            "second_start":
                self.second_start.to_dict(),

            "same_release_environment":
                self.same_release_environment,

            "same_network_binding":
                self.same_network_binding,

            "restart_succeeded":
                self.restart_succeeded,

            "boundaries": {
                "restart_is_not_state_persistence_proof":
                    True,

                "restart_is_not_deployment_authority":
                    True,

                "restart_is_not_trial_authorization":
                    True,

                "restart_is_not_production_activation":
                    True,

                "restart_does_not_grant_business_readiness":
                    True,
            },
        }


def probe_governance_release_process_restart(
    *,
    repo_root: Path,
    environment: Mapping[str, str],
    host: str,
    port: int,
    startup_timeout_seconds: float = 15.0,
) -> GovernanceReleaseProcessRestartReceipt:
    first_start = (
        probe_governance_release_process_start(
            repo_root=repo_root,
            environment=environment,
            host=host,
            port=port,
            startup_timeout_seconds=(
                startup_timeout_seconds
            ),
        )
    )

    second_start = (
        probe_governance_release_process_start(
            repo_root=repo_root,
            environment=environment,
            host=host,
            port=port,
            startup_timeout_seconds=(
                startup_timeout_seconds
            ),
        )
    )

    same_release_environment = (
        first_start.release_environment
        == second_start.release_environment
    )

    same_network_binding = (
        first_start.host
        == second_start.host
        == host
        and first_start.port
        == second_start.port
        == port
    )

    first_start_healthy = (
        first_start.health_status_code
        == 200
        and first_start.version_status_code
        == 200
        and first_start.storage_status_code
        == 200
    )

    second_start_healthy = (
        second_start.health_status_code
        == 200
        and second_start.version_status_code
        == 200
        and second_start.storage_status_code
        == 200
    )

    restart_succeeded = (
        first_start_healthy
        and second_start_healthy
        and same_release_environment
        and same_network_binding
        and first_start.storage_paths_exposed
        is False
        and second_start.storage_paths_exposed
        is False
    )

    if not restart_succeeded:
        raise GovernanceReleaseProcessRestartError(
            "governance release process restart "
            "proof failed"
        )

    return (
        GovernanceReleaseProcessRestartReceipt(
            host=host,
            port=port,
            first_start=first_start,
            second_start=second_start,
            same_release_environment=(
                same_release_environment
            ),
            same_network_binding=(
                same_network_binding
            ),
            restart_succeeded=True,
        )
    )