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
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from scripts import record_real_paid_assessment_client_response as cli
from tests.test_governance_real_paid_assessment_client_response import (
    build_acknowledged_payload,
    build_client_response_payload,
)


def build_cli_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    acknowledged_path = tmp_path / "client-receipt-recorded.json"

    acknowledged_path.write_text(
        json.dumps(
            acknowledged_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    response_path = tmp_path / "client-response.json"

    response_path.write_text(
        json.dumps(
            response_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return {
        "files": files,
        "acknowledged_payload": acknowledged_payload,
        "acknowledged_path": acknowledged_path,
        "response_payload": response_payload,
        "response_path": response_path,
    }


def run_cli(
    *,
    database,
    acknowledged,
    response,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "record_real_paid_assessment_client_response",
            "--database",
            str(database),
            "--acknowledged-json",
            str(acknowledged),
            "--client-response-json",
            str(response),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_real_cli_records_exactly_one_durable_client_response(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    acknowledgment = (
        inputs["acknowledged_payload"]["result"][
            "client_acknowledgment"
        ]
    )

    context = CommercialHierarchyContext(
        tenant_id=acknowledgment["tenant_id"],
        client_id=acknowledgment["client_id"],
        engagement_id=acknowledgment["engagement_id"],
        assessment_id=acknowledgment["assessment_id"],
    )

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    before = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(before) == 0

    output = tmp_path / "client-response-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    after = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(after) == 1

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["client_response_recording_passed"] is True
    assert payload["client_response_recorded"] is True

    result = payload["result"]

    assert (
        result["response_status"]
        == "client_response_recorded"
    )

    assert (
        result["client_response"]["response_status"]
        == "client_response_recorded"
    )

    assert (
        after[0].payload["response_id"]
        == result["client_response"]["response_id"]
    )

    assert (
        after[0].payload["response_hash"]
        == result["client_response"]["response_hash"]
    )

    assert repository.verify_chain(
        context=context
    ) is True

    assert payload["boundaries"][
        "pa007_remains_client_response_authority"
    ] is True

    assert payload["boundaries"][
        "client_response_is_not_administrative_closeout"
    ] is True


def test_retry_same_response_does_not_duplicate_artifact(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    acknowledgment = (
        inputs["acknowledged_payload"]["result"][
            "client_acknowledgment"
        ]
    )

    context = CommercialHierarchyContext(
        tenant_id=acknowledgment["tenant_id"],
        client_id=acknowledgment["client_id"],
        engagement_id=acknowledgment["engagement_id"],
        assessment_id=acknowledgment["assessment_id"],
    )

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    first_output = tmp_path / "response-first.json"

    first_exit = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=first_output,
        monkeypatch=monkeypatch,
    )

    first_captured = capsys.readouterr()

    assert first_exit == 0
    assert first_captured.err == ""

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second_output = tmp_path / "response-second.json"

    second_exit = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=second_output,
        monkeypatch=monkeypatch,
    )

    second_captured = capsys.readouterr()

    assert second_exit == 0
    assert second_captured.err == ""

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
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
        second_payload["result"]["client_response"]["response_hash"]
        == first_payload["result"]["client_response"]["response_hash"]
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_acknowledgment_identity_mismatch_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["response_payload"]
    payload["acknowledgment_id"] = "wrong-acknowledgment"

    inputs["response_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "acknowledgment_id does not match client acknowledgment"
        in captured.err
    )
    assert not output.exists()


def test_invalid_disposition_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["response_payload"]
    payload["findings_disposition"] = "invented-status"

    inputs["response_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "findings_disposition must be one of" in captured.err
    assert not output.exists()


def test_malformed_client_response_json_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    inputs["response_path"].write_text(
        "{not valid json",
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "client_response_json is not valid UTF-8 JSON"
        in captured.err
    )
    assert not output.exists()


def test_existing_output_fails_before_governed_service_runs(
    tmp_path,
    monkeypatch,
    capsys,
):
    database = tmp_path / "assessment.sqlite3"

    acknowledged = tmp_path / "acknowledged.json"
    acknowledged.write_text(
        "{}",
        encoding="utf-8",
    )

    response = tmp_path / "response.json"
    response.write_text(
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
                "governed service must not run "
                "when output already exists"
            )

    monkeypatch.setattr(
        cli,
        "GovernanceRealPaidAssessmentClientResponseService",
        ForbiddenService,
    )

    exit_code = run_cli(
        database=database,
        acknowledged=acknowledged,
        response=response,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "output path already exists" in captured.err
    assert output.read_bytes() == original


def test_cli_output_does_not_create_closeout_or_intervention_authority(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    acknowledgment = (
        inputs["acknowledged_payload"]["result"][
            "client_acknowledgment"
        ]
    )

    context = CommercialHierarchyContext(
        tenant_id=acknowledgment["tenant_id"],
        client_id=acknowledgment["client_id"],
        engagement_id=acknowledgment["engagement_id"],
        assessment_id=acknowledgment["assessment_id"],
    )

    output = tmp_path / "client-response-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    closeout = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(closeout) == 0

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    serialized = json.dumps(payload)

    assert '"administrative_closeout"' not in serialized
    assert '"intervention_authorized"' not in serialized
    assert '"intervention_executed"' not in serialized
    assert '"remediation_success"' not in serialized
    assert '"roi_verified"' not in serialized
    assert '"customer_outcome"' not in serialized

    assert payload["boundaries"][
        "client_response_is_not_administrative_closeout"
    ] is True

    assert payload["boundaries"][
        "client_response_is_not_intervention_authorization"
    ] is True

    assert payload["boundaries"][
        "recommendation_acceptance_is_not_implementation"
    ] is True