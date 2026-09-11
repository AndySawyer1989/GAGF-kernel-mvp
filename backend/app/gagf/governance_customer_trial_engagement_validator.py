from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
    SUPPORTED_DATA_CLASSIFICATIONS,
)


SUPPORTED_EVIDENCE_FORMATS = (
    "csv",
)


@dataclass(frozen=True)
class CustomerTrialValidationIssue:
    code: str
    field: str
    message: str


@dataclass(frozen=True)
class CustomerTrialValidationResult:
    trial_ready: bool
    issue_count: int
    issues: tuple[
        CustomerTrialValidationIssue,
        ...
    ]


def _parse_iso_date(
    value: str,
    *,
    field: str,
) -> tuple[
    date | None,
    CustomerTrialValidationIssue | None,
]:
    try:
        parsed = date.fromisoformat(
            value
        )
    except ValueError:
        return (
            None,
            CustomerTrialValidationIssue(
                code="INVALID_DATE",
                field=field,
                message=(
                    f"{field} must be a valid "
                    "ISO date in YYYY-MM-DD format"
                ),
            ),
        )

    return parsed, None


def _validate_evidence_requirement(
    requirement:
        CustomerTrialEvidenceRequirement,
) -> tuple[
    CustomerTrialValidationIssue,
    ...
]:
    issues: list[
        CustomerTrialValidationIssue
    ] = []

    unsupported_formats = tuple(
        evidence_format
        for evidence_format
        in requirement.accepted_formats
        if evidence_format
        not in SUPPORTED_EVIDENCE_FORMATS
    )

    if unsupported_formats:
        issues.append(
            CustomerTrialValidationIssue(
                code=(
                    "UNSUPPORTED_EVIDENCE_FORMAT"
                ),
                field=(
                    "evidence_requirements."
                    f"{requirement.requirement_id}."
                    "accepted_formats"
                ),
                message=(
                    "unsupported evidence format(s): "
                    + ", ".join(
                        unsupported_formats
                    )
                ),
            )
        )

    return tuple(
        issues
    )


def _contains_intervention_authority_boundary(
    package:
        CustomerTrialEngagementPackage,
) -> bool:
    normalized = tuple(
        boundary.lower()
        for boundary
        in package.trial_boundaries
    )

    return any(
        "intervention authority" in boundary
        and (
            "does not" in boundary
            or "not authorize" in boundary
            or "no " in boundary
        )
        for boundary
        in normalized
    )


def validate_customer_trial_engagement_package(
    package:
        CustomerTrialEngagementPackage,
) -> CustomerTrialValidationResult:
    issues: list[
        CustomerTrialValidationIssue
    ] = []

    start_date, start_issue = (
        _parse_iso_date(
            package.period_start,
            field="period_start",
        )
    )

    end_date, end_issue = (
        _parse_iso_date(
            package.period_end,
            field="period_end",
        )
    )

    if start_issue is not None:
        issues.append(
            start_issue
        )

    if end_issue is not None:
        issues.append(
            end_issue
        )

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        issues.append(
            CustomerTrialValidationIssue(
                code=(
                    "INVALID_ASSESSMENT_PERIOD"
                ),
                field="assessment_period",
                message=(
                    "period_start must be on or "
                    "before period_end"
                ),
            )
        )

    if (
        package.data_classification
        not in SUPPORTED_DATA_CLASSIFICATIONS
    ):
        issues.append(
            CustomerTrialValidationIssue(
                code=(
                    "UNSUPPORTED_DATA_CLASSIFICATION"
                ),
                field="data_classification",
                message=(
                    "data classification is not "
                    "supported for controlled "
                    "customer trials"
                ),
            )
        )

    for requirement in (
        package.evidence_requirements
    ):
        issues.extend(
            _validate_evidence_requirement(
                requirement
            )
        )

    if not package.customer_deliverables:
        issues.append(
            CustomerTrialValidationIssue(
                code=(
                    "CUSTOMER_DELIVERABLES_REQUIRED"
                ),
                field="customer_deliverables",
                message=(
                    "at least one explicit customer "
                    "deliverable is required"
                ),
            )
        )

    if not package.trial_boundaries:
        issues.append(
            CustomerTrialValidationIssue(
                code="TRIAL_BOUNDARIES_REQUIRED",
                field="trial_boundaries",
                message=(
                    "controlled customer trial "
                    "boundaries must be explicit"
                ),
            )
        )

    if not package.completion_criteria:
        issues.append(
            CustomerTrialValidationIssue(
                code=(
                    "COMPLETION_CRITERIA_REQUIRED"
                ),
                field="completion_criteria",
                message=(
                    "explicit trial completion "
                    "criteria are required"
                ),
            )
        )

    if (
        package.trial_boundaries
        and not
        _contains_intervention_authority_boundary(
            package
        )
    ):
        issues.append(
            CustomerTrialValidationIssue(
                code=(
                    "INTERVENTION_AUTHORITY_"
                    "BOUNDARY_REQUIRED"
                ),
                field="trial_boundaries",
                message=(
                    "trial boundaries must explicitly "
                    "state that the assessment does "
                    "not grant intervention authority"
                ),
            )
        )

    frozen_issues = tuple(
        issues
    )

    return CustomerTrialValidationResult(
        trial_ready=(
            len(
                frozen_issues
            )
            == 0
        ),
        issue_count=len(
            frozen_issues
        ),
        issues=frozen_issues,
    )