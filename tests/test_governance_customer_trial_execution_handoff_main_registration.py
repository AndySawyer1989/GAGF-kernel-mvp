from __future__ import annotations

from backend.app.main import app

from backend.app.gagf.governance_customer_trial_execution_handoff_api import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_api_registration import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_BINDING_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY,
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_STORE_STATE_KEY,
)


def registered_paths() -> set[str]:
    return {
        route.path
        for route in app.routes
        if hasattr(
            route,
            "path",
        )
    }


def test_main_registers_execution_handoff_post_route():
    paths = registered_paths()

    assert (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + "/execution-handoff"
        in paths
    )


def test_main_registers_execution_handoff_status_route():
    paths = registered_paths()

    assert (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "execution-handoff-status"
        )
        in paths
    )


def test_main_registers_no_customer_trial_execute_route():
    paths = registered_paths()

    assert (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        + "/execute"
        not in paths
    )


def test_main_publishes_execution_handoff_service():
    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY,
    )


def test_main_publishes_execution_handoff_store():
    assert hasattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_STORE_STATE_KEY,
    )


def test_main_reuses_exact_execution_input_binding_service():
    handoff_binding_service = getattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_BINDING_SERVICE_STATE_KEY,
    )

    assessment_binding_service = (
        app.state
        .governance_commercial_paid_assessment_execution_input_binding_service
    )

    assert (
        handoff_binding_service
        is assessment_binding_service
    )


def test_main_reuses_existing_customer_trial_preflight_service():
    handoff_service = getattr(
        app.state,
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_STATE_KEY,
    )

    assert (
        handoff_service._bridge._preflight_service
        is app.state.governance_customer_trial_preflight_service
    )