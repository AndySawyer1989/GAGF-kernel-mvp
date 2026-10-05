from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_TYPE,
    GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_VERSION,
    GovernanceReleaseAcceptanceManifestProofResult,
    evaluate_governance_release_acceptance_manifest_proof,
)
from backend.app.gagf.governance_release_acceptance_suite import (
    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED,
    GovernanceReleaseAcceptanceSuiteResult,
)


def build_acceptance_suite(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    passed: bool = True,
    disposition: str = (
        RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    ),
    checks: dict[str, bool] | None = None,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceSuiteResult:
    if checks is None:
        checks = {
            "synthetic":
                passed,
        }

    return GovernanceReleaseAcceptanceSuiteResult(
        release_environment=release_environment,
        backup_id=backup_id,
        disposition=disposition,
        passed=passed,
        checks=checks,
        failure_reasons=failure_reasons,
    )


def build_acceptance_manifest(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    status: str = (
        ACCEPTANCE_MANIFEST_STATUS_READY
    ),
    acceptance_passed: bool = True,
    acceptance_disposition: str = (
        RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    ),
    checks: dict[str, bool] | None = None,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceManifest:
    if checks is None:
        checks = {
            "synthetic":
                acceptance_passed,
        }

    return GovernanceReleaseAcceptanceManifest(
        release_environment=release_environment,
        backup_id=backup_id,
        status=status,
        acceptance_passed=acceptance_passed,
        acceptance_disposition=acceptance_disposition,
        checks=checks,
        failure_reasons=failure_reasons,
    )


def build_manifest_proof(
    *,
    acceptance_suite:
        GovernanceReleaseAcceptanceSuiteResult
        | None = None,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest
        | None = None,
) -> GovernanceReleaseAcceptanceManifestProofResult:
    return evaluate_governance_release_acceptance_manifest_proof(
        acceptance_suite=(
            acceptance_suite
            if acceptance_suite is not None
            else build_acceptance_suite()
        ),
        acceptance_manifest=(
            acceptance_manifest
            if acceptance_manifest is not None
            else build_acceptance_manifest()
        ),
    )


def test_manifest_proof_passes_for_matching_ready_evidence(
) -> None:
    result = build_manifest_proof()

    assert isinstance(
        result,
        GovernanceReleaseAcceptanceManifestProofResult,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"
    assert result.passed is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_manifest_proof_blocks_non_paid_trial_environment(
) -> None:
    result = build_manifest_proof(
        acceptance_suite=(
            build_acceptance_suite(
                release_environment="prelive"
            )
        ),
        acceptance_manifest=(
            build_acceptance_manifest(
                release_environment="prelive"
            )
        ),
    )

    assert result.passed is False

    assert (
        "paid_trial_environment"
        in result.failure_reasons
    )


def test_manifest_proof_blocks_failed_acceptance_suite(
) -> None:
    result = build_manifest_proof(
        acceptance_suite=(
            build_acceptance_suite(
                passed=False,
                disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                ),
                checks={
                    "synthetic":
                        False,
                },
                failure_reasons=(
                    "synthetic",
                ),
            )
        ),
        acceptance_manifest=(
            build_acceptance_manifest(
                status=(
                    ACCEPTANCE_MANIFEST_STATUS_BLOCKED
                ),
                acceptance_passed=False,
                acceptance_disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                ),
                checks={
                    "synthetic":
                        False,
                },
                failure_reasons=(
                    "synthetic",
                ),
            )
        ),
    )

    assert result.passed is False

    assert (
        "acceptance_suite_passed"
        in result.failure_reasons
    )

    assert (
        "acceptance_suite_disposition_accepted"
        in result.failure_reasons
    )


def test_manifest_proof_requires_ready_manifest(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                status=(
                    ACCEPTANCE_MANIFEST_STATUS_BLOCKED
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "acceptance_manifest_ready"
        in result.failure_reasons
    )


def test_manifest_proof_requires_manifest_acceptance_passed(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                acceptance_passed=False
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_acceptance_passed"
        in result.failure_reasons
    )

    assert (
        "manifest_matches_acceptance_passed"
        in result.failure_reasons
    )


def test_manifest_proof_blocks_release_environment_mismatch(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                release_environment="prelive"
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_matches_release_environment"
        in result.failure_reasons
    )


def test_manifest_proof_blocks_backup_identity_mismatch(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                backup_id="backup-002"
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_matches_backup_identity"
        in result.failure_reasons
    )


def test_manifest_proof_blocks_acceptance_disposition_mismatch(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                acceptance_disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_matches_acceptance_disposition"
        in result.failure_reasons
    )


def test_manifest_proof_blocks_check_mismatch(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                checks={
                    "different":
                        True,
                }
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_matches_checks"
        in result.failure_reasons
    )


def test_manifest_proof_blocks_failure_reason_mismatch(
) -> None:
    result = build_manifest_proof(
        acceptance_manifest=(
            build_acceptance_manifest(
                failure_reasons=(
                    "synthetic",
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_matches_failure_reasons"
        in result.failure_reasons
    )

    assert (
        "acceptance_manifest_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_manifest_proof_requires_empty_suite_failure_reasons(
) -> None:
    result = build_manifest_proof(
        acceptance_suite=(
            build_acceptance_suite(
                failure_reasons=(
                    "synthetic",
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_matches_failure_reasons"
        in result.failure_reasons
    )

    assert (
        "acceptance_suite_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_manifest_proof_preserves_deterministic_failure_order(
) -> None:
    result = build_manifest_proof(
        acceptance_suite=(
            build_acceptance_suite(
                release_environment="prelive",
                backup_id="backup-001",
                passed=False,
                disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                ),
                checks={
                    "suite_check":
                        False,
                },
                failure_reasons=(
                    "suite_failure",
                ),
            )
        ),
        acceptance_manifest=(
            build_acceptance_manifest(
                release_environment="paid_trial",
                backup_id="backup-002",
                status=(
                    ACCEPTANCE_MANIFEST_STATUS_BLOCKED
                ),
                acceptance_passed=False,
                acceptance_disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
                ),
                checks={
                    "manifest_check":
                        True,
                },
                failure_reasons=(
                    "manifest_failure",
                ),
            )
        ),
    )

    assert result.failure_reasons == (
        "paid_trial_environment",
        "acceptance_suite_passed",
        "acceptance_suite_disposition_accepted",
        "acceptance_manifest_ready",
        "manifest_acceptance_passed",
        "manifest_matches_release_environment",
        "manifest_matches_backup_identity",
        "manifest_matches_acceptance_disposition",
        "manifest_matches_checks",
        "manifest_matches_failure_reasons",
        "acceptance_suite_has_no_failure_reasons",
        "acceptance_manifest_has_no_failure_reasons",
    )


def test_manifest_proof_public_projection_preserves_boundaries(
) -> None:
    payload = (
        build_manifest_proof()
        .to_dict()
    )

    assert (
        payload["proof_type"]
        == GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_VERSION
    )

    assert payload["release_environment"] == "paid_trial"
    assert payload["backup_id"] == "backup-001"
    assert payload["passed"] is True
    assert payload["failure_reasons"] == []

    boundaries = payload["boundaries"]

    expected_boundaries = {
        "proof_is_read_only",
        "proof_validates_existing_acceptance_evidence_only",
        "proof_does_not_execute_release_operations",
        "proof_does_not_execute_paid_assessment",
        "proof_does_not_invoke_pa014_or_pa015",
        "proof_passed_is_not_trial_authorization",
        "proof_passed_is_not_deployment_authorization",
        "proof_passed_is_not_customer_execution_authority",
        "proof_passed_is_not_delivery_authorization",
        "proof_passed_is_not_production_activation",
        "proof_passed_is_not_intervention_authority",
        "proof_requires_separate_trial_authorization_gate",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )


def test_manifest_proof_result_is_immutable(
) -> None:
    result = build_manifest_proof()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.passed = False


@pytest.mark.parametrize(
    "argument_name",
    (
        "acceptance_suite",
        "acceptance_manifest",
    ),
)
def test_manifest_proof_rejects_wrong_input_type(
    argument_name: str,
) -> None:
    kwargs = {
        "acceptance_suite":
            build_acceptance_suite(),
        "acceptance_manifest":
            build_acceptance_manifest(),
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError
    ):
        evaluate_governance_release_acceptance_manifest_proof(
            acceptance_suite=kwargs[
                "acceptance_suite"
            ],
            acceptance_manifest=kwargs[
                "acceptance_manifest"
            ],
        )
