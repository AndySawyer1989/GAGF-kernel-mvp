import json

import pytest

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    PaidAssessmentClientAcknowledgmentError,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_real_paid_assessment_client_receipt import (
    GovernanceRealPaidAssessmentClientReceiptService,
    RealPaidAssessmentClientReceiptError,
)
from tests.test_record_real_paid_assessment_delivery import (
    build_cli_inputs as build_delivery_cli_inputs,
    run_cli as run_delivery_cli,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


SERVICE = GovernanceRealPaidAssessmentClientReceiptService()


def build_delivered_payload(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_delivery_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    output = tmp_path / "delivery-recorded.json"

    exit_code = run_delivery_cli(
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
    assert output.exists()

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["delivery_recording_passed"] is True
    assert payload["delivery_recorded"] is True

    return inputs["files"], payload


def build_client_receipt_payload(
    delivered_payload,
):
    event = delivered_payload["result"]["delivery_event"]

    return {
        "acknowledgment_id": "real-client-ack-001",
        "tenant_id": event["tenant_id"],
        "client_id": event["client_id"],
        "engagement_id": event["engagement_id"],
        "assessment_id": event["assessment_id"],
        "report_id": event["report_id"],
        "delivery_event_id": event["delivery_event_id"],
        "delivery_event_hash": event["delivery_event_hash"],
        "acknowledged_by": "Authorized Client Representative",
        "acknowledged_at": "2026-08-22T05:30:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "client-mail-reply-001",
        "client_acknowledged_receipt": True,
    }


def test_real_delivered_state_records_one_durable_client_receipt(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    event = delivered_payload["result"]["delivery_event"]

    context = CommercialHierarchyContext(
        tenant_id=event["tenant_id"],
        client_id=event["client_id"],
        engagement_id=event["engagement_id"],
        assessment_id=event["assessment_id"],
    )


    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    before = repository.list_artifacts(
        context=context
    )

    acknowledgments_before = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(before) == 11
    assert len(acknowledgments_before) == 0

    result = SERVICE.record(
        database_path=files["database"],
        delivered_payload=delivered_payload,
        receipt_payload=receipt_payload,
    )

    assert (
        result.acknowledgment_status
        == "client_receipt_acknowledged"
    )

    assert (
        result.client_acknowledgment.acknowledgment_status
        == "client_receipt_acknowledged"
    )

    assert (
        result.client_acknowledgment.delivery_event_id
        == result.delivery_event.delivery_event_id
    )

    assert (
        result.client_acknowledgment.delivery_event_hash
        == result.delivery_event.delivery_event_hash
    )

    assert (
        result.client_acknowledgment.acknowledgment_evidence_hash
        == result.receipt_evidence.acknowledgment_evidence_hash
    )

    after = repository.list_artifacts(
        context=context
    )

    acknowledgments_after = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(after) == 12
    assert len(acknowledgments_after) == 1

    assert (
        acknowledgments_after[0].payload["acknowledgment_id"]
        == result.client_acknowledgment.acknowledgment_id
    )

    assert (
        acknowledgments_after[0].payload["acknowledgment_hash"]
        == result.client_acknowledgment.acknowledgment_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True

    payload = result.to_dict()

    assert payload["client_receipt_acknowledged"] is True

    assert payload["boundaries"][
        "pa006_remains_client_acknowledgment_authority"
    ] is True

    assert payload["boundaries"][
        "pa012_remains_lifecycle_persistence_authority"
    ] is True

    assert payload["boundaries"][
        "client_receipt_is_not_client_response"
    ] is True


def test_exact_client_receipt_retry_does_not_duplicate_artifact(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    event = delivered_payload["result"]["delivery_event"]


    context = CommercialHierarchyContext(
        tenant_id=event["tenant_id"],
        client_id=event["client_id"],
        engagement_id=event["engagement_id"],
        assessment_id=event["assessment_id"],
    )

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    first = SERVICE.record(
        database_path=files["database"],
        delivered_payload=delivered_payload,
        receipt_payload=receipt_payload,
    )

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second = SERVICE.record(
        database_path=files["database"],
        delivered_payload=delivered_payload,
        receipt_payload=receipt_payload,
    )

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
    )

    assert len(after_second) == 1

    assert (
        second.client_acknowledgment.acknowledgment_hash
        == first.client_acknowledgment.acknowledgment_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_receipt_must_be_explicitly_acknowledged(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    receipt_payload["client_acknowledged_receipt"] = False

    with pytest.raises(
        RealPaidAssessmentClientReceiptError,
        match=(
            "client_acknowledged_receipt must be "
            "explicitly true"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            delivered_payload=delivered_payload,
            receipt_payload=receipt_payload,
        )


def test_receipt_delivery_identity_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    receipt_payload["delivery_event_id"] = "wrong-event"

    with pytest.raises(
        RealPaidAssessmentClientReceiptError,
        match=(
            "delivery_event_id does not match delivered event"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            delivered_payload=delivered_payload,
            receipt_payload=receipt_payload,
        )


def test_tampered_serialized_delivery_event_hash_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    delivered_payload["result"]["delivery_event"][
        "delivery_event_hash"
    ] = "0" * 64

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    with pytest.raises(
        RealPaidAssessmentClientReceiptError,
        match="serialized PA005 delivery event hash is invalid",
    ):
        SERVICE.record(
            database_path=files["database"],
            delivered_payload=delivered_payload,
            receipt_payload=receipt_payload,
        )


def test_unsuccessful_pilot008_payload_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    delivered_payload["delivery_recording_passed"] = False

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    with pytest.raises(
        RealPaidAssessmentClientReceiptError,
        match="PILOT-008 delivery recording is not successful",
    ):
        SERVICE.record(
            database_path=files["database"],
            delivered_payload=delivered_payload,
            receipt_payload=receipt_payload,
        )


def test_invalid_acknowledgment_timestamp_is_rejected_by_pa006_type(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    receipt_payload["acknowledged_at"] = "not-a-timestamp"

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="acknowledged_at must be ISO-8601",
    ):
        SERVICE.record(
            database_path=files["database"],
            delivered_payload=delivered_payload,
            receipt_payload=receipt_payload,
        )


def test_client_receipt_does_not_create_response_or_acceptance(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, delivered_payload = build_delivered_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    receipt_payload = build_client_receipt_payload(
        delivered_payload
    )

    result = SERVICE.record(
        database_path=files["database"],
        delivered_payload=delivered_payload,
        receipt_payload=receipt_payload,
    )

    serialized = json.dumps(
        result.to_dict()
    )

    assert '"client_response"' not in serialized
    assert '"findings_accepted"' not in serialized
    assert '"recommendations_accepted"' not in serialized
    assert '"client_acceptance"' not in serialized
    assert '"intervention_authorized"' not in serialized
    assert '"customer_outcome"' not in serialized