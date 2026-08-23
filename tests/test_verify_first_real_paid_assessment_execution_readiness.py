from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from scripts import (
    verify_first_real_paid_assessment_execution_readiness as cli,
)


PA015_TEST_PATH = Path(
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


def build_operator_files(tmp_path: Path):
    preflight_tests = load_module(
        PA015_TEST_PATH,
        "pilot012_cli_existing_preflight_fixture",
    )

    values = preflight_tests.build_governed_values(
        tmp_path
    )

    return values["files"]


def run_cli(
    *,
    database,
    intake,
    authorization,
    contract_event,
    request,
    approvals,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_first_real_paid_assessment_execution_readiness",
            "--database",
            str(database),
            "--intake-json",
            str(intake),
            "--authorization-json",
            str(authorization),
            "--contract-event-json",
            str(contract_event),
            "--request-json",
            str(request),
            "--evidence-approvals-json",
            str(approvals),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_ready_cli_emits_governed_readiness_without_execution(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    database = Path(files["database"])

    assert not database.exists()

    output = tmp_path / "pilot012-ready.json"

    exit_code = run_cli(
        database=database,
        intake=files["intake"],
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload["first_real_execution_readiness_evaluated"]
        is True
    )

    assert payload["ready_for_controlled_execution"] is True

    assert payload["status"] == "ready_for_controlled_execution"

    assert (
        payload["required_operator_action"]
        == "begin_controlled_real_paid_assessment_execution"
    )

    assert payload["result"]["blockers"] == []

    assert not database.exists()


def test_existing_database_is_governed_blocked_result_not_cli_failure(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    database = Path(files["database"])

    database.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    original = b"existing-assessment-database"

    database.write_bytes(original)

    output = tmp_path / "pilot012-blocked.json"

    exit_code = run_cli(
        database=database,
        intake=files["intake"],
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload["first_real_execution_readiness_evaluated"]
        is True
    )

    assert payload["ready_for_controlled_execution"] is False
    assert payload["status"] == "blocked"

    assert (
        "preflight:"
        "database_already_exists_use_governed_recovery_path"
        in payload["result"]["blockers"]
    )

    assert database.read_bytes() == original


def test_output_collision_fails_before_governed_input_construction(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    output = tmp_path / "existing-readiness.json"

    original = b"preserve-me"

    output.write_bytes(original)

    class ForbiddenBuild:
        def __call__(self, **kwargs):
            raise AssertionError(
                "governed input construction must not run "
                "when output already exists"
            )

    monkeypatch.setattr(
        cli,
        "_build_governed_inputs",
        ForbiddenBuild(),
    )

    exit_code = run_cli(
        database=tmp_path / "database.sqlite3",
        intake=tmp_path / "missing-intake.json",
        authorization=tmp_path / "missing-authorization.json",
        contract_event=tmp_path / "missing-contract-event.json",
        request=tmp_path / "missing-request.json",
        approvals=tmp_path / "missing-approvals.json",
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    assert (
        "output JSON already exists"
        in captured.err
    )

    assert output.read_bytes() == original


def test_missing_input_fails_closed_without_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    missing_intake = (
        tmp_path / "does-not-exist-intake.json"
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=files["database"],
        intake=missing_intake,
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    assert "intake_json does not exist" in captured.err

    assert not output.exists()


def test_malformed_governed_input_fails_closed_without_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    intake_path = Path(files["intake"])

    intake_path.write_text(
        "{this is not valid json",
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=files["database"],
        intake=intake_path,
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.err
    assert not output.exists()


def test_repeated_readiness_evaluation_is_deterministic_and_non_mutating(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    database = Path(files["database"])

    first_output = tmp_path / "readiness-first.json"

    first_exit = run_cli(
        database=database,
        intake=files["intake"],
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=first_output,
        monkeypatch=monkeypatch,
    )

    first_capture = capsys.readouterr()

    assert first_exit == 0
    assert first_capture.err == ""
    assert not database.exists()

    second_output = tmp_path / "readiness-second.json"

    second_exit = run_cli(
        database=database,
        intake=files["intake"],
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=second_output,
        monkeypatch=monkeypatch,
    )

    second_capture = capsys.readouterr()

    assert second_exit == 0
    assert second_capture.err == ""
    assert not database.exists()

    first_payload = json.loads(
        first_output.read_text(
            encoding="utf-8"
        )
    )

    second_payload = json.loads(
        second_output.read_text(
            encoding="utf-8"
        )
    )

    assert first_payload == second_payload


def test_cli_preserves_constitutional_execution_boundaries(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    database = Path(files["database"])

    output = tmp_path / "readiness-boundaries.json"

    exit_code = run_cli(
        database=database,
        intake=files["intake"],
        authorization=files["authorization"],
        contract_event=files["contract_event"],
        request=files["request"],
        approvals=files["approvals"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert not database.exists()

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    boundaries = payload["boundaries"]

    assert boundaries["pilot012_is_read_only"] is True

    assert (
        boundaries[
            "readiness_evaluation_is_not_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "ready_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "paid_work_authorization_remains_external"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_remains_existing_execution_readiness_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa015_or_governed_recovery_remains_execution_path"
        ]
        is True
    )

    assert boundaries["no_database_created_by_pilot012"] is True
    assert boundaries["no_delivery_authority_created"] is True
    assert boundaries["no_intervention_authority_created"] is True
    assert boundaries["no_outcome_claim_created"] is True

    serialized = json.dumps(
        payload,
        sort_keys=True,
    )

    assert '"assessment_execution_complete"' not in serialized
    assert '"intervention_authorized": true' not in serialized
    assert '"customer_outcome_verified": true' not in serialized