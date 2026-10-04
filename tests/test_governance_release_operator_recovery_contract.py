from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_backup_recovery_gate import (
    GovernanceReleaseBackupRecoveryGateResult,
)
from backend.app.gagf.governance_release_operator_recovery_contract import (
    GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_TYPE,
    GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_VERSION,
    OPERATOR_RECOVERY_DISPOSITION_BLOCKED,
    OPERATOR_RECOVERY_DISPOSITION_VERIFIED,
    GovernanceReleaseOperatorRecoveryContractResult,
    evaluate_governance_release_operator_recovery_contract,
)
from backend.app.gagf.governance_release_runtime_gate import (
    GovernanceReleaseRuntimeGateResult,
)
from backend.app.gagf.governance_release_security_gate import (
    GovernanceReleaseSecurityGateResult,
)


def build_backup_recovery_gate(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    passed: bool = True,
) -> GovernanceReleaseBackupRecoveryGateResult:
    return GovernanceReleaseBackupRecoveryGateResult(
        release_environment=release_environment,
        backup_id=backup_id,
        passed=passed,
        checks={
            "backup_recovery_ready":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "backup_recovery_not_ready",
            )
        ),
    )


def build_runtime_gate(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseRuntimeGateResult:
    return GovernanceReleaseRuntimeGateResult(
        release_environment=release_environment,
        passed=passed,
        checks={
            "runtime_ready":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "runtime_not_ready",
            )
        ),
    )


def build_security_gate(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseSecurityGateResult:
    return GovernanceReleaseSecurityGateResult(
        release_environment=release_environment,
        passed=passed,
        checks={
            "security_ready":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "security_not_ready",
            )
        ),
    )


def build_contract_kwargs(
) -> dict[str, object]:
    return {
        "backup_recovery_gate":
            build_backup_recovery_gate(),
        "runtime_gate":
            build_runtime_gate(),
        "security_gate":
            build_security_gate(),
    }


def evaluate(
    **overrides: object,
) -> GovernanceReleaseOperatorRecoveryContractResult:
    kwargs = build_contract_kwargs()

    kwargs.update(
        overrides
    )

    return evaluate_governance_release_operator_recovery_contract(
        backup_recovery_gate=kwargs[
            "backup_recovery_gate"
        ],
        runtime_gate=kwargs[
            "runtime_gate"
        ],
        security_gate=kwargs[
            "security_gate"
        ],
    )


def test_operator_recovery_contract_passes_when_all_gates_pass(
) -> None:
    result = evaluate()

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"
    assert result.passed is True

    assert (
        result.disposition
        == OPERATOR_RECOVERY_DISPOSITION_VERIFIED
    )

    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_operator_recovery_contract_requires_paid_trial(
) -> None:
    result = evaluate(
        backup_recovery_gate=(
            build_backup_recovery_gate(
                release_environment="prelive"
            )
        ),
        runtime_gate=(
            build_runtime_gate(
                release_environment="prelive"
            )
        ),
        security_gate=(
            build_security_gate(
                release_environment="prelive"
            )
        ),
    )

    assert result.passed is False

    assert (
        result.disposition
        == OPERATOR_RECOVERY_DISPOSITION_BLOCKED
    )

    assert result.failure_reasons == (
        "paid_trial_environment",
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "failed_value",
        "expected_failure",
    ),
    (
        (
            "backup_recovery_gate",
            build_backup_recovery_gate(
                passed=False
            ),
            "backup_recovery_gate_passed",
        ),
        (
            "runtime_gate",
            build_runtime_gate(
                passed=False
            ),
            "runtime_gate_passed",
        ),
        (
            "security_gate",
            build_security_gate(
                passed=False
            ),
            "security_gate_passed",
        ),
    ),
)
def test_operator_recovery_contract_blocks_failed_gate(
    argument_name: str,
    failed_value: object,
    expected_failure: str,
) -> None:
    result = evaluate(
        **{
            argument_name:
                failed_value,
        }
    )

    assert result.passed is False

    assert (
        result.disposition
        == OPERATOR_RECOVERY_DISPOSITION_BLOCKED
    )

    assert (
        expected_failure
        in result.failure_reasons
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "mismatched_value",
        "expected_failure",
    ),
    (
        (
            "runtime_gate",
            build_runtime_gate(
                release_environment="prelive"
            ),
            "runtime_gate_matches_recovery_environment",
        ),
        (
            "security_gate",
            build_security_gate(
                release_environment="prelive"
            ),
            "security_gate_matches_recovery_environment",
        ),
    ),
)
def test_operator_recovery_contract_rejects_environment_mismatch(
    argument_name: str,
    mismatched_value: object,
    expected_failure: str,
) -> None:
    result = evaluate(
        **{
            argument_name:
                mismatched_value,
        }
    )

    assert result.passed is False

    assert (
        expected_failure
        in result.failure_reasons
    )


def test_operator_recovery_contract_failure_order_is_deterministic(
) -> None:
    result = evaluate(
        backup_recovery_gate=(
            build_backup_recovery_gate(
                release_environment="prelive",
                passed=False,
            )
        ),
        runtime_gate=(
            build_runtime_gate(
                release_environment="paid_trial",
                passed=False,
            )
        ),
        security_gate=(
            build_security_gate(
                release_environment="test",
                passed=False,
            )
        ),
    )

    assert result.passed is False

    assert result.failure_reasons == (
        "paid_trial_environment",
        "backup_recovery_gate_passed",
        "runtime_gate_passed",
        "security_gate_passed",
        "runtime_gate_matches_recovery_environment",
        "security_gate_matches_recovery_environment",
    )


def test_operator_recovery_contract_public_projection_preserves_boundaries(
) -> None:
    payload = evaluate().to_dict()

    assert (
        payload["contract_type"]
        == GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_OPERATOR_RECOVERY_CONTRACT_VERSION
    )

    assert payload[
        "release_environment"
    ] == "paid_trial"

    assert payload[
        "backup_id"
    ] == "backup-001"

    assert (
        payload["disposition"]
        == OPERATOR_RECOVERY_DISPOSITION_VERIFIED
    )

    assert payload["passed"] is True

    assert payload[
        "failure_reasons"
    ] == []

    boundaries = payload[
        "boundaries"
    ]

    assert isinstance(
        boundaries,
        dict,
    )

    expected_boundaries = {
        "contract_is_read_only",
        "contract_evaluates_existing_evidence_only",
        "contract_does_not_execute_backup",
        "contract_does_not_execute_restore",
        "contract_does_not_start_process",
        "contract_does_not_restart_process",
        "contract_does_not_resolve_secret_material",
        "contract_does_not_execute_paid_assessment",
        "contract_does_not_invoke_pa014_or_pa015",
        "contract_is_not_deployment_activation",
        "contract_is_not_trial_authorization",
        "contract_is_not_customer_execution_authority",
        "contract_is_not_delivery_authorization",
        "contract_is_not_production_activation",
        "contract_is_not_intervention_authority",
        "recovery_verified_is_not_resume_authority",
    }

    assert (
        set(
            boundaries
        )
        == expected_boundaries
    )

    assert all(
        value is True
        for value
        in boundaries.values()
    )


def test_operator_recovery_contract_result_is_immutable(
) -> None:
    result = evaluate()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.passed = False


@pytest.mark.parametrize(
    "argument_name",
    (
        "backup_recovery_gate",
        "runtime_gate",
        "security_gate",
    ),
)
def test_operator_recovery_contract_rejects_wrong_evidence_type(
    argument_name: str,
) -> None:
    kwargs = build_contract_kwargs()

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError,
    ):
        evaluate_governance_release_operator_recovery_contract(
            backup_recovery_gate=kwargs[
                "backup_recovery_gate"
            ],
            runtime_gate=kwargs[
                "runtime_gate"
            ],
            security_gate=kwargs[
                "security_gate"
            ],
        )