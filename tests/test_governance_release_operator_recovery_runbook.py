from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_operator_recovery_action_matrix import (
    ACTION_INSPECT_RUNTIME_READINESS,
    ACTION_RECOVERY_VERIFIED,
    ACTION_STOP_AND_PRESERVE,
    GovernanceReleaseOperatorRecoveryActionMatrixResult,
)
from backend.app.gagf.governance_release_operator_recovery_contract import (
    OPERATOR_RECOVERY_DISPOSITION_BLOCKED,
    OPERATOR_RECOVERY_DISPOSITION_VERIFIED,
    GovernanceReleaseOperatorRecoveryContractResult,
)
from backend.app.gagf.governance_release_operator_recovery_runbook import (
    GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_TYPE,
    GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_VERSION,
    OPERATOR_SEQUENCE,
    RUNBOOK_STAGE_BLOCKED,
    RUNBOOK_STAGE_RECOVERY_VERIFIED,
    GovernanceReleaseOperatorRecoveryRunbook,
    build_governance_release_operator_recovery_runbook,
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


def build_action_matrix(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    recovery_verified: bool = True,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseOperatorRecoveryActionMatrixResult:
    if recovery_verified:
        primary_action = (
            ACTION_RECOVERY_VERIFIED
        )

        actions = (
            ACTION_RECOVERY_VERIFIED,
        )
    else:
        primary_action = (
            ACTION_STOP_AND_PRESERVE
        )

        actions = (
            ACTION_STOP_AND_PRESERVE,
            ACTION_INSPECT_RUNTIME_READINESS,
        )

    return GovernanceReleaseOperatorRecoveryActionMatrixResult(
        release_environment=release_environment,
        backup_id=backup_id,
        recovery_verified=recovery_verified,
        primary_action=primary_action,
        actions=actions,
        failure_reasons=failure_reasons,
    )


def build_runbook(
    *,
    contract: GovernanceReleaseOperatorRecoveryContractResult
        | None = None,
    action_matrix:
        GovernanceReleaseOperatorRecoveryActionMatrixResult
        | None = None,
) -> GovernanceReleaseOperatorRecoveryRunbook:
    if contract is None:
        contract = build_contract()

    if action_matrix is None:
        action_matrix = build_action_matrix()

    return build_governance_release_operator_recovery_runbook(
        recovery_contract=contract,
        action_matrix=action_matrix,
    )


def test_runbook_projects_verified_recovery(
) -> None:
    result = build_runbook()

    assert isinstance(
        result,
        GovernanceReleaseOperatorRecoveryRunbook,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"

    assert (
        result.stage
        == RUNBOOK_STAGE_RECOVERY_VERIFIED
    )

    assert result.recovery_verified is True

    assert (
        result.primary_action
        == ACTION_RECOVERY_VERIFIED
    )

    assert result.actions == (
        ACTION_RECOVERY_VERIFIED,
    )

    assert result.failure_reasons == ()

    assert (
        result.operator_sequence
        == OPERATOR_SEQUENCE
    )


def test_runbook_projects_blocked_recovery(
) -> None:
    failure_reasons = (
        "runtime_gate_passed",
    )

    result = build_runbook(
        contract=(
            build_contract(
                passed=False,
                failure_reasons=failure_reasons,
            )
        ),
        action_matrix=(
            build_action_matrix(
                recovery_verified=False,
                failure_reasons=failure_reasons,
            )
        ),
    )

    assert (
        result.stage
        == RUNBOOK_STAGE_BLOCKED
    )

    assert result.recovery_verified is False

    assert (
        result.primary_action
        == ACTION_STOP_AND_PRESERVE
    )

    assert result.actions == (
        ACTION_STOP_AND_PRESERVE,
        ACTION_INSPECT_RUNTIME_READINESS,
    )

    assert (
        result.failure_reasons
        == failure_reasons
    )


def test_runbook_rejects_release_environment_mismatch(
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "release environments must match"
        ),
    ):
        build_runbook(
            action_matrix=(
                build_action_matrix(
                    release_environment="prelive"
                )
            )
        )


def test_runbook_rejects_backup_id_mismatch(
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "backup ids must match"
        ),
    ):
        build_runbook(
            action_matrix=(
                build_action_matrix(
                    backup_id="backup-002"
                )
            )
        )


def test_runbook_rejects_recovery_verification_mismatch(
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "recovery verification state must match"
        ),
    ):
        build_runbook(
            action_matrix=(
                build_action_matrix(
                    recovery_verified=False
                )
            )
        )


def test_runbook_rejects_failure_reason_mismatch(
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "failure reasons must match"
        ),
    ):
        build_runbook(
            contract=(
                build_contract(
                    passed=False,
                    failure_reasons=(
                        "runtime_gate_passed",
                    ),
                )
            ),
            action_matrix=(
                build_action_matrix(
                    recovery_verified=False,
                    failure_reasons=(
                        "security_gate_passed",
                    ),
                )
            ),
        )


def test_runbook_operator_sequence_is_fixed_and_ordered(
) -> None:
    result = build_runbook()

    assert result.operator_sequence == (
        "stop_and_preserve_evidence",
        "review_recovery_contract",
        "review_action_matrix",
        "resolve_governed_blockers",
        "rerun_applicable_readiness_checks",
        "stop_before_resume_authority",
    )


def test_runbook_public_projection_preserves_boundaries(
) -> None:
    payload = build_runbook().to_dict()

    assert (
        payload["runbook_type"]
        == GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_OPERATOR_RECOVERY_RUNBOOK_VERSION
    )

    assert payload[
        "release_environment"
    ] == "paid_trial"

    assert payload[
        "backup_id"
    ] == "backup-001"

    assert (
        payload["stage"]
        == RUNBOOK_STAGE_RECOVERY_VERIFIED
    )

    assert payload[
        "recovery_verified"
    ] is True

    assert (
        payload["primary_action"]
        == ACTION_RECOVERY_VERIFIED
    )

    assert payload[
        "operator_sequence"
    ] == list(
        OPERATOR_SEQUENCE
    )

    boundaries = payload[
        "boundaries"
    ]

    assert isinstance(
        boundaries,
        dict,
    )

    expected_boundaries = {
        "runbook_is_read_only",
        "runbook_projects_existing_evidence_only",
        "runbook_does_not_execute_backup",
        "runbook_does_not_execute_restore",
        "runbook_does_not_start_or_restart_process",
        "runbook_does_not_resolve_secret_material",
        "runbook_does_not_execute_paid_assessment",
        "runbook_does_not_invoke_pa014_or_pa015",
        "runbook_is_not_resume_authority",
        "runbook_is_not_trial_authorization",
        "runbook_is_not_deployment_activation",
        "runbook_is_not_delivery_authorization",
        "runbook_is_not_production_activation",
        "runbook_is_not_intervention_authority",
        "operator_sequence_requires_separate_governed_authority",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value
        in boundaries.values()
    )


def test_runbook_result_is_immutable(
) -> None:
    result = build_runbook()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.stage = RUNBOOK_STAGE_BLOCKED


@pytest.mark.parametrize(
    "argument_name",
    (
        "recovery_contract",
        "action_matrix",
    ),
)
def test_runbook_rejects_wrong_input_type(
    argument_name: str,
) -> None:
    kwargs = {
        "recovery_contract":
            build_contract(),
        "action_matrix":
            build_action_matrix(),
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError,
    ):
        build_governance_release_operator_recovery_runbook(
            recovery_contract=kwargs[
                "recovery_contract"
            ],
            action_matrix=kwargs[
                "action_matrix"
            ],
        )