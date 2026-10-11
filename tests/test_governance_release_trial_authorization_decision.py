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
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_TYPE,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_VERSION,
    TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    TRIAL_AUTHORIZATION_DECISION_DENY,
    TRIAL_AUTHORIZATION_STATUS_AUTHORIZED,
    TRIAL_AUTHORIZATION_STATUS_BLOCKED,
    TRIAL_AUTHORIZATION_STATUS_DENIED,
    GovernanceReleaseTrialAuthorizationDecision,
    evaluate_governance_release_trial_authorization_decision,
)


def build_acceptance_manifest(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    status: str = ACCEPTANCE_MANIFEST_STATUS_READY,
    acceptance_passed: bool = True,
    acceptance_disposition: str = (
        RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
    ),
    checks: dict[str, bool] | None = None,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceManifest:
    if checks is None:
        checks = {
            "release_acceptance":
                True,
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
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
    passed: bool = True,
    checks: dict[str, bool] | None = None,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceManifestProofResult:
    if checks is None:
        checks = {
            "manifest_integrity":
                True,
        }

    return GovernanceReleaseAcceptanceManifestProofResult(
        release_environment=release_environment,
        backup_id=backup_id,
        passed=passed,
        checks=checks,
        failure_reasons=failure_reasons,
    )


def evaluate_decision(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest
        | None = None,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult
        | None = None,
    decision_id: str = "trial-auth-001",
    decided_by: str = "release-operator",
    decided_at: str = "2026-10-07T16:00:00Z",
    decision: str = TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
) -> GovernanceReleaseTrialAuthorizationDecision:
    return evaluate_governance_release_trial_authorization_decision(
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
        decision_id=decision_id,
        decided_by=decided_by,
        decided_at=decided_at,
        decision=decision,
    )


def test_explicit_authorize_creates_trial_authorization(
) -> None:
    result = evaluate_decision()

    assert isinstance(
        result,
        GovernanceReleaseTrialAuthorizationDecision,
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
        == TRIAL_AUTHORIZATION_STATUS_AUTHORIZED
    )

    assert result.trial_authorized is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_explicit_deny_creates_denied_decision_not_blocked(
) -> None:
    result = evaluate_decision(
        decision=TRIAL_AUTHORIZATION_DECISION_DENY
    )

    assert (
        result.decision
        == TRIAL_AUTHORIZATION_DECISION_DENY
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_DENIED
    )

    assert result.trial_authorized is False
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_non_paid_trial_environment_blocks_authorization(
) -> None:
    result = evaluate_decision(
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
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert result.trial_authorized is False

    assert result.failure_reasons == (
        "paid_trial_environment",
    )


def test_unready_acceptance_manifest_blocks_authorization(
) -> None:
    result = evaluate_decision(
        acceptance_manifest=(
            build_acceptance_manifest(
                status=ACCEPTANCE_MANIFEST_STATUS_BLOCKED
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert result.trial_authorized is False

    assert (
        "acceptance_manifest_ready"
        in result.failure_reasons
    )


def test_failed_acceptance_manifest_blocks_authorization(
) -> None:
    result = evaluate_decision(
        acceptance_manifest=(
            build_acceptance_manifest(
                acceptance_passed=False
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert result.trial_authorized is False

    assert (
        "acceptance_manifest_passed"
        in result.failure_reasons
    )


def test_acceptance_manifest_failure_reasons_block_authorization(
) -> None:
    result = evaluate_decision(
        acceptance_manifest=(
            build_acceptance_manifest(
                failure_reasons=(
                    "synthetic_acceptance_failure",
                )
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert (
        "acceptance_manifest_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_failed_manifest_proof_blocks_authorization(
) -> None:
    result = evaluate_decision(
        manifest_proof=(
            build_manifest_proof(
                passed=False
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert result.trial_authorized is False

    assert (
        "manifest_proof_passed"
        in result.failure_reasons
    )


def test_manifest_proof_failure_reasons_block_authorization(
) -> None:
    result = evaluate_decision(
        manifest_proof=(
            build_manifest_proof(
                failure_reasons=(
                    "synthetic_proof_failure",
                )
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert (
        "manifest_proof_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_release_environment_mismatch_blocks_authorization(
) -> None:
    result = evaluate_decision(
        manifest_proof=(
            build_manifest_proof(
                release_environment="prelive"
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert (
        "manifest_proof_matches_release_environment"
        in result.failure_reasons
    )


def test_backup_identity_mismatch_blocks_authorization(
) -> None:
    result = evaluate_decision(
        manifest_proof=(
            build_manifest_proof(
                backup_id="backup-002"
            )
        )
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert (
        "manifest_proof_matches_backup_identity"
        in result.failure_reasons
    )


def test_authorization_failure_order_is_deterministic(
) -> None:
    result = evaluate_decision(
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
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_STATUS_BLOCKED
    )

    assert result.trial_authorized is False


def test_decision_input_is_normalized(
) -> None:
    result = evaluate_decision(
        decision_id="  trial-auth-001  ",
        decided_by="  release-operator  ",
        decided_at="  2026-10-07T16:00:00Z  ",
        decision="  AUTHORIZE  ",
    )

    assert result.decision_id == "trial-auth-001"
    assert result.decided_by == "release-operator"
    assert result.decided_at == "2026-10-07T16:00:00Z"

    assert (
        result.decision
        == TRIAL_AUTHORIZATION_DECISION_AUTHORIZE
    )

    assert result.trial_authorized is True


@pytest.mark.parametrize(
    (
        "argument_name",
        "value",
        "expected_message",
    ),
    (
        (
            "decision_id",
            "",
            "decision_id must not be empty",
        ),
        (
            "decision_id",
            "   ",
            "decision_id must not be empty",
        ),
        (
            "decided_by",
            "",
            "decided_by must not be empty",
        ),
        (
            "decided_by",
            "   ",
            "decided_by must not be empty",
        ),
        (
            "decided_at",
            "",
            "decided_at must not be empty",
        ),
        (
            "decided_at",
            "   ",
            "decided_at must not be empty",
        ),
    ),
)
def test_empty_required_human_decision_fields_are_rejected(
    argument_name: str,
    value: str,
    expected_message: str,
) -> None:
    kwargs = {
        "decision_id":
            "trial-auth-001",
        "decided_by":
            "release-operator",
        "decided_at":
            "2026-10-07T16:00:00Z",
        "decision":
            TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    }

    kwargs[
        argument_name
    ] = value

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        evaluate_decision(
            **kwargs
        )


@pytest.mark.parametrize(
    "argument_name",
    (
        "decision_id",
        "decided_by",
        "decided_at",
    ),
)
def test_non_string_required_human_decision_fields_are_rejected(
    argument_name: str,
) -> None:
    kwargs = {
        "decision_id":
            "trial-auth-001",
        "decided_by":
            "release-operator",
        "decided_at":
            "2026-10-07T16:00:00Z",
        "decision":
            TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError,
        match=f"{argument_name} must be a string",
    ):
        evaluate_decision(
            **kwargs
        )


@pytest.mark.parametrize(
    "decision",
    (
        "",
        "approve",
        "approved",
        "trial_authorized",
        "allow",
        "reject",
    ),
)
def test_unsupported_decision_values_are_rejected(
    decision: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="decision must be 'authorize' or 'deny'",
    ):
        evaluate_decision(
            decision=decision
        )


def test_non_string_decision_is_rejected(
) -> None:
    with pytest.raises(
        TypeError,
        match="decision must be a string",
    ):
        evaluate_decision(
            decision=object()
        )


@pytest.mark.parametrize(
    "argument_name",
    (
        "acceptance_manifest",
        "manifest_proof",
    ),
)
def test_wrong_evidence_types_are_rejected(
    argument_name: str,
) -> None:
    kwargs = {
        "acceptance_manifest":
            build_acceptance_manifest(),
        "manifest_proof":
            build_manifest_proof(),
        "decision_id":
            "trial-auth-001",
        "decided_by":
            "release-operator",
        "decided_at":
            "2026-10-07T16:00:00Z",
        "decision":
            TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError
    ):
        evaluate_governance_release_trial_authorization_decision(
            **kwargs
        )


def test_trial_authorization_decision_is_immutable(
) -> None:
    result = evaluate_decision()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.trial_authorized = False


def test_trial_authorization_public_projection_preserves_authority_boundaries(
) -> None:
    payload = (
        evaluate_decision()
        .to_dict()
    )

    assert (
        payload["decision_type"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_VERSION
    )

    assert payload["release_environment"] == "paid_trial"
    assert payload["backup_id"] == "backup-001"
    assert payload["decision_id"] == "trial-auth-001"
    assert payload["decided_by"] == "release-operator"
    assert payload["decided_at"] == "2026-10-07T16:00:00Z"

    assert (
        payload["decision"]
        == TRIAL_AUTHORIZATION_DECISION_AUTHORIZE
    )

    assert (
        payload["status"]
        == TRIAL_AUTHORIZATION_STATUS_AUTHORIZED
    )

    assert payload["trial_authorized"] is True
    assert payload["failure_reasons"] == []

    boundaries = payload[
        "boundaries"
    ]

    expected_boundaries = {
        "decision_requires_explicit_human_input",
        "release_acceptance_does_not_self_authorize",
        "manifest_readiness_does_not_self_authorize",
        "manifest_proof_does_not_self_authorize",
        "trial_authorization_is_not_deployment_execution",
        "trial_authorization_is_not_paid_assessment_execution",
        "trial_authorization_is_not_pa001_paid_work_authorization",
        "trial_authorization_is_not_delivery_approval",
        "trial_authorization_is_not_production_activation",
        "trial_authorization_is_not_intervention_authority",
        "trial_authorization_does_not_invoke_pa014_or_pa015",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )


def test_acceptance_evidence_cannot_self_authorize_without_decision(
) -> None:
    manifest = build_acceptance_manifest()
    proof = build_manifest_proof()

    assert manifest.status == ACCEPTANCE_MANIFEST_STATUS_READY
    assert manifest.acceptance_passed is True
    assert proof.passed is True

    assert not hasattr(
        manifest,
        "trial_authorized",
    )

    assert not hasattr(
        proof,
        "trial_authorized",
    )


def test_trial_authorization_does_not_create_pa001_or_execution_authority(
) -> None:
    payload = (
        evaluate_decision()
        .to_dict()
    )

    assert payload["trial_authorized"] is True

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "trial_authorization_is_not_pa001_paid_work_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_authorization_is_not_paid_assessment_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_authorization_is_not_deployment_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_authorization_is_not_delivery_approval"
        ]
        is True
    )

    assert (
        boundaries[
            "trial_authorization_is_not_intervention_authority"
        ]
        is True
    )