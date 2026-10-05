from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_acceptance_suite import (
    GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_TYPE,
    GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_VERSION,
    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED,
    GovernanceReleaseAcceptanceSuiteResult,
    evaluate_governance_release_acceptance_suite,
)
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
            "synthetic":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "synthetic",
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
            "synthetic":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "synthetic",
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
            "synthetic":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "synthetic",
            )
        ),
    )


def build_recovery_contract(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    passed: bool = True,
    disposition: str = (
        OPERATOR_RECOVERY_DISPOSITION_VERIFIED
    ),
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseOperatorRecoveryContractResult:
    return GovernanceReleaseOperatorRecoveryContractResult(
        release_environment=release_environment,
        backup_id=backup_id,
        disposition=disposition,
        passed=passed,
        checks={
            "synthetic":
                passed,
        },
        failure_reasons=failure_reasons,
    )


def build_recovery_runbook(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    recovery_verified: bool = True,
    stage: str = (
        RUNBOOK_STAGE_RECOVERY_VERIFIED
    ),
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseOperatorRecoveryRunbook:
    return GovernanceReleaseOperatorRecoveryRunbook(
        release_environment=release_environment,
        backup_id=backup_id,
        stage=stage,
        recovery_verified=recovery_verified,
        primary_action=(
            "recovery_verified"
            if recovery_verified
            else "stop_and_preserve"
        ),
        actions=(
            (
                "recovery_verified",
            )
            if recovery_verified
            else (
                "stop_and_preserve",
            )
        ),
        failure_reasons=failure_reasons,
        operator_sequence=(
            "stop_and_preserve_evidence",
            "review_recovery_contract",
            "review_action_matrix",
            "resolve_governed_blockers",
            "rerun_applicable_readiness_checks",
            "stop_before_resume_authority",
        ),
    )


def build_acceptance_suite(
    *,
    backup_recovery_gate:
        GovernanceReleaseBackupRecoveryGateResult
        | None = None,
    runtime_gate:
        GovernanceReleaseRuntimeGateResult
        | None = None,
    security_gate:
        GovernanceReleaseSecurityGateResult
        | None = None,
    recovery_contract:
        GovernanceReleaseOperatorRecoveryContractResult
        | None = None,
    recovery_runbook:
        GovernanceReleaseOperatorRecoveryRunbook
        | None = None,
) -> GovernanceReleaseAcceptanceSuiteResult:
    return evaluate_governance_release_acceptance_suite(
        backup_recovery_gate=(
            backup_recovery_gate
            if backup_recovery_gate is not None
            else build_backup_recovery_gate()
        ),
        runtime_gate=(
            runtime_gate
            if runtime_gate is not None
            else build_runtime_gate()
        ),
        security_gate=(
            security_gate
            if security_gate is not None
            else build_security_gate()
        ),
        recovery_contract=(
            recovery_contract
            if recovery_contract is not None
            else build_recovery_contract()
        ),
        recovery_runbook=(
            recovery_runbook
            if recovery_runbook is not None
            else build_recovery_runbook()
        ),
    )


def test_acceptance_suite_passes_when_all_authoritative_evidence_passes(
) -> None:
    result = build_acceptance_suite()

    assert isinstance(
        result,
        GovernanceReleaseAcceptanceSuiteResult,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"

    assert (
        result.disposition
        == RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    )

    assert result.passed is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "replacement",
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
        (
            "recovery_contract",
            build_recovery_contract(
                passed=False,
                disposition="blocked",
                failure_reasons=(
                    "synthetic",
                ),
            ),
            "operator_recovery_contract_passed",
        ),
        (
            "recovery_runbook",
            build_recovery_runbook(
                recovery_verified=False,
                stage="blocked",
                failure_reasons=(
                    "synthetic",
                ),
            ),
            "operator_recovery_runbook_verified",
        ),
    ),
)
def test_acceptance_suite_blocks_failed_authoritative_evidence(
    argument_name: str,
    replacement: object,
    expected_failure: str,
) -> None:
    kwargs = {
        argument_name:
            replacement,
    }

    result = build_acceptance_suite(
        **kwargs
    )

    assert result.passed is False

    assert (
        result.disposition
        == RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
    )

    assert (
        expected_failure
        in result.failure_reasons
    )


def test_acceptance_suite_rejects_non_paid_trial_environment(
) -> None:
    result = build_acceptance_suite(
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
        recovery_contract=(
            build_recovery_contract(
                release_environment="prelive"
            )
        ),
        recovery_runbook=(
            build_recovery_runbook(
                release_environment="prelive"
            )
        ),
    )

    assert result.passed is False

    assert (
        "paid_trial_environment"
        in result.failure_reasons
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "replacement",
        "expected_failure",
    ),
    (
        (
            "runtime_gate",
            build_runtime_gate(
                release_environment="prelive"
            ),
            "runtime_gate_matches_release_environment",
        ),
        (
            "security_gate",
            build_security_gate(
                release_environment="prelive"
            ),
            "security_gate_matches_release_environment",
        ),
        (
            "recovery_contract",
            build_recovery_contract(
                release_environment="prelive"
            ),
            "operator_contract_matches_release_environment",
        ),
        (
            "recovery_runbook",
            build_recovery_runbook(
                release_environment="prelive"
            ),
            "operator_runbook_matches_release_environment",
        ),
    ),
)
def test_acceptance_suite_blocks_release_environment_mismatch(
    argument_name: str,
    replacement: object,
    expected_failure: str,
) -> None:
    result = build_acceptance_suite(
        **{
            argument_name:
                replacement,
        }
    )

    assert result.passed is False

    assert (
        expected_failure
        in result.failure_reasons
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "replacement",
        "expected_failure",
    ),
    (
        (
            "recovery_contract",
            build_recovery_contract(
                backup_id="backup-002"
            ),
            "operator_contract_matches_backup_identity",
        ),
        (
            "recovery_runbook",
            build_recovery_runbook(
                backup_id="backup-002"
            ),
            "operator_runbook_matches_backup_identity",
        ),
    ),
)
def test_acceptance_suite_blocks_backup_identity_mismatch(
    argument_name: str,
    replacement: object,
    expected_failure: str,
) -> None:
    result = build_acceptance_suite(
        **{
            argument_name:
                replacement,
        }
    )

    assert result.passed is False

    assert (
        expected_failure
        in result.failure_reasons
    )


def test_acceptance_suite_requires_verified_contract_disposition(
) -> None:
    result = build_acceptance_suite(
        recovery_contract=(
            build_recovery_contract(
                disposition="blocked"
            )
        )
    )

    assert result.passed is False

    assert (
        "operator_recovery_contract_verified"
        in result.failure_reasons
    )


def test_acceptance_suite_requires_verified_runbook_stage(
) -> None:
    result = build_acceptance_suite(
        recovery_runbook=(
            build_recovery_runbook(
                stage="blocked"
            )
        )
    )

    assert result.passed is False

    assert (
        "operator_recovery_runbook_stage_verified"
        in result.failure_reasons
    )


def test_acceptance_suite_requires_empty_contract_failure_reasons(
) -> None:
    result = build_acceptance_suite(
        recovery_contract=(
            build_recovery_contract(
                failure_reasons=(
                    "synthetic",
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "operator_contract_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_acceptance_suite_requires_empty_runbook_failure_reasons(
) -> None:
    result = build_acceptance_suite(
        recovery_runbook=(
            build_recovery_runbook(
                failure_reasons=(
                    "synthetic",
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "operator_runbook_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_acceptance_suite_preserves_deterministic_failure_order(
) -> None:
    result = build_acceptance_suite(
        runtime_gate=(
            build_runtime_gate(
                release_environment="prelive",
                passed=False,
            )
        ),
        security_gate=(
            build_security_gate(
                release_environment="prelive",
                passed=False,
            )
        ),
        recovery_contract=(
            build_recovery_contract(
                release_environment="prelive",
                backup_id="backup-002",
                passed=False,
                disposition="blocked",
                failure_reasons=(
                    "synthetic",
                ),
            )
        ),
        recovery_runbook=(
            build_recovery_runbook(
                release_environment="prelive",
                backup_id="backup-002",
                recovery_verified=False,
                stage="blocked",
                failure_reasons=(
                    "synthetic",
                ),
            )
        ),
    )

    assert result.failure_reasons == (
        "runtime_gate_passed",
        "security_gate_passed",
        "operator_recovery_contract_passed",
        "operator_recovery_contract_verified",
        "operator_recovery_runbook_verified",
        "operator_recovery_runbook_stage_verified",
        "runtime_gate_matches_release_environment",
        "security_gate_matches_release_environment",
        "operator_contract_matches_release_environment",
        "operator_runbook_matches_release_environment",
        "operator_contract_matches_backup_identity",
        "operator_runbook_matches_backup_identity",
        "operator_contract_has_no_failure_reasons",
        "operator_runbook_has_no_failure_reasons",
    )


def test_acceptance_suite_public_projection_preserves_boundaries(
) -> None:
    payload = (
        build_acceptance_suite()
        .to_dict()
    )

    assert (
        payload["suite_type"]
        == GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_ACCEPTANCE_SUITE_VERSION
    )

    assert payload["release_environment"] == "paid_trial"
    assert payload["backup_id"] == "backup-001"

    assert (
        payload["disposition"]
        == RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    )

    assert payload["passed"] is True
    assert payload["failure_reasons"] == []

    boundaries = payload["boundaries"]

    expected_boundaries = {
        "suite_is_read_only",
        "suite_evaluates_existing_evidence_only",
        "suite_does_not_execute_backup",
        "suite_does_not_execute_restore",
        "suite_does_not_start_or_restart_process",
        "suite_does_not_resolve_secret_material",
        "suite_does_not_execute_paid_assessment",
        "suite_does_not_invoke_pa014_or_pa015",
        "acceptance_passed_is_not_trial_authorization",
        "acceptance_passed_is_not_deployment_authorization",
        "acceptance_passed_is_not_customer_execution_authority",
        "acceptance_passed_is_not_delivery_authorization",
        "acceptance_passed_is_not_production_activation",
        "acceptance_passed_is_not_intervention_authority",
        "acceptance_requires_separate_release_authorization_gate",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )


def test_acceptance_suite_result_is_immutable(
) -> None:
    result = build_acceptance_suite()

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
        "recovery_contract",
        "recovery_runbook",
    ),
)
def test_acceptance_suite_rejects_wrong_input_type(
    argument_name: str,
) -> None:
    kwargs = {
        "backup_recovery_gate":
            build_backup_recovery_gate(),
        "runtime_gate":
            build_runtime_gate(),
        "security_gate":
            build_security_gate(),
        "recovery_contract":
            build_recovery_contract(),
        "recovery_runbook":
            build_recovery_runbook(),
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError,
    ):
        evaluate_governance_release_acceptance_suite(
            backup_recovery_gate=kwargs[
                "backup_recovery_gate"
            ],
            runtime_gate=kwargs[
                "runtime_gate"
            ],
            security_gate=kwargs[
                "security_gate"
            ],
            recovery_contract=kwargs[
                "recovery_contract"
            ],
            recovery_runbook=kwargs[
                "recovery_runbook"
            ],
        )