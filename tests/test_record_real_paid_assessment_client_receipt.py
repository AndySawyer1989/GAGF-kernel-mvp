import json
import sys

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
)
from scripts import record_real_paid_assessment_client_receipt as cli
from tests.test_governance_real_paid_assessment_client_receipt import (
    build_client_receipt_payload,
    build_delivered_payload,
)


def build_cli_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    delivered_path = tmp_path / "delivered.json"

    delivered_path.write_text(
        json.dumps(
            delivered_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    receipt_path = tmp_path / "client-receipt.json"

    receipt_path.write_text(
        json.dumps(
            receipt_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return {
        "files": files,
        "delivered_payload": delivered_payload,
        "delivered_path": delivered_path,
        "receipt_payload": receipt_payload,
        "receipt_path": receipt_path,
    }


def run_cli(
    *,
    database,
    delivered,
    receipt,
    output,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "record_real_paid_assessment_client_receipt",
            "--database",
            str(database),
            "--delivered-json",
            str(delivered),
            "--client-receipt-json",
            str(receipt),
            "--output-json",
            str(output),
        ],
    )

    return cli.main()


def test_real_cli_records_exactly_one_durable_client_receipt(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    event = inputs["delivered_payload"]["result"]["delivery_event"]

    context = CommercialHierarchyContext(
        tenant_id=event["tenant_id"],
        client_id=event["client_id"],
        engagement_id=event["engagement_id"],
        assessment_id=event["assessment_id"],
    )

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    before = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(before) == 0

    output = tmp_path / "client-receipt-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    after = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(after) == 1

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["client_receipt_recording_passed"] is True
    assert payload["client_receipt_acknowledged"] is True

    result = payload["result"]

    assert (
        result["acknowledgment_status"]
        == "client_receipt_acknowledged"
    )

    assert (
        result["client_acknowledgment"]["acknowledgment_status"]
        == "client_receipt_acknowledged"
    )

    assert (
        after[0].payload["acknowledgment_id"]
        == result["client_acknowledgment"]["acknowledgment_id"]
    )

    assert repository.verify_chain(
        context=context
    ) is True

    assert payload["boundaries"][
        "pa006_remains_client_acknowledgment_authority"
    ] is True

    assert payload["boundaries"][
        "client_receipt_is_not_client_response"
    ] is True


def test_retry_same_receipt_does_not_duplicate_artifact(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    event = inputs["delivered_payload"]["result"]["delivery_event"]

    context = CommercialHierarchyContext(
        tenant_id=event["tenant_id"],
        client_id=event["client_id"],
        engagement_id=event["engagement_id"],
        assessment_id=event["assessment_id"],
    )

    repository = GovernanceAssessmentRepository(
        inputs["files"]["database"]
    )

    first_output = tmp_path / "receipt-first.json"

    first_exit = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
        output=first_output,
        monkeypatch=monkeypatch,
    )

    first_captured = capsys.readouterr()

    assert first_exit == 0
    assert first_captured.err == ""

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second_output = tmp_path / "receipt-second.json"

    second_exit = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
        output=second_output,
        monkeypatch=monkeypatch,
    )

    second_captured = capsys.readouterr()

    assert second_exit == 0
    assert second_captured.err == ""

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
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
        second_payload["result"]["client_acknowledgment"][
            "acknowledgment_hash"
        ]
        == first_payload["result"]["client_acknowledgment"][
            "acknowledgment_hash"
        ]
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_false_client_receipt_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["receipt_payload"]
    payload["client_acknowledged_receipt"] = False

    inputs["receipt_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "client_acknowledged_receipt must be explicitly true"
        in captured.err
    )
    assert not output.exists()


def test_receipt_identity_mismatch_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    payload = inputs["receipt_payload"]
    payload["delivery_event_id"] = "wrong-delivery-event"

    inputs["receipt_path"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "delivery_event_id does not match delivered event" in captured.err
    assert not output.exists()


def test_malformed_receipt_json_fails_closed_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    inputs["receipt_path"].write_text(
        "{not valid json",
        encoding="utf-8",
    )

    output = tmp_path / "should-not-exist.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "client_receipt_json is not valid UTF-8 JSON"
        in captured.err
    )
    assert not output.exists()


def test_existing_output_fails_before_governed_service_runs(
    tmp_path,
    monkeypatch,
    capsys,
):
    database = tmp_path / "assessment.sqlite3"

    delivered = tmp_path / "delivered.json"
    delivered.write_text(
        "{}",
        encoding="utf-8",
    )

    receipt = tmp_path / "receipt.json"
    receipt.write_text(
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
        "GovernanceRealPaidAssessmentClientReceiptService",
        ForbiddenService,
    )

    exit_code = run_cli(
        database=database,
        delivered=delivered,
        receipt=receipt,
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "output path already exists" in captured.err
    assert output.read_bytes() == original


def test_cli_output_does_not_create_downstream_response_authority(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    output = tmp_path / "client-receipt-recorded.json"

    exit_code = run_cli(
        database=inputs["files"]["database"],
        delivered=inputs["delivered_path"],
        receipt=inputs["receipt_path"],
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

    assert '"client_response"' not in serialized
    assert '"findings_accepted"' not in serialized
    assert '"recommendations_accepted"' not in serialized
    assert '"client_acceptance"' not in serialized
    assert '"intervention_authorized"' not in serialized
    assert '"customer_outcome"' not in serialized

    assert payload["boundaries"][
        "client_receipt_is_not_client_response"
    ] is True

    assert payload["boundaries"][
        "client_receipt_is_not_findings_acceptance"
    ] is True

    assert payload["boundaries"][
        "client_receipt_is_not_recommendation_acceptance"
    ] is True

    assert payload["boundaries"][
        "client_receipt_is_not_customer_outcome"
    ] is True