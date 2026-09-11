from dataclasses import replace

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
)
from backend.app.gagf.governance_customer_trial_engagement_validator import (
    validate_customer_trial_engagement_package,
)


def build_package():
    return CustomerTrialEngagementPackage(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        client_display_name="Customer 001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        assessment_name=(
            "FIP Governance Assessment"
        ),
        period_start="2026-09-01",
        period_end="2026-09-30",
        workflows=(
            "Production change approval",
        ),
        organizational_units=(
            "Platform Engineering",
        ),
        objectives=(
            "Measure governance friction",
        ),
        expected_outcomes=(
            "Produce deterministic "
            "assessment findings",
        ),
        evidence_requirements=(
            CustomerTrialEvidenceRequirement(
                requirement_id="EVID-001",
                description=(
                    "Governed workflow evidence"
                ),
                minimum_records=30,
                accepted_formats=(
                    "csv",
                ),
            ),
        ),
        data_classification="sanitized",
        prepared_by="FIP Trial Operator",
        customer_deliverables=(
            "Governance assessment report",
        ),
        trial_boundaries=(
            "Assessment ranking does not "
            "establish root cause.",
            "Recommendations do not authorize "
            "implementation.",
            "Assessment does not grant "
            "intervention authority.",
        ),
        completion_criteria=(
            "Governed report delivered",
            "Client receipt recorded",
            "Client response recorded",
            "Administrative closeout recorded",
        ),
    )


def test_accepts_trial_ready_package():
    result = (
        validate_customer_trial_engagement_package(
            build_package()
        )
    )

    assert result.trial_ready is True
    assert result.issue_count == 0
    assert result.issues == ()


def test_rejects_invalid_assessment_period():
    package = replace(
        build_package(),
        period_start="2026-10-01",
        period_end="2026-09-30",
    )

    result = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    assert result.trial_ready is False

    assert (
        "INVALID_ASSESSMENT_PERIOD"
        in {
            issue.code
            for issue in result.issues
        }
    )


def test_rejects_invalid_iso_date():
    package = replace(
        build_package(),
        period_start="09/01/2026",
    )

    result = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    assert result.trial_ready is False

    assert (
        "INVALID_DATE"
        in {
            issue.code
            for issue in result.issues
        }
    )


def test_rejects_unsupported_evidence_format():
    package = replace(
        build_package(),
        evidence_requirements=(
            CustomerTrialEvidenceRequirement(
                requirement_id="EVID-002",
                description="Ticket evidence",
                minimum_records=10,
                accepted_formats=(
                    "xlsx",
                ),
            ),
        ),
    )

    result = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    assert result.trial_ready is False

    assert (
        "UNSUPPORTED_EVIDENCE_FORMAT"
        in {
            issue.code
            for issue in result.issues
        }
    )


def test_requires_intervention_authority_boundary():
    package = replace(
        build_package(),
        trial_boundaries=(
            "Assessment ranking does not "
            "establish root cause.",
        ),
    )

    result = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    assert result.trial_ready is False

    assert (
        "INTERVENTION_AUTHORITY_BOUNDARY_REQUIRED"
        in {
            issue.code
            for issue in result.issues
        }
    )


def test_validation_is_deterministic():
    package = build_package()

    first = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    second = (
        validate_customer_trial_engagement_package(
            package
        )
    )

    assert first == second