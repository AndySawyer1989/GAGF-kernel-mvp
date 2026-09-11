from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_customer_trial_execution_handoff_api import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_api_registration import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_BINDING_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_STORE_STATE_KEY,
    register_customer_trial_execution_handoff_api,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_service import (
    GovernanceCustomerTrialExecutionHandoffService,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from tests.test_governance_customer_trial_execution_handoff_bridge import (
    StubAssessmentExecutionRequest,
    build_services,
    record_ready_preflight,
)


BINDING_HASH = "a" * 64

HIERARCHY_KEY = (
    "tenant-alpha/"
    "client-customer-001/"
    "engagement-trial-001/"
    "assessment-trial-001"
)


class StubExecutionInputBindingService:
    def __init__(
        self,
    ) -> None:
        self.binding = SimpleNamespace(
            hierarchy_key=HIERARCHY_KEY,
            binding_hash=BINDING_HASH,
            assessment_execution_request_hash=(
                "b" * 64
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


def build_registered_app(
    tmp_path,
):
    preflight_service, _ = (
        build_services(
            tmp_path
        )
    )

    binding_service = (
        StubExecutionInputBindingService()
    )

    app = FastAPI()

    register_customer_trial_execution_handoff_api(
        app=app,
        database_path=(
            tmp_path
            / "registered-customer-trial-handoff.sqlite3"
        ),
        preflight_service=preflight_service,
        execution_input_binding_service=(
            binding_service
        ),
    )

    return (
        app,
        preflight_service,
        binding_service,
    )


def test_registration_exposes_handoff_routes(
    tmp_path,
):
    app, _, _ = build_registered_app(
        tmp_path
    )

    paths = {
        route.path
        for route in app.routes
        if hasattr(
            route,
            "path",
        )
    }

    assert (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + "/execution-handoff"
        in paths
    )

    assert (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "execution-handoff-status"
        )
        in paths
    )


def test_registration_exposes_no_execute_route(
    tmp_path,
):
    app, _, _ = build_registered_app(
        tmp_path
    )

    paths = {
        route.path
        for route in app.routes
        if hasattr(
            route,
            "path",
        )
    }

    assert (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + "/execute"
        not in paths
    )


def test_registration_publishes_service_state(
    tmp_path,
):
    app, _, _ = build_registered_app(
        tmp_path
    )

    value = getattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY,
    )

    assert isinstance(
        value,
        GovernanceCustomerTrialExecutionHandoffService,
    )


def test_registration_publishes_store_state(
    tmp_path,
):
    app, _, _ = build_registered_app(
        tmp_path
    )

    value = getattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_STORE_STATE_KEY,
    )

    assert isinstance(
        value,
        GovernanceCustomerTrialExecutionHandoffReceiptStore,
    )


def test_registration_reuses_exact_binding_service(
    tmp_path,
):
    (
        app,
        _,
        binding_service,
    ) = build_registered_app(
        tmp_path
    )

    registered = getattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_BINDING_SERVICE_STATE_KEY,
    )

    assert (
        registered
        is binding_service
    )


def test_registration_invalidates_openapi_cache(
    tmp_path,
):
    app = FastAPI()

    app.openapi()

    assert (
        app.openapi_schema
        is not None
    )

    preflight_service, _ = (
        build_services(
            tmp_path
        )
    )

    binding_service = (
        StubExecutionInputBindingService()
    )

    register_customer_trial_execution_handoff_api(
        app=app,
        database_path=(
            tmp_path
            / "openapi-handoff.sqlite3"
        ),
        preflight_service=preflight_service,
        execution_input_binding_service=(
            binding_service
        ),
    )

    assert app.openapi_schema is None


def test_registered_status_endpoint_is_read_only(
    tmp_path,
):
    app, _, _ = build_registered_app(
        tmp_path
    )

    client = TestClient(
        app
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
        payload["authority"]
        == "READ_ONLY"
    )

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


def test_registered_post_still_requires_preflight(
    tmp_path,
):
    app, _, _ = build_registered_app(
        tmp_path
    )

    client = TestClient(
        app
    )

    response = client.post(
        (
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
            + "/execution-handoff"
        ),
        json={
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
        },
    )

    assert response.status_code == 422

    assert (
        response.json()[
            "detail"
        ]["code"]
        == (
            "CUSTOMER_TRIAL_"
            "EXECUTION_HANDOFF_VALIDATION_ERROR"
        )
    )
