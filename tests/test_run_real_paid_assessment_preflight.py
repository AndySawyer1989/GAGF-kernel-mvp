from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

PREFLIGHT_SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "run_real_paid_assessment_preflight.py"
)

PA015_TEST_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test_run_real_paid_assessment.py"
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


def build_operator_files(tmp_path: Path):
    pa015_tests = load_module(
        PA015_TEST_PATH,
        "pilot004_cli_pa015_fixture",
    )

    return pa015_tests.build_operator_files(
        tmp_path
    )


def run_preflight(
    monkeypatch,
    *,
    files,
    output_path: Path | None = None,
):
    runner = load_module(
        PREFLIGHT_SCRIPT_PATH,
        "pilot004_preflight_runner",
    )

    arguments = [
        str(PREFLIGHT_SCRIPT_PATH),
        "--database",
        str(files["database"]),
        "--intake-json",
        str(files["intake"]),
        "--authorization-json",
        str(files["authorization"]),
        "--contract-event-json",
        str(files["contract_event"]),
        "--request-json",
        str(files["request"]),
        "--evidence-approvals-json",
        str(files["approvals"]),
    ]

    if output_path is not None:
        arguments.extend(
            [
                "--output-json",
                str(output_path),
            ]
        )

    monkeypatch.setattr(
        sys,
        "argv",
        arguments,
    )

    exit_code = runner.main()

    return runner, exit_code


def test_ready_preflight_returns_zero_without_execution(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    database_path = files["database"]

    assert not database_path.exists()

    _, exit_code = run_preflight(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload["preflight_passed"] is True

    result = payload["result"]

    assert result["status"] == "ready"
    assert result["blockers"] == []
    assert result["database_exists"] is False
    assert result["ready_for_operator_execution"] is True

    assert payload["boundaries"] == {
        "preflight_is_not_paid_work_authorization": True,
        "preflight_is_not_execution": True,
        "preflight_is_not_execution_authority": True,
        "preflight_is_not_recovery_authority": True,
        "ready_does_not_mean_executed": True,
        "pa015_remains_operator_execution_entry_point": True,
    }

    # Strongest CLI boundary proof:
    # preflight did not create the execution database.
    assert not database_path.exists()


def test_existing_database_returns_blocked_exit_two(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    database_path = files["database"]

    original_bytes = b"PILOT004-existing-database"
    database_path.write_bytes(original_bytes)

    _, exit_code = run_preflight(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""

    payload = json.loads(captured.err)

    assert payload["preflight_passed"] is False

    result = payload["result"]

    assert result["status"] == "blocked"
    assert result["ready_for_operator_execution"] is False

    assert result["blockers"] == [
        "database_already_exists_use_governed_recovery_path"
    ]

    assert database_path.read_bytes() == original_bytes


def test_invalid_governed_input_returns_one_without_database(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    authorization = json.loads(
        files["authorization"].read_text(
            encoding="utf-8"
        )
    )

    authorization["paid_assessment_authorized"] = False

    files["authorization"].write_text(
        json.dumps(
            authorization,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    _, exit_code = run_preflight(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    # The existing governed PA015 builder/bridge fails closed
    # before PILOT-004 can declare operational readiness.
    assert exit_code == 1
    assert captured.out == ""

    payload = json.loads(captured.err)

    assert payload["preflight_passed"] is False
    assert "governed real paid-assessment preflight failure" in (
        payload["error"]
    )

    assert not files["database"].exists()


def test_ready_preflight_can_write_exclusive_evidence(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    output_path = tmp_path / "preflight-result.json"

    _, exit_code = run_preflight(
        monkeypatch,
        files=files,
        output_path=output_path,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    stdout_payload = json.loads(captured.out)
    file_payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert stdout_payload == file_payload
    assert file_payload["preflight_passed"] is True

    assert not files["database"].exists()


def test_existing_output_is_preserved_and_fails_before_preflight(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    output_path = tmp_path / "preflight-result.json"

    original_bytes = (
        b"PILOT004-DO-NOT-OVERWRITE"
    )

    output_path.write_bytes(original_bytes)

    _, exit_code = run_preflight(
        monkeypatch,
        files=files,
        output_path=output_path,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""

    payload = json.loads(captured.err)

    assert payload["preflight_passed"] is False
    assert "refusing to overwrite preflight evidence" in (
        payload["error"]
    )

    assert output_path.read_bytes() == original_bytes

    # Collision was rejected before governed execution/preflight.
    assert not files["database"].exists()


def test_preflight_script_does_not_import_recovery_service():
    source = PREFLIGHT_SCRIPT_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "GovernanceRealPaidAssessmentExecutionRecoveryService"
        not in source
    )

    assert (
        "GovernanceRealPaidAssessmentExecutionService"
        not in source
    )

    assert ".execute(" not in source


def test_preflight_script_reuses_pa015_governed_input_builder():
    source = PREFLIGHT_SCRIPT_PATH.read_text(
        encoding="utf-8"
    )

    assert "_build_governed_inputs" in source

    assert (
        "GovernanceRealPaidAssessmentPreflightService"
        in source
    )