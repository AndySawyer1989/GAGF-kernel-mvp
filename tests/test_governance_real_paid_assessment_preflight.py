from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.gagf.governance_real_paid_assessment_preflight import (
    PREFLIGHT_STATUS_BLOCKED,
    PREFLIGHT_STATUS_READY,
    GovernanceRealPaidAssessmentPreflightService,
    RealPaidAssessmentPreflightError,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

PA015_TEST_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test_run_real_paid_assessment.py"
)

PA015_RUNNER_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "run_real_paid_assessment.py"
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
    fixture_module = load_module(
        PA015_TEST_PATH,
        "pilot004_pa015_test_fixture",
    )

    runner = load_module(
        PA015_RUNNER_PATH,
        "pilot004_pa015_runner",
    )

    files = fixture_module.build_operator_files(
        tmp_path
    )

    (
        intake,
        bridge,
        authorization,
        request,
        evidence_binding,
        contract_event,
    ) = runner._build_governed_inputs(
        database_path=files["database"],
        intake_json_path=files["intake"],
        authorization_json_path=files["authorization"],
        contract_event_json_path=files["contract_event"],
        request_json_path=files["request"],
        evidence_approvals_json_path=files["approvals"],
    )

    return {
        "files": files,
        "intake": intake,
        "bridge": bridge,
        "authorization": authorization,
        "request": request,
        "evidence_binding": evidence_binding,
        "contract_event": contract_event,
    }


def evaluate(values):
    return (
        GovernanceRealPaidAssessmentPreflightService()
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


def test_fresh_governed_paid_assessment_is_ready(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    database_path = values["files"]["database"]

    assert not database_path.exists()

    result = evaluate(values)

    assert result.status == PREFLIGHT_STATUS_READY
    assert result.ready_for_operator_execution is True
    assert result.blockers == ()
    assert result.database_exists is False
    assert result.intake_storage_matches_database is True
    assert result.hierarchy_consistent is True
    assert result.authorization_affirmative is True
    assert result.authorization_bridge_ready is True
    assert result.evidence_binding_approved is True
    assert result.contract_event_matches_authorization is True

    assert result.hierarchy_key == (
        "tenant-alpha/"
        "client-acme/"
        "engagement-001/"
        "assessment-001"
    )

    # PILOT-004 is preflight only.
    assert not database_path.exists()

    payload = result.to_dict()

    assert payload["status"] == "ready"
    assert payload["ready_for_operator_execution"] is True
    assert payload["boundaries"] == {
        "preflight_is_not_paid_work_authorization": True,
        "preflight_is_not_execution": True,
        "preflight_is_not_execution_authority": True,
        "preflight_is_not_recovery_authority": True,
        "ready_does_not_mean_executed": True,
    }


def test_existing_database_is_blocked_without_mutation(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    database_path = values["files"]["database"]

    original_bytes = b"PILOT004-existing-database-sentinel"
    database_path.write_bytes(original_bytes)

    result = evaluate(values)

    assert result.status == PREFLIGHT_STATUS_BLOCKED
    assert result.ready_for_operator_execution is False
    assert result.database_exists is True

    assert result.blockers == (
        "database_already_exists_use_governed_recovery_path",
    )

    assert database_path.read_bytes() == original_bytes


def test_contract_event_mismatch_is_blocked(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    values["contract_event"] = {
        **values["contract_event"],
        "contract_execution_event_id": (
            "different-contract-event"
        ),
    }

    result = evaluate(values)

    assert result.status == PREFLIGHT_STATUS_BLOCKED
    assert result.ready_for_operator_execution is False

    assert result.blockers == (
        "contract_event_authorization_mismatch",
    )

    assert not values["files"]["database"].exists()


def test_corrupted_authorization_not_affirmative_is_blocked(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    authorization = values["authorization"]

    # The domain constructor already requires this field to be true.
    # PILOT-004 still fails closed if an otherwise-valid frozen
    # authorization object is corrupted after construction.
    object.__setattr__(
        authorization,
        "paid_assessment_authorized",
        False,
    )

    result = evaluate(values)

    assert result.status == PREFLIGHT_STATUS_BLOCKED
    assert result.ready_for_operator_execution is False

    assert (
        "paid_work_authorization_not_affirmative"
        in result.blockers
    )

    assert not values["files"]["database"].exists()


def test_authorization_hierarchy_mismatch_is_blocked(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    values["authorization"] = replace(
        values["authorization"],
        assessment_id="assessment-other",
    )

    result = evaluate(values)

    assert result.status == PREFLIGHT_STATUS_BLOCKED
    assert result.ready_for_operator_execution is False

    assert "commercial_hierarchy_mismatch" in result.blockers

    assert not values["files"]["database"].exists()


def test_evidence_binding_not_approved_is_blocked(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    values["evidence_binding"] = replace(
        values["evidence_binding"],
        binding_status="blocked",
    )

    result = evaluate(values)

    assert result.status == PREFLIGHT_STATUS_BLOCKED
    assert result.ready_for_operator_execution is False

    assert (
        "execution_evidence_not_approved"
        in result.blockers
    )

    assert not values["files"]["database"].exists()


def test_wrong_input_type_fails_closed(
    tmp_path: Path,
):
    values = build_governed_values(tmp_path)

    with pytest.raises(
        RealPaidAssessmentPreflightError,
        match="intake must be a RealPaidAssessmentIntake",
    ):
        GovernanceRealPaidAssessmentPreflightService().evaluate(
            database_path=values["files"]["database"],
            intake=object(),
            authorization_bridge=values["bridge"],
            evidence_binding=values["evidence_binding"],
            contract_execution_event=values["contract_event"],
            paid_work_authorization=values["authorization"],
            request=values["request"],
        )

    assert not values["files"]["database"].exists()