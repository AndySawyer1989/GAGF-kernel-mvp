from copy import deepcopy

import pytest

from backend.app.gagf.governance_real_paid_assessment_delivery_approval_handoff import (
    GovernanceRealPaidAssessmentDeliveryApprovalHandoffService,
    RealPaidAssessmentDeliveryApprovalHandoffError,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_readiness import (
    GovernanceRealPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    PaidAssessmentDeliveryEnvelopeError,
)
from scripts.run_real_paid_assessment import main as run_operator_main
from tests.test_run_real_paid_assessment import build_operator_files


SERVICE = (
    GovernanceRealPaidAssessmentDeliveryApprovalHandoffService()
)


def build_readiness(
    tmp_path,
    monkeypatch,
    capsys,
):
    import json
    import sys

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

    readiness = (
        GovernanceRealPaidAssessmentDeliveryReadinessService()
        .verify(
            database_path=files["database"],
            operator_payload=operator_payload,
        )
    )

    return files, readiness


def build_approval_payload(readiness):
    execution_result = readiness.execution_result

    return {
        "approval_id": "real-delivery-approval-001",
        "tenant_id": execution_result.tenant_id,
        "client_id": execution_result.client_id,
        "engagement_id": execution_result.engagement_id,
        "assessment_id": execution_result.assessment_id,
        "report_id": execution_result.report_id,
        "approved_by": "Authorized Human Reviewer",
        "approved_at": "2026-08-22T02:30:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }


def test_real_readiness_and_explicit_human_approval_build_pa003_envelope(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)

    database_bytes_before = files["database"].read_bytes()

    result = SERVICE.handoff(
        readiness=readiness,
        approval_payload=approval_payload,
    )

    database_bytes_after = files["database"].read_bytes()

    assert result.handoff_status == "approved_for_human_delivery"
    assert result.hierarchy_key == readiness.hierarchy_key

    assert (
        result.delivery_envelope.delivery_status
        == "approved_for_human_delivery"
    )

    assert (
        result.delivery_envelope.execution_result_hash
        == readiness.execution_result.execution_result_hash
    )

    assert (
        result.delivery_envelope.application_hash
        == readiness.execution_result.application_hash
    )

    assert (
        result.delivery_envelope.report_package_hash
        == readiness.report_package.manifest.package_hash
    )

    assert (
        result.delivery_envelope.report_markdown_hash
        == readiness.report_package.manifest.markdown_hash
    )

    assert (
        result.delivery_envelope.delivery_approval_hash
        == result.delivery_approval.approval_hash
    )

    assert (
        result.delivery_approval.approved_by
        == approval_payload["approved_by"]
    )

    assert (
        result.delivery_approval.approved_at
        == approval_payload["approved_at"]
    )

    assert database_bytes_after == database_bytes_before

    payload = result.to_dict()

    assert payload["approved_for_human_delivery"] is True

    assert payload["boundaries"][
        "readiness_is_not_human_approval"
    ] is True

    assert payload["boundaries"][
        "human_approval_is_not_pa003_envelope"
    ] is True

    assert payload["boundaries"][
        "pa003_remains_delivery_envelope_authority"
    ] is True

    assert payload["boundaries"][
        "approved_for_human_delivery_is_not_delivery"
    ] is True


@pytest.mark.parametrize(
    "field_name",
    [
        "scope_approved",
        "evidence_boundary_approved",
        "buyer_language_approved",
        "delivery_approved",
    ],
)
def test_each_human_approval_flag_must_be_explicitly_true(
    tmp_path,
    monkeypatch,
    capsys,
    field_name,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)
    approval_payload[field_name] = False

    with pytest.raises(
        RealPaidAssessmentDeliveryApprovalHandoffError,
        match=f"{field_name} must be explicitly true",
    ):
        SERVICE.handoff(
            readiness=readiness,
            approval_payload=approval_payload,
        )


def test_missing_human_approval_flag_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)
    del approval_payload["delivery_approved"]

    with pytest.raises(
        RealPaidAssessmentDeliveryApprovalHandoffError,
        match="delivery_approved must be explicitly true",
    ):
        SERVICE.handoff(
            readiness=readiness,
            approval_payload=approval_payload,
        )


def test_human_approval_identity_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)
    approval_payload["assessment_id"] = "wrong-assessment"

    with pytest.raises(
        RealPaidAssessmentDeliveryApprovalHandoffError,
        match="assessment_id does not match verified readiness",
    ):
        SERVICE.handoff(
            readiness=readiness,
            approval_payload=approval_payload,
        )


def test_report_identity_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)
    approval_payload["report_id"] = "wrong-report"

    with pytest.raises(
        RealPaidAssessmentDeliveryApprovalHandoffError,
        match="report_id does not match verified readiness",
    ):
        SERVICE.handoff(
            readiness=readiness,
            approval_payload=approval_payload,
        )


def test_malformed_timestamp_is_rejected_by_existing_pa003_type(
    tmp_path,
    monkeypatch,
    capsys,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)
    approval_payload["approved_at"] = "not-a-timestamp"

    with pytest.raises(
        PaidAssessmentDeliveryEnvelopeError,
        match="approved_at must be ISO-8601",
    ):
        SERVICE.handoff(
            readiness=readiness,
            approval_payload=approval_payload,
        )


def test_non_readiness_input_is_rejected():
    approval_payload = {
        "approval_id": "approval-001",
        "tenant_id": "tenant",
        "client_id": "client",
        "engagement_id": "engagement",
        "assessment_id": "assessment",
        "report_id": "report",
        "approved_by": "Human",
        "approved_at": "2026-08-22T02:30:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }

    with pytest.raises(
        RealPaidAssessmentDeliveryApprovalHandoffError,
        match=(
            "readiness must be a "
            "RealPaidAssessmentDeliveryReadinessResult"
        ),
    ):
        SERVICE.handoff(
            readiness=object(),
            approval_payload=approval_payload,
        )


def test_handoff_does_not_create_delivery_event(
    tmp_path,
    monkeypatch,
    capsys,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)

    result = SERVICE.handoff(
        readiness=readiness,
        approval_payload=approval_payload,
    )

    payload = result.to_dict()

    assert "delivery_event" not in payload
    assert "delivery_event_id" not in payload
    assert "client_receipt" not in payload
    assert "client_acceptance" not in payload


def test_approval_payload_is_not_mutated(
    tmp_path,
    monkeypatch,
    capsys,
):
    _, readiness = build_readiness(
        tmp_path,
        monkeypatch,
        capsys,
    )

    approval_payload = build_approval_payload(readiness)
    original = deepcopy(approval_payload)

    SERVICE.handoff(
        readiness=readiness,
        approval_payload=approval_payload,
    )

    assert approval_payload == original