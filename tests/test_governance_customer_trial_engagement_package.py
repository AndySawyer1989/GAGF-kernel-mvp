import pytest

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CUSTOMER_TRIAL_PROGRAM,
    CUSTOMER_TRIAL_SCHEMA_VERSION,
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
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
            "Security review",
        ),
        organizational_units=(
            "Platform Engineering",
            "Security Engineering",
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
                    "Governed workflow event evidence"
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
            "Evidence-backed findings",
            "Prioritized recommendations",
        ),
        trial_boundaries=(
            "Assessment does not establish "
            "root cause by ranking alone",
            "Recommendations do not authorize "
            "implementation",
            "Assessment does not grant "
            "intervention authority",
        ),
        completion_criteria=(
            "Governed report delivered",
            "Client receipt recorded",
            "Client response recorded",
            "Administrative closeout recorded",
        ),
    )


def test_builds_customer_trial_engagement_package():
    package = build_package()

    assert (
        package.program
        == CUSTOMER_TRIAL_PROGRAM
    )

    assert (
        package.schema_version
        == CUSTOMER_TRIAL_SCHEMA_VERSION
    )

    assert (
        package.data_classification
        == "sanitized"
    )

    assert (
        len(package.evidence_requirements)
        == 1
    )


def test_serializes_customer_trial_package():
    payload = build_package().to_dict()

    assert payload["client_id"] == (
        "client-customer-001"
    )

    assert (
        payload["evidence_requirements"][0]
        ["requirement_id"]
        == "EVID-001"
    )


def test_rejects_unsupported_classification():
    package = build_package()

    with pytest.raises(
        ValueError,
        match="unsupported data_classification",
    ):
        CustomerTrialEngagementPackage(
            **{
                **package.to_dict(),
                "data_classification":
                    "restricted-secret",
            }
        )


def test_rejects_empty_required_collection():
    package = build_package()

    with pytest.raises(
        ValueError,
        match="workflows must not be empty",
    ):
        CustomerTrialEngagementPackage(
            **{
                **package.to_dict(),
                "workflows": (),
            }
        )


def test_requires_positive_evidence_minimum():
    with pytest.raises(
        ValueError,
        match="minimum_records",
    ):
        CustomerTrialEvidenceRequirement(
            requirement_id="EVID-001",
            description="Workflow evidence",
            minimum_records=0,
            accepted_formats=("csv",),
        )