from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    GovernanceReleaseStorageConfiguration,
    load_governance_release_storage_configuration,
)


GOVERNANCE_RELEASE_RUNTIME_PREFLIGHT_TYPE = (
    "governance-release-runtime-preflight"
)

GOVERNANCE_RELEASE_RUNTIME_PREFLIGHT_VERSION = "0.1.0"


class GovernanceReleaseRuntimePreflightError(RuntimeError):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseRuntimePreflightResult:
    release_environment: str
    effective_data_root: Path
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    preflight_type: str = (
        GOVERNANCE_RELEASE_RUNTIME_PREFLIGHT_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_RUNTIME_PREFLIGHT_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "preflight_type":
                self.preflight_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "effective_data_root":
                str(
                    self.effective_data_root
                ),

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
                "preflight_is_not_process_start":
                    True,

                "preflight_is_not_deployment_authority":
                    True,

                "preflight_is_not_trial_authorization":
                    True,

                "preflight_does_not_mutate_storage":
                    True,

                "preflight_does_not_bind_network_port":
                    True,
            },
        }


def evaluate_governance_release_runtime_preflight(
    *,
    application_data_root: Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseRuntimePreflightResult:
    configuration = (
        load_governance_release_storage_configuration(
            application_data_root=(
                application_data_root
            ),
            environment=environment,
        )
    )

    checks = {
        "paid_trial_environment":
            (
                configuration.release_environment
                == RELEASE_ENVIRONMENT_PAID_TRIAL
            ),

        "explicit_release_data_root":
            configuration.explicit_data_root,

        "effective_root_is_absolute":
            (
                configuration.effective_data_root
                .is_absolute()
            ),

        "effective_root_is_namespaced":
            (
                configuration.effective_data_root.name
                == RELEASE_ENVIRONMENT_PAID_TRIAL
            ),

        "fastapi_available":
            (
                importlib.util.find_spec(
                    "fastapi"
                )
                is not None
            ),

        "uvicorn_available":
            (
                importlib.util.find_spec(
                    "uvicorn"
                )
                is not None
            ),

        "release_environment_present":
            bool(
                environment.get(
                    GAGF_RELEASE_ENVIRONMENT_ENV,
                    "",
                ).strip()
            ),

        "release_data_root_present":
            bool(
                environment.get(
                    GAGF_RELEASE_DATA_ROOT_ENV,
                    "",
                ).strip()
            ),
    }

    failure_reasons = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return (
        GovernanceReleaseRuntimePreflightResult(
            release_environment=(
                configuration.release_environment
            ),
            effective_data_root=(
                configuration.effective_data_root
            ),
            passed=not failure_reasons,
            checks=checks,
            failure_reasons=failure_reasons,
        )
    )