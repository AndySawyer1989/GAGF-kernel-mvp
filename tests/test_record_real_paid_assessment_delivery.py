import json
import sys

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    DELIVERY_ARTIFACT_TYPE,
)
from scripts import record_real_paid_assessment_delivery as cli
from tests.test_governance_real_paid_assessment_delivery_recording import (
    build_approved_delivery_payload,
    build_context,
    build_human_confirmation_payload,
)


def build_cli_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, approved_payload = (
        build_approved_delivery_payload(
            tmp_path,
            monkeypatch,
            capsys,
        )
    )

    approved_path = (
        tmp_path / "approved-for-human-delivery.json"
    )

    approved_path.write_text(
        json.dumps(
            approved_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    human_confirmation_payload = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    human_confirmation_path = (
        tmp_path / "human-delivery-confirmation.json"
    )

    human_confirmation_path.write_text(
        json.dumps(
            human_confirmation_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return {
        "files": files,
        "approved_payload": approved_payload,
        "approved_path": approved_path,
        "human_confirmation_payload": (
            human_confirmation_payload
        ),
        "human_confirmation_path": (
            human_confirmation_path
        ),
    }


def run_cli(
    *,
    database,
    approved_delivery,
    human_confirmation,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "record_real_paid_assessment_delivery",
            "--database",
            str(database),
            "--approved-delivery-json",
            str(approved_delivery),
            "--human-delivery-confirmation-json",
            str(human_confirmation),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_real_cli_records_exactly_one_durable_delivery_event(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    database = inputs["files"]["database"]
    approved_payload = inputs["approved_payload"]
    context = build_context(approved_payload)

    repository = GovernanceAssessmentRepository(
        database
    )

    before = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(before) == 0

    output = tmp_path / "delivery-recorded.json"

    exit_code = run_cli(
        database=database,
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    after = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(after) == 1

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["delivery_recording_passed"] is True
    assert payload["delivery_recorded"] is True

    result = payload["result"]

    assert result["delivery_status"] == "delivered"
    assert result["delivery_recorded"] is True

    assert (
        result["delivery_event"]["delivery_status"]
        == "delivered"
    )

    assert (
        after[0].payload["delivery_event_id"]
        == result["delivery_event"]["delivery_event_id"]
    )

    assert repository.verify_chain(
        context=context
    ) is True

    assert payload["boundaries"][
        "human_delivery_confirmation_must_preexist_command"
    ] is True

    assert payload["boundaries"][
        "command_does_not_infer_delivery_from_approval"
    ] is True

    assert payload["boundaries"][
        "pa005_remains_delivery_event_authority"
    ] is True

    assert payload["boundaries"][
        "pa012_remains_lifecycle_persistence_authority"
    ] is True


def test_retry_same_delivery_does_not_duplicate_durable_event(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    database = inputs["files"]["database"]
    approved_payload = inputs["approved_payload"]
    context = build_context(approved_payload)

    repository = GovernanceAssessmentRepository(
        database
    )

    first_output = tmp_path / "delivery-first.json"

    first_exit = run_cli(
        database=database,
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
        output=first_output,
        monkeypatch=monkeypatch,
    )

    first_captured = capsys.readouterr()

    assert first_exit == 0
    assert first_captured.err == ""

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second_output = tmp_path / "delivery-second.json"

    second_exit = run_cli(
        database=database,
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
        output=second_output,
        monkeypatch=monkeypatch,
    )

    second_captured = capsys.readouterr()

    assert second_exit == 0
    assert second_captured.err == ""

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
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
        second_payload["result"]["delivery_event"][
            "delivery_event_hash"
        ]
        == first_payload["result"]["delivery_event"][
            "delivery_event_hash"
        ]
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_false_delivery_completed_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["human_confirmation_payload"]
    payload["delivery_completed"] = False

    inputs["human_confirmation_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "delivery_completed must be explicitly true"
        in captured.err
    )
    assert not output.exists()


def test_delivery_identity_mismatch_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["human_confirmation_payload"]
    payload["report_id"] = "wrong-report-id"

    inputs["human_confirmation_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "report_id does not match approved delivery envelope"
        in captured.err
    )
    assert not output.exists()


def test_malformed_human_confirmation_json_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    inputs["human_confirmation_path"].write_text(
        "{not valid json",
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "human_delivery_confirmation_json "
        "is not valid UTF-8 JSON"
        in captured.err
    )
    assert not output.exists()


def test_existing_output_fails_before_governed_service_runs(
    tmp_path,
    monkeypatch,
    capsys,
):
    database = tmp_path / "assessment.sqlite3"

    approved = tmp_path / "approved.json"
    approved.write_text(
        "{}",
        encoding="utf-8",
    )

    confirmation = tmp_path / "confirmation.json"
    confirmation.write_text(
        "{}",
        encoding="utf-8",
    )

    output = tmp_path / "existing-output.json"
    original = b"preserve-existing-output"
    output.write_bytes(original)

    class ForbiddenService:
        def __init__(self):
            raise AssertionError(
                "governed service must not run "
                "when output already exists"
            )

    monkeypatch.setattr(
        cli,
        "GovernanceRealPaidAssessmentDeliveryRecordingService",
        ForbiddenService,
    )

    exit_code = run_cli(
        database=database,
        approved_delivery=approved,
        human_confirmation=confirmation,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "output path already exists" in captured.err
    assert output.read_bytes() == original


def test_cli_output_does_not_create_downstream_client_authority(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    output = tmp_path / "delivery-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        approved_delivery=inputs["approved_path"],
        human_confirmation=(
            inputs["human_confirmation_path"]
        ),
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

    assert '"client_receipt"' not in serialized
    assert '"client_acknowledgment"' not in serialized
    assert '"client_acceptance"' not in serialized
    assert '"customer_outcome"' not in serialized

    assert payload["boundaries"][
        "delivery_is_not_client_receipt"
    ] is True

    assert payload["boundaries"][
        "delivery_is_not_client_acknowledgment"
    ] is True

    assert payload["boundaries"][
        "delivery_is_not_client_acceptance"
    ] is True

    assert payload["boundaries"][
        "delivery_is_not_customer_outcome"
    ] is True