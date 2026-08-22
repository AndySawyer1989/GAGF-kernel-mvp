import json

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    PaidAssessmentDeliveryEventError,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_recording import (
    GovernanceRealPaidAssessmentDeliveryRecordingService,
    RealPaidAssessmentDeliveryRecordingError,
)
from tests.test_approve_real_paid_assessment_for_human_delivery import (
    build_completed_operator_result,
    build_human_approval,
    run_cli as run_approval_cli,
)


SERVICE = GovernanceRealPaidAssessmentDeliveryRecordingService()


def build_approved_delivery_payload(
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

    approval_path, _ = build_human_approval(
        tmp_path,
        execution,
    )

    approved_output = (
        tmp_path / "approved-for-human-delivery.json"
    )

    exit_code = run_approval_cli(
        database=files["database"],
        operator_result=operator_output,
        human_approval=approval_path,
        output=approved_output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert approved_output.exists()

    payload = json.loads(
        approved_output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["approved_for_human_delivery"] is True

    return files, payload


def build_human_confirmation_payload(
    approved_payload,
):
    envelope = (
        approved_payload["result"]["delivery_envelope"]
    )

    return {
        "delivery_event_id": "real-delivery-event-001",
        "tenant_id": envelope["tenant_id"],
        "client_id": envelope["client_id"],
        "engagement_id": envelope["engagement_id"],
        "assessment_id": envelope["assessment_id"],
        "report_id": envelope["report_id"],
        "delivered_by": "Authorized Human Deliverer",
        "delivered_at": "2026-08-22T03:00:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "real-mail-message-001",
        "delivery_completed": True,
    }


def build_context(approved_payload):
    envelope = (
        approved_payload["result"]["delivery_envelope"]
    )

    return CommercialHierarchyContext(
        tenant_id=envelope["tenant_id"],
        client_id=envelope["client_id"],
        engagement_id=envelope["engagement_id"],
        assessment_id=envelope["assessment_id"],
    )


def test_real_pilot007_output_records_one_durable_delivery_event(
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

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    context = build_context(approved_payload)

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    before = repository.list_artifacts(
        context=context
    )

    delivery_before = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(before) == 10
    assert len(delivery_before) == 0

    result = SERVICE.record(
        database_path=files["database"],
        approved_delivery_payload=approved_payload,
        human_confirmation_payload=human_confirmation,
    )

    assert result.delivery_status == "delivered"
    assert result.delivery_event.delivery_status == "delivered"

    assert (
        result.delivery_event.delivery_event_id
        == human_confirmation["delivery_event_id"]
    )

    assert (
        result.delivery_event.delivery_envelope_hash
        == result.delivery_envelope.envelope_hash
    )

    assert (
        result.delivery_event.human_delivery_confirmation_hash
        == result.human_confirmation.confirmation_hash
    )

    after = repository.list_artifacts(
        context=context
    )

    delivery_after = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(after) == 11
    assert len(delivery_after) == 1

    assert (
        delivery_after[0].payload["delivery_event_id"]
        == result.delivery_event.delivery_event_id
    )

    assert (
        delivery_after[0].payload["delivery_event_hash"]
        == result.delivery_event.delivery_event_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True

    persistence_payload = (
        result.persistence_result.to_dict()
    )

    assert persistence_payload[
        "repository_chain_valid"
    ] is True

    assert persistence_payload["boundaries"][
        "operator_command_is_not_event_authority"
    ] is True

    assert persistence_payload["boundaries"][
        "runner_is_not_a_second_workflow_ledger"
    ] is True

    result_payload = result.to_dict()

    assert result_payload["delivery_recorded"] is True

    assert result_payload["boundaries"][
        "pa005_remains_delivery_event_authority"
    ] is True

    assert result_payload["boundaries"][
        "pa012_remains_lifecycle_persistence_authority"
    ] is True

    assert result_payload["boundaries"][
        "delivery_is_not_client_receipt"
    ] is True


def test_retry_same_delivery_does_not_append_duplicate_event(
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

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    context = build_context(approved_payload)

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    first = SERVICE.record(
        database_path=files["database"],
        approved_delivery_payload=approved_payload,
        human_confirmation_payload=human_confirmation,
    )

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second = SERVICE.record(
        database_path=files["database"],
        approved_delivery_payload=approved_payload,
        human_confirmation_payload=human_confirmation,
    )

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=DELIVERY_ARTIFACT_TYPE,
    )

    assert len(after_second) == 1

    assert (
        second.delivery_event.delivery_event_hash
        == first.delivery_event.delivery_event_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_delivery_completed_must_be_explicitly_true(
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

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    human_confirmation["delivery_completed"] = False

    with pytest.raises(
        RealPaidAssessmentDeliveryRecordingError,
        match="delivery_completed must be explicitly true",
    ):
        SERVICE.record(
            database_path=files["database"],
            approved_delivery_payload=approved_payload,
            human_confirmation_payload=human_confirmation,
        )


def test_delivery_identity_mismatch_is_rejected(
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

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    human_confirmation["assessment_id"] = "wrong-assessment"

    with pytest.raises(
        RealPaidAssessmentDeliveryRecordingError,
        match=(
            "assessment_id does not match "
            "approved delivery envelope"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            approved_delivery_payload=approved_payload,
            human_confirmation_payload=human_confirmation,
        )


def test_tampered_serialized_envelope_hash_is_rejected(
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

    approved_payload["result"]["delivery_envelope"][
        "envelope_hash"
    ] = "0" * 64

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    with pytest.raises(
        RealPaidAssessmentDeliveryRecordingError,
        match=(
            "serialized PA003 delivery envelope hash "
            "is invalid"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            approved_delivery_payload=approved_payload,
            human_confirmation_payload=human_confirmation,
        )


def test_unapproved_pilot007_payload_is_rejected(
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

    approved_payload["approved_for_human_delivery"] = False

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    with pytest.raises(
        RealPaidAssessmentDeliveryRecordingError,
        match=(
            "PILOT-007 result is not "
            "approved_for_human_delivery"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            approved_delivery_payload=approved_payload,
            human_confirmation_payload=human_confirmation,
        )


def test_invalid_delivery_timestamp_is_rejected_by_pa005_type(
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

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    human_confirmation["delivered_at"] = "not-a-timestamp"

    with pytest.raises(
        PaidAssessmentDeliveryEventError,
        match="delivered_at must be ISO-8601",
    ):
        SERVICE.record(
            database_path=files["database"],
            approved_delivery_payload=approved_payload,
            human_confirmation_payload=human_confirmation,
        )


def test_delivery_recording_does_not_create_client_receipt(
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

    human_confirmation = (
        build_human_confirmation_payload(
            approved_payload
        )
    )

    result = SERVICE.record(
        database_path=files["database"],
        approved_delivery_payload=approved_payload,
        human_confirmation_payload=human_confirmation,
    )

    serialized = json.dumps(
        result.to_dict()
    )

    assert '"client_receipt"' not in serialized
    assert '"client_acknowledgment"' not in serialized
    assert '"client_acceptance"' not in serialized
    assert '"customer_outcome"' not in serialized