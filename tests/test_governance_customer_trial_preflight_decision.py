from dataclasses import replace

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
)
from backend.app.gagf.governance_customer_trial_preflight_decision import (
    AUTHORITY_BOUNDARY,
    DECISION_APPROVED,
    DECISION_BLOCKED,
    build_customer_trial_preflight_decision,
)


EVALUATED_AT = "2026-09-10T21:45:00+00:00"


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
                accepted_formats=("csv",),
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


def test_builds_approved_preflight_decision():
    result = (
        build_customer_trial_preflight_decision(
            build_package(),
            evaluated_at=EVALUATED_AT,
        )
    )

    assert result.decision == DECISION_APPROVED
    assert result.trial_ready is True
    assert result.blocking_issue_count == 0
    assert result.blocking_codes == ()
    assert result.evaluated_at == EVALUATED_AT


def test_builds_blocked_preflight_decision():
    package = replace(
        build_package(),
        period_start="2026-10-01",
        period_end="2026-09-30",
    )

    result = (
        build_customer_trial_preflight_decision(
            package,
            evaluated_at=EVALUATED_AT,
        )
    )

    assert result.decision == DECISION_BLOCKED
    assert result.trial_ready is False
    assert result.blocking_issue_count >= 1

    assert (
        "INVALID_ASSESSMENT_PERIOD"
        in result.blocking_codes
    )


def test_binds_package_identity():
    result = (
        build_customer_trial_preflight_decision(
            build_package(),
            evaluated_at=EVALUATED_AT,
        )
    )

    identity = result.package_identity

    assert identity.tenant_id == "tenant-alpha"
    assert identity.client_id == (
        "client-customer-001"
    )
    assert identity.engagement_id == (
        "engagement-trial-001"
    )
    assert identity.assessment_id == (
        "assessment-trial-001"
    )


def test_preserves_authority_boundary():
    result = (
        build_customer_trial_preflight_decision(
            build_package(),
            evaluated_at=EVALUATED_AT,
        )
    )

    assert (
        result.authority_boundary
        == AUTHORITY_BOUNDARY
    )

    normalized = (
        result.authority_boundary.lower()
    )

    assert "does not authorize" in normalized
    assert "execution" in normalized
    assert "delivery" in normalized
    assert "closeout" in normalized
    assert "intervention" in normalized


def test_serializes_preflight_decision():
    result = (
        build_customer_trial_preflight_decision(
            build_package(),
            evaluated_at=EVALUATED_AT,
        )
    )

    payload = result.to_dict()

    assert payload["decision"] == (
        DECISION_APPROVED
    )

    assert (
        payload["package_identity"]
        ["assessment_id"]
        == "assessment-trial-001"
    )


def test_preflight_is_deterministic_for_fixed_time():
    package = build_package()

    first = (
        build_customer_trial_preflight_decision(
            package,
            evaluated_at=EVALUATED_AT,
        )
    )

    second = (
        build_customer_trial_preflight_decision(
            package,
            evaluated_at=EVALUATED_AT,
        )
    )

    assert first == second