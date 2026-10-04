from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_operator_recovery_action_matrix import (
    GovernanceReleaseOperatorRecoveryActionMatrixResult,
)
from backend.app.gagf.governance_release_operator_recovery_contract import (
    GovernanceReleaseOperatorRecoveryContractResult,
)


GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_TYPE = (
    "governance-release-operator-recovery-runbook"
)

GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_VERSION = (
    "0.1.0"
)

RUNBOOK_STAGE_RECOVERY_VERIFIED = (
    "recovery_verified"
)

RUNBOOK_STAGE_BLOCKED = (
    "blocked"
)

OPERATOR_SEQUENCE = (
    "stop_and_preserve_evidence",
    "review_recovery_contract",
    "review_action_matrix",
    "resolve_governed_blockers",
    "rerun_applicable_readiness_checks",
    "stop_before_resume_authority",
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseOperatorRecoveryRunbook:
    release_environment: str
    backup_id: str
    stage: str
    recovery_verified: bool
    primary_action: str
    actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    operator_sequence: tuple[str, ...]

    runbook_type: str = (
        GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "runbook_type":
                self.runbook_type,
            "version":
                self.version,
            "release_environment":
                self.release_environment,
            "backup_id":
                self.backup_id,
            "stage":
                self.stage,
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
            "operator_sequence":
                list(
                    self.operator_sequence
                ),
            "boundaries": {
                "runbook_is_read_only":
                    True,
                "runbook_projects_existing_evidence_only":
                    True,
                "runbook_does_not_execute_backup":
                    True,
                "runbook_does_not_execute_restore":
                    True,
                "runbook_does_not_start_or_restart_process":
                    True,
                "runbook_does_not_resolve_secret_material":
                    True,
                "runbook_does_not_execute_paid_assessment":
                    True,
                "runbook_does_not_invoke_pa014_or_pa015":
                    True,
                "runbook_is_not_resume_authority":
                    True,
                "runbook_is_not_trial_authorization":
                    True,
                "runbook_is_not_deployment_activation":
                    True,
                "runbook_is_not_delivery_authorization":
                    True,
                "runbook_is_not_production_activation":
                    True,
                "runbook_is_not_intervention_authority":
                    True,
                "operator_sequence_requires_separate_governed_authority":
                    True,
            },
        }


def build_governance_release_operator_recovery_runbook(
    *,
    recovery_contract:
        GovernanceReleaseOperatorRecoveryContractResult,
    action_matrix:
        GovernanceReleaseOperatorRecoveryActionMatrixResult,
) -> GovernanceReleaseOperatorRecoveryRunbook:
    _require_types(
        recovery_contract=recovery_contract,
        action_matrix=action_matrix,
    )

    if (
        recovery_contract.release_environment
        != action_matrix.release_environment
    ):
        raise ValueError(
            "recovery contract and action matrix "
            "release environments must match"
        )

    if (
        recovery_contract.backup_id
        != action_matrix.backup_id
    ):
        raise ValueError(
            "recovery contract and action matrix "
            "backup ids must match"
        )

    if (
        recovery_contract.passed
        != action_matrix.recovery_verified
    ):
        raise ValueError(
            "recovery verification state must match"
        )

    if (
        recovery_contract.failure_reasons
        != action_matrix.failure_reasons
    ):
        raise ValueError(
            "failure reasons must match"
        )

    stage = (
        RUNBOOK_STAGE_RECOVERY_VERIFIED
        if recovery_contract.passed
        else RUNBOOK_STAGE_BLOCKED
    )

    return GovernanceReleaseOperatorRecoveryRunbook(
        release_environment=(
            recovery_contract.release_environment
        ),
        backup_id=(
            recovery_contract.backup_id
        ),
        stage=(
            stage
        ),
        recovery_verified=(
            recovery_contract.passed
        ),
        primary_action=(
            action_matrix.primary_action
        ),
        actions=(
            action_matrix.actions
        ),
        failure_reasons=(
            recovery_contract.failure_reasons
        ),
        operator_sequence=(
            OPERATOR_SEQUENCE
        ),
    )


def _require_types(
    *,
    recovery_contract: object,
    action_matrix: object,
) -> None:
    if not isinstance(
        recovery_contract,
        GovernanceReleaseOperatorRecoveryContractResult,
    ):
        raise TypeError(
            "recovery_contract must be a "
            "GovernanceReleaseOperatorRecoveryContractResult"
        )

    if not isinstance(
        action_matrix,
        GovernanceReleaseOperatorRecoveryActionMatrixResult,
    ):
        raise TypeError(
            "action_matrix must be a "
            "GovernanceReleaseOperatorRecoveryActionMatrixResult"
        )