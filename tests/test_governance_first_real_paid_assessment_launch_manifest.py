from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_first_real_paid_assessment_launch_manifest import (
    ACTION_RESOLVE_LAUNCH_BLOCKERS,
    ACTION_REVIEW_CONTROLLED_LAUNCH,
    FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_ID,
    LAUNCH_MANIFEST_STATUS_BLOCKED,
    LAUNCH_MANIFEST_STATUS_READY,
    FirstRealPaidAssessmentLaunchManifestError,
    GovernanceFirstRealPaidAssessmentLaunchManifestService,
)


ROOT = Path(__file__).resolve().parents[1]

SERVICE = GovernanceFirstRealPaidAssessmentLaunchManifestService()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    return module


PREFLIGHT_TEST_MODULE = load_module(
    ROOT
    / "tests"
    / "test_governance_real_paid_assessment_preflight.py",
    "pilot013_preflight_fixture",
)

PILOT012_TEST_MODULE = load_module(
    ROOT
    / "tests"
    / "test_governance_first_real_paid_assessment_execution_readiness.py",
    "pilot013_execution_readiness_fixture",
)

PAYMENT_TEST_MODULE = load_module(
    ROOT
    / "tests"
    / "test_assessment_factory_lite_payment_confirmation_event_service.py",
    "pilot013_payment_confirmation_fixture",
)


def build_launch_values(tmp_path: Path):
    values = PREFLIGHT_TEST_MODULE.build_governed_values(tmp_path)

    readiness = PILOT012_TEST_MODULE.evaluate(values)

    payment_confirmation_event = (
        PAYMENT_TEST_MODULE.build_confirmed_event()
    )

    return {
        "values": values,
        "contract_execution_event": values["contract_event"],
        "payment_confirmation_event": payment_confirmation_event,
        "paid_work_authorization": values["authorization"],
        "authorization_bridge": values["bridge"],
        "execution_readiness": readiness,
    }


def build_manifest(launch_values):
    return SERVICE.build_manifest(
        contract_execution_event=(
            launch_values["contract_execution_event"]
        ),
        payment_confirmation_event=(
            launch_values["payment_confirmation_event"]
        ),
        paid_work_authorization=(
            launch_values["paid_work_authorization"]
        ),
        authorization_bridge=(
            launch_values["authorization_bridge"]
        ),
        execution_readiness=(
            launch_values["execution_readiness"]
        ),
    )


def test_ready_commercial_and_execution_authority_converge(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    result = build_manifest(launch_values)

    assert result.status == LAUNCH_MANIFEST_STATUS_READY
    assert result.ready_for_human_launch_review is True
    assert (
        result.required_operator_action
        == ACTION_REVIEW_CONTROLLED_LAUNCH
    )
    assert result.blockers == ()

    authorization = launch_values["paid_work_authorization"]

    assert result.tenant_id == authorization.tenant_id
    assert result.client_id == authorization.client_id
    assert result.engagement_id == authorization.engagement_id
    assert result.assessment_id == authorization.assessment_id

    assert (
        result.contract_execution_event_id
        == authorization.contract_execution_event_id
    )

    assert (
        result.paid_work_authorization_id
        == authorization.authorization_id
    )

    assert (
        result.authorization_id
        == authorization.authorization_id
    )

    assert (
        result.payment_confirmation_event_id
        == "payment-confirmation-event-001"
    )


def test_contract_execution_event_mismatch_blocks_launch(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    event = dict(
        launch_values["contract_execution_event"]
    )
    event["contract_execution_event_id"] = (
        "different-contract-event"
    )

    launch_values["contract_execution_event"] = event

    result = build_manifest(launch_values)

    assert result.status == LAUNCH_MANIFEST_STATUS_BLOCKED
    assert result.ready_for_human_launch_review is False
    assert (
        result.required_operator_action
        == ACTION_RESOLVE_LAUNCH_BLOCKERS
    )
    assert (
        "authorization:contract_event_mismatch"
        in result.blockers
    )


def test_unconfirmed_payment_blocks_launch(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    event = dict(
        launch_values["payment_confirmation_event"]
    )
    event["event_status"] = "pending_payment_confirmation"

    commercial_boundary = dict(
        event["commercial_boundary"]
    )
    commercial_boundary["payment_confirmation_recorded"] = False
    commercial_boundary["payment_confirmed"] = False
    event["commercial_boundary"] = commercial_boundary

    launch_values["payment_confirmation_event"] = event

    result = build_manifest(launch_values)

    assert result.status == LAUNCH_MANIFEST_STATUS_BLOCKED
    assert result.ready_for_human_launch_review is False

    assert (
        "payment_confirmation:not_payment_confirmed"
        in result.blockers
    )
    assert (
        "payment_confirmation:confirmation_not_recorded"
        in result.blockers
    )
    assert (
        "payment_confirmation:payment_not_confirmed"
        in result.blockers
    )


def test_authorization_bridge_hierarchy_mismatch_blocks_launch(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    bridge = replace(
        launch_values["authorization_bridge"],
        assessment_id="different-assessment",
    )

    launch_values["authorization_bridge"] = bridge

    result = build_manifest(launch_values)

    assert result.status == LAUNCH_MANIFEST_STATUS_BLOCKED
    assert result.ready_for_human_launch_review is False
    assert (
        "authorization_bridge:commercial_hierarchy_mismatch"
        in result.blockers
    )


def test_blocked_pilot012_readiness_blocks_launch(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    readiness = replace(
        launch_values["execution_readiness"],
        status="blocked",
        ready_for_controlled_execution=False,
        blockers=("preflight:synthetic_blocker",),
    )

    launch_values["execution_readiness"] = readiness

    result = build_manifest(launch_values)

    assert result.status == LAUNCH_MANIFEST_STATUS_BLOCKED
    assert result.ready_for_human_launch_review is False

    assert (
        "execution_readiness:not_ready"
        in result.blockers
    )
    assert (
        "execution_readiness:controlled_execution_not_ready"
        in result.blockers
    )
    assert (
        "execution_readiness:has_blockers"
        in result.blockers
    )


def test_structurally_invalid_input_fails_closed(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    with pytest.raises(
        FirstRealPaidAssessmentLaunchManifestError,
        match="payment_confirmation_event must be a dict",
    ):
        SERVICE.build_manifest(
            contract_execution_event=(
                launch_values["contract_execution_event"]
            ),
            payment_confirmation_event=None,
            paid_work_authorization=(
                launch_values["paid_work_authorization"]
            ),
            authorization_bridge=(
                launch_values["authorization_bridge"]
            ),
            execution_readiness=(
                launch_values["execution_readiness"]
            ),
        )


def test_manifest_preserves_constitutional_boundaries(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    result = build_manifest(launch_values)
    payload = result.to_dict()

    assert (
        payload["manifest_type"]
        == FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_ID
    )

    assert payload["status"] == LAUNCH_MANIFEST_STATUS_READY

    boundaries = payload["boundaries"]

    assert boundaries == {
        "pilot013_is_read_only": True,
        "launch_manifest_does_not_create_commercial_events": True,
        "launch_manifest_does_not_create_paid_work_authorization": True,
        "launch_manifest_does_not_create_execution_authority": True,
        "launch_manifest_does_not_execute_assessment": True,
        "payment_confirmation_is_not_paid_work_authorization": True,
        "paid_work_authorization_is_independent_authority": True,
        "pilot012_remains_execution_readiness_authority": True,
        "human_launch_review_remains_required": True,
        "pa015_remains_execution_path": True,
        "launch_ready_does_not_mean_executed": True,
        "launch_ready_does_not_mean_delivered": True,
        "launch_ready_does_not_mean_customer_accepted": True,
        "launch_ready_does_not_verify_outcomes": True,
    }

    assert "execution_result" not in payload
    assert "assessment_executed" not in payload
    assert "delivery_approved" not in payload
    assert "customer_outcome" not in payload


def test_manifest_is_deterministic_and_nonmutating(
    tmp_path: Path,
):
    launch_values = build_launch_values(tmp_path)

    contract_before = dict(
        launch_values["contract_execution_event"]
    )

    payment_before = dict(
        launch_values["payment_confirmation_event"]
    )

    first = build_manifest(launch_values)
    second = build_manifest(launch_values)

    assert first == second
    assert first.to_dict() == second.to_dict()

    assert (
        launch_values["contract_execution_event"]
        == contract_before
    )

    assert (
        launch_values["payment_confirmation_event"]
        == payment_before
    )