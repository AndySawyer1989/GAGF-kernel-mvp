import json
import sys

from scripts import approve_real_paid_assessment_for_human_delivery as cli
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

    operator_payload = json.loads(
        operator_output.read_text(
            encoding="utf-8"
        )
    )

    execution = operator_payload["result"]["execution_result"]

    return files, operator_output, execution


def build_human_approval(
    tmp_path,
    execution,
):
    approval_path = tmp_path / "human-approval.json"

    payload = {
        "approval_id": "real-delivery-approval-001",
        "tenant_id": execution["tenant_id"],
        "client_id": execution["client_id"],
        "engagement_id": execution["engagement_id"],
        "assessment_id": execution["assessment_id"],
        "report_id": execution["report_id"],
        "approved_by": "Authorized Human Reviewer",
        "approved_at": "2026-08-22T02:30:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }

    approval_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return approval_path, payload


def run_cli(
    *,
    database,
    operator_result,
    human_approval,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "approve_real_paid_assessment_for_human_delivery",
            "--database",
            str(database),
            "--operator-result-json",
            str(operator_result),
            "--human-approval-json",
            str(human_approval),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_real_operator_result_and_human_approval_produce_pa003_envelope(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, operator_output, execution = (
        build_completed_operator_result(
            tmp_path,
            monkeypatch,
            capsys,
        )
    )

    approval_path, approval_payload = build_human_approval(
        tmp_path,
        execution,
    )

    output = tmp_path / "approved-for-human-delivery.json"

    database_before = files["database"].read_bytes()

    exit_code = run_cli(
        database=files["database"],
        operator_result=operator_output,
        human_approval=approval_path,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    database_after = files["database"].read_bytes()

    assert database_after == database_before

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["operator_handoff_passed"] is True
    assert payload["approved_for_human_delivery"] is True

    result = payload["result"]

    assert result["handoff_status"] == "approved_for_human_delivery"

    assert (
        result["delivery_envelope"]["delivery_status"]
        == "approved_for_human_delivery"
    )

    assert (
        result["delivery_approval"]["approved_by"]
        == approval_payload["approved_by"]
    )

    assert (
        result["delivery_envelope"]["delivery_approval_hash"]
        == result["delivery_approval"]["approval_hash"]
    )

    assert payload["boundaries"][
        "human_approval_must_preexist_command"
    ] is True

    assert payload["boundaries"][
        "command_does_not_manufacture_human_approval"
    ] is True

    assert payload["boundaries"][
        "pa003_remains_delivery_envelope_authority"
    ] is True

    assert payload["boundaries"][
        "command_does_not_create_delivery_event"
    ] is True

    serialized = json.dumps(payload)

    assert '"delivery_event"' not in serialized
    assert '"client_receipt"' not in serialized
    assert '"client_acceptance"' not in serialized


def test_false_human_approval_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, operator_output, execution = (
        build_completed_operator_result(
            tmp_path,
            monkeypatch,
            capsys,
        )
    )

    approval_path, approval_payload = build_human_approval(
        tmp_path,
        execution,
    )

    approval_payload["delivery_approved"] = False

    approval_path.write_text(
        json.dumps(approval_payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=files["database"],
        operator_result=operator_output,
        human_approval=approval_path,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "delivery_approved must be explicitly true"
        in captured.err
    )
    assert not output.exists()


def test_human_approval_identity_mismatch_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, operator_output, execution = (
        build_completed_operator_result(
            tmp_path,
            monkeypatch,
            capsys,
        )
    )

    approval_path, approval_payload = build_human_approval(
        tmp_path,
        execution,
    )

    approval_payload["report_id"] = "wrong-report"

    approval_path.write_text(
        json.dumps(approval_payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=files["database"],
        operator_result=operator_output,
        human_approval=approval_path,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "report_id does not match verified readiness"
        in captured.err
    )
    assert not output.exists()


def test_malformed_human_approval_json_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, operator_output, _ = (
        build_completed_operator_result(
            tmp_path,
            monkeypatch,
            capsys,
        )
    )

    approval_path = tmp_path / "malformed-approval.json"

    approval_path.write_text(
        "{not valid json",
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=files["database"],
        operator_result=operator_output,
        human_approval=approval_path,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "human_approval_json is not valid UTF-8 JSON" in captured.err
    assert not output.exists()


def test_existing_output_fails_before_governed_services_run(
    tmp_path,
    monkeypatch,
    capsys,
):
    operator_result = tmp_path / "operator.json"
    operator_result.write_text(
        "{}",
        encoding="utf-8",
    )

    human_approval = tmp_path / "approval.json"
    human_approval.write_text(
        "{}",
        encoding="utf-8",
    )

    database = tmp_path / "assessment.sqlite3"

    output = tmp_path / "existing.json"
    original = b"preserve-this-output"
    output.write_bytes(original)

    class ForbiddenReadinessService:
        def __init__(self):
            raise AssertionError(
                "readiness service must not run when output exists"
            )

    class ForbiddenHandoffService:
        def __init__(self):
            raise AssertionError(
                "handoff service must not run when output exists"
            )

    monkeypatch.setattr(
        cli,
        "GovernanceRealPaidAssessmentDeliveryReadinessService",
        ForbiddenReadinessService,
    )

    monkeypatch.setattr(
        cli,
        "GovernanceRealPaidAssessmentDeliveryApprovalHandoffService",
        ForbiddenHandoffService,
    )

    exit_code = run_cli(
        database=database,
        operator_result=operator_result,
        human_approval=human_approval,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "output path already exists" in captured.err
    assert output.read_bytes() == original


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

    human_approval = tmp_path / "approval.json"

    human_approval.write_text(
        json.dumps(
            {
                "approval_id": "approval-001",
            }
        ),
        encoding="utf-8",
    )

    database = tmp_path / "assessment.sqlite3"
    database.write_bytes(b"placeholder")

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=database,
        operator_result=operator_result,
        human_approval=human_approval,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "operator result is not successful" in captured.err
    assert not output.exists()