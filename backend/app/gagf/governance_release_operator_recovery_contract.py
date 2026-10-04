from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_backup_recovery_gate import (
    GovernanceReleaseBackupRecoveryGateResult,
)
from backend.app.gagf.governance_release_runtime_gate import (
    GovernanceReleaseRuntimeGateResult,
)
from backend.app.gagf.governance_release_security_gate import (
    GovernanceReleaseSecurityGateResult,
)


GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_TYPE = (
    "governance-release-operator-recovery-contract"
)

GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_VERSION = (
    "0.1.0"
)

OPERATOR_RECOVERY_DISPOSITION_VERIFIED = (
    "recovery_verified"
)

OPERATOR_RECOVERY_DISPOSITION_BLOCKED = (
    "blocked"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseOperatorRecoveryContractResult:
    release_environment: str
    backup_id: str
    disposition: str
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    contract_type: str = (
        GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "contract_type":
                self.contract_type,
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
                "contract_is_read_only":
                    True,
                "contract_evaluates_existing_evidence_only":
                    True,
                "contract_does_not_execute_backup":
                    True,
                "contract_does_not_execute_restore":
                    True,
                "contract_does_not_start_process":
                    True,
                "contract_does_not_restart_process":
                    True,
                "contract_does_not_resolve_secret_material":
                    True,
                "contract_does_not_execute_paid_assessment":
                    True,
                "contract_does_not_invoke_pa014_or_pa015":
                    True,
                "contract_is_not_deployment_activation":
                    True,
                "contract_is_not_trial_authorization":
                    True,
                "contract_is_not_customer_execution_authority":
                    True,
                "contract_is_not_delivery_authorization":
                    True,
                "contract_is_not_production_activation":
                    True,
                "contract_is_not_intervention_authority":
                    True,
                "recovery_verified_is_not_resume_authority":
                    True,
            },
        }


def evaluate_governance_release_operator_recovery_contract(
    *,
    backup_recovery_gate:
        GovernanceReleaseBackupRecoveryGateResult,
    runtime_gate:
        GovernanceReleaseRuntimeGateResult,
    security_gate:
        GovernanceReleaseSecurityGateResult,
) -> GovernanceReleaseOperatorRecoveryContractResult:
    _require_types(
        backup_recovery_gate=backup_recovery_gate,
        runtime_gate=runtime_gate,
        security_gate=security_gate,
    )

    release_environment = (
        backup_recovery_gate.release_environment
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
        "runtime_gate_matches_recovery_environment":
            runtime_gate.release_environment
            == release_environment,
        "security_gate_matches_recovery_environment":
            security_gate.release_environment
            == release_environment,
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
        OPERATOR_RECOVERY_DISPOSITION_VERIFIED
        if passed
        else OPERATOR_RECOVERY_DISPOSITION_BLOCKED
    )

    return GovernanceReleaseOperatorRecoveryContractResult(
        release_environment=(
            release_environment
        ),
        backup_id=(
            backup_recovery_gate.backup_id
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
) -> None:
    expected = (
        (
            "backup_recovery_gate",
            backup_recovery_gate,
            GovernanceReleaseBackupRecoveryGateResult,
        ),
        (
            "runtime_gate",
            runtime_gate,
            GovernanceReleaseRuntimeGateResult,
        ),
        (
            "security_gate",
            security_gate,
            GovernanceReleaseSecurityGateResult,
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