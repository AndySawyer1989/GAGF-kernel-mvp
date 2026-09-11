from dataclasses import replace

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    GovernanceCustomerTrialPreflightReceiptStore,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


EVALUATED_AT = "2026-09-11T02:30:00+00:00"


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


def build_service(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    return GovernanceCustomerTrialPreflightService(
        receipt_store=store
    )


def test_executes_ready_preflight(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    result = service.execute(
        package=build_package(),
        evaluated_at=EVALUATED_AT,
    )

    assert result.trial_ready is True
    assert (
        result.decision.blocking_issue_count
        == 0
    )

    assert (
        result.receipt.decision_payload[
            "trial_ready"
        ]
        is True
    )


def test_executes_blocked_preflight(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    package = replace(
        build_package(),
        period_start="2026-10-01",
        period_end="2026-09-30",
    )

    result = service.execute(
        package=package,
        evaluated_at=EVALUATED_AT,
    )

    assert result.trial_ready is False

    assert (
        "INVALID_ASSESSMENT_PERIOD"
        in result.decision.blocking_codes
    )


def test_status_restores_persisted_receipt(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    executed = service.execute(
        package=build_package(),
        evaluated_at=EVALUATED_AT,
    )

    status = service.status(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id=(
            "engagement-trial-001"
        ),
        assessment_id=(
            "assessment-trial-001"
        ),
    )

    assert status.receipt_found is True
    assert status.trial_ready is True

    assert status.receipt is not None

    assert (
        status.receipt.receipt_hash
        == executed.receipt.receipt_hash
    )


def test_status_is_not_started_when_no_receipt_exists(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    status = service.status(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id=(
            "engagement-trial-001"
        ),
        assessment_id=(
            "assessment-trial-001"
        ),
    )

    assert status.receipt_found is False
    assert status.trial_ready is None
    assert status.receipt is None


def test_identical_service_execution_is_idempotent(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    package = build_package()

    first = service.execute(
        package=package,
        evaluated_at=EVALUATED_AT,
    )

    second = service.execute(
        package=package,
        evaluated_at=EVALUATED_AT,
    )

    assert (
        second.receipt.receipt_hash
        == first.receipt.receipt_hash
    )


def test_execution_result_preserves_authority_boundaries(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    payload = service.execute(
        package=build_package(),
        evaluated_at=EVALUATED_AT,
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "preflight_is_not_paid_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_is_not_delivery_approval"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_is_not_administrative_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_is_not_intervention_authority"
        ]
        is True
    )


def test_status_result_is_read_only(
    tmp_path,
):
    service = build_service(
        tmp_path
    )

    service.execute(
        package=build_package(),
        evaluated_at=EVALUATED_AT,
    )

    payload = service.status(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id=(
            "engagement-trial-001"
        ),
        assessment_id=(
            "assessment-trial-001"
        ),
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "status_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "status_does_not_authorize_execution"
        ]
        is True
    )