from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_suite import (
    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
    GovernanceReleaseAcceptanceSuiteResult,
)


GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_TYPE = (
    "governance-release-acceptance-manifest-proof"
)

GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_VERSION = (
    "0.1.0"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseAcceptanceManifestProofResult:
    release_environment: str
    backup_id: str
    passed: bool
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    proof_type: str = (
        GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_PROOF_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "proof_type":
                self.proof_type,
            "version":
                self.version,
            "release_environment":
                self.release_environment,
            "backup_id":
                self.backup_id,
            "passed":
                self.passed,
            "checks":
                dict(
                    self.checks
                ),
            "failure_reasons":
                list(
                    self.failure_reasons
                ),
            "boundaries": {
                "proof_is_read_only":
                    True,
                "proof_validates_existing_acceptance_evidence_only":
                    True,
                "proof_does_not_execute_release_operations":
                    True,
                "proof_does_not_execute_paid_assessment":
                    True,
                "proof_does_not_invoke_pa014_or_pa015":
                    True,
                "proof_passed_is_not_trial_authorization":
                    True,
                "proof_passed_is_not_deployment_authorization":
                    True,
                "proof_passed_is_not_customer_execution_authority":
                    True,
                "proof_passed_is_not_delivery_authorization":
                    True,
                "proof_passed_is_not_production_activation":
                    True,
                "proof_passed_is_not_intervention_authority":
                    True,
                "proof_requires_separate_trial_authorization_gate":
                    True,
            },
        }


def evaluate_governance_release_acceptance_manifest_proof(
    *,
    acceptance_suite:
        GovernanceReleaseAcceptanceSuiteResult,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
) -> GovernanceReleaseAcceptanceManifestProofResult:
    _require_types(
        acceptance_suite=acceptance_suite,
        acceptance_manifest=acceptance_manifest,
    )

    release_environment = (
        acceptance_suite.release_environment
    )

    backup_id = (
        acceptance_suite.backup_id
    )

    checks = {
        "paid_trial_environment":
            release_environment
            == "paid_trial",

        "acceptance_suite_passed":
            acceptance_suite.passed
            is True,

        "acceptance_suite_disposition_accepted":
            acceptance_suite.disposition
            == RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,

        "acceptance_manifest_ready":
            acceptance_manifest.status
            == ACCEPTANCE_MANIFEST_STATUS_READY,

        "manifest_acceptance_passed":
            acceptance_manifest.acceptance_passed
            is True,

        "manifest_matches_release_environment":
            acceptance_manifest.release_environment
            == release_environment,

        "manifest_matches_backup_identity":
            acceptance_manifest.backup_id
            == backup_id,

        "manifest_matches_acceptance_passed":
            acceptance_manifest.acceptance_passed
            == acceptance_suite.passed,

        "manifest_matches_acceptance_disposition":
            acceptance_manifest.acceptance_disposition
            == acceptance_suite.disposition,

        "manifest_matches_checks":
            acceptance_manifest.checks
            == acceptance_suite.checks,

        "manifest_matches_failure_reasons":
            acceptance_manifest.failure_reasons
            == acceptance_suite.failure_reasons,

        "acceptance_suite_has_no_failure_reasons":
            acceptance_suite.failure_reasons
            == (),

        "acceptance_manifest_has_no_failure_reasons":
            acceptance_manifest.failure_reasons
            == (),
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    return GovernanceReleaseAcceptanceManifestProofResult(
        release_environment=(
            release_environment
        ),
        backup_id=(
            backup_id
        ),
        passed=(
            not failure_reasons
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
    acceptance_suite: object,
    acceptance_manifest: object,
) -> None:
    if not isinstance(
        acceptance_suite,
        GovernanceReleaseAcceptanceSuiteResult,
    ):
        raise TypeError(
            "acceptance_suite must be a "
            "GovernanceReleaseAcceptanceSuiteResult"
        )

    if not isinstance(
        acceptance_manifest,
        GovernanceReleaseAcceptanceManifest,
    ):
        raise TypeError(
            "acceptance_manifest must be a "
            "GovernanceReleaseAcceptanceManifest"
        )