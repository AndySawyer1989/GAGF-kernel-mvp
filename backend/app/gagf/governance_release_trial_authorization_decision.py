from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GovernanceReleaseAcceptanceManifestProofResult,
)


GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_TYPE = (
    "governance-release-trial-authorization-decision"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_VERSION = (
    "0.1.0"
)

TRIAL_AUTHORIZATION_DECISION_AUTHORIZE = (
    "authorize"
)

TRIAL_AUTHORIZATION_DECISION_DENY = (
    "deny"
)

TRIAL_AUTHORIZATION_STATUS_AUTHORIZED = (
    "trial_authorized"
)

TRIAL_AUTHORIZATION_STATUS_DENIED = (
    "trial_denied"
)

TRIAL_AUTHORIZATION_STATUS_BLOCKED = (
    "blocked"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseTrialAuthorizationDecision:
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

    decision_type: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_DECISION_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "decision_type":
                self.decision_type,
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
                "decision_requires_explicit_human_input":
                    True,
                "release_acceptance_does_not_self_authorize":
                    True,
                "manifest_readiness_does_not_self_authorize":
                    True,
                "manifest_proof_does_not_self_authorize":
                    True,
                "trial_authorization_is_not_deployment_execution":
                    True,
                "trial_authorization_is_not_paid_assessment_execution":
                    True,
                "trial_authorization_is_not_pa001_paid_work_authorization":
                    True,
                "trial_authorization_is_not_delivery_approval":
                    True,
                "trial_authorization_is_not_production_activation":
                    True,
                "trial_authorization_is_not_intervention_authority":
                    True,
                "trial_authorization_does_not_invoke_pa014_or_pa015":
                    True,
            },
        }


def evaluate_governance_release_trial_authorization_decision(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    decision_id: str,
    decided_by: str,
    decided_at: str,
    decision: str,
) -> GovernanceReleaseTrialAuthorizationDecision:
    _require_types(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
    )

    normalized_decision_id = _normalize_required_text(
        name="decision_id",
        value=decision_id,
    )

    normalized_decided_by = _normalize_required_text(
        name="decided_by",
        value=decided_by,
    )

    normalized_decided_at = _normalize_required_text(
        name="decided_at",
        value=decided_at,
    )

    normalized_decision = _normalize_decision(
        decision
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

        "decision_id_present":
            bool(
                normalized_decision_id
            ),

        "decided_by_present":
            bool(
                normalized_decided_by
            ),

        "decided_at_present":
            bool(
                normalized_decided_at
            ),

        "decision_is_supported":
            normalized_decision
            in {
                TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
                TRIAL_AUTHORIZATION_DECISION_DENY,
            },
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    prerequisites_passed = (
        not failure_reasons
    )

    if not prerequisites_passed:
        status = (
            TRIAL_AUTHORIZATION_STATUS_BLOCKED
        )

        trial_authorized = False

    elif (
        normalized_decision
        == TRIAL_AUTHORIZATION_DECISION_AUTHORIZE
    ):
        status = (
            TRIAL_AUTHORIZATION_STATUS_AUTHORIZED
        )

        trial_authorized = True

    else:
        status = (
            TRIAL_AUTHORIZATION_STATUS_DENIED
        )

        trial_authorized = False

    return GovernanceReleaseTrialAuthorizationDecision(
        release_environment=(
            release_environment
        ),
        backup_id=(
            backup_id
        ),
        decision_id=(
            normalized_decision_id
        ),
        decided_by=(
            normalized_decided_by
        ),
        decided_at=(
            normalized_decided_at
        ),
        decision=(
            normalized_decision
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


def _require_types(
    *,
    acceptance_manifest: object,
    manifest_proof: object,
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


def _normalize_required_text(
    *,
    name: str,
    value: object,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{name} must be a string"
        )

    normalized = (
        value.strip()
    )

    if not normalized:
        raise ValueError(
            f"{name} must not be empty"
        )

    return normalized


def _normalize_decision(
    value: object,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "decision must be a string"
        )

    normalized = (
        value
        .strip()
        .lower()
    )

    if normalized not in {
        TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
        TRIAL_AUTHORIZATION_DECISION_DENY,
    }:
        raise ValueError(
            "decision must be "
            "'authorize' or 'deny'"
        )

    return normalized