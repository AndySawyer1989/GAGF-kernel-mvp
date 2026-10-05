from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_release_acceptance_suite import (
    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
    GovernanceReleaseAcceptanceSuiteResult,
)


GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_TYPE = (
    "governance-release-acceptance-manifest"
)

GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_VERSION = (
    "0.1.0"
)

ACCEPTANCE_MANIFEST_STATUS_READY = (
    "acceptance_ready"
)

ACCEPTANCE_MANIFEST_STATUS_BLOCKED = (
    "blocked"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseAcceptanceManifest:
    release_environment: str
    backup_id: str
    status: str
    acceptance_passed: bool
    acceptance_disposition: str
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...]

    manifest_type: str = (
        GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_ACCEPTANCE_MANIFEST_VERSION
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
            "status":
                self.status,
            "acceptance_passed":
                self.acceptance_passed,
            "acceptance_disposition":
                self.acceptance_disposition,
            "checks":
                dict(
                    self.checks
                ),
            "failure_reasons":
                list(
                    self.failure_reasons
                ),
            "boundaries": {
                "manifest_is_read_only":
                    True,
                "manifest_projects_existing_acceptance_evidence_only":
                    True,
                "manifest_does_not_execute_release_operations":
                    True,
                "manifest_does_not_execute_paid_assessment":
                    True,
                "manifest_does_not_invoke_pa014_or_pa015":
                    True,
                "acceptance_ready_is_not_trial_authorization":
                    True,
                "acceptance_ready_is_not_deployment_authorization":
                    True,
                "acceptance_ready_is_not_customer_execution_authority":
                    True,
                "acceptance_ready_is_not_delivery_authorization":
                    True,
                "acceptance_ready_is_not_production_activation":
                    True,
                "acceptance_ready_is_not_intervention_authority":
                    True,
                "manifest_requires_separate_trial_authorization_gate":
                    True,
            },
        }


def build_governance_release_acceptance_manifest(
    *,
    acceptance_suite:
        GovernanceReleaseAcceptanceSuiteResult,
) -> GovernanceReleaseAcceptanceManifest:
    _require_type(
        acceptance_suite=acceptance_suite
    )

    status = (
        ACCEPTANCE_MANIFEST_STATUS_READY
        if (
            acceptance_suite.passed
            and (
                acceptance_suite.disposition
                == RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
            )
        )
        else ACCEPTANCE_MANIFEST_STATUS_BLOCKED
    )

    return GovernanceReleaseAcceptanceManifest(
        release_environment=(
            acceptance_suite.release_environment
        ),
        backup_id=(
            acceptance_suite.backup_id
        ),
        status=(
            status
        ),
        acceptance_passed=(
            acceptance_suite.passed
        ),
        acceptance_disposition=(
            acceptance_suite.disposition
        ),
        checks=(
            dict(
                acceptance_suite.checks
            )
        ),
        failure_reasons=(
            acceptance_suite.failure_reasons
        ),
    )


def _require_type(
    *,
    acceptance_suite: object,
) -> None:
    if not isinstance(
        acceptance_suite,
        GovernanceReleaseAcceptanceSuiteResult,
    ):
        raise TypeError(
            "acceptance_suite must be a "
            "GovernanceReleaseAcceptanceSuiteResult"
        )