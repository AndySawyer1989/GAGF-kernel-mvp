from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_operator_recovery_action_matrix import (
    ACTION_INSPECT_BACKUP_RECOVERY,
    ACTION_INSPECT_RUNTIME_READINESS,
    ACTION_INSPECT_SECURITY_READINESS,
    ACTION_RECOVERY_VERIFIED,
    ACTION_RESOLVE_ENVIRONMENT_MISMATCH,
    ACTION_STOP_AND_PRESERVE,
    GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_TYPE,
    GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_VERSION,
    GovernanceReleaseOperatorRecoveryActionMatrixResult,
    classify_governance_release_operator_recovery_action,
)
from backend.app.gagf.governance_release_operator_recovery_contract import (
    OPERATOR_RECOVERY_DISPOSITION_BLOCKED,
    OPERATOR_RECOVERY_DISPOSITION_VERIFIED,
    GovernanceReleaseOperatorRecoveryContractResult,
)


def build_contract(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    passed: bool = True,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseOperatorRecoveryContractResult:
    return GovernanceReleaseOperatorRecoveryContractResult(
        release_environment=release_environment,
        backup_id=backup_id,
        disposition=(
            OPERATOR_RECOVERY_DISPOSITION_VERIFIED
            if passed
            else OPERATOR_RECOVERY_DISPOSITION_BLOCKED
        ),
        passed=passed,
        checks={
            "synthetic":
                passed,
        },
        failure_reasons=failure_reasons,
    )


def test_action_matrix_returns_verified_when_recovery_contract_passes(
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=build_contract()
        )
    )

    assert isinstance(
        result,
        GovernanceReleaseOperatorRecoveryActionMatrixResult,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"
    assert result.recovery_verified is True
    assert result.primary_action == ACTION_RECOVERY_VERIFIED
    assert result.actions == (
        ACTION_RECOVERY_VERIFIED,
    )
    assert result.failure_reasons == ()


def test_action_matrix_stops_and_preserves_on_failed_contract(
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=(
                build_contract(
                    passed=False,
                    failure_reasons=(
                        "backup_recovery_gate_passed",
                    ),
                )
            )
        )
    )

    assert result.recovery_verified is False
    assert result.primary_action == ACTION_STOP_AND_PRESERVE

    assert result.actions[0] == (
        ACTION_STOP_AND_PRESERVE
    )


@pytest.mark.parametrize(
    (
        "failure_reason",
        "expected_action",
    ),
    (
        (
            "backup_recovery_gate_passed",
            ACTION_INSPECT_BACKUP_RECOVERY,
        ),
        (
            "runtime_gate_passed",
            ACTION_INSPECT_RUNTIME_READINESS,
        ),
        (
            "security_gate_passed",
            ACTION_INSPECT_SECURITY_READINESS,
        ),
    ),
)
def test_action_matrix_maps_gate_failure_to_inspection_action(
    failure_reason: str,
    expected_action: str,
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=(
                build_contract(
                    passed=False,
                    failure_reasons=(
                        failure_reason,
                    ),
                )
            )
        )
    )

    assert result.actions == (
        ACTION_STOP_AND_PRESERVE,
        expected_action,
    )


@pytest.mark.parametrize(
    "failure_reason",
    (
        "paid_trial_environment",
        "runtime_gate_matches_recovery_environment",
        "security_gate_matches_recovery_environment",
    ),
)
def test_action_matrix_maps_environment_failure(
    failure_reason: str,
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=(
                build_contract(
                    passed=False,
                    failure_reasons=(
                        failure_reason,
                    ),
                )
            )
        )
    )

    assert result.actions == (
        ACTION_STOP_AND_PRESERVE,
        ACTION_RESOLVE_ENVIRONMENT_MISMATCH,
    )


def test_action_matrix_preserves_deterministic_action_order(
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=(
                build_contract(
                    passed=False,
                    failure_reasons=(
                        "security_gate_passed",
                        "runtime_gate_matches_recovery_environment",
                        "backup_recovery_gate_passed",
                        "runtime_gate_passed",
                    ),
                )
            )
        )
    )

    assert result.actions == (
        ACTION_STOP_AND_PRESERVE,
        ACTION_RESOLVE_ENVIRONMENT_MISMATCH,
        ACTION_INSPECT_BACKUP_RECOVERY,
        ACTION_INSPECT_RUNTIME_READINESS,
        ACTION_INSPECT_SECURITY_READINESS,
    )


def test_action_matrix_deduplicates_environment_action(
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=(
                build_contract(
                    passed=False,
                    failure_reasons=(
                        "paid_trial_environment",
                        "runtime_gate_matches_recovery_environment",
                        "security_gate_matches_recovery_environment",
                    ),
                )
            )
        )
    )

    assert result.actions == (
        ACTION_STOP_AND_PRESERVE,
        ACTION_RESOLVE_ENVIRONMENT_MISMATCH,
    )


def test_action_matrix_preserves_failure_reasons(
) -> None:
    failure_reasons = (
        "backup_recovery_gate_passed",
        "security_gate_passed",
    )

    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=(
                build_contract(
                    passed=False,
                    failure_reasons=failure_reasons,
                )
            )
        )
    )

    assert result.failure_reasons == failure_reasons


def test_action_matrix_public_projection_preserves_boundaries(
) -> None:
    payload = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=build_contract()
        ).to_dict()
    )

    assert (
        payload["matrix_type"]
        == GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_OPERATOR_RECOVERY_ACTION_MATRIX_VERSION
    )

    assert payload["release_environment"] == "paid_trial"
    assert payload["backup_id"] == "backup-001"
    assert payload["recovery_verified"] is True
    assert payload["primary_action"] == ACTION_RECOVERY_VERIFIED
    assert payload["actions"] == [
        ACTION_RECOVERY_VERIFIED,
    ]
    assert payload["failure_reasons"] == []

    boundaries = payload["boundaries"]

    assert isinstance(
        boundaries,
        dict,
    )

    expected_boundaries = {
        "matrix_is_read_only",
        "matrix_classifies_existing_failure_reasons_only",
        "matrix_does_not_execute_recovery",
        "matrix_does_not_execute_restore",
        "matrix_does_not_retry_process",
        "matrix_does_not_resume_paid_assessment",
        "matrix_does_not_invoke_pa014_or_pa015",
        "matrix_is_not_trial_authorization",
        "matrix_is_not_deployment_activation",
        "matrix_is_not_delivery_authorization",
        "matrix_is_not_production_activation",
        "matrix_is_not_intervention_authority",
        "operator_action_is_not_execution_authority",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )


def test_action_matrix_result_is_immutable(
) -> None:
    result = (
        classify_governance_release_operator_recovery_action(
            recovery_contract=build_contract()
        )
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.primary_action = ACTION_STOP_AND_PRESERVE


def test_action_matrix_rejects_wrong_contract_type(
) -> None:
    with pytest.raises(
        TypeError,
    ):
        classify_governance_release_operator_recovery_action(
            recovery_contract=object()
        )