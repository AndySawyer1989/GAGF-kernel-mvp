from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_acceptance_manifest import (
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GovernanceReleaseAcceptanceManifestProofResult,
)
from backend.app.gagf.governance_release_trial_authorization_decision import (
    GovernanceReleaseTrialAuthorizationDecision,
    evaluate_governance_release_trial_authorization_decision,
)
from backend.app.gagf.governance_release_trial_authorization_manifest import (
    GovernanceReleaseTrialAuthorizationManifest,
    build_governance_release_trial_authorization_manifest,
)


GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_TYPE = (
    "governance-release-trial-authorization-gate"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_VERSION = (
    "0.1.0"
)

TRIAL_AUTHORIZATION_GATE_STATUS_VERIFIED = (
    "verified"
)

TRIAL_AUTHORIZATION_GATE_STATUS_BLOCKED = (
    "blocked"
)


@dataclass(frozen=True, slots=True)
class GovernanceReleaseTrialAuthorizationGateResult:
    release_environment: str
    backup_id: str
    decision_id: str
    status: str
    passed: bool
    trial_authorized: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    gate_type: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_GATE_VERSION
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "gate_type": self.gate_type,
            "version": self.version,
            "release_environment": self.release_environment,
            "backup_id": self.backup_id,
            "decision_id": self.decision_id,
            "status": self.status,
            "passed": self.passed,
            "trial_authorized": self.trial_authorized,
            "checks": dict(self.checks),
            "failure_reasons": list(self.failure_reasons),
            "boundaries": {
                "gate_is_read_only": True,
                "gate_verifies_supplied_evidence_only": True,
                "gate_does_not_create_authorization": True,
                "gate_does_not_authenticate_decision_actor": True,
                "gate_does_not_verify_actor_role_authority": True,
                "gate_does_not_verify_cryptographic_signature": True,
                "gate_does_not_verify_durable_decision_record": True,
                "gate_passed_is_not_trial_execution_permission": True,
                "gate_is_not_deployment_execution": True,
                "gate_is_not_paid_assessment_execution": True,
                "gate_is_not_pa001_paid_work_authorization": True,
                "gate_is_not_delivery_approval": True,
                "gate_is_not_production_activation": True,
                "gate_is_not_intervention_authority": True,
                "gate_does_not_invoke_pa014_or_pa015": True,
            },
        }


def evaluate_governance_release_trial_authorization_gate(
    *,
    acceptance_manifest: GovernanceReleaseAcceptanceManifest,
    manifest_proof: GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision: GovernanceReleaseTrialAuthorizationDecision,
    authorization_manifest: GovernanceReleaseTrialAuthorizationManifest,
) -> GovernanceReleaseTrialAuthorizationGateResult:
    _require_types(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
    )

    # Re-evaluate the decision against the supplied release evidence.
    # This checks internal consistency, not external authenticity.
    decision_recomputed = None

    try:
        decision_recomputed = (
            evaluate_governance_release_trial_authorization_decision(
                acceptance_manifest=acceptance_manifest,
                manifest_proof=manifest_proof,
                decision_id=authorization_decision.decision_id,
                decided_by=authorization_decision.decided_by,
                decided_at=authorization_decision.decided_at,
                decision=authorization_decision.decision,
            )
        )
    except (TypeError, ValueError):
        pass

    # Independently reconstruct the authorization manifest.
    manifest_recomputed = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
        )
    )

    decision_matches = (
        decision_recomputed is not None
        and authorization_decision.to_dict()
        == decision_recomputed.to_dict()
    )

    manifest_matches = (
        authorization_manifest.to_dict()
        == manifest_recomputed.to_dict()
    )

    checks = {
        "paid_trial_environment":
            acceptance_manifest.release_environment == "paid_trial",

        "manifest_proof_passed":
            manifest_proof.passed is True,

        "manifest_proof_has_no_failure_reasons":
            manifest_proof.failure_reasons == (),

        "manifest_proof_checks_passed":
            bool(manifest_proof.checks)
            and all(
                value is True
                for value in manifest_proof.checks.values()
            ),

        "proof_matches_release_environment":
            manifest_proof.release_environment
            == acceptance_manifest.release_environment,

        "proof_matches_backup_identity":
            manifest_proof.backup_id
            == acceptance_manifest.backup_id,

        "decision_recomputation_succeeded":
            decision_recomputed is not None,

        "decision_matches_recomputed_evidence":
            decision_matches,

        "authorization_manifest_matches_recomputed_projection":
            manifest_matches,

        "authorization_manifest_not_blocked":
            not manifest_recomputed.failure_reasons,

        "authorization_manifest_checks_passed":
            bool(manifest_recomputed.checks)
            and all(
                value is True
                for value in manifest_recomputed.checks.values()
            ),
    }

    failure_reasons = tuple(
        name
        for name, check_passed in checks.items()
        if not check_passed
    )

    passed = not failure_reasons

    status = (
        TRIAL_AUTHORIZATION_GATE_STATUS_VERIFIED
        if passed
        else TRIAL_AUTHORIZATION_GATE_STATUS_BLOCKED
    )

    return GovernanceReleaseTrialAuthorizationGateResult(
        release_environment=acceptance_manifest.release_environment,
        backup_id=acceptance_manifest.backup_id,
        decision_id=authorization_decision.decision_id,
        status=status,
        passed=passed,
        trial_authorized=(
            passed
            and manifest_recomputed.trial_authorized is True
        ),
        checks=checks,
        failure_reasons=failure_reasons,
    )


def _require_types(
    *,
    acceptance_manifest: object,
    manifest_proof: object,
    authorization_decision: object,
    authorization_manifest: object,
) -> None:
    expected = (
        (
            "acceptance_manifest",
            acceptance_manifest,
            GovernanceReleaseAcceptanceManifest,
        ),
        (
            "manifest_proof",
            manifest_proof,
            GovernanceReleaseAcceptanceManifestProofResult,
        ),
        (
            "authorization_decision",
            authorization_decision,
            GovernanceReleaseTrialAuthorizationDecision,
        ),
        (
            "authorization_manifest",
            authorization_manifest,
            GovernanceReleaseTrialAuthorizationManifest,
        ),
    )

    for name, value, expected_type in expected:
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{name} must be a {expected_type.__name__}"
            )