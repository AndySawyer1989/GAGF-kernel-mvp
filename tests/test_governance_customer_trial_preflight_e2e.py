from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_preflight_api import (
    CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX,
)
from backend.app.gagf.governance_customer_trial_preflight_api_registration import (
    register_customer_trial_preflight_api,
)


EVALUATED_AT = "2026-09-11T03:00:00+00:00"


def build_realistic_customer_package():
    return {
        "tenant_id":
            "tenant-northstar",
        "client_id":
            "client-northstar-logistics",
        "client_display_name":
            "Northstar Logistics Group",
        "engagement_id":
            "engagement-governance-health-001",
        "assessment_id":
            "assessment-customer-trial-001",
        "assessment_name":
            (
                "Northstar Logistics "
                "Governance Assessment"
            ),
        "period_start":
            "2026-07-01",
        "period_end":
            "2026-07-31",
        "workflows": [
            "Production change approval",
            "Security exception review",
            (
                "Cross-team dependency "
                "resolution"
            ),
            "Release readiness",
        ],
        "organizational_units": [
            "Platform Engineering",
            "Security Engineering",
            "Application Delivery",
            "Operations",
        ],
        "objectives": [
            (
                "Measure governance friction "
                "across selected operational "
                "workflows"
            ),
        ],
        "expected_outcomes": [
            (
                "Produce deterministic "
                "evidence-backed governance "
                "assessment findings"
            ),
            (
                "Identify prioritized "
                "governance improvement "
                "opportunities"
            ),
        ],
        "evidence_requirements": [
            {
                "requirement_id":
                    "EVID-WORKFLOW-001",
                "description":
                    (
                        "Governed workflow event "
                        "evidence for the "
                        "assessment period"
                    ),
                "minimum_records":
                    30,
                "accepted_formats": [
                    "csv"
                ],
            }
        ],
        "data_classification":
            "sanitized",
        "prepared_by":
            "FIP Customer Trial Operator",
        "customer_deliverables": [
            "Governance assessment report",
            "Evidence-backed findings",
            "Prioritized recommendations",
        ],
        "trial_boundaries": [
            (
                "Assessment ranking does not "
                "establish root cause."
            ),
            (
                "Recommendations do not "
                "authorize implementation."
            ),
            (
                "Assessment does not grant "
                "intervention authority."
            ),
        ],
        "completion_criteria": [
            "Governed report delivered",
            "Client receipt recorded",
            "Client response recorded",
            (
                "Administrative closeout "
                "recorded"
            ),
        ],
        "evaluated_at":
            EVALUATED_AT,
    }


def build_app(
    database_path: Path,
) -> FastAPI:
    app = FastAPI()

    register_customer_trial_preflight_api(
        app=app,
        database_path=database_path,
    )

    return app


def status_url() -> str:
    return (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/tenant-northstar/"
        "client-northstar-logistics/"
        "engagement-governance-health-001/"
        "assessment-customer-trial-001/"
        "preflight-status"
    )


def preflight_url() -> str:
    return (
        CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        + "/preflight"
    )


def test_controlled_customer_trial_preflight_e2e(
    tmp_path,
):
    database_path = (
        tmp_path
        / "customer-trial-preflight.sqlite3"
    )

    first_app = build_app(
        database_path
    )

    first_client = TestClient(
        first_app
    )

    package = (
        build_realistic_customer_package()
    )

    create_response = (
        first_client.post(
            preflight_url(),
            json=package,
        )
    )

    assert (
        create_response.status_code
        == 201
    )

    created = (
        create_response.json()
    )

    assert (
        created["authority"]
        == "READINESS_ONLY"
    )

    result = created[
        "result"
    ]

    assert (
        result["trial_ready"]
        is True
    )

    assert (
        result["decision"][
            "blocking_issue_count"
        ]
        == 0
    )

    receipt = result[
        "receipt"
    ]

    assert (
        len(
            receipt[
                "decision_payload_hash"
            ]
        )
        == 64
    )

    assert (
        len(
            receipt[
                "receipt_hash"
            ]
        )
        == 64
    )

    original_receipt_hash = (
        receipt["receipt_hash"]
    )

    status_response = (
        first_client.get(
            status_url()
        )
    )

    assert (
        status_response.status_code
        == 200
    )

    status_payload = (
        status_response.json()
    )

    assert (
        status_payload["authority"]
        == "READ_ONLY"
    )

    assert (
        status_payload["result"][
            "receipt_found"
        ]
        is True
    )

    assert (
        status_payload["result"][
            "receipt"
        ][
            "receipt_hash"
        ]
        == original_receipt_hash
    )

    second_app = build_app(
        database_path
    )

    second_client = TestClient(
        second_app
    )

    restarted_status = (
        second_client.get(
            status_url()
        )
    )

    assert (
        restarted_status.status_code
        == 200
    )

    restarted_payload = (
        restarted_status.json()
    )

    assert (
        restarted_payload[
            "result"
        ][
            "receipt_found"
        ]
        is True
    )

    assert (
        restarted_payload[
            "result"
        ][
            "receipt"
        ][
            "receipt_hash"
        ]
        == original_receipt_hash
    )

    identical_retry = (
        second_client.post(
            preflight_url(),
            json=package,
        )
    )

    assert (
        identical_retry.status_code
        == 201
    )

    assert (
        identical_retry.json()[
            "result"
        ][
            "receipt"
        ][
            "receipt_hash"
        ]
        == original_receipt_hash
    )

    conflicting = dict(
        package
    )

    conflicting[
        "period_start"
    ] = "2026-08-01"

    conflicting[
        "period_end"
    ] = "2026-08-31"

    conflict_response = (
        second_client.post(
            preflight_url(),
            json=conflicting,
        )
    )

    assert (
        conflict_response.status_code
        == 409
    )

    assert (
        conflict_response.json()[
            "detail"
        ][
            "code"
        ]
        == (
            "CUSTOMER_TRIAL_"
            "PREFLIGHT_RECEIPT_CONFLICT"
        )
    )

    execute_response = (
        second_client.post(
            (
                CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
                + "/execute"
            ),
            json={},
        )
    )

    assert (
        execute_response.status_code
        == 404
    )

    boundaries = (
        restarted_payload[
            "result"
        ][
            "receipt"
        ][
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "receipt_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_delivery_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )