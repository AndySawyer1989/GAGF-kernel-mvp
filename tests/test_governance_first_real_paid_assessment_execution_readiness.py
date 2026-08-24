from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_first_real_paid_assessment_execution_readiness import (
    ACTION_BEGIN_CONTROLLED_EXECUTION,
    ACTION_RESOLVE_EXECUTION_READINESS_BLOCKERS,
    FIRST_REAL_EXECUTION_STATUS_BLOCKED,
    FIRST_REAL_EXECUTION_STATUS_READY,
    FirstRealPaidAssessmentExecutionReadinessError,
    GovernanceFirstRealPaidAssessmentExecutionReadinessService,
)
from backend.app.gagf.governance_real_paid_assessment_preflight import (
    PREFLIGHT_STATUS_READY,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    READINESS_STATUS_READY,
)


PREFLIGHT_TEST_PATH = Path(
    "tests/test_governance_real_paid_assessment_preflight.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def build_governed_values(tmp_path: Path):
    preflight_tests = load_module(
        PREFLIGHT_TEST_PATH,
        "pilot012_existing_preflight_fixture",
    )

    return preflight_tests.build_governed_values(
        tmp_path
    )


def evaluate(values):
    return (
        GovernanceFirstRealPaidAssessmentExecutionReadinessService()
        .evaluate(
            database_path=values["files"]["database"],
            intake=values["intake"],
            authorization_bridge=values["bridge"],
            evidence_binding=values["evidence_binding"],
            contract_execution_event=values["contract_event"],
            paid_work_authorization=values["authorization"],
            request=values["request"],
        )
    )


def test_fully_governed_fresh_assessment_is_ready_for_controlled_execution(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    database = Path(
        values["files"]["database"]
    )

    assert not database.exists()

    result = evaluate(values)

    assert (
        result.status
        == FIRST_REAL_EXECUTION_STATUS_READY
    )

    assert result.ready_for_controlled_execution is True

    assert (
        result.required_operator_action
        == ACTION_BEGIN_CONTROLLED_EXECUTION
    )

    assert result.blockers == ()

    assert (
        result.intake_readiness.readiness_status
        == READINESS_STATUS_READY
    )

    assert (
        result.intake_readiness
        .ready_for_paid_work_authorization
        is True
    )

    assert result.execution_preflight is not None

    assert (
        result.execution_preflight.status
        == PREFLIGHT_STATUS_READY
    )

    assert (
        result.execution_preflight
        .ready_for_operator_execution
        is True
    )

    assert not database.exists()


def test_intake_blocker_short_circuits_execution_preflight(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    values["intake"] = replace(
        values["intake"],
        assessment_scope_confirmed=False,
    )

    service = (
        GovernanceFirstRealPaidAssessmentExecutionReadinessService()
    )

    class ForbiddenPreflight:
        def evaluate(self, **kwargs):
            raise AssertionError(
                "execution preflight must not run when "
                "intake readiness is blocked"
            )

    service._preflight = ForbiddenPreflight()

    result = service.evaluate(
        database_path=values["files"]["database"],
        intake=values["intake"],
        authorization_bridge=values["bridge"],
        evidence_binding=values["evidence_binding"],
        contract_execution_event=values["contract_event"],
        paid_work_authorization=values["authorization"],
        request=values["request"],
    )

    assert (
        result.status
        == FIRST_REAL_EXECUTION_STATUS_BLOCKED
    )

    assert result.ready_for_controlled_execution is False

    assert (
        result.required_operator_action
        == ACTION_RESOLVE_EXECUTION_READINESS_BLOCKERS
    )

    assert result.execution_preflight is None

    assert (
        "intake:assessment_scope_not_confirmed"
        in result.blockers
    )


def test_contract_event_mismatch_surfaces_deterministic_preflight_blocker(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    contract_event = dict(
        values["contract_event"]
    )

    contract_event[
        "contract_execution_event_id"
    ] = "wrong-contract-event"

    values["contract_event"] = contract_event

    result = evaluate(values)

    assert (
        result.status
        == FIRST_REAL_EXECUTION_STATUS_BLOCKED
    )

    assert result.ready_for_controlled_execution is False

    assert result.execution_preflight is not None

    assert (
        "preflight:contract_event_authorization_mismatch"
        in result.blockers
    )


def test_request_hierarchy_mismatch_is_blocked(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    wrong_context = replace(
        values["request"].context,
        assessment_id="different-assessment",
    )

    values["request"] = replace(
        values["request"],
        context=wrong_context,
    )

    result = evaluate(values)

    assert (
        result.status
        == FIRST_REAL_EXECUTION_STATUS_BLOCKED
    )

    assert result.ready_for_controlled_execution is False

    assert result.execution_preflight is not None

    assert (
        "preflight:commercial_hierarchy_mismatch"
        in result.blockers
    )

def test_existing_database_routes_to_governed_recovery(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    database = Path(
        values["files"]["database"]
    )

    database.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    database.write_bytes(
        b"existing governed assessment database"
    )

    before = database.read_bytes()

    result = evaluate(values)

    assert (
        result.status
        == FIRST_REAL_EXECUTION_STATUS_BLOCKED
    )

    assert result.ready_for_controlled_execution is False

    assert result.execution_preflight is not None

    assert (
        "preflight:"
        "database_already_exists_use_governed_recovery_path"
        in result.blockers
    )

    assert database.read_bytes() == before


def test_gate_is_read_only_and_does_not_claim_execution_or_outcomes(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    database = Path(
        values["files"]["database"]
    )

    assert not database.exists()

    result = evaluate(values)

    assert not database.exists()

    payload = result.to_dict()

    assert payload[
        "ready_for_controlled_execution"
    ] is True

    boundaries = payload["boundaries"]

    assert boundaries["pilot012_is_read_only"] is True

    assert (
        boundaries[
            "readiness_is_not_paid_work_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "readiness_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_is_not_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "ready_does_not_mean_executed"
        ]
        is True
    )

    assert (
        boundaries[
            "ready_does_not_create_intervention_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "ready_does_not_verify_remediation_success"
        ]
        is True
    )

    assert (
        boundaries[
            "ready_does_not_verify_roi"
        ]
        is True
    )

    assert (
        boundaries[
            "ready_does_not_verify_customer_outcome"
        ]
        is True
    )

    serialized = json.dumps(
        payload,
        sort_keys=True,
    )

    assert '"assessment_execution_complete"' not in serialized
    assert '"intervention_authorized": true' not in serialized
    assert '"remediation_success": true' not in serialized
    assert '"roi_verified": true' not in serialized
    assert '"customer_outcome_verified": true' not in serialized


def test_structurally_invalid_intake_fails_closed(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    service = (
        GovernanceFirstRealPaidAssessmentExecutionReadinessService()
    )

    with pytest.raises(
        FirstRealPaidAssessmentExecutionReadinessError,
        match=(
            "intake must be a "
            "RealPaidAssessmentIntake"
        ),
    ):
        service.evaluate(
            database_path=values["files"]["database"],
            intake={},
            authorization_bridge=values["bridge"],
            evidence_binding=values["evidence_binding"],
            contract_execution_event=values["contract_event"],
            paid_work_authorization=values["authorization"],
            request=values["request"],
        )