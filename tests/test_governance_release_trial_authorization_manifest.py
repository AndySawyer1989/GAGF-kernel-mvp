from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GovernanceReleaseAcceptanceManifestProofResult,
)
from backend.app.gagf.governance_release_acceptance_suite import (
    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
)
from backend.app.gagf.governance_release_trial_authorization_decision import (
    TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    TRIAL_AUTHORIZATION_DECISION_DENY,
    TRIAL_AUTHORIZATION_STATUS_AUTHORIZED,
    TRIAL_AUTHORIZATION_STATUS_BLOCKED,
    TRIAL_AUTHORIZATION_STATUS_DENIED,
    GovernanceReleaseTrialAuthorizationDecision,
)
from backend.app.gagf.governance_release_trial_authorization_manifest import (
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_TYPE,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_VERSION,
    TRIAL_AUTHORIZATION_MANIFEST_STATUS_AUTHORIZED,
    TRIAL_AUTHORIZATION_MANIFEST_STATUS_BLOCKED,
    TRIAL_AUTHORIZATION_MANIFEST_STATUS_DENIED,
    GovernanceReleaseTrialAuthorizationManifest,
    build_governance_release_trial_authorization_manifest,
)


def build_acceptance_manifest(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    status: str = ACCEPTANCE_MANIFEST_STATUS_READY,
    acceptance_passed: bool = True,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceManifest:
    return GovernanceReleaseAcceptanceManifest(
        release_environment=release_environment,
        backup_id=backup_id,
        status=status,
        acceptance_passed=acceptance_passed,
        acceptance_disposition=(
            RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
        ),
        checks={
            "release_acceptance":
                acceptance_passed,
        },
        failure_reasons=failure_reasons,
    )


def build_manifest_proof(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    passed: bool = True,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceManifestProofResult:
    return GovernanceReleaseAcceptanceManifestProofResult(
        release_environment=release_environment,
        backup_id=backup_id,
        passed=passed,
        checks={
            "manifest_integrity":
                passed,
        },
        failure_reasons=failure_reasons,
    )


def build_authorization_decision(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    decision_id: str = "trial-auth-001",
    decided_by: str = "release-operator",
    decided_at: str = "2026-10-07T16:00:00Z",
    decision: str = TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    status: str = TRIAL_AUTHORIZATION_STATUS_AUTHORIZED,
    trial_authorized: bool = True,
    checks: dict[str, bool] | None = None,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseTrialAuthorizationDecision:
    if checks is None:
        checks = {
            "decision_valid":
                True,
        }

    return GovernanceReleaseTrialAuthorizationDecision(
        release_environment=release_environment,
        backup_id=backup_id,
        decision_id=decision_id,
        decided_by=decided_by,
        decided_at=decided_at,
        decision=decision,
        status=status,
        trial_authorized=trial_authorized,
        checks=checks,
        failure_reasons=failure_reasons,
    )


def build_manifest(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest
        | None = None,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult
        | None = None,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision
        | None = None,
) -> GovernanceReleaseTrialAuthorizationManifest:
    return build_governance_release_trial_authorization_manifest(
        acceptance_manifest=(
            acceptance_manifest
            if acceptance_manifest is not None
            else build_acceptance_manifest()
        ),
        manifest_proof=(
            manifest_proof
            if manifest_proof is not None
            else build_manifest_proof()
        ),
        authorization_decision=(
            authorization_decision
            if authorization_decision is not None
            else build_authorization_decision()
        ),
    )


def test_authorized_decision_projects_authorized_manifest(
) -> None:
    result = build_manifest()

    assert isinstance(
        result,
        GovernanceReleaseTrialAuthorizationManifest,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"
    assert result.decision_id == "trial-auth-001"
    assert result.decided_by == "release-operator"
    assert result.decided_at == "2026-10-07T16:00:00Z"

    assert (
        result.decision
        == TRIAL_AUTHORIZATION_DECISION_AUTHORIZE
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_MANIFEST_STATUS_AUTHORIZED
    )

    assert result.trial_authorized is True
    assert result.failure_reasons == ()
    assert all(result.checks.values())


def test_denied_decision_projects_denied_manifest(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                decision=TRIAL_AUTHORIZATION_DECISION_DENY,
                status=TRIAL_AUTHORIZATION_STATUS_DENIED,
                trial_authorized=False,
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_MANIFEST_STATUS_DENIED
    )

    assert result.trial_authorized is False
    assert result.failure_reasons == ()
    assert all(result.checks.values())


def test_non_paid_trial_environment_blocks_manifest(
) -> None:
    result = build_manifest(
        acceptance_manifest=(
            build_acceptance_manifest(
                release_environment="prelive"
            )
        ),
        manifest_proof=(
            build_manifest_proof(
                release_environment="prelive"
            )
        ),
        authorization_decision=(
            build_authorization_decision(
                release_environment="prelive"
            )
        ),
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_MANIFEST_STATUS_BLOCKED
    )

    assert result.trial_authorized is False
    assert result.failure_reasons == (
        "paid_trial_environment",
    )


def test_unready_acceptance_manifest_blocks_projection(
) -> None:
    result = build_manifest(
        acceptance_manifest=(
            build_acceptance_manifest(
                status=ACCEPTANCE_MANIFEST_STATUS_BLOCKED
            )
        )
    )

    assert (
        "acceptance_manifest_ready"
        in result.failure_reasons
    )

    assert result.trial_authorized is False


def test_failed_acceptance_manifest_blocks_projection(
) -> None:
    result = build_manifest(
        acceptance_manifest=(
            build_acceptance_manifest(
                acceptance_passed=False
            )
        )
    )

    assert (
        "acceptance_manifest_passed"
        in result.failure_reasons
    )

    assert result.trial_authorized is False


def test_acceptance_failure_reasons_block_projection(
) -> None:
    result = build_manifest(
        acceptance_manifest=(
            build_acceptance_manifest(
                failure_reasons=(
                    "acceptance_failure",
                )
            )
        )
    )

    assert (
        "acceptance_manifest_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_failed_manifest_proof_blocks_projection(
) -> None:
    result = build_manifest(
        manifest_proof=(
            build_manifest_proof(
                passed=False
            )
        )
    )

    assert (
        "manifest_proof_passed"
        in result.failure_reasons
    )


def test_manifest_proof_failure_reasons_block_projection(
) -> None:
    result = build_manifest(
        manifest_proof=(
            build_manifest_proof(
                failure_reasons=(
                    "proof_failure",
                )
            )
        )
    )

    assert (
        "manifest_proof_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_manifest_proof_environment_mismatch_blocks_projection(
) -> None:
    result = build_manifest(
        manifest_proof=(
            build_manifest_proof(
                release_environment="prelive"
            )
        )
    )

    assert (
        "manifest_proof_matches_release_environment"
        in result.failure_reasons
    )


def test_manifest_proof_backup_mismatch_blocks_projection(
) -> None:
    result = build_manifest(
        manifest_proof=(
            build_manifest_proof(
                backup_id="backup-002"
            )
        )
    )

    assert (
        "manifest_proof_matches_backup_identity"
        in result.failure_reasons
    )


def test_authorization_environment_mismatch_blocks_projection(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                release_environment="prelive"
            )
        )
    )

    assert (
        "authorization_decision_matches_release_environment"
        in result.failure_reasons
    )


def test_authorization_backup_mismatch_blocks_projection(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                backup_id="backup-002"
            )
        )
    )

    assert (
        "authorization_decision_matches_backup_identity"
        in result.failure_reasons
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "expected_failure",
    ),
    (
        (
            "decision_id",
            "authorization_decision_identity_present",
        ),
        (
            "decided_by",
            "authorization_decision_actor_present",
        ),
        (
            "decided_at",
            "authorization_decision_time_present",
        ),
    ),
)
def test_missing_decision_identity_fields_block_projection(
    field_name: str,
    expected_failure: str,
) -> None:
    kwargs = {
        "decision_id":
            "trial-auth-001",
        "decided_by":
            "release-operator",
        "decided_at":
            "2026-10-07T16:00:00Z",
    }

    kwargs[
        field_name
    ] = ""

    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                **kwargs
            )
        )
    )

    assert (
        expected_failure
        in result.failure_reasons
    )

    assert result.trial_authorized is False


def test_unsupported_authorization_decision_blocks_projection(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                decision="approve"
            )
        )
    )

    assert (
        "authorization_decision_supported"
        in result.failure_reasons
    )

    assert (
        "authorization_decision_state_consistent"
        in result.failure_reasons
    )


def test_blocked_authorization_decision_cannot_be_projected_as_authorized(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                status=TRIAL_AUTHORIZATION_STATUS_BLOCKED,
                trial_authorized=False,
                checks={
                    "decision_valid":
                        False,
                },
                failure_reasons=(
                    "decision_blocked",
                ),
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_MANIFEST_STATUS_BLOCKED
    )

    assert result.trial_authorized is False

    assert (
        "authorization_decision_not_blocked"
        in result.failure_reasons
    )

    assert (
        "authorization_decision_has_no_failure_reasons"
        in result.failure_reasons
    )

    assert (
        "authorization_decision_checks_passed"
        in result.failure_reasons
    )

    assert (
        "authorization_decision_state_consistent"
        in result.failure_reasons
    )


def test_authorized_status_with_false_authorization_is_inconsistent(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                trial_authorized=False
            )
        )
    )

    assert (
        "authorization_decision_state_consistent"
        in result.failure_reasons
    )

    assert result.trial_authorized is False


def test_denied_status_with_authorize_decision_is_inconsistent(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                decision=TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
                status=TRIAL_AUTHORIZATION_STATUS_DENIED,
                trial_authorized=False,
            )
        )
    )

    assert (
        "authorization_decision_state_consistent"
        in result.failure_reasons
    )


def test_authorized_decision_with_failure_reasons_is_blocked(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                failure_reasons=(
                    "synthetic_failure",
                )
            )
        )
    )

    assert (
        "authorization_decision_has_no_failure_reasons"
        in result.failure_reasons
    )

    assert (
        "authorization_decision_state_consistent"
        in result.failure_reasons
    )


def test_authorization_decision_checks_must_all_pass(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                checks={
                    "first":
                        True,
                    "second":
                        False,
                }
            )
        )
    )

    assert (
        "authorization_decision_checks_passed"
        in result.failure_reasons
    )

    assert result.trial_authorized is False


def test_empty_authorization_decision_checks_block_projection(
) -> None:
    result = build_manifest(
        authorization_decision=(
            build_authorization_decision(
                checks={}
            )
        )
    )

    assert (
        "authorization_decision_checks_passed"
        in result.failure_reasons
    )


def test_manifest_failure_order_is_deterministic(
) -> None:
    result = build_manifest(
        acceptance_manifest=(
            build_acceptance_manifest(
                release_environment="prelive",
                backup_id="backup-001",
                status=ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
                acceptance_passed=False,
                failure_reasons=(
                    "acceptance_failure",
                ),
            )
        ),
        manifest_proof=(
            build_manifest_proof(
                release_environment="paid_trial",
                backup_id="backup-002",
                passed=False,
                failure_reasons=(
                    "proof_failure",
                ),
            )
        ),
        authorization_decision=(
            build_authorization_decision(
                release_environment="paid_trial",
                backup_id="backup-003",
                decision_id="",
                decided_by="",
                decided_at="",
                decision="approve",
                status=TRIAL_AUTHORIZATION_STATUS_BLOCKED,
                trial_authorized=False,
                checks={
                    "decision_valid":
                        False,
                },
                failure_reasons=(
                    "decision_failure",
                ),
            )
        ),
    )

    assert result.failure_reasons == (
        "paid_trial_environment",
        "acceptance_manifest_ready",
        "acceptance_manifest_passed",
        "acceptance_manifest_has_no_failure_reasons",
        "manifest_proof_passed",
        "manifest_proof_has_no_failure_reasons",
        "manifest_proof_matches_release_environment",
        "manifest_proof_matches_backup_identity",
        "authorization_decision_matches_release_environment",
        "authorization_decision_matches_backup_identity",
        "authorization_decision_identity_present",
        "authorization_decision_actor_present",
        "authorization_decision_time_present",
        "authorization_decision_supported",
        "authorization_decision_not_blocked",
        "authorization_decision_has_no_failure_reasons",
        "authorization_decision_checks_passed",
        "authorization_decision_state_consistent",
    )


@pytest.mark.parametrize(
    "argument_name",
    (
        "acceptance_manifest",
        "manifest_proof",
        "authorization_decision",
    ),
)
def test_wrong_input_types_are_rejected(
    argument_name: str,
) -> None:
    kwargs = {
        "acceptance_manifest":
            build_acceptance_manifest(),
        "manifest_proof":
            build_manifest_proof(),
        "authorization_decision":
            build_authorization_decision(),
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError
    ):
        build_governance_release_trial_authorization_manifest(
            **kwargs
        )


def test_trial_authorization_manifest_is_immutable(
) -> None:
    result = build_manifest()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.trial_authorized = False


def test_public_projection_preserves_authority_boundaries(
) -> None:
    payload = (
        build_manifest()
        .to_dict()
    )

    assert (
        payload["manifest_type"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_VERSION
    )

    assert payload["trial_authorized"] is True

    boundaries = payload[
        "boundaries"
    ]

    expected_boundaries = {
        "manifest_is_projection_only",
        "manifest_does_not_create_trial_authorization",
        "manifest_requires_preexisting_authorization_decision",
        "manifest_binds_authorization_to_release_evidence",
        "manifest_is_not_deployment_execution",
        "manifest_is_not_paid_assessment_execution",
        "manifest_is_not_pa001_paid_work_authorization",
        "manifest_is_not_delivery_approval",
        "manifest_is_not_production_activation",
        "manifest_is_not_intervention_authority",
        "manifest_does_not_invoke_pa014_or_pa015",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )