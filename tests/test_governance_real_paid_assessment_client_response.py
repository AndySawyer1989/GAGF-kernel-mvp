import json

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    PaidAssessmentClientResponseError,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_real_paid_assessment_client_response import (
    GovernanceRealPaidAssessmentClientResponseService,
    RealPaidAssessmentClientResponseError,
)
from tests.test_record_real_paid_assessment_client_receipt import (
    build_cli_inputs as build_receipt_cli_inputs,
    run_cli as run_receipt_cli,
)


SERVICE = GovernanceRealPaidAssessmentClientResponseService()


def build_acknowledged_payload(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_receipt_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    output = tmp_path / "client-receipt-recorded.json"

    exit_code = run_receipt_cli(
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

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["client_receipt_recording_passed"] is True
    assert payload["client_receipt_acknowledged"] is True

    return inputs["files"], payload


def build_client_response_payload(
    acknowledged_payload,
):
    acknowledgment = (
        acknowledged_payload["result"]["client_acknowledgment"]
    )

    return {
        "response_id": "real-client-response-001",
        "tenant_id": acknowledgment["tenant_id"],
        "client_id": acknowledgment["client_id"],
        "engagement_id": acknowledgment["engagement_id"],
        "assessment_id": acknowledgment["assessment_id"],
        "report_id": acknowledgment["report_id"],
        "acknowledgment_id": acknowledgment["acknowledgment_id"],
        "acknowledgment_hash": acknowledgment["acknowledgment_hash"],
        "responded_by": "Authorized Client Representative",
        "responded_at": "2026-08-23T10:30:00+00:00",
        "response_method": "email_reply",
        "response_reference": "client-response-mail-001",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
        "response_note": (
            "Client accepts recommendations for planning review."
        ),
    }


def build_context(
    acknowledged_payload,
):
    acknowledgment = (
        acknowledged_payload["result"]["client_acknowledgment"]
    )

    return CommercialHierarchyContext(
        tenant_id=acknowledgment["tenant_id"],
        client_id=acknowledgment["client_id"],
        engagement_id=acknowledgment["engagement_id"],
        assessment_id=acknowledgment["assessment_id"],
    )


def test_real_client_receipt_records_one_durable_client_response(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    context = build_context(
        acknowledged_payload
    )

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    before = repository.list_artifacts(
        context=context
    )

    responses_before = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(before) == 12
    assert len(responses_before) == 0

    result = SERVICE.record(
        database_path=files["database"],
        acknowledged_payload=acknowledged_payload,
        response_payload=response_payload,
    )

    assert result.response_status == "client_response_recorded"

    assert (
        result.client_response.response_status
        == "client_response_recorded"
    )

    assert (
        result.client_response.acknowledgment_id
        == result.client_acknowledgment.acknowledgment_id
    )

    assert (
        result.client_response.acknowledgment_hash
        == result.client_acknowledgment.acknowledgment_hash
    )

    assert (
        result.client_response.response_evidence_hash
        == result.response_evidence.response_evidence_hash
    )

    assert (
        result.client_response.findings_disposition
        == "acknowledged"
    )

    assert (
        result.client_response.recommendations_disposition
        == "accepted"
    )

    after = repository.list_artifacts(
        context=context
    )

    responses_after = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(after) == 13
    assert len(responses_after) == 1

    assert (
        responses_after[0].payload["response_id"]
        == result.client_response.response_id
    )

    assert (
        responses_after[0].payload["response_hash"]
        == result.client_response.response_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True

    payload = result.to_dict()

    assert payload["client_response_recorded"] is True

    assert payload["boundaries"][
        "pa007_remains_client_response_authority"
    ] is True

    assert payload["boundaries"][
        "recommendation_acceptance_is_not_implementation"
    ] is True

    assert payload["boundaries"][
        "response_is_not_intervention_authorization"
    ] is True


def test_exact_client_response_retry_does_not_duplicate_artifact(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    context = build_context(
        acknowledged_payload
    )

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    first = SERVICE.record(
        database_path=files["database"],
        acknowledged_payload=acknowledged_payload,
        response_payload=response_payload,
    )

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second = SERVICE.record(
        database_path=files["database"],
        acknowledged_payload=acknowledged_payload,
        response_payload=response_payload,
    )

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert len(after_second) == 1

    assert (
        second.client_response.response_hash
        == first.client_response.response_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_response_acknowledgment_identity_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    response_payload["acknowledgment_id"] = "wrong-acknowledgment"

    with pytest.raises(
        RealPaidAssessmentClientResponseError,
        match=(
            "acknowledgment_id does not match "
            "client acknowledgment"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            acknowledged_payload=acknowledged_payload,
            response_payload=response_payload,
        )


def test_tampered_serialized_acknowledgment_hash_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    acknowledged_payload["result"]["client_acknowledgment"][
        "acknowledgment_hash"
    ] = "0" * 64

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    with pytest.raises(
        RealPaidAssessmentClientResponseError,
        match=(
            "serialized PA006 client acknowledgment hash "
            "is invalid"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            acknowledged_payload=acknowledged_payload,
            response_payload=response_payload,
        )


def test_unsuccessful_pilot009_payload_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    acknowledged_payload[
        "client_receipt_recording_passed"
    ] = False

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    with pytest.raises(
        RealPaidAssessmentClientResponseError,
        match=(
            "PILOT-009 client receipt recording "
            "is not successful"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            acknowledged_payload=acknowledged_payload,
            response_payload=response_payload,
        )


def test_invalid_findings_disposition_is_rejected_by_pa007_type(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    response_payload["findings_disposition"] = "invented-status"

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="findings_disposition must be one of",
    ):
        SERVICE.record(
            database_path=files["database"],
            acknowledged_payload=acknowledged_payload,
            response_payload=response_payload,
        )


def test_invalid_response_timestamp_is_rejected_by_pa007_type(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    response_payload["responded_at"] = "not-a-timestamp"

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="responded_at must be ISO-8601",
    ):
        SERVICE.record(
            database_path=files["database"],
            acknowledged_payload=acknowledged_payload,
            response_payload=response_payload,
        )


def test_client_response_does_not_create_closeout_or_intervention_authority(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, acknowledged_payload = build_acknowledged_payload(
        tmp_path,
        monkeypatch,
        capsys,
    )

    response_payload = build_client_response_payload(
        acknowledged_payload
    )

    context = build_context(
        acknowledged_payload
    )

    result = SERVICE.record(
        database_path=files["database"],
        acknowledged_payload=acknowledged_payload,
        response_payload=response_payload,
    )

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    closeout = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(closeout) == 0

    serialized = json.dumps(
        result.to_dict()
    )

    assert '"administrative_closeout"' not in serialized
    assert '"intervention_authorized"' not in serialized
    assert '"intervention_executed"' not in serialized
    assert '"remediation_success"' not in serialized
    assert '"roi_verified"' not in serialized
    assert '"customer_outcome"' not in serialized

    assert result.to_dict()["boundaries"][
        "response_is_not_intervention_authorization"
    ] is True

    assert result.to_dict()["boundaries"][
        "response_is_not_customer_outcome"
    ] is True