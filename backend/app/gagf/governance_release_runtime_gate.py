from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_process_restart_probe import (
    GovernanceReleaseProcessRestartReceipt,
)
from backend.app.gagf.governance_release_process_start_probe import (
    GovernanceReleaseProcessStartReceipt,
)
from backend.app.gagf.governance_release_restart_persistence_probe import (
    GovernanceReleaseRestartPersistenceReceipt,
)
from backend.app.gagf.governance_release_runtime_failure_probe import (
    GovernanceReleaseRuntimeFailureReceipt,
)
from backend.app.gagf.governance_release_runtime_preflight import (
    GovernanceReleaseRuntimePreflightResult,
)


GOVERNANCE_RELEASE_RUNTIME_GATE_TYPE = (
    "governance-release-runtime-gate"
)

GOVERNANCE_RELEASE_RUNTIME_GATE_VERSION = (
    "0.1.0"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseRuntimeGateResult:
    release_environment: str
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    gate_type: str = (
        GOVERNANCE_RELEASE_RUNTIME_GATE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_RUNTIME_GATE_VERSION
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
                "gate_is_not_process_execution":
                    True,

                "gate_is_not_deployment_activation":
                    True,

                "gate_is_not_trial_authorization":
                    True,

                "gate_is_not_production_activation":
                    True,

                "gate_is_not_intervention_authority":
                    True,

                "gate_evaluates_existing_evidence_only":
                    True,

                "runtime_readiness_is_not_customer_trial_authority":
                    True,
            },
        }


def evaluate_governance_release_runtime_gate(
    *,
    preflight:
        GovernanceReleaseRuntimePreflightResult,
    process_start:
        GovernanceReleaseProcessStartReceipt,
    process_restart:
        GovernanceReleaseProcessRestartReceipt,
    persistence:
        GovernanceReleaseRestartPersistenceReceipt,
    failure_probe:
        GovernanceReleaseRuntimeFailureReceipt,
) -> GovernanceReleaseRuntimeGateResult:
    _require_types(
        preflight=preflight,
        process_start=process_start,
        process_restart=process_restart,
        persistence=persistence,
        failure_probe=failure_probe,
    )

    release_environment = (
        preflight.release_environment
    )

    checks = {
        "preflight_passed":
            preflight.passed
            is True,

        "paid_trial_environment":
            release_environment
            == "paid_trial",

        "clean_start_health_passed":
            process_start.health_status_code
            == 200,

        "clean_start_version_passed":
            process_start.version_status_code
            == 200,

        "clean_start_storage_status_passed":
            process_start.storage_status_code
            == 200,

        "start_environment_matches_preflight":
            process_start.release_environment
            == release_environment,

        "storage_paths_remain_redacted":
            process_start.storage_paths_exposed
            is False,

        "restart_succeeded":
            process_restart.restart_succeeded
            is True,

        "restart_preserved_environment":
            (
                process_restart.same_release_environment
                is True
                and
                process_restart.first_start.release_environment
                == release_environment
                and
                process_restart.second_start.release_environment
                == release_environment
            ),

        "restart_preserved_network_binding":
            process_restart.same_network_binding
            is True,

        "post_restart_persistence_proven":
            persistence.persistence_proven
            is True,

        "post_restart_first_runtime_healthy":
            persistence.first_runtime_healthy
            is True,

        "post_restart_second_runtime_healthy":
            persistence.second_runtime_healthy
            is True,

        "pa012_repository_chain_valid":
            persistence.repository_chain_valid
            is True,

        "pa012_lifecycle_state_rehydrated":
            (
                persistence.current_stage
                == "client_response_recorded"
                and
                persistence.pending_next_step
                == "none"
                and
                persistence.lifecycle_artifact_count
                == 3
            ),

        "invalid_configuration_failed_closed":
            (
                failure_probe.failure_proven
                is True
                and
                failure_probe.process_exited
                is True
                and
                failure_probe.health_reached
                is False
            ),

        "invalid_configuration_nonzero_exit":
            (
                failure_probe.exit_code
                is not None
                and
                failure_probe.exit_code
                != 0
            ),
    }

    failure_reasons = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return GovernanceReleaseRuntimeGateResult(
        release_environment=(
            release_environment
        ),
        passed=(
            not failure_reasons
        ),
        checks=checks,
        failure_reasons=(
            failure_reasons
        ),
    )


def _require_types(
    *,
    preflight: object,
    process_start: object,
    process_restart: object,
    persistence: object,
    failure_probe: object,
) -> None:
    expected = (
        (
            "preflight",
            preflight,
            GovernanceReleaseRuntimePreflightResult,
        ),
        (
            "process_start",
            process_start,
            GovernanceReleaseProcessStartReceipt,
        ),
        (
            "process_restart",
            process_restart,
            GovernanceReleaseProcessRestartReceipt,
        ),
        (
            "persistence",
            persistence,
            GovernanceReleaseRestartPersistenceReceipt,
        ),
        (
            "failure_probe",
            failure_probe,
            GovernanceReleaseRuntimeFailureReceipt,
        ),
    )

    for (
        name,
        value,
        expected_type,
    ) in expected:
        if not isinstance(
            value,
            expected_type,
        ):
            raise TypeError(
                f"{name} must be a "
                f"{expected_type.__name__}"
            )