import inspect
import json
import sys

from scripts import verify_real_paid_assessment_delivery_readiness as cli
from scripts.run_real_paid_assessment import main as run_operator_main
from tests.test_run_real_paid_assessment import build_operator_files


def build_completed_operator_result(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    operator_output = tmp_path / "pa015-result.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_real_paid_assessment",
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
            str(operator_output),
        ],
    )

    exit_code = run_operator_main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert operator_output.exists()

    return files, operator_output


def run_readiness_cli(
    *,
    database,
    operator_result,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_real_paid_assessment_delivery_readiness",
            "--database",
            str(database),
            "--operator-result-json",
            str(operator_result),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_completed_pa015_result_produces_delivery_readiness_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, operator_output = build_completed_operator_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    readiness_output = tmp_path / "delivery-readiness.json"

    exit_code = run_readiness_cli(
        database=files["database"],
        operator_result=operator_output,
        output=readiness_output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert readiness_output.exists()

    payload = json.loads(
        readiness_output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["post_execution_verified"] is True
    assert (
        payload["ready_for_delivery_approval_review"]
        is True
    )

    result = payload["result"]

    assert (
        result["delivery_readiness_status"]
        == "ready_for_delivery_approval_review"
    )
    assert result["artifact_count"] == 10
    assert result["repository_chain_valid"] is True

    assert (
        result["execution_result"]["hierarchy_key"]
        == result["report_package"]["hierarchy_key"]
    )

    assert (
        result["execution_result"]["report_id"]
        == result["report_package"]["report_id"]
    )

    boundaries = payload["boundaries"]

    assert boundaries[
        "verification_command_is_not_paid_work_authorization"
    ] is True
    assert boundaries[
        "verification_command_is_not_execution_authority"
    ] is True
    assert boundaries[
        "verification_command_is_not_recovery_authority"
    ] is True
    assert boundaries[
        "verification_command_is_not_delivery_approval"
    ] is True
    assert boundaries[
        "verification_command_is_not_pa003_delivery_envelope"
    ] is True
    assert boundaries[
        "verification_command_does_not_deliver_report"
    ] is True
    assert boundaries[
        "pa003_remains_delivery_envelope_authority"
    ] is True


def test_existing_output_fails_before_readiness_verification(
    tmp_path,
    monkeypatch,
    capsys,
):
    operator_result = tmp_path / "operator-result.json"
    operator_result.write_text(
        json.dumps(
            {
                "operator_run_passed": True,
            }
        ),
        encoding="utf-8",
    )

    database = tmp_path / "assessment.sqlite3"

    output = tmp_path / "existing-output.json"
    original_bytes = b"preserve-me-exactly"
    output.write_bytes(original_bytes)

    class ForbiddenService:
        def __init__(self):
            raise AssertionError(
                "readiness service must not be constructed "
                "when output already exists"
            )

    monkeypatch.setattr(
        cli,
        "GovernanceRealPaidAssessmentDeliveryReadinessService",
        ForbiddenService,
    )

    exit_code = run_readiness_cli(
        database=database,
        operator_result=operator_result,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "output path already exists" in captured.err
    assert output.read_bytes() == original_bytes


def test_malformed_operator_json_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    operator_result = tmp_path / "malformed.json"
    operator_result.write_text(
        "{this is not valid json",
        encoding="utf-8",
    )

    database = tmp_path / "assessment.sqlite3"
    output = tmp_path / "readiness.json"

    exit_code = run_readiness_cli(
        database=database,
        operator_result=operator_result,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "not valid UTF-8 JSON" in captured.err
    assert not output.exists()


def test_unsuccessful_pa015_result_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    operator_result = tmp_path / "failed-pa015.json"
    operator_result.write_text(
        json.dumps(
            {
                "operator_run_passed": False,
                "result": {},
            }
        ),
        encoding="utf-8",
    )

    database = tmp_path / "assessment.sqlite3"
    database.write_bytes(b"placeholder")

    output = tmp_path / "readiness.json"

    exit_code = run_readiness_cli(
        database=database,
        operator_result=operator_result,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "operator result is not successful" in captured.err
    assert not output.exists()


def test_cli_does_not_import_or_invoke_pa003_delivery_envelope():
    source = inspect.getsource(cli)

    assert (
        "governance_paid_assessment_delivery_envelope"
        not in source
    )
    assert "GovernancePaidAssessmentDeliveryEnvelopeService" not in source
    assert "PaidAssessmentDeliveryApproval" not in source
    assert "build_envelope(" not in source