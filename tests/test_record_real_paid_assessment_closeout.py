import json
import sys

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
)
from scripts import record_real_paid_assessment_closeout as cli
from tests.test_governance_real_paid_assessment_closeout import (
    build_client_response_result,
    build_closeout_payload,
)


def build_cli_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    client_response_path = (
        tmp_path / "client-response-recorded.json"
    )

    client_response_path.write_text(
        json.dumps(
            client_response_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    closeout_path = tmp_path / "closeout-confirmation.json"

    closeout_path.write_text(
        json.dumps(
            closeout_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return {
        "files": files,
        "client_response_payload": client_response_payload,
        "client_response_path": client_response_path,
        "closeout_payload": closeout_payload,
        "closeout_path": closeout_path,
    }


def run_cli(
    *,
    database,
    client_response,
    closeout,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "record_real_paid_assessment_closeout",
            "--database",
            str(database),
            "--client-response-json",
            str(client_response),
            "--closeout-json",
            str(closeout),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def build_context(
    client_response_payload,
):
    response = (
        client_response_payload["result"]["client_response"]
    )

    return CommercialHierarchyContext(
        tenant_id=response["tenant_id"],
        client_id=response["client_id"],
        engagement_id=response["engagement_id"],
        assessment_id=response["assessment_id"],
    )


def test_real_cli_records_exactly_one_administrative_closeout(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    context = build_context(
        inputs["client_response_payload"]
    )

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    before = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(before) == 0

    output = tmp_path / "assessment-closeout-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    after = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(after) == 1

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload["administrative_closeout_recording_passed"]
        is True
    )

    assert payload["assessment_closed"] is True

    assert (
        payload["result"]["closeout_status"]
        == "assessment_closed"
    )

    assert (
        payload["result"]["closeout_artifact_id"]
        == after[0].artifact_id
    )

    assert (
        payload["result"]["closeout_artifact_hash"]
        == after[0].artifact_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_exact_cli_retry_does_not_duplicate_closeout(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    context = build_context(
        inputs["client_response_payload"]
    )

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    first_output = tmp_path / "closeout-first.json"

    first_exit = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=first_output,
        monkeypatch=monkeypatch,
    )

    first_captured = capsys.readouterr()

    assert first_exit == 0
    assert first_captured.err == ""

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second_output = tmp_path / "closeout-second.json"

    second_exit = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=second_output,
        monkeypatch=monkeypatch,
    )

    second_captured = capsys.readouterr()

    assert second_exit == 0
    assert second_captured.err == ""

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(after_second) == 1

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

    assert (
        second_payload["result"]["closeout_artifact_id"]
        == first_payload["result"]["closeout_artifact_id"]
    )

    assert (
        second_payload["result"]["closeout_artifact_hash"]
        == first_payload["result"]["closeout_artifact_hash"]
    )


def test_closeout_identity_mismatch_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["closeout_payload"]
    payload["assessment_id"] = "wrong-assessment"

    inputs["closeout_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    assert (
        "assessment_id does not match PILOT-010 "
        "client-response lineage"
        in captured.err
    )

    assert not output.exists()


def test_explicit_confirmation_false_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["closeout_payload"]

    payload[
        "administrative_closeout_confirmed"
    ] = False

    inputs["closeout_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    assert (
        "administrative_closeout_confirmed must be true"
        in captured.err
    )

    assert not output.exists()


def test_malformed_closeout_json_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    inputs["closeout_path"].write_text(
        "{not valid json",
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    assert (
        "closeout_json is not valid UTF-8 JSON"
        in captured.err
    )

    assert not output.exists()


def test_existing_output_fails_before_closeout_service_runs(
    tmp_path,
    monkeypatch,
    capsys,
):
    database = tmp_path / "assessment.sqlite3"

    client_response = tmp_path / "client-response.json"

    client_response.write_text(
        "{}",
        encoding="utf-8",
    )

    closeout = tmp_path / "closeout.json"

    closeout.write_text(
        "{}",
        encoding="utf-8",
    )

    output = tmp_path / "existing-output.json"

    original = b"preserve-existing-output"

    output.write_bytes(
        original
    )

    class ForbiddenService:
        def __init__(self):
            raise AssertionError(
                "closeout service must not run "
                "when output already exists"
            )

    monkeypatch.setattr(
        cli,
        "GovernanceRealPaidAssessmentCloseoutService",
        ForbiddenService,
    )

    exit_code = run_cli(
        database=database,
        client_response=client_response,
        closeout=closeout,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "output path already exists" in captured.err
    assert output.read_bytes() == original


def test_cli_closeout_does_not_create_intervention_or_outcome_authority(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    output = tmp_path / "assessment-closeout-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        client_response=inputs["client_response_path"],
        closeout=inputs["closeout_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    serialized = json.dumps(payload)

    assert '"intervention_authorized"' not in serialized
    assert '"intervention_executed"' not in serialized
    assert '"recommendation_implemented"' not in serialized
    assert '"remediation_success"' not in serialized
    assert '"roi_verified"' not in serialized
    assert '"customer_outcome_verified"' not in serialized

    boundaries = payload["boundaries"]

    assert boundaries[
        "closeout_is_not_recommendation_implementation"
    ] is True

    assert boundaries[
        "closeout_is_not_intervention_authorization"
    ] is True

    assert boundaries[
        "closeout_is_not_execution"
    ] is True

    assert boundaries[
        "closeout_is_not_roi_verification"
    ] is True

    assert boundaries[
        "closeout_is_not_remediation_success"
    ] is True

    assert boundaries[
        "closeout_is_not_customer_outcome"
    ] is True