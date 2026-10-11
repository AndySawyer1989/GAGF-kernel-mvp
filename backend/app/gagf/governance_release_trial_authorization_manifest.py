from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GovernanceReleaseAcceptanceManifestProofResult,
)
from backend.app.gagf.governance_release_trial_authorization_decision import (
    TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    TRIAL_AUTHORIZATION_DECISION_DENY,
    TRIAL_AUTHORIZATION_STATUS_AUTHORIZED,
    TRIAL_AUTHORIZATION_STATUS_BLOCKED,
    TRIAL_AUTHORIZATION_STATUS_DENIED,
    GovernanceReleaseTrialAuthorizationDecision,
)


GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_TYPE = (
    "governance-release-trial-authorization-manifest"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_VERSION = (
    "0.1.0"
)

TRIAL_AUTHORIZATION_MANIFEST_STATUS_AUTHORIZED = (
    "trial_authorized"
)

TRIAL_AUTHORIZATION_MANIFEST_STATUS_DENIED = (
    "trial_denied"
)

TRIAL_AUTHORIZATION_MANIFEST_STATUS_BLOCKED = (
    "blocked"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseTrialAuthorizationManifest:
    release_environment: str
    backup_id: str
    decision_id: str
    decided_by: str
    decided_at: str
    decision: str
    status: str
    trial_authorized: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    manifest_type: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_MANIFEST_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "manifest_type":
                self.manifest_type,
            "version":
                self.version,
            "release_environment":
                self.release_environment,
            "backup_id":
                self.backup_id,
            "decision_id":
                self.decision_id,
            "decided_by":
                self.decided_by,
            "decided_at":
                self.decided_at,
            "decision":
                self.decision,
            "status":
                self.status,
            "trial_authorized":
                self.trial_authorized,
            "checks":
                dict(
                    self.checks
                ),
            "failure_reasons":
                list(
                    self.failure_reasons
                ),
            "boundaries": {
                "manifest_is_projection_only":
                    True,
                "manifest_does_not_create_trial_authorization":
                    True,
                "manifest_requires_preexisting_authorization_decision":
                    True,
                "manifest_binds_authorization_to_release_evidence":
                    True,
                "manifest_is_not_deployment_execution":
                    True,
                "manifest_is_not_paid_assessment_execution":
                    True,
                "manifest_is_not_pa001_paid_work_authorization":
                    True,
                "manifest_is_not_delivery_approval":
                    True,
                "manifest_is_not_production_activation":
                    True,
                "manifest_is_not_intervention_authority":
                    True,
                "manifest_does_not_invoke_pa014_or_pa015":
                    True,
            },
        }


def build_governance_release_trial_authorization_manifest(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
) -> GovernanceReleaseTrialAuthorizationManifest:
    _require_types(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
    )

    release_environment = (
        acceptance_manifest.release_environment
    )

    backup_id = (
        acceptance_manifest.backup_id
    )

    checks = {
        "paid_trial_environment":
            release_environment
            == "paid_trial",

        "acceptance_manifest_ready":
            acceptance_manifest.status
            == ACCEPTANCE_MANIFEST_STATUS_READY,

        "acceptance_manifest_passed":
            acceptance_manifest.acceptance_passed
            is True,

        "acceptance_manifest_has_no_failure_reasons":
            acceptance_manifest.failure_reasons
            == (),

        "manifest_proof_passed":
            manifest_proof.passed
            is True,

        "manifest_proof_has_no_failure_reasons":
            manifest_proof.failure_reasons
            == (),

        "manifest_proof_matches_release_environment":
            manifest_proof.release_environment
            == release_environment,

        "manifest_proof_matches_backup_identity":
            manifest_proof.backup_id
            == backup_id,

        "authorization_decision_matches_release_environment":
            authorization_decision.release_environment
            == release_environment,

        "authorization_decision_matches_backup_identity":
            authorization_decision.backup_id
            == backup_id,

        "authorization_decision_identity_present":
            bool(
                authorization_decision.decision_id
            ),

        "authorization_decision_actor_present":
            bool(
                authorization_decision.decided_by
            ),

        "authorization_decision_time_present":
            bool(
                authorization_decision.decided_at
            ),

        "authorization_decision_supported":
            authorization_decision.decision
            in {
                TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
                TRIAL_AUTHORIZATION_DECISION_DENY,
            },

        "authorization_decision_not_blocked":
            authorization_decision.status
            != TRIAL_AUTHORIZATION_STATUS_BLOCKED,

        "authorization_decision_has_no_failure_reasons":
            authorization_decision.failure_reasons
            == (),

        "authorization_decision_checks_passed":
            bool(
                authorization_decision.checks
            )
            and all(
                authorization_decision.checks.values()
            ),

        "authorization_decision_state_consistent":
            _decision_state_is_consistent(
                authorization_decision
            ),
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    if failure_reasons:
        status = (
            TRIAL_AUTHORIZATION_MANIFEST_STATUS_BLOCKED
        )

        trial_authorized = False

    elif (
        authorization_decision.status
        == TRIAL_AUTHORIZATION_STATUS_AUTHORIZED
    ):
        status = (
            TRIAL_AUTHORIZATION_MANIFEST_STATUS_AUTHORIZED
        )

        trial_authorized = True

    elif (
        authorization_decision.status
        == TRIAL_AUTHORIZATION_STATUS_DENIED
    ):
        status = (
            TRIAL_AUTHORIZATION_MANIFEST_STATUS_DENIED
        )

        trial_authorized = False

    else:
        status = (
            TRIAL_AUTHORIZATION_MANIFEST_STATUS_BLOCKED
        )

        trial_authorized = False

    return GovernanceReleaseTrialAuthorizationManifest(
        release_environment=(
            release_environment
        ),
        backup_id=(
            backup_id
        ),
        decision_id=(
            authorization_decision.decision_id
        ),
        decided_by=(
            authorization_decision.decided_by
        ),
        decided_at=(
            authorization_decision.decided_at
        ),
        decision=(
            authorization_decision.decision
        ),
        status=(
            status
        ),
        trial_authorized=(
            trial_authorized
        ),
        checks=(
            checks
        ),
        failure_reasons=(
            failure_reasons
        ),
    )


def _decision_state_is_consistent(
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
) -> bool:
    if (
        authorization_decision.status
        == TRIAL_AUTHORIZATION_STATUS_AUTHORIZED
    ):
        return (
            authorization_decision.decision
            == TRIAL_AUTHORIZATION_DECISION_AUTHORIZE
            and authorization_decision.trial_authorized
            is True
            and authorization_decision.failure_reasons
            == ()
        )

    if (
        authorization_decision.status
        == TRIAL_AUTHORIZATION_STATUS_DENIED
    ):
        return (
            authorization_decision.decision
            == TRIAL_AUTHORIZATION_DECISION_DENY
            and authorization_decision.trial_authorized
            is False
            and authorization_decision.failure_reasons
            == ()
        )

    return False


def _require_types(
    *,
    acceptance_manifest: object,
    manifest_proof: object,
    authorization_decision: object,
) -> None:
    if not isinstance(
        acceptance_manifest,
        GovernanceReleaseAcceptanceManifest,
    ):
        raise TypeError(
            "acceptance_manifest must be a "
            "GovernanceReleaseAcceptanceManifest"
        )

    if not isinstance(
        manifest_proof,
        GovernanceReleaseAcceptanceManifestProofResult,
    ):
        raise TypeError(
            "manifest_proof must be a "
            "GovernanceReleaseAcceptanceManifestProofResult"
        )

    if not isinstance(
        authorization_decision,
        GovernanceReleaseTrialAuthorizationDecision,
    ):
        raise TypeError(
            "authorization_decision must be a "
            "GovernanceReleaseTrialAuthorizationDecision"
        )