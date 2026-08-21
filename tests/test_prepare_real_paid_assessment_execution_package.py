from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

PACKAGE_SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "prepare_real_paid_assessment_execution_package.py"
)

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


def build_files(tmp_path: Path):
    fixture = load_module(
        PA015_TEST_PATH,
        "pilot005_pa015_fixture",
    )

    files = fixture.build_operator_files(tmp_path)

    files["preflight"] = (
        tmp_path / "preflight.json"
    )

    files["execution_output"] = (
        tmp_path / "execution-result.json"
    )

    files["package"] = (
        tmp_path / "execution-package.json"
    )

    return files


def run_preflight(
    monkeypatch,
    *,
    files,
):
    runner = load_module(
        PREFLIGHT_SCRIPT_PATH,
        "pilot005_preflight_runner",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
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
            "--output-json",
            str(files["preflight"]),
        ],
    )

    return runner.main()


def run_package(
    monkeypatch,
    *,
    files,
):
    runner = load_module(
        PACKAGE_SCRIPT_PATH,
        "pilot005_package_runner",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(PACKAGE_SCRIPT_PATH),
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
            "--preflight-json",
            str(files["preflight"]),
            "--execution-output-json",
            str(files["execution_output"]),
            "--output-json",
            str(files["package"]),
        ],
    )

    return runner, runner.main()


def test_ready_preflight_builds_non_executing_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_files(tmp_path)

    assert run_preflight(
        monkeypatch,
        files=files,
    ) == 0

    capsys.readouterr()

    runner, exit_code = run_package(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload["package_type"] == (
        "first_real_paid_assessment_execution_package"
    )

    assert payload[
        "pilot004_preflight"
    ]["ready_for_operator_execution"] is True

    assert payload[
        "execution"
    ]["human_go_no_go_required"] is True

    assert payload[
        "execution"
    ]["automatically_execute"] is False

    assert payload["execution"]["argv"][1:3] == [
        "-m",
        "scripts.run_real_paid_assessment",
    ]

    assert payload[
        "post_execution_verification"
    ]["expected_core_artifact_count_after"] == 10

    assert payload[
        "boundaries"
    ]["package_is_not_execution"] is True

    assert payload[
        "boundaries"
    ]["package_is_not_paid_work_authorization"] is True

    # Package preparation must not invoke PA015.
    assert not files["database"].exists()
    assert not files["execution_output"].exists()

    assert files["package"].exists()

    file_payload = json.loads(
        files["package"].read_text(
            encoding="utf-8"
        )
    )

    assert file_payload == payload

    package_body = dict(payload)
    package_hash = package_body.pop(
        "package_hash"
    )

    assert package_hash == runner._package_hash(
        package_body
    )


def test_package_binds_exact_controlled_input_bytes(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_files(tmp_path)

    assert run_preflight(
        monkeypatch,
        files=files,
    ) == 0

    capsys.readouterr()

    _, exit_code = run_package(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 0

    payload = json.loads(captured.out)

    commitments = {
        item["label"]: item
        for item in payload["controlled_inputs"]
    }

    assert set(commitments) == {
        "intake_json",
        "authorization_json",
        "contract_event_json",
        "request_json",
        "evidence_approvals_json",
    }

    for item in commitments.values():
        assert len(item["sha256"]) == 64
        assert item["byte_count"] > 0
        assert Path(item["path"]).is_absolute()

    assert len(payload["evidence_files"]) >= 1

    for evidence in payload["evidence_files"]:
        assert evidence["source_id"]
        assert len(evidence["sha256"]) == 64
        assert evidence["byte_count"] > 0
        assert Path(evidence["path"]).is_absolute()


def test_non_ready_preflight_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_files(tmp_path)

    assert run_preflight(
        monkeypatch,
        files=files,
    ) == 0

    capsys.readouterr()

    payload = json.loads(
        files["preflight"].read_text(
            encoding="utf-8"
        )
    )

    payload["preflight_passed"] = False
    payload["result"]["status"] = "blocked"
    payload[
        "result"
    ]["ready_for_operator_execution"] = False

    files["preflight"].write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    _, exit_code = run_package(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""

    error = json.loads(captured.err)

    assert error[
        "package_preparation_passed"
    ] is False

    assert "preflight did not pass" in error["error"]

    assert not files["package"].exists()
    assert not files["database"].exists()


def test_stale_preflight_fails_if_database_now_exists(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_files(tmp_path)

    assert run_preflight(
        monkeypatch,
        files=files,
    ) == 0

    capsys.readouterr()

    sentinel = b"PILOT005-stale-preflight"

    files["database"].write_bytes(
        sentinel
    )

    _, exit_code = run_package(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    error = json.loads(captured.err)

    assert "READY evidence is stale" in error["error"]

    assert not files["package"].exists()
    assert files["database"].read_bytes() == sentinel


def test_existing_package_output_is_preserved(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_files(tmp_path)

    assert run_preflight(
        monkeypatch,
        files=files,
    ) == 0

    capsys.readouterr()

    original = b"PILOT005-PRESERVE-PACKAGE"

    files["package"].write_bytes(original)

    _, exit_code = run_package(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""

    assert files["package"].read_bytes() == original
    assert not files["database"].exists()


def test_existing_pa015_output_blocks_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_files(tmp_path)

    assert run_preflight(
        monkeypatch,
        files=files,
    ) == 0

    capsys.readouterr()

    original = b"PILOT005-PRESERVE-EXECUTION"

    files["execution_output"].write_bytes(
        original
    )

    _, exit_code = run_package(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    error = json.loads(captured.err)

    assert "execution output already exists" in (
        error["error"]
    )

    assert (
        files["execution_output"].read_bytes()
        == original
    )

    assert not files["package"].exists()
    assert not files["database"].exists()


def test_package_script_never_invokes_execution():
    source = PACKAGE_SCRIPT_PATH.read_text(
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

    assert "_build_governed_inputs" in source
    assert "human_go_no_go_required" in source
    assert '"automatically_execute": False' in source


def test_real_assessment_cli_modules_are_importable():
    import subprocess

    modules = (
        "scripts.run_real_paid_assessment_preflight",
        "scripts.prepare_real_paid_assessment_execution_package",
        "scripts.run_real_paid_assessment",
    )

    for module in modules:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                module,
                "--help",
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, (
            module,
            completed.stdout,
            completed.stderr,
        )