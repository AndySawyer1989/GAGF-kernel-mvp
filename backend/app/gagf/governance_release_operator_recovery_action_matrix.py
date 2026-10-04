from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_operator_recovery_contract import (
    GovernanceReleaseOperatorRecoveryContractResult,
)


GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_TYPE = (
    "governance-release-operator-recovery-action-matrix"
)

GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_VERSION = (
    "0.1.0"
)

ACTION_RECOVERY_VERIFIED = (
    "recovery_verified"
)

ACTION_STOP_AND_PRESERVE = (
    "stop_and_preserve"
)

ACTION_INSPECT_BACKUP_RECOVERY = (
    "inspect_backup_recovery"
)

ACTION_INSPECT_RUNTIME_READINESS = (
    "inspect_runtime_readiness"
)

ACTION_INSPECT_SECURITY_READINESS = (
    "inspect_security_readiness"
)

ACTION_RESOLVE_ENVIRONMENT_MISMATCH = (
    "resolve_environment_mismatch"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseOperatorRecoveryActionMatrixResult:
    release_environment: str
    backup_id: str
    recovery_verified: bool
    primary_action: str
    actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]

    matrix_type: str = (
        GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "matrix_type":
                self.matrix_type,
            "version":
                self.version,
            "release_environment":
                self.release_environment,
            "backup_id":
                self.backup_id,
            "recovery_verified":
                self.recovery_verified,
            "primary_action":
                self.primary_action,
            "actions":
                list(
                    self.actions
                ),
            "failure_reasons":
                list(
                    self.failure_reasons
                ),
            "boundaries": {
                "matrix_is_read_only":
                    True,
                "matrix_classifies_existing_failure_reasons_only":
                    True,
                "matrix_does_not_execute_recovery":
                    True,
                "matrix_does_not_execute_restore":
                    True,
                "matrix_does_not_retry_process":
                    True,
                "matrix_does_not_resume_paid_assessment":
                    True,
                "matrix_does_not_invoke_pa014_or_pa015":
                    True,
                "matrix_is_not_trial_authorization":
                    True,
                "matrix_is_not_deployment_activation":
                    True,
                "matrix_is_not_delivery_authorization":
                    True,
                "matrix_is_not_production_activation":
                    True,
                "matrix_is_not_intervention_authority":
                    True,
                "operator_action_is_not_execution_authority":
                    True,
            },
        }


def classify_governance_release_operator_recovery_action(
    *,
    recovery_contract:
        GovernanceReleaseOperatorRecoveryContractResult,
) -> GovernanceReleaseOperatorRecoveryActionMatrixResult:
    if not isinstance(
        recovery_contract,
        GovernanceReleaseOperatorRecoveryContractResult,
    ):
        raise TypeError(
            "recovery_contract must be a "
            "GovernanceReleaseOperatorRecoveryContractResult"
        )

    if recovery_contract.passed:
        return GovernanceReleaseOperatorRecoveryActionMatrixResult(
            release_environment=(
                recovery_contract.release_environment
            ),
            backup_id=(
                recovery_contract.backup_id
            ),
            recovery_verified=True,
            primary_action=(
                ACTION_RECOVERY_VERIFIED
            ),
            actions=(
                ACTION_RECOVERY_VERIFIED,
            ),
            failure_reasons=(),
        )

    actions: list[str] = [
        ACTION_STOP_AND_PRESERVE,
    ]

    failure_reasons = (
        recovery_contract.failure_reasons
    )

    environment_failures = {
        "paid_trial_environment",
        "runtime_gate_matches_recovery_environment",
        "security_gate_matches_recovery_environment",
    }

    if any(
        reason in environment_failures
        for reason in failure_reasons
    ):
        actions.append(
            ACTION_RESOLVE_ENVIRONMENT_MISMATCH
        )

    if (
        "backup_recovery_gate_passed"
        in failure_reasons
    ):
        actions.append(
            ACTION_INSPECT_BACKUP_RECOVERY
        )

    if (
        "runtime_gate_passed"
        in failure_reasons
    ):
        actions.append(
            ACTION_INSPECT_RUNTIME_READINESS
        )

    if (
        "security_gate_passed"
        in failure_reasons
    ):
        actions.append(
            ACTION_INSPECT_SECURITY_READINESS
        )

    return GovernanceReleaseOperatorRecoveryActionMatrixResult(
        release_environment=(
            recovery_contract.release_environment
        ),
        backup_id=(
            recovery_contract.backup_id
        ),
        recovery_verified=False,
        primary_action=(
            actions[0]
        ),
        actions=(
            tuple(
                actions
            )
        ),
        failure_reasons=(
            failure_reasons
        ),
    )