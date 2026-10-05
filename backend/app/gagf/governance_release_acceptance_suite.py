from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_backup_recovery_gate import (
    GovernanceReleaseBackupRecoveryGateResult,
)
from backend.app.gagf.governance_release_operator_recovery_contract import (
    OPERATOR_RECOVERY_DISPOSITION_VERIFIED,
    GovernanceReleaseOperatorRecoveryContractResult,
)
from backend.app.gagf.governance_release_operator_recovery_runbook import (
    RUNBOOK_STAGE_RECOVERY_VERIFIED,
    GovernanceReleaseOperatorRecoveryRunbook,
)
from backend.app.gagf.governance_release_runtime_gate import (
    GovernanceReleaseRuntimeGateResult,
)
from backend.app.gagf.governance_release_security_gate import (
    GovernanceReleaseSecurityGateResult,
)


GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_TYPE = (
    "governance-release-acceptance-suite"
)

GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_VERSION = (
    "0.1.0"
)

RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED = (
    "acceptance_passed"
)

RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED = (
    "blocked"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseAcceptanceSuiteResult:
    release_environment: str
    backup_id: str
    disposition: str
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    suite_type: str = (
        GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "suite_type":
                self.suite_type,
            "version":
                self.version,
            "release_environment":
                self.release_environment,
            "backup_id":
                self.backup_id,
            "disposition":
                self.disposition,
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
                "suite_is_read_only":
                    True,
                "suite_evaluates_existing_evidence_only":
                    True,
                "suite_does_not_execute_backup":
                    True,
                "suite_does_not_execute_restore":
                    True,
                "suite_does_not_start_or_restart_process":
                    True,
                "suite_does_not_resolve_secret_material":
                    True,
                "suite_does_not_execute_paid_assessment":
                    True,
                "suite_does_not_invoke_pa014_or_pa015":
                    True,
                "acceptance_passed_is_not_trial_authorization":
                    True,
                "acceptance_passed_is_not_deployment_authorization":
                    True,
                "acceptance_passed_is_not_customer_execution_authority":
                    True,
                "acceptance_passed_is_not_delivery_authorization":
                    True,
                "acceptance_passed_is_not_production_activation":
                    True,
                "acceptance_passed_is_not_intervention_authority":
                    True,
                "acceptance_requires_separate_release_authorization_gate":
                    True,
            },
        }


def evaluate_governance_release_acceptance_suite(
    *,
    backup_recovery_gate:
        GovernanceReleaseBackupRecoveryGateResult,
    runtime_gate:
        GovernanceReleaseRuntimeGateResult,
    security_gate:
        GovernanceReleaseSecurityGateResult,
    recovery_contract:
        GovernanceReleaseOperatorRecoveryContractResult,
    recovery_runbook:
        GovernanceReleaseOperatorRecoveryRunbook,
) -> GovernanceReleaseAcceptanceSuiteResult:
    _require_types(
        backup_recovery_gate=backup_recovery_gate,
        runtime_gate=runtime_gate,
        security_gate=security_gate,
        recovery_contract=recovery_contract,
        recovery_runbook=recovery_runbook,
    )

    release_environment = (
        backup_recovery_gate.release_environment
    )

    backup_id = (
        backup_recovery_gate.backup_id
    )

    checks = {
        "paid_trial_environment":
            release_environment
            == "paid_trial",

        "backup_recovery_gate_passed":
            backup_recovery_gate.passed
            is True,

        "runtime_gate_passed":
            runtime_gate.passed
            is True,

        "security_gate_passed":
            security_gate.passed
            is True,

        "operator_recovery_contract_passed":
            recovery_contract.passed
            is True,

        "operator_recovery_contract_verified":
            recovery_contract.disposition
            == OPERATOR_RECOVERY_DISPOSITION_VERIFIED,

        "operator_recovery_runbook_verified":
            recovery_runbook.recovery_verified
            is True,

        "operator_recovery_runbook_stage_verified":
            recovery_runbook.stage
            == RUNBOOK_STAGE_RECOVERY_VERIFIED,

        "runtime_gate_matches_release_environment":
            runtime_gate.release_environment
            == release_environment,

        "security_gate_matches_release_environment":
            security_gate.release_environment
            == release_environment,

        "operator_contract_matches_release_environment":
            recovery_contract.release_environment
            == release_environment,

        "operator_runbook_matches_release_environment":
            recovery_runbook.release_environment
            == release_environment,

        "operator_contract_matches_backup_identity":
            recovery_contract.backup_id
            == backup_id,

        "operator_runbook_matches_backup_identity":
            recovery_runbook.backup_id
            == backup_id,

        "operator_contract_has_no_failure_reasons":
            recovery_contract.failure_reasons
            == (),

        "operator_runbook_has_no_failure_reasons":
            recovery_runbook.failure_reasons
            == (),
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    passed = (
        not failure_reasons
    )

    disposition = (
        RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
        if passed
        else RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
    )

    return GovernanceReleaseAcceptanceSuiteResult(
        release_environment=(
            release_environment
        ),
        backup_id=(
            backup_id
        ),
        disposition=(
            disposition
        ),
        passed=(
            passed
        ),
        checks=(
            checks
        ),
        failure_reasons=(
            failure_reasons
        ),
    )


def _require_types(
    *,
    backup_recovery_gate: object,
    runtime_gate: object,
    security_gate: object,
    recovery_contract: object,
    recovery_runbook: object,
) -> None:
    if not isinstance(
        backup_recovery_gate,
        GovernanceReleaseBackupRecoveryGateResult,
    ):
        raise TypeError(
            "backup_recovery_gate must be a "
            "GovernanceReleaseBackupRecoveryGateResult"
        )

    if not isinstance(
        runtime_gate,
        GovernanceReleaseRuntimeGateResult,
    ):
        raise TypeError(
            "runtime_gate must be a "
            "GovernanceReleaseRuntimeGateResult"
        )

    if not isinstance(
        security_gate,
        GovernanceReleaseSecurityGateResult,
    ):
        raise TypeError(
            "security_gate must be a "
            "GovernanceReleaseSecurityGateResult"
        )

    if not isinstance(
        recovery_contract,
        GovernanceReleaseOperatorRecoveryContractResult,
    ):
        raise TypeError(
            "recovery_contract must be a "
            "GovernanceReleaseOperatorRecoveryContractResult"
        )

    if not isinstance(
        recovery_runbook,
        GovernanceReleaseOperatorRecoveryRunbook,
    ):
        raise TypeError(
            "recovery_runbook must be a "
            "GovernanceReleaseOperatorRecoveryRunbook"
        )