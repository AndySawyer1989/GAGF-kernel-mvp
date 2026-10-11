from dataclasses import FrozenInstanceError, replace

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
    TRIAL_AUTHORIZATION_STATUS_DENIED,
    GovernanceReleaseTrialAuthorizationDecision,
    evaluate_governance_release_trial_authorization_decision,
)
from backend.app.gagf.governance_release_trial_authorization_gate import (
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_TYPE,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_VERSION,
    TRIAL_AUTHORIZATION_GATE_STATUS_BLOCKED,
    TRIAL_AUTHORIZATION_GATE_STATUS_VERIFIED,
    GovernanceReleaseTrialAuthorizationGateResult,
    evaluate_governance_release_trial_authorization_gate,
)
from backend.app.gagf.governance_release_trial_authorization_manifest import (
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
    checks: dict[str, bool] | None = None,
    failure_reasons: tuple[str, ...] = (),
) -> GovernanceReleaseAcceptanceManifestProofResult:
    if checks is None:
        checks = {
            "manifest_integrity":
                passed,
        }

    return GovernanceReleaseAcceptanceManifestProofResult(
        release_environment=release_environment,
        backup_id=backup_id,
        passed=passed,
        checks=checks,
        failure_reasons=failure_reasons,
    )


def build_authorization_decision(
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
    source_manifest = (
        acceptance_manifest
        if acceptance_manifest is not None
        else build_acceptance_manifest()
    )

    source_proof = (
        manifest_proof
        if manifest_proof is not None
        else build_manifest_proof()
    )

    return evaluate_governance_release_trial_authorization_decision(
        acceptance_manifest=source_manifest,
        manifest_proof=source_proof,
        decision_id=decision_id,
        decided_by=decided_by,
        decided_at=decided_at,
        decision=decision,
    )


def build_authorization_manifest(
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
    source_manifest = (
        acceptance_manifest
        if acceptance_manifest is not None
        else build_acceptance_manifest()
    )

    source_proof = (
        manifest_proof
        if manifest_proof is not None
        else build_manifest_proof()
    )

    source_decision = (
        authorization_decision
        if authorization_decision is not None
        else build_authorization_decision(
            acceptance_manifest=source_manifest,
            manifest_proof=source_proof,
        )
    )

    return build_governance_release_trial_authorization_manifest(
        acceptance_manifest=source_manifest,
        manifest_proof=source_proof,
        authorization_decision=source_decision,
    )


def build_gate(
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
    authorization_manifest:
        GovernanceReleaseTrialAuthorizationManifest
        | None = None,
) -> GovernanceReleaseTrialAuthorizationGateResult:
    source_manifest = (
        acceptance_manifest
        if acceptance_manifest is not None
        else build_acceptance_manifest()
    )

    source_proof = (
        manifest_proof
        if manifest_proof is not None
        else build_manifest_proof()
    )

    source_decision = (
        authorization_decision
        if authorization_decision is not None
        else build_authorization_decision(
            acceptance_manifest=source_manifest,
            manifest_proof=source_proof,
        )
    )

    source_authorization_manifest = (
        authorization_manifest
        if authorization_manifest is not None
        else build_authorization_manifest(
            acceptance_manifest=source_manifest,
            manifest_proof=source_proof,
            authorization_decision=source_decision,
        )
    )

    return evaluate_governance_release_trial_authorization_gate(
        acceptance_manifest=source_manifest,
        manifest_proof=source_proof,
        authorization_decision=source_decision,
        authorization_manifest=source_authorization_manifest,
    )


def test_authorized_chain_is_verified_and_authorized(
) -> None:
    result = build_gate()

    assert isinstance(
        result,
        GovernanceReleaseTrialAuthorizationGateResult,
    )

    assert result.release_environment == "paid_trial"
    assert result.backup_id == "backup-001"
    assert result.decision_id == "trial-auth-001"

    assert (
        result.status
        == TRIAL_AUTHORIZATION_GATE_STATUS_VERIFIED
    )

    assert result.passed is True
    assert result.trial_authorized is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_denied_chain_can_be_verified_without_being_authorized(
) -> None:
    acceptance_manifest = build_acceptance_manifest()
    manifest_proof = build_manifest_proof()

    decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        decision=TRIAL_AUTHORIZATION_DECISION_DENY,
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=decision,
        )
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=decision,
        authorization_manifest=authorization_manifest,
    )

    assert (
        decision.status
        == TRIAL_AUTHORIZATION_STATUS_DENIED
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_GATE_STATUS_VERIFIED
    )

    assert result.passed is True
    assert result.trial_authorized is False
    assert result.failure_reasons == ()


def test_failed_manifest_proof_blocks_gate(
) -> None:
    acceptance_manifest = build_acceptance_manifest()

    manifest_proof = build_manifest_proof(
        passed=False,
        checks={
            "manifest_integrity":
                False,
        },
        failure_reasons=(
            "manifest_integrity",
        ),
    )

    decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=decision,
        )
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=decision,
        authorization_manifest=authorization_manifest,
    )

    assert (
        result.status
        == TRIAL_AUTHORIZATION_GATE_STATUS_BLOCKED
    )

    assert result.passed is False
    assert result.trial_authorized is False

    assert (
        "manifest_proof_passed"
        in result.failure_reasons
    )


def test_manifest_proof_failure_reasons_block_gate(
) -> None:
    result = build_gate(
        manifest_proof=(
            build_manifest_proof(
                failure_reasons=(
                    "synthetic_failure",
                )
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_proof_has_no_failure_reasons"
        in result.failure_reasons
    )


def test_manifest_proof_checks_must_all_pass(
) -> None:
    result = build_gate(
        manifest_proof=(
            build_manifest_proof(
                checks={
                    "first":
                        True,
                    "second":
                        False,
                }
            )
        )
    )

    assert result.passed is False

    assert (
        "manifest_proof_checks_passed"
        in result.failure_reasons
    )


def test_empty_manifest_proof_checks_block_gate(
) -> None:
    result = build_gate(
        manifest_proof=(
            build_manifest_proof(
                checks={}
            )
        )
    )

    assert (
        "manifest_proof_checks_passed"
        in result.failure_reasons
    )


def test_manifest_proof_environment_mismatch_blocks_gate(
) -> None:
    acceptance_manifest = build_acceptance_manifest()

    manifest_proof = build_manifest_proof(
        release_environment="prelive"
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    assert (
        "proof_matches_release_environment"
        in result.failure_reasons
    )

    assert result.trial_authorized is False


def test_manifest_proof_backup_mismatch_blocks_gate(
) -> None:
    acceptance_manifest = build_acceptance_manifest()

    manifest_proof = build_manifest_proof(
        backup_id="backup-002"
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    assert (
        "proof_matches_backup_identity"
        in result.failure_reasons
    )


def test_tampered_decision_is_detected_by_recomputation(
) -> None:
    acceptance_manifest = build_acceptance_manifest()
    manifest_proof = build_manifest_proof()

    original_decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    tampered_decision = replace(
        original_decision,
        trial_authorized=False,
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=tampered_decision,
        )
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=tampered_decision,
        authorization_manifest=authorization_manifest,
    )

    assert result.passed is False
    assert result.trial_authorized is False

    assert (
        "decision_matches_recomputed_evidence"
        in result.failure_reasons
    )


def test_rebound_decision_identity_requires_external_trust_anchor(
) -> None:
    acceptance_manifest = build_acceptance_manifest()
    manifest_proof = build_manifest_proof()

    original_decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    rebound_decision = replace(
        original_decision,
        decision_id="rebound-decision",
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=rebound_decision,
        )
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=rebound_decision,
        authorization_manifest=authorization_manifest,
    )

    assert result.passed is True
    assert result.trial_authorized is True
    assert result.decision_id == "rebound-decision"
    assert result.failure_reasons == ()

    boundaries = result.to_dict()[
        "boundaries"
    ]

    assert (
        boundaries[
            "gate_does_not_verify_durable_decision_record"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_does_not_verify_cryptographic_signature"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_does_not_authenticate_decision_actor"
        ]
        is True
    )


def test_tampered_authorization_manifest_is_detected(
) -> None:
    acceptance_manifest = build_acceptance_manifest()
    manifest_proof = build_manifest_proof()

    decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    original_manifest = build_authorization_manifest(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=decision,
    )

    tampered_manifest = replace(
        original_manifest,
        trial_authorized=False,
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=decision,
        authorization_manifest=tampered_manifest,
    )

    assert result.passed is False
    assert result.trial_authorized is False

    assert (
        "authorization_manifest_matches_recomputed_projection"
        in result.failure_reasons
    )


def test_blocked_acceptance_evidence_cannot_pass_gate(
) -> None:
    acceptance_manifest = build_acceptance_manifest(
        status=ACCEPTANCE_MANIFEST_STATUS_BLOCKED,
        acceptance_passed=False,
        failure_reasons=(
            "release_acceptance",
        ),
    )

    manifest_proof = build_manifest_proof()

    decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=decision,
        )
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=decision,
        authorization_manifest=authorization_manifest,
    )

    assert result.passed is False
    assert result.trial_authorized is False


def test_non_paid_trial_environment_blocks_gate(
) -> None:
    acceptance_manifest = build_acceptance_manifest(
        release_environment="prelive"
    )

    manifest_proof = build_manifest_proof(
        release_environment="prelive"
    )

    decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=decision,
        )
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=decision,
        authorization_manifest=authorization_manifest,
    )

    assert result.passed is False
    assert result.trial_authorized is False

    assert (
        "paid_trial_environment"
        in result.failure_reasons
    )


def test_gate_failure_order_is_deterministic(
) -> None:
    acceptance_manifest = build_acceptance_manifest(
        release_environment="prelive",
        backup_id="backup-001",
    )

    manifest_proof = build_manifest_proof(
        release_environment="paid_trial",
        backup_id="backup-002",
        passed=False,
        checks={
            "manifest_integrity":
                False,
        },
        failure_reasons=(
            "proof_failure",
        ),
    )

    decision = build_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    tampered_decision = replace(
        decision,
        trial_authorized=True,
    )

    authorization_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=tampered_decision,
        )
    )

    tampered_manifest = replace(
        authorization_manifest,
        trial_authorized=True,
    )

    result = build_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=tampered_decision,
        authorization_manifest=tampered_manifest,
    )

    assert result.failure_reasons == (
        "paid_trial_environment",
        "manifest_proof_passed",
        "manifest_proof_has_no_failure_reasons",
        "manifest_proof_checks_passed",
        "proof_matches_release_environment",
        "proof_matches_backup_identity",
        "decision_matches_recomputed_evidence",
        "authorization_manifest_matches_recomputed_projection",
        "authorization_manifest_not_blocked",
        "authorization_manifest_checks_passed",
    )


@pytest.mark.parametrize(
    "argument_name",
    (
        "acceptance_manifest",
        "manifest_proof",
        "authorization_decision",
        "authorization_manifest",
    ),
)
def test_wrong_input_types_are_rejected(
    argument_name: str,
) -> None:
    acceptance_manifest = build_acceptance_manifest()
    manifest_proof = build_manifest_proof()

    authorization_decision = (
        build_authorization_decision(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
        )
    )

    authorization_manifest = (
        build_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
        )
    )

    kwargs = {
        "acceptance_manifest":
            acceptance_manifest,
        "manifest_proof":
            manifest_proof,
        "authorization_decision":
            authorization_decision,
        "authorization_manifest":
            authorization_manifest,
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError
    ):
        evaluate_governance_release_trial_authorization_gate(
            **kwargs
        )


def test_gate_result_is_immutable(
) -> None:
    result = build_gate()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.passed = False


def test_public_projection_preserves_gate_boundaries(
) -> None:
    payload = (
        build_gate()
        .to_dict()
    )

    assert (
        payload["gate_type"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_VERSION
    )

    boundaries = payload[
        "boundaries"
    ]

    expected_boundaries = {
        "gate_is_read_only",
        "gate_verifies_supplied_evidence_only",
        "gate_does_not_create_authorization",
        "gate_does_not_authenticate_decision_actor",
        "gate_does_not_verify_actor_role_authority",
        "gate_does_not_verify_cryptographic_signature",
        "gate_does_not_verify_durable_decision_record",
        "gate_passed_is_not_trial_execution_permission",
        "gate_is_not_deployment_execution",
        "gate_is_not_paid_assessment_execution",
        "gate_is_not_pa001_paid_work_authorization",
        "gate_is_not_delivery_approval",
        "gate_is_not_production_activation",
        "gate_is_not_intervention_authority",
        "gate_does_not_invoke_pa014_or_pa015",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )