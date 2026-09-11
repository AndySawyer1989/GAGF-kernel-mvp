from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_preflight_api import (
    CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX,
    create_customer_trial_preflight_router,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    GovernanceCustomerTrialPreflightReceiptStore,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


EVALUATED_AT = "2026-09-11T02:30:00+00:00"


def build_client(
    tmp_path,
) -> TestClient:
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialPreflightService(
            receipt_store=store
        )
    )

    app = FastAPI()

    app.include_router(
        create_customer_trial_preflight_router(
            service=service
        )
    )

    return TestClient(
        app
    )


def request_payload():
    return {
        "tenant_id":
            "tenant-alpha",
        "client_id":
            "client-customer-001",
        "client_display_name":
            "Customer 001",
        "engagement_id":
            "engagement-trial-001",
        "assessment_id":
            "assessment-trial-001",
        "assessment_name":
            "FIP Governance Assessment",
        "period_start":
            "2026-09-01",
        "period_end":
            "2026-09-30",
        "workflows": [
            "Production change approval"
        ],
        "organizational_units": [
            "Platform Engineering"
        ],
        "objectives": [
            "Measure governance friction"
        ],
        "expected_outcomes": [
            (
                "Produce deterministic "
                "assessment findings"
            )
        ],
        "evidence_requirements": [
            {
                "requirement_id":
                    "EVID-001",
                "description":
                    "Governed workflow evidence",
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
            "FIP Trial Operator",
        "customer_deliverables": [
            "Governance assessment report"
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


def test_executes_ready_preflight_over_api(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/preflight"
        ),
        json=request_payload(),
    )

    assert response.status_code == 201

    payload = response.json()

    assert (
        payload["operation"]
        == "preflight"
    )

    assert (
        payload["authority"]
        == "READINESS_ONLY"
    )

    assert (
        payload["result"][
            "trial_ready"
        ]
        is True
    )

    assert (
        payload["result"][
            "boundaries"
        ][
            "preflight_is_not_paid_execution_authority"
        ]
        is True
    )


def test_api_persists_receipt_and_status_reads_it(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    create_response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/preflight"
        ),
        json=request_payload(),
    )

    assert (
        create_response.status_code
        == 201
    )

    status_response = client.get(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/tenant-alpha/"
            "client-customer-001/"
            "engagement-trial-001/"
            "assessment-trial-001/"
            "preflight-status"
        )
    )

    assert (
        status_response.status_code
        == 200
    )

    payload = (
        status_response.json()
    )

    assert (
        payload["authority"]
        == "READ_ONLY"
    )

    assert (
        payload["result"][
            "receipt_found"
        ]
        is True
    )

    assert (
        payload["result"][
            "trial_ready"
        ]
        is True
    )


def test_missing_status_is_not_started(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    response = client.get(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/tenant-alpha/"
            "client-customer-001/"
            "engagement-trial-001/"
            "assessment-trial-001/"
            "preflight-status"
        )
    )

    assert response.status_code == 200

    result = response.json()[
        "result"
    ]

    assert (
        result["receipt_found"]
        is False
    )

    assert (
        result["trial_ready"]
        is None
    )

    assert result["receipt"] is None


def test_blocked_package_is_still_governed_decision(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    request = request_payload()

    request["period_start"] = (
        "2026-10-01"
    )

    request["period_end"] = (
        "2026-09-30"
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/preflight"
        ),
        json=request,
    )

    assert response.status_code == 201

    result = response.json()[
        "result"
    ]

    assert (
        result["trial_ready"]
        is False
    )

    assert (
        "INVALID_ASSESSMENT_PERIOD"
        in result["decision"][
            "blocking_codes"
        ]
    )


def test_conflicting_second_preflight_is_rejected(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    first = request_payload()

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/preflight"
        ),
        json=first,
    )

    assert response.status_code == 201

    changed = request_payload()

    changed["period_start"] = (
        "2026-10-01"
    )

    changed["period_end"] = (
        "2026-09-30"
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/preflight"
        ),
        json=changed,
    )

    assert response.status_code == 409

    detail = response.json()[
        "detail"
    ]

    assert (
        detail["code"]
        == (
            "CUSTOMER_TRIAL_"
            "PREFLIGHT_RECEIPT_CONFLICT"
        )
    )


def test_pydantic_rejects_structurally_empty_workflows(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    request = request_payload()

    request["workflows"] = []

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/preflight"
        ),
        json=request,
    )

    assert response.status_code == 422


def test_api_does_not_expose_execution_route(
    tmp_path,
):
    client = build_client(
        tmp_path
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
            + "/execute"
        ),
        json=request_payload(),
    )

    assert response.status_code == 404