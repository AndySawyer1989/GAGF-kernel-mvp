from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_execution_handoff_api import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX,
    create_customer_trial_execution_handoff_router,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_service import (
    GovernanceCustomerTrialExecutionHandoffService,
)
from tests.test_governance_customer_trial_execution_handoff_bridge import (
    StubAssessmentExecutionRequest,
    build_services,
    record_ready_preflight,
)


BINDING_HASH = "a" * 64
REQUEST_HASH = "b" * 64

HIERARCHY_KEY = (
    "tenant-alpha/"
    "client-customer-001/"
    "engagement-trial-001/"
    "assessment-trial-001"
)


class StubExecutionInputBindingService:
    def __init__(
        self,
        *,
        binding_hash: str = BINDING_HASH,
    ) -> None:
        self.binding = SimpleNamespace(
            hierarchy_key=HIERARCHY_KEY,
            binding_hash=binding_hash,
            assessment_execution_request_hash=(
                REQUEST_HASH
            ),
        )

    def get(
        self,
        *,
        hierarchy_key: str,
    ):
        if hierarchy_key != HIERARCHY_KEY:
            raise ValueError(
                "execution-input binding not found"
            )

        return self.binding

    def reconstruct_request(
        self,
        *,
        binding,
    ):
        if (
            binding.hierarchy_key
            != HIERARCHY_KEY
        ):
            raise ValueError(
                "binding hierarchy mismatch"
            )

        request = (
            StubAssessmentExecutionRequest()
        )

        request.context.hierarchy_key = (
            HIERARCHY_KEY
        )

        return request


def build_client(
    tmp_path,
    *,
    binding_hash: str = BINDING_HASH,
):
    preflight_service, bridge = (
        build_services(
            tmp_path
        )
    )

    receipt_store = (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            tmp_path
            / "customer-trial-handoff-api.sqlite3"
        )
    )

    handoff_service = (
        GovernanceCustomerTrialExecutionHandoffService(
            bridge=bridge,
            receipt_store=receipt_store,
        )
    )

    binding_service = (
        StubExecutionInputBindingService(
            binding_hash=binding_hash
        )
    )

    app = FastAPI()

    app.include_router(
        create_customer_trial_execution_handoff_router(
            service=handoff_service,
            execution_input_binding_service=(
                binding_service
            ),
        )
    )

    return (
        TestClient(app),
        preflight_service,
        handoff_service,
    )


def build_payload(
    **overrides,
):
    payload = {
        "tenant_id":
            "tenant-alpha",
        "client_id":
            "client-customer-001",
        "engagement_id":
            "engagement-trial-001",
        "assessment_id":
            "assessment-trial-001",
        "execution_input_binding_hash":
            BINDING_HASH,
        "contract_execution_event": {
            "contract_execution_event_id":
                "contract-event-001",
            "contract_executed":
                True,
            "contract_execution_review_ready":
                True,
            "contract_execution_confirmed":
                True,
            "executed_contract_reference_recorded":
                True,
            "executed_at_recorded":
                True,
            "all_required_signatures_recorded":
                True,
            "human_operator_confirmed_execution":
                True,
            "requires_final_paid_work_authorization":
                True,
            "human_boundary_required":
                True,
            "gagf_kernel_authoritative":
                True,
            "ai_override_allowed":
                False,
        },
        "paid_work_authorization": {
            "authorization_id":
                "paid-work-auth-001",
            "tenant_id":
                "tenant-alpha",
            "client_id":
                "client-customer-001",
            "engagement_id":
                "engagement-trial-001",
            "assessment_id":
                "assessment-trial-001",
            "contract_execution_event_id":
                "contract-event-001",
            "authorized_by":
                "FIP Trial Operator",
            "authorized_at":
                "2026-09-11T03:25:00+00:00",
            "paid_assessment_authorized":
                True,
        },
    }

    payload.update(
        overrides
    )

    return payload


def test_post_prepares_and_persists_handoff(
    tmp_path,
):
    client, preflight_service, _ = (
        build_client(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=build_payload(),
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["status"] == "ok"

    assert (
        payload["authority"]
        == "HANDOFF_PREPARATION_ONLY"
    )

    assert (
        payload[
            "execution_input_binding"
        ]["binding_hash"]
        == BINDING_HASH
    )

    assert (
        payload["result"][
            "receipt"
        ]["execution_handoff_lineage"][
            "handoff_hash"
        ]
    )

    assert (
        payload["boundaries"][
            "api_does_not_execute_assessment"
        ]
        is True
    )


def test_post_requires_preflight_receipt(
    tmp_path,
):
    client, _, _ = build_client(
        tmp_path
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=build_payload(),
    )

    assert response.status_code == 422

    detail = response.json()[
        "detail"
    ]

    assert (
        detail["code"]
        == (
            "CUSTOMER_TRIAL_"
            "EXECUTION_HANDOFF_VALIDATION_ERROR"
        )
    )


def test_post_rejects_binding_hash_mismatch(
    tmp_path,
):
    client, preflight_service, _ = (
        build_client(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    payload = build_payload(
        execution_input_binding_hash=(
            "c" * 64
        )
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=payload,
    )

    assert response.status_code == 422

    assert (
        "binding hash"
        in response.json()[
            "detail"
        ]["message"]
    )


def test_post_rejects_false_paid_authorization(
    tmp_path,
):
    client, preflight_service, _ = (
        build_client(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    payload = build_payload()

    payload[
        "paid_work_authorization"
    ] = dict(
        payload[
            "paid_work_authorization"
        ]
    )

    payload[
        "paid_work_authorization"
    ][
        "paid_assessment_authorized"
    ] = False

    response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=payload,
    )

    assert response.status_code == 422

    assert (
        "paid_assessment_authorized"
        in response.json()[
            "detail"
        ]["message"]
    )


def test_identical_post_is_idempotent(
    tmp_path,
):
    client, preflight_service, _ = (
        build_client(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    first = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=build_payload(),
    )

    second = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=build_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_receipt = (
        first.json()["result"][
            "receipt"
        ]["receipt_hash"]
    )

    second_receipt = (
        second.json()["result"][
            "receipt"
        ]["receipt_hash"]
    )

    assert (
        second_receipt
        == first_receipt
    )


def test_get_status_restores_persisted_receipt(
    tmp_path,
):
    (
        client,
        preflight_service,
        _,
    ) = build_client(
        tmp_path
    )

    record_ready_preflight(
        preflight_service
    )

    post_response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json=build_payload(),
    )

    assert (
        post_response.status_code
        == 201
    )

    response = client.get(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/tenant-alpha/"
            + "client-customer-001/"
            + "engagement-trial-001/"
            + "assessment-trial-001/"
            + "execution-handoff-status"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authority"] == "READ_ONLY"

    assert (
        payload["result"][
            "receipt_found"
        ]
        is True
    )

    assert (
        payload["result"][
            "receipt"
        ]["receipt_hash"]
        == post_response.json()[
            "result"
        ]["receipt"]["receipt_hash"]
    )


def test_get_missing_status_is_read_only(
    tmp_path,
):
    client, _, _ = build_client(
        tmp_path
    )

    response = client.get(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/tenant-alpha/"
            + "client-customer-001/"
            + "engagement-trial-001/"
            + "assessment-trial-001/"
            + "execution-handoff-status"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["result"][
            "receipt_found"
        ]
        is False
    )

    assert (
        payload["boundaries"][
            "status_is_not_execution_authority"
        ]
        is True
    )


def test_router_exposes_no_execute_route(
    tmp_path,
):
    client, _, _ = build_client(
        tmp_path
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execute"
        ),
        json={},
    )

    assert response.status_code == 404
