from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
)
from backend.app.gagf.governance_customer_trial_engagement_validator import (
    CustomerTrialValidationResult,
    validate_customer_trial_engagement_package,
)


PREFLIGHT_DECISION_SCHEMA_VERSION = "1.0"

DECISION_APPROVED = "trial_ready"
DECISION_BLOCKED = "trial_blocked"

AUTHORITY_BOUNDARY = (
    "Customer trial preflight readiness does not authorize "
    "paid assessment execution, delivery, administrative "
    "closeout, recommendation implementation, or intervention."
)


@dataclass(frozen=True)
class CustomerTrialPackageIdentity:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str


@dataclass(frozen=True)
class CustomerTrialPreflightDecision:
    decision: str
    trial_ready: bool
    blocking_issue_count: int
    blocking_codes: tuple[str, ...]
    package_identity: CustomerTrialPackageIdentity
    evaluated_at: str
    authority_boundary: str
    schema_version: str = (
        PREFLIGHT_DECISION_SCHEMA_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return asdict(self)


def _package_identity(
    package: CustomerTrialEngagementPackage,
) -> CustomerTrialPackageIdentity:
    return CustomerTrialPackageIdentity(
        tenant_id=package.tenant_id,
        client_id=package.client_id,
        engagement_id=package.engagement_id,
        assessment_id=package.assessment_id,
    )


def build_customer_trial_preflight_decision(
    package: CustomerTrialEngagementPackage,
    *,
    evaluated_at: str | None = None,
) -> CustomerTrialPreflightDecision:
    validation: CustomerTrialValidationResult = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    if evaluated_at is None:
        evaluated_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    blocking_codes = tuple(
        issue.code
        for issue in validation.issues
    )

    return CustomerTrialPreflightDecision(
        decision=(
            DECISION_APPROVED
            if validation.trial_ready
            else DECISION_BLOCKED
        ),
        trial_ready=validation.trial_ready,
        blocking_issue_count=(
            validation.issue_count
        ),
        blocking_codes=blocking_codes,
        package_identity=(
            _package_identity(
                package
            )
        ),
        evaluated_at=evaluated_at,
        authority_boundary=AUTHORITY_BOUNDARY,
    )