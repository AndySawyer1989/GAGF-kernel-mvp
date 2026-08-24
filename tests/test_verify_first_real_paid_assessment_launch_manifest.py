from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from backend.app.gagf.governance_first_real_paid_assessment_launch_manifest import (
    ACTION_RESOLVE_LAUNCH_BLOCKERS,
    ACTION_REVIEW_CONTROLLED_LAUNCH,
    LAUNCH_MANIFEST_STATUS_BLOCKED,
    LAUNCH_MANIFEST_STATUS_READY,
)
from scripts import (
    verify_first_real_paid_assessment_launch_manifest as cli,
)


ROOT = Path(__file__).resolve().parents[1]

PILOT012_CLI_TEST_PATH = (
    ROOT
    / "tests"
    / "test_verify_first_real_paid_assessment_execution_readiness.py"
)

PAYMENT_TEST_PATH = (
    ROOT
    / "tests"
    / "test_assessment_factory_lite_payment_confirmation_event_service.py"
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


PILOT012_CLI_TESTS = load_module(
    PILOT012_CLI_TEST_PATH,
    "pilot013_cli_pilot012_fixture",
)

PAYMENT_TESTS = load_module(
    PAYMENT_TEST_PATH,
    "pilot013_cli_payment_fixture",
)


def build_operator_files(tmp_path: Path):
    return PILOT012_CLI_TESTS.build_operator_files(
        tmp_path
    )


def write_payment_confirmation(
    tmp_path: Path,
    *,
    event: dict | None = None,
) -> Path:
    payload = (
        PAYMENT_TESTS.build_confirmed_event()
        if event is None
        else event
    )

    path = tmp_path / "payment-confirmation.json"

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path


def run_cli(
    *,
    files,
    payment_confirmation: Path,
    output: Path,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_first_real_paid_assessment_launch_manifest",
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
            "--payment-confirmation-json",
            str(payment_confirmation),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_ready_cli_emits_launch_manifest_without_execution(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = write_payment_confirmation(
        tmp_path
    )

    output = tmp_path / "pilot013-ready.json"

    assert files["database"].exists() is False

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 0
    assert output.exists() is True

    payload = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert (
        payload[
            "first_real_paid_assessment_launch_manifest_evaluated"
        ]
        is True
    )
    assert (
        payload["status"]
        == LAUNCH_MANIFEST_STATUS_READY
    )
    assert (
        payload["ready_for_human_launch_review"]
        is True
    )
    assert (
        payload["required_operator_action"]
        == ACTION_REVIEW_CONTROLLED_LAUNCH
    )
    assert payload["result"]["blockers"] == []

    assert files["database"].exists() is False

    captured = capsys.readouterr()

    assert (
        "ready_for_human_launch_review"
        in captured.out
    )


def test_unconfirmed_payment_is_governed_blocked_result(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    event = PAYMENT_TESTS.build_confirmed_event()

    event["event_status"] = (
        "pending_payment_confirmation"
    )

    commercial_boundary = dict(
        event["commercial_boundary"]
    )
    commercial_boundary[
        "payment_confirmation_recorded"
    ] = False
    commercial_boundary["payment_confirmed"] = False

    event["commercial_boundary"] = commercial_boundary

    payment_confirmation = write_payment_confirmation(
        tmp_path,
        event=event,
    )

    output = tmp_path / "pilot013-blocked-payment.json"

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 0
    assert output.exists() is True

    payload = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert (
        payload["status"]
        == LAUNCH_MANIFEST_STATUS_BLOCKED
    )
    assert (
        payload["ready_for_human_launch_review"]
        is False
    )
    assert (
        payload["required_operator_action"]
        == ACTION_RESOLVE_LAUNCH_BLOCKERS
    )

    blockers = payload["result"]["blockers"]

    assert (
        "payment_confirmation:not_payment_confirmed"
        in blockers
    )

    assert (
        payload["boundaries"][
            "blocked_is_a_governed_result_not_an_execution_failure"
        ]
        is True
    )

    capsys.readouterr()


def test_existing_database_is_governed_blocked_not_cli_failure(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = write_payment_confirmation(
        tmp_path
    )

    files["database"].parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    files["database"].touch()

    output = tmp_path / "pilot013-existing-db.json"

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 0
    assert output.exists() is True

    payload = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert (
        payload["status"]
        == LAUNCH_MANIFEST_STATUS_BLOCKED
    )
    assert (
        payload["ready_for_human_launch_review"]
        is False
    )

    blockers = payload["result"]["blockers"]

    assert (
        "execution_readiness:not_ready"
        in blockers
    )
    assert (
        "execution_readiness:"
        "controlled_execution_not_ready"
        in blockers
    )
    assert (
        "execution_readiness:has_blockers"
        in blockers
    )

    capsys.readouterr()


def test_output_collision_fails_before_evaluation(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = write_payment_confirmation(
        tmp_path
    )

    output = tmp_path / "existing-output.json"

    original = '{"preserve": true}\n'

    output.write_text(
        original,
        encoding="utf-8",
    )

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 1

    assert (
        output.read_text(encoding="utf-8")
        == original
    )

    captured = capsys.readouterr()

    assert "already exists" in captured.err


def test_missing_payment_confirmation_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = (
        tmp_path / "missing-payment-confirmation.json"
    )

    output = tmp_path / "missing-payment-output.json"

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 1
    assert output.exists() is False
    assert files["database"].exists() is False

    captured = capsys.readouterr()

    assert (
        "payment_confirmation_json does not exist"
        in captured.err
    )


def test_malformed_payment_confirmation_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = (
        tmp_path / "malformed-payment-confirmation.json"
    )

    payment_confirmation.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    output = tmp_path / "malformed-payment-output.json"

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 1
    assert output.exists() is False
    assert files["database"].exists() is False

    captured = capsys.readouterr()

    assert (
        "PILOT-013 launch manifest evaluation failed"
        in captured.err
    )


def test_repeated_cli_evaluation_is_deterministic_and_nonmutating(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = write_payment_confirmation(
        tmp_path
    )

    tracked_inputs = (
        files["intake"],
        files["authorization"],
        files["contract_event"],
        files["request"],
        files["approvals"],
        payment_confirmation,
    )

    before = {
        path: path.read_bytes()
        for path in tracked_inputs
    }

    first_output = tmp_path / "pilot013-first.json"

    first_exit = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=first_output,
        monkeypatch=monkeypatch,
    )

    capsys.readouterr()

    second_output = tmp_path / "pilot013-second.json"

    second_exit = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=second_output,
        monkeypatch=monkeypatch,
    )

    capsys.readouterr()

    assert first_exit == 0
    assert second_exit == 0

    first_payload = json.loads(
        first_output.read_text(encoding="utf-8")
    )
    second_payload = json.loads(
        second_output.read_text(encoding="utf-8")
    )

    assert first_payload == second_payload

    for path in tracked_inputs:
        assert path.read_bytes() == before[path]

    assert files["database"].exists() is False


def test_cli_preserves_constitutional_launch_boundaries(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    payment_confirmation = write_payment_confirmation(
        tmp_path
    )

    output = tmp_path / "pilot013-boundaries.json"

    exit_code = run_cli(
        files=files,
        payment_confirmation=payment_confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    assert exit_code == 0

    payload = json.loads(
        output.read_text(encoding="utf-8")
    )

    boundaries = payload["boundaries"]

    assert boundaries[
        "pilot013_is_read_only"
    ] is True
    assert boundaries[
        "manifest_evaluation_is_not_execution"
    ] is True
    assert boundaries[
        "launch_ready_is_not_execution_authority"
    ] is True
    assert boundaries[
        "launch_ready_is_not_human_launch_approval"
    ] is True
    assert boundaries[
        "payment_confirmation_is_not_paid_work_authorization"
    ] is True
    assert boundaries[
        "paid_work_authorization_remains_independent"
    ] is True
    assert boundaries[
        "pilot012_remains_execution_readiness_authority"
    ] is True
    assert boundaries[
        "pa015_remains_execution_entry_point"
    ] is True
    assert boundaries[
        "no_commercial_event_created"
    ] is True
    assert boundaries[
        "no_paid_work_authorization_created"
    ] is True
    assert boundaries[
        "no_execution_performed"
    ] is True
    assert boundaries[
        "no_delivery_performed"
    ] is True
    assert boundaries[
        "no_customer_outcome_claimed"
    ] is True

    result_boundaries = payload["result"]["boundaries"]

    assert result_boundaries[
        "pilot013_is_read_only"
    ] is True
    assert result_boundaries[
        "human_launch_review_remains_required"
    ] is True
    assert result_boundaries[
        "pa015_remains_execution_path"
    ] is True
    assert result_boundaries[
        "launch_ready_does_not_mean_executed"
    ] is True

    assert "execution_result" not in payload
    assert "assessment_executed" not in payload
    assert "delivery_approved" not in payload
    assert "customer_outcome" not in payload

    assert files["database"].exists() is False

    capsys.readouterr()