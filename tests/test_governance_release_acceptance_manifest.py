from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_TYPE,
    GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_VERSION,
    GovernanceReleaseAcceptanceManifest,
    build_governance_release_acceptance_manifest,
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


def test_acceptance_manifest_is_ready_when_acceptance_passes(
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite()
        )
    )

    assert isinstance(
        result,
        GovernanceReleaseAcceptanceManifest,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"

    assert (
        result.status
        == ACCEPTANCE_MANIFEST_STATUS_READY
    )

    assert result.acceptance_passed is True

    assert (
        result.acceptance_disposition
        == RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    )

    assert result.checks == {
        "synthetic":
            True,
    }

    assert result.failure_reasons == ()


def test_acceptance_manifest_is_blocked_when_acceptance_fails(
) -> None:
    result = build_governance_release_acceptance_manifest(
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
        )
    )

    assert (
        result.status
        == ACCEPTANCE_MANIFEST_STATUS_BLOCKED
    )

    assert result.acceptance_passed is False

    assert (
        result.acceptance_disposition
        == RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
    )

    assert result.failure_reasons == (
        "synthetic",
    )


def test_acceptance_manifest_blocks_inconsistent_passed_and_disposition(
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite(
                passed=True,
                disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                ),
            )
        )
    )

    assert (
        result.status
        == ACCEPTANCE_MANIFEST_STATUS_BLOCKED
    )

    assert result.acceptance_passed is True

    assert (
        result.acceptance_disposition
        == RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
    )


def test_acceptance_manifest_preserves_release_environment(
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite(
                release_environment="paid_trial"
            )
        )
    )

    assert result.release_environment == "paid_trial"


def test_acceptance_manifest_preserves_backup_identity(
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite(
                backup_id="backup-xyz"
            )
        )
    )

    assert result.backup_id == "backup-xyz"


def test_acceptance_manifest_copies_checks(
) -> None:
    source_checks = {
        "first":
            True,
        "second":
            False,
    }

    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite(
                passed=False,
                disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                ),
                checks=source_checks,
                failure_reasons=(
                    "second",
                ),
            )
        )
    )

    assert result.checks == source_checks
    assert result.checks is not source_checks


def test_acceptance_manifest_preserves_failure_reasons(
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite(
                passed=False,
                disposition=(
                    RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED
                ),
                failure_reasons=(
                    "first_failure",
                    "second_failure",
                ),
            )
        )
    )

    assert result.failure_reasons == (
        "first_failure",
        "second_failure",
    )


def test_acceptance_manifest_public_projection_preserves_boundaries(
) -> None:
    payload = (
        build_governance_release_acceptance_manifest(
            acceptance_suite=(
                build_acceptance_suite()
            )
        )
        .to_dict()
    )

    assert (
        payload["manifest_type"]
        == GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_VERSION
    )

    assert payload["release_environment"] == "paid_trial"
    assert payload["backup_id"] == "backup-001"

    assert (
        payload["status"]
        == ACCEPTANCE_MANIFEST_STATUS_READY
    )

    assert payload["acceptance_passed"] is True

    assert (
        payload["acceptance_disposition"]
        == RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    )

    assert payload["checks"] == {
        "synthetic":
            True,
    }

    assert payload["failure_reasons"] == []

    boundaries = payload["boundaries"]

    expected_boundaries = {
        "manifest_is_read_only",
        "manifest_projects_existing_acceptance_evidence_only",
        "manifest_does_not_execute_release_operations",
        "manifest_does_not_execute_paid_assessment",
        "manifest_does_not_invoke_pa014_or_pa015",
        "acceptance_ready_is_not_trial_authorization",
        "acceptance_ready_is_not_deployment_authorization",
        "acceptance_ready_is_not_customer_execution_authority",
        "acceptance_ready_is_not_delivery_authorization",
        "acceptance_ready_is_not_production_activation",
        "acceptance_ready_is_not_intervention_authority",
        "manifest_requires_separate_trial_authorization_gate",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )


def test_acceptance_manifest_result_is_immutable(
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite()
        )
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.status = "mutated"


def test_acceptance_manifest_rejects_wrong_input_type(
) -> None:
    with pytest.raises(
        TypeError,
    ):
        build_governance_release_acceptance_manifest(
            acceptance_suite=object(),
        )


@pytest.mark.parametrize(
    (
        "passed",
        "disposition",
        "expected_status",
    ),
    (
        (
            True,
            RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
            ACCEPTANCE_MANIFEST_STATUS_READY,
        ),
        (
            True,
            RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED,
            ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
        ),
        (
            False,
            RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
            ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
        ),
        (
            False,
            RELEASE_ACCEPTANCE_DISPOSITION_BLOCKED,
            ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
        ),
    ),
)
def test_acceptance_manifest_status_requires_both_pass_and_accepted_disposition(
    passed: bool,
    disposition: str,
    expected_status: str,
) -> None:
    result = build_governance_release_acceptance_manifest(
        acceptance_suite=(
            build_acceptance_suite(
                passed=passed,
                disposition=disposition,
            )
        )
    )

    assert result.status == expected_status