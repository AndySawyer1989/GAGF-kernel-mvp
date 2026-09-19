from pathlib import Path

import pytest

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
from backend.app.gagf.governance_release_runtime_gate import (
    evaluate_governance_release_runtime_gate,
)
from backend.app.gagf.governance_release_runtime_preflight import (
    GovernanceReleaseRuntimePreflightResult,
)


def build_start_receipt(
    *,
    release_environment: str = "paid_trial",
    health_status_code: int = 200,
) -> GovernanceReleaseProcessStartReceipt:
    return GovernanceReleaseProcessStartReceipt(
        host="127.0.0.1",
        port=8123,
        health_status_code=(
            health_status_code
        ),
        version_status_code=200,
        storage_status_code=200,
        release_environment=(
            release_environment
        ),
        storage_paths_exposed=False,
    )


def build_preflight(
    *,
    passed: bool = True,
    release_environment: str = "paid_trial",
) -> GovernanceReleaseRuntimePreflightResult:
    return GovernanceReleaseRuntimePreflightResult(
        release_environment=(
            release_environment
        ),
        effective_data_root=(
            Path("C:/release/paid_trial")
        ),
        passed=passed,
        checks={
            "paid_trial_environment":
                passed,
        },
        failure_reasons=(
            ()
            if passed
            else (
                "paid_trial_environment",
            )
        ),
    )


def build_restart(
    *,
    restart_succeeded: bool = True,
    release_environment: str = "paid_trial",
) -> GovernanceReleaseProcessRestartReceipt:
    first = build_start_receipt(
        release_environment=(
            release_environment
        )
    )

    second = build_start_receipt(
        release_environment=(
            release_environment
        )
    )

    return GovernanceReleaseProcessRestartReceipt(
        host="127.0.0.1",
        port=8123,
        first_start=first,
        second_start=second,
        same_release_environment=True,
        same_network_binding=True,
        restart_succeeded=(
            restart_succeeded
        ),
    )


def build_persistence(
    *,
    persistence_proven: bool = True,
    repository_chain_valid: bool = True,
) -> GovernanceReleaseRestartPersistenceReceipt:
    return GovernanceReleaseRestartPersistenceReceipt(
        tenant_id="restart-tenant",
        client_id="restart-client",
        engagement_id="restart-engagement",
        assessment_id="restart-assessment",
        current_stage=(
            "client_response_recorded"
        ),
        pending_next_step="none",
        lifecycle_artifact_count=3,
        repository_chain_valid=(
            repository_chain_valid
        ),
        first_runtime_healthy=True,
        second_runtime_healthy=True,
        persistence_proven=(
            persistence_proven
        ),
    )


def build_failure_probe(
    *,
    failure_proven: bool = True,
    exit_code: int | None = 1,
) -> GovernanceReleaseRuntimeFailureReceipt:
    return GovernanceReleaseRuntimeFailureReceipt(
        host="127.0.0.1",
        port=8124,
        process_exited=True,
        health_reached=False,
        exit_code=exit_code,
        failure_proven=(
            failure_proven
        ),
    )


def evaluate_default():
    return evaluate_governance_release_runtime_gate(
        preflight=build_preflight(),
        process_start=(
            build_start_receipt()
        ),
        process_restart=(
            build_restart()
        ),
        persistence=(
            build_persistence()
        ),
        failure_probe=(
            build_failure_probe()
        ),
    )


def test_complete_runtime_evidence_passes() -> None:
    result = evaluate_default()

    assert result.passed is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_failed_preflight_fails_gate() -> None:
    result = (
        evaluate_governance_release_runtime_gate(
            preflight=build_preflight(
                passed=False
            ),
            process_start=(
                build_start_receipt()
            ),
            process_restart=(
                build_restart()
            ),
            persistence=(
                build_persistence()
            ),
            failure_probe=(
                build_failure_probe()
            ),
        )
    )

    assert result.passed is False

    assert (
        "preflight_passed"
        in result.failure_reasons
    )


def test_environment_mismatch_fails_gate() -> None:
    result = (
        evaluate_governance_release_runtime_gate(
            preflight=build_preflight(),
            process_start=(
                build_start_receipt(
                    release_environment="prelive"
                )
            ),
            process_restart=(
                build_restart()
            ),
            persistence=(
                build_persistence()
            ),
            failure_probe=(
                build_failure_probe()
            ),
        )
    )

    assert result.passed is False

    assert (
        "start_environment_matches_preflight"
        in result.failure_reasons
    )


def test_failed_restart_fails_gate() -> None:
    result = (
        evaluate_governance_release_runtime_gate(
            preflight=build_preflight(),
            process_start=(
                build_start_receipt()
            ),
            process_restart=(
                build_restart(
                    restart_succeeded=False
                )
            ),
            persistence=(
                build_persistence()
            ),
            failure_probe=(
                build_failure_probe()
            ),
        )
    )

    assert result.passed is False

    assert (
        "restart_succeeded"
        in result.failure_reasons
    )


def test_failed_persistence_fails_gate() -> None:
    result = (
        evaluate_governance_release_runtime_gate(
            preflight=build_preflight(),
            process_start=(
                build_start_receipt()
            ),
            process_restart=(
                build_restart()
            ),
            persistence=(
                build_persistence(
                    persistence_proven=False
                )
            ),
            failure_probe=(
                build_failure_probe()
            ),
        )
    )

    assert result.passed is False

    assert (
        "post_restart_persistence_proven"
        in result.failure_reasons
    )


def test_missing_fail_closed_proof_fails_gate() -> None:
    result = (
        evaluate_governance_release_runtime_gate(
            preflight=build_preflight(),
            process_start=(
                build_start_receipt()
            ),
            process_restart=(
                build_restart()
            ),
            persistence=(
                build_persistence()
            ),
            failure_probe=(
                build_failure_probe(
                    failure_proven=False
                )
            ),
        )
    )

    assert result.passed is False

    assert (
        "invalid_configuration_failed_closed"
        in result.failure_reasons
    )


def test_runtime_gate_preserves_authority_boundaries() -> None:
    result = evaluate_default()

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "gate_is_not_process_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_deployment_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_intervention_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_evaluates_existing_evidence_only"
        ]
        is True
    )

    assert (
        boundaries[
            "runtime_readiness_is_not_customer_trial_authority"
        ]
        is True
    )


def test_runtime_gate_rejects_wrong_evidence_type() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "process_start must be a "
            "GovernanceReleaseProcessStartReceipt"
        ),
    ):
        evaluate_governance_release_runtime_gate(
            preflight=build_preflight(),
            process_start=object(),
            process_restart=(
                build_restart()
            ),
            persistence=(
                build_persistence()
            ),
            failure_probe=(
                build_failure_probe()
            ),
        )